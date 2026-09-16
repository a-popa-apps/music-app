import json
import os
import time
from datetime import datetime, timezone

import essentia.standard as es
import mutagen
import sentry_sdk
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from . import ai_budget
from .admin_store import (
    create_discount_code,
    delete_user_account,
    get_stats,
    list_discount_codes,
    list_users,
    reset_usage,
    set_admin_flag,
    set_discount_code_active,
    set_user_plan,
)
from .analysis_process_pool import ensure_started
from .anon_trial_store import ANON_TRIAL_LIMIT, check_and_reserve_trial
from .auth import (
    delete_user,
    generate_password_reset_link,
    generate_verification_link,
    get_app,
    get_current_user,
    get_user_by_email,
    get_user_record,
)
from .billing import (
    create_billing_portal_session,
    create_checkout_session,
    get_billing_stats,
    handle_webhook_event,
)
from .email_service import notify_admins, send_email
from .email_templates import (
    invite_email_html,
    new_feedback_email_html,
    password_changed_email_html,
    password_reset_email_html,
    usage_limit_warning_email_html,
    verification_email_html,
    welcome_email_html,
)
from .feedback_store import (
    create_feedback,
    delete_feedback,
    delete_feedback_batch,
    list_feedback,
    mark_feedback_read,
)
from .feedback_summary import generate_feedback_summary
from .history_store import add_history_entries, clear_history, list_history
from .invite_store import (
    InviteLimitError,
    create_invite,
    get_invite_by_token,
    list_all_invites,
    list_invites_for_uid,
    redeem_invite,
    revoke_invite,
)
from .process_audio import (
    MAX_FILES_FREE,
    MAX_FILES_PRO,
    PROCESS_CONCURRENCY,
    build_corrected_zip,
    build_zip,
    validate_files,
)
from .profile_store import (
    FREE_MONTHLY_TRACK_LIMIT,
    check_and_reserve_usage,
    delete_settings,
    get_settings,
    mark_welcome_email_sent,
    save_settings,
)
from .rate_limit import MAX_REQUESTS_FREE, MAX_REQUESTS_PRO, _client_ip, enforce_rate_limit

# Optional -- no-op if SENTRY_DSN isn't set, same pattern as every other
# integration in this codebase (Firebase, Spotify, Gemini). Reports
# unhandled exceptions from the FastAPI app so a silent 500 in production
# actually surfaces somewhere instead of just failing a request unnoticed.
if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=0.0,
    )

app = FastAPI(title="CratePrep Backend")

