import os

import essentia.standard as es
import mutagen
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

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
from .auth import delete_user, get_app, get_current_user
from .billing import (
    create_billing_portal_session,
    create_checkout_session,
    get_billing_stats,
    handle_webhook_event,
)
from .detect_bpm import warm_up
from .history_store import add_history_entries, clear_history, list_history
from .process_audio import MAX_FILES_FREE, MAX_FILES_PRO, build_zip, validate_files
from .profile_store import check_and_reserve_usage, delete_settings, get_settings, save_settings
from .rate_limit import MAX_REQUESTS_FREE, MAX_REQUESTS_PRO, enforce_rate_limit

app = FastAPI(title="CratePrep Backend")

ALLOWED_ORIGINS = [
    "https://music-app-sage-sigma.vercel.app",
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
def startup():
    warm_up()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "essentia": es.__file__ is not None,
        "mutagen": mutagen.version_string,
        "firebase_configured": get_app() is not None,
        "spotify_configured": bool(
            os.environ.get("SPOTIFY_CLIENT_ID") and os.environ.get("SPOTIFY_CLIENT_SECRET")
        ),
    }


class ProfileUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    artist_name: str | None = None
    role: str | None = None
    primary_genres: list[str] | None = None
    filename_template: str | None = None
    discogs_deep_search: bool | None = None


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


@app.get("/admin/stats")
def admin_stats(request: Request):
    _require_admin(request)
    return get_stats()


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


def _frontend_base_url(request: Request) -> str:
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        return origin
    return ALLOWED_ORIGINS[0]


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
    uid = _require_user(request)

    filename_template = None
    deep_search = False
    plan = "free"
    try:
        settings = get_settings(uid)
        plan = settings.get("plan", "free")
        deep_search = bool(settings.get("discogs_deep_search"))
        if plan == "pro":
            filename_template = settings.get("filename_template")
    except Exception:
        filename_template = None  # don't let a profile lookup failure block processing
        deep_search = False
        plan = "free"

    max_requests = MAX_REQUESTS_PRO if plan == "pro" else MAX_REQUESTS_FREE
    enforce_rate_limit(request, key=uid, max_requests=max_requests)

    max_files = MAX_FILES_PRO if plan == "pro" else MAX_FILES_FREE
    validate_files(files, max_files=max_files)

    try:
        check_and_reserve_usage(uid, len(files), plan)
    except ValueError as e:
        raise HTTPException(402, str(e))

    zip_bytes, manifest = await build_zip(
        files, filename_template=filename_template, deep_search=deep_search
    )
    try:
        add_history_entries(uid, manifest)
    except Exception:
        pass  # don't let a history-write failure block returning the processed zip

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=crateprep-export.zip"},
    )