ALLOWED_ORIGINS = [
    "https://crateprep.app",
    "https://www.crateprep.app",
    "https://music-app-sage-sigma.vercel.app",  # old domain, still aliased on Vercel
    "http://localhost:5173",  # vite dev server
    "http://localhost:4173",  # vite preview server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # Analysis now runs in isolated worker processes (see
    # analysis_process_pool.py), not in this process, so warming up
    # essentia here would just be wasted work -- this instead starts the
    # actual worker pool and waits for every worker to warm up, so the
    # first real upload after a deploy doesn't pay that cold-start cost.
    await ensure_started(PROCESS_CONCURRENCY)


@app.get("/health")
def health():
    # Public and unauthenticated (uptime monitors hit this) -- deliberately
    # bare. Which third-party integrations are configured, AI usage/limits,
    # etc. used to live here too, but that's operational detail an anonymous
    # caller has no business reading; it's on the admin-only /admin/stats
    # instead.
    return {
        "status": "ok",
        "essentia": es.__file__ is not None,
        "mutagen": mutagen.version_string,
        "firebase_configured": get_app() is not None,
    }


class ProfileUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    artist_name: str | None = None
    role: str | None = None
    primary_genres: list[str] | None = None
    filename_template: str | None = None
    discogs_deep_search: bool | None = None
    enhanced_detection: bool | None = None
    ai_filename_cleanup: bool | None = None
    auto_sort_by_energy: bool | None = None


def _require_user(request: Request) -> str:
    uid = get_current_user(request)
    if uid is None:
        raise HTTPException(401, "Sign in required.")
    return uid


def _require_admin(request: Request) -> str:
    uid = _require_user(request)
    if not get_settings(uid).get("is_admin"):
        raise HTTPException(403, "Admin access required.")
    return uid


class PlanUpdate(BaseModel):
    plan: str


class AdminFlagUpdate(BaseModel):
    is_admin: bool


class DiscountCodeCreate(BaseModel):
    percent_off: int
    max_uses: int = 1


class DiscountCodeActiveUpdate(BaseModel):
    active: bool


@app.get("/admin/users")
def admin_list_users(request: Request):
    _require_admin(request)
    return list_users()


@app.put("/admin/users/{uid}/plan")
def admin_set_plan(uid: str, update: PlanUpdate, request: Request):
    _require_admin(request)
    try:
        return set_user_plan(uid, update.plan)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.put("/admin/users/{uid}/admin")
def admin_set_admin_flag(uid: str, update: AdminFlagUpdate, request: Request):
    _require_admin(request)
    return set_admin_flag(uid, update.is_admin)


@app.delete("/admin/users/{uid}")
def admin_delete_user(uid: str, request: Request):
    _require_admin(request)
    delete_user_account(uid)
    return {"status": "deleted"}


@app.post("/admin/users/{uid}/reset-usage")
def admin_reset_usage(uid: str, request: Request):
    _require_admin(request)
    return reset_usage(uid)


@app.get("/admin/users/{uid}/profile")
def admin_read_user_profile(uid: str, request: Request):
    _require_admin(request)
    return get_settings(uid)


@app.put("/admin/users/{uid}/profile")
def admin_update_user_profile(uid: str, update: ProfileUpdate, request: Request):
    _require_admin(request)
    payload = {k: v for k, v in update.model_dump().items() if v is not None}
    try:
        return save_settings(uid, payload)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/admin/users/{uid}/history")
def admin_read_user_history(uid: str, request: Request):
    _require_admin(request)
    return list_history(uid)


@app.get("/admin/stats")
def admin_stats(request: Request):
    _require_admin(request)
    return {
        **get_stats(),
        # Which integrations are configured -- moved off the public /health
        # endpoint, which had no business handing this to an anonymous caller.
        "spotify_configured": bool(
            os.environ.get("SPOTIFY_CLIENT_ID") and os.environ.get("SPOTIFY_CLIENT_SECRET")
        ),
        "ai_cleanup_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "sentry_configured": bool(os.environ.get("SENTRY_DSN")),
        "email_configured": bool(os.environ.get("RESEND_API_KEY")),
        "stripe_configured": bool(
            os.environ.get("STRIPE_SECRET_KEY")
            and os.environ.get("STRIPE_WEBHOOK_SECRET")
            and os.environ.get("STRIPE_PRICE_MONTHLY")
            and os.environ.get("STRIPE_PRICE_ANNUAL")
        ),
    }


@app.get("/admin/billing-stats")
def admin_billing_stats(request: Request):
    _require_admin(request)
    try:
        return get_billing_stats()
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.get("/admin/discount-codes")
def admin_list_discount_codes(request: Request):
    _require_admin(request)
    return list_discount_codes()


@app.post("/admin/discount-codes")
def admin_create_discount_code(body: DiscountCodeCreate, request: Request):
    uid = _require_admin(request)
    try:
        return create_discount_code(body.percent_off, uid, max_uses=body.max_uses)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        # Surface Stripe API errors (invalid params, rate limits, etc.)
        # instead of a bare 500 with no detail.
        raise HTTPException(502, f"Stripe error: {type(e).__name__}: {e}")


@app.patch("/admin/discount-codes/{code}")
def admin_set_discount_code_active(code: str, body: DiscountCodeActiveUpdate, request: Request):
    _require_admin(request)
    try:
        return set_discount_code_active(code, body.active)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Stripe error: {type(e).__name__}: {e}")


class AdminInviteCreate(BaseModel):
    email: str
    name: str | None = None
    admin_note: str | None = None


class UserInviteCreate(BaseModel):
    email: str
    name: str | None = None


class InviteRevoke(BaseModel):
    status: str


def _send_invite_email(request: Request, invite: dict) -> None:
    if invite["status"] != "pending":
        # "existing_user" (recipient already has an account) or a reused
        # pending invite from the duplicate-send cooldown -- either way,
        # nothing new to email.
        return
    invite_url = f"{_frontend_base_url(request)}/auth?invite={invite['token']}"
    send_email(
        invite["email"],
        f"{invite['inviter_label']} invited you to CratePrep",
        invite_email_html(invite["name"], invite["inviter_label"], invite_url, invite.get("admin_note")),
    )


@app.get("/admin/invites")
def admin_list_invites(request: Request):
    _require_admin(request)
    return list_all_invites()


@app.post("/admin/invites")
def admin_create_invite(body: AdminInviteCreate, request: Request):
    uid = _require_admin(request)
    admin_record = get_user_record(uid)
    admin_email = admin_record.email if admin_record and admin_record.email else uid
    try:
        invite = create_invite(
            body.email,
            body.name,
            source="admin",
            invited_by_uid=uid,
            invited_by_email=admin_email,
            inviter_label="The CratePrep team",
            admin_note=body.admin_note,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    _send_invite_email(request, invite)
    return invite


@app.patch("/admin/invites/{invite_id}")
def admin_revoke_invite(invite_id: str, body: InviteRevoke, request: Request):
    _require_admin(request)
    if body.status != "revoked":
        raise HTTPException(400, "Only revoking a pending invite is supported.")
    try:
        return revoke_invite(invite_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/invites/mine")
def read_my_invites(request: Request):
    uid = _require_user(request)
    return list_invites_for_uid(uid)


@app.post("/invites")
def send_invite(body: UserInviteCreate, request: Request):
    uid = _require_user(request)
    user = get_user_record(uid)
    if user is None or not user.email:
        raise HTTPException(400, "Your account has no email on file.")

    settings = get_settings(uid)
    inviter_label = settings.get("name") or user.email

    try:
        invite = create_invite(
            body.email,
            body.name,
            source="user",
            invited_by_uid=uid,
            invited_by_email=user.email,
            inviter_label=inviter_label,
        )
    except InviteLimitError as e:
        raise HTTPException(429, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    _send_invite_email(request, invite)
    return invite


@app.get("/invites/{token}")
def read_invite(token: str):
    """Public and unauthenticated by design -- looked up from the signup
    page (AuthPage, via the ?invite= link) before the visitor has any
    account at all. Returns just enough to prefill the signup form and show
    "so-and-so invited you" -- never the invite's internal id, status
    history, or who else has been invited."""
    invite = get_invite_by_token(token)
    if invite is None or invite["status"] != "pending":
        return {"valid": False}
    return {"valid": True, "email": invite["email"], "name": invite["name"], "inviter_label": invite["inviter_label"]}


@app.post("/invites/{token}/redeem")
def redeem_invite_route(token: str, request: Request):
    """Best-effort, called right after a new account finishes signing up on
    AuthPage when an invite token was present -- same "never block or alarm
    the user" spirit as sendWelcomeEmail/notifyPasswordChanged. Requires the
    newly-created account's own token, so this can only ever mark an invite
    accepted by the account that actually signed up, never an arbitrary
    uid."""
    uid = _require_user(request)
    redeem_invite(token, uid)
    return {"ok": True}


class FeedbackReadUpdate(BaseModel):
    read: bool


@app.get("/admin/feedback")
def admin_list_feedback(request: Request):
    _require_admin(request)
    return list_feedback()


@app.patch("/admin/feedback/{feedback_id}")
def admin_mark_feedback_read(feedback_id: str, body: FeedbackReadUpdate, request: Request):
    _require_admin(request)
    try:
        return mark_feedback_read(feedback_id, body.read)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.delete("/admin/feedback/{feedback_id}")
def admin_delete_feedback(feedback_id: str, request: Request):
    _require_admin(request)
    try:
        delete_feedback(feedback_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"deleted": True}


class FeedbackBulkDelete(BaseModel):
    feedback_ids: list[str]


@app.post("/admin/feedback/bulk-delete")
def admin_bulk_delete_feedback(body: FeedbackBulkDelete, request: Request):
    _require_admin(request)
    delete_feedback_batch(body.feedback_ids)
    return {"deleted": len(body.feedback_ids)}


@app.post("/admin/feedback/summarize")
def admin_summarize_feedback(request: Request):
    _require_admin(request)
    unread = [f for f in list_feedback() if not f.get("read")]
    return {"summary": generate_feedback_summary(unread)}


def _frontend_base_url(request: Request) -> str:
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        return origin
    return ALLOWED_ORIGINS[0]


@app.post("/auth/send-verification-email")
def send_verification_email(request: Request):
    """Sends CratePrep's own branded verification email instead of relying
    on Firebase's default one -- same account only (the caller's own uid),
    since there's no reason this endpoint should ever email someone else."""
    uid = _require_user(request)
    enforce_rate_limit(request, key=uid, max_requests=MAX_REQUESTS_FREE)

    user = get_user_record(uid)
    if user is None or user.email_verified:
        return {"sent": False}

    link = generate_verification_link(user.email, f"{_frontend_base_url(request)}/auth/action")
    if link is None:
        return {"sent": False}

    sent = send_email(user.email, "Verify your email for CratePrep", verification_email_html(link))
    return {"sent": sent}


class ForgotPasswordRequest(BaseModel):
    email: str


@app.post("/auth/forgot-password")
def forgot_password(body: ForgotPasswordRequest, request: Request):
    """Unauthenticated by nature (the whole point is the caller is locked
    out) -- rate-limited by IP, and always returns the same response
    whether or not the email is registered, so this can't be used to probe
    which emails have CratePrep accounts."""
    enforce_rate_limit(request, max_requests=MAX_REQUESTS_FREE)

    link = generate_password_reset_link(body.email, f"{_frontend_base_url(request)}/auth/action")
    if link is not None:
        send_email(body.email, "Reset your CratePrep password", password_reset_email_html(link))

    return {"sent": True}


class WelcomeEmailRequest(BaseModel):
    email: str


@app.post("/auth/welcome-email")
def send_welcome_email(body: WelcomeEmailRequest, request: Request):
    """Public and unauthenticated by nature -- called right after a user
    completes email verification via the Firebase client SDK on
    AuthActionPage, which happens before they're necessarily signed in on
    this device/browser. Rate-limited by IP; a no-op unless the given email
    belongs to an actually-verified account that hasn't received this email
    yet, so it can't be used to spam arbitrary or unverified addresses, or
    to re-send the same user a welcome email over and over."""
    enforce_rate_limit(request, max_requests=MAX_REQUESTS_FREE)

    user = get_user_by_email(body.email)
    if user is None or not user.email_verified:
        return {"sent": False}

    if get_settings(user.uid).get("welcome_email_sent"):
        return {"sent": False}

    sent = send_email(user.email, "Welcome to CratePrep!", welcome_email_html(_frontend_base_url(request)))
    if sent:
        mark_welcome_email_sent(user.uid)
    return {"sent": sent}


class PasswordChangedRequest(BaseModel):
    email: str


@app.post("/auth/password-changed-notice")
def password_changed_notice(body: PasswordChangedRequest, request: Request):
    """Public and unauthenticated by nature -- called by AuthActionPage
    right after a password reset succeeds via the Firebase client SDK,
    which the backend has no direct visibility into. Same exposure as
    /auth/forgot-password: rate-limited by IP, no stronger proof a reset
    just happened, and always returns the same response either way. A
    false positive here is a mildly annoying email, not a security hole --
    same bar the app already accepts for forgot-password."""
    enforce_rate_limit(request, max_requests=MAX_REQUESTS_FREE)

    user = get_user_by_email(body.email)
    if user is not None:
        send_email(
            user.email,
            "Your CratePrep password was changed",
            password_changed_email_html(f"{_frontend_base_url(request)}/auth"),
        )

    return {"sent": True}


class CheckoutRequest(BaseModel):
    billing_cycle: str


@app.post("/billing/checkout")
def billing_checkout(body: CheckoutRequest, request: Request):
    uid = _require_user(request)
    base = _frontend_base_url(request)
    try:
        url = create_checkout_session(
            uid,
            body.billing_cycle,
            success_url=f"{base}/profile?checkout=success",
            cancel_url=f"{base}/profile?checkout=cancelled",
        )
        return {"url": url}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.post("/billing/portal")
def billing_portal(request: Request):
    uid = _require_user(request)
    base = _frontend_base_url(request)
    try:
        url = create_billing_portal_session(uid, return_url=f"{base}/profile")
        return {"url": url}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        handle_webhook_event(payload, sig_header)
    except Exception as e:
        raise HTTPException(400, f"Webhook error: {e}")
    return {"status": "ok"}


class FeedbackCreate(BaseModel):
    category: str
    message: str
    email: str | None = None
    subject: str | None = None
    # Anti-spam, both optional and never surfaced to the user as validation
    # errors -- a bot that gets an error message just learns to adapt.
    website: str | None = None  # honeypot: real users never see or fill this
    form_rendered_at: float | None = None  # JS epoch-ms when the form appeared


MIN_FEEDBACK_SUBMIT_SECONDS = 2


@app.post("/feedback")
def submit_feedback(body: FeedbackCreate, request: Request):
    # Public -- works for logged-out visitors, so this can't require auth.
    # Still IP-rate-limited to bound spam (enforce_rate_limit falls back to
    # the client's IP when no key is given, same as any other unauthed use).
    enforce_rate_limit(request)
    uid = get_current_user(request)  # opportunistic -- None for anonymous

    filled_honeypot = bool(body.website)
    submitted_too_fast = (
        body.form_rendered_at is not None
        and (time.time() * 1000 - body.form_rendered_at) < MIN_FEEDBACK_SUBMIT_SECONDS * 1000
    )
    if filled_honeypot or submitted_too_fast:
        # Silently discard rather than erroring -- an error response teaches
        # a bot what tripped it and invites it to adapt. Return a normal-
        # looking success instead, without actually persisting anything.
        return {
            "feedback_id": "discarded",
            "category": body.category,
            "subject": body.subject,
            "message": body.message,
            "email": body.email,
            "uid": uid,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
        }

    try:
        doc = create_feedback(
            body.category, body.message, email=body.email, subject=body.subject, uid=uid
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    admin_url = f"{_frontend_base_url(request)}/admin"
    html = new_feedback_email_html(body.category, body.subject, body.message, body.email, admin_url)
    notify_admins(f"New CratePrep {body.category}", html)

    return doc


@app.get("/profile")
def read_profile(request: Request):
    uid = _require_user(request)
    return get_settings(uid)


@app.put("/profile")
def update_profile(update: ProfileUpdate, request: Request):
    uid = _require_user(request)
    payload = {k: v for k, v in update.model_dump().items() if v is not None}
    try:
        return save_settings(uid, payload)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.delete("/profile")
def delete_account(request: Request):
    uid = _require_user(request)
    clear_history(uid)
    delete_settings(uid)
    delete_user(uid)
    return {"status": "deleted"}


@app.get("/history")
def read_history(request: Request):
    uid = _require_user(request)
    return list_history(uid)


@app.delete("/history")
def delete_history(request: Request):
    uid = _require_user(request)
    clear_history(uid)
    return {"status": "cleared"}


@app.post("/process")
async def process(request: Request, files: list[UploadFile] = File(...)):
    uid = get_current_user(request)

    if uid is None:
        # No-signup trial: up to ANON_TRIAL_LIMIT tracks, once, ever -- lets
        # a visitor see real value before hitting a signup wall, without
        # giving away the actual Free plan (10/month, requires an account).
        enforce_rate_limit(request)
        validate_files(files, max_files=ANON_TRIAL_LIMIT)
        try:
            check_and_reserve_trial(_client_ip(request), len(files))
        except ValueError as e:
            raise HTTPException(402, str(e))

        zip_path, _manifest = await build_zip(files)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=crateprep-export.zip"},
            background=BackgroundTask(os.remove, zip_path),
        )

    filename_template = None
    deep_search = False
    enhanced_detection = False
    ai_cleanup = False
    plan = "free"
    settings = None
    try:
        settings = get_settings(uid)
        plan = settings.get("plan", "free")
        deep_search = bool(settings.get("discogs_deep_search"))
        if plan == "pro":
            filename_template = settings.get("filename_template")
            # Double-gated: only ever honored for Pro, regardless of what's
            # stored, the same trust model filename_template already uses.
            enhanced_detection = bool(settings.get("enhanced_detection"))
            ai_cleanup = bool(settings.get("ai_filename_cleanup"))
    except Exception:
        filename_template = None  # don't let a profile lookup failure block processing
        deep_search = False
        enhanced_detection = False
        ai_cleanup = False
        plan = "free"
        settings = None

    max_requests = MAX_REQUESTS_PRO if plan == "pro" else MAX_REQUESTS_FREE
    enforce_rate_limit(request, key=uid, max_requests=max_requests)

    max_files = MAX_FILES_PRO if plan == "pro" else MAX_FILES_FREE
    validate_files(files, max_files=max_files)

    try:
        # Reads the usage counter fresh inside a Firestore transaction
        # rather than reusing the `settings` fetched above -- two
        # concurrent requests both reading "under limit" before either
        # write lands would otherwise let combined usage exceed the quota.
        tracks_used, should_warn_usage = check_and_reserve_usage(uid, len(files), plan)
    except ValueError as e:
        raise HTTPException(402, str(e))

    if should_warn_usage:
        user = get_user_record(uid)
        if user and user.email:
            send_email(
                user.email,
                "You're close to your CratePrep Free plan limit",
                usage_limit_warning_email_html(
                    tracks_used, FREE_MONTHLY_TRACK_LIMIT, f"{_frontend_base_url(request)}/pricing"
                ),
            )

    zip_path, manifest = await build_zip(
        files,
        filename_template=filename_template,
        deep_search=deep_search,
        enhanced_detection=enhanced_detection,
        ai_cleanup=ai_cleanup,
    )
    try:
        # Firestore calls are synchronous network I/O -- run off the event
        # loop so one user's history write can't stall every other
        # concurrent request on this single-instance backend.
        await run_in_threadpool(add_history_entries, uid, manifest)
    except Exception:
        pass  # don't let a history-write failure block returning the processed zip

    return FileResponse(
        zip_path,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=crateprep-export.zip"},
        background=BackgroundTask(os.remove, zip_path),
    )


@app.post("/process/retag")
async def retag_process(
    request: Request,
    files: list[UploadFile] = File(...),
    corrections: str = Form(...),
):
    """Re-tags an already-processed batch with corrected artist/title/
    genre/BPM/key from the results table, without spending any more of
    the caller's monthly quota -- these are files they already processed
    once with /process; this only fixes what gets written into them.
    `corrections` is a JSON-encoded list, one entry per file, same order
    as `files`."""
    uid = get_current_user(request)

    filename_template = None
    plan = "free"
    if uid:
        try:
            settings = get_settings(uid)
            plan = settings.get("plan", "free")
            if plan == "pro":
                filename_template = settings.get("filename_template")
        except Exception:
            plan = "free"
            filename_template = None

    max_requests = MAX_REQUESTS_PRO if plan == "pro" else MAX_REQUESTS_FREE
    enforce_rate_limit(request, key=uid, max_requests=max_requests)

    max_files = MAX_FILES_PRO if plan == "pro" else MAX_FILES_FREE
    validate_files(files, max_files=max_files)

    try:
        corrections_data = json.loads(corrections)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(400, "Invalid corrections payload.")

    if not isinstance(corrections_data, list) or len(corrections_data) != len(files):
        raise HTTPException(400, "corrections must be a list with one entry per file.")

    zip_path = await build_corrected_zip(files, corrections_data, filename_template=filename_template)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=crateprep-export.zip"},
        background=BackgroundTask(os.remove, zip_path),
    )
