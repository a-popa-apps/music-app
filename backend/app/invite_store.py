from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from firebase_admin import firestore

from .auth import get_app, get_user_by_email

# A rolling 24h cap on user-sent invites, not a calendar-day one -- computed
# from each invite's own sent_at rather than a shared counter, so it can't
# be reset early by, say, sending a batch right before midnight UTC.
MAX_USER_INVITES_PER_DAY = 10

# How long an unredeemed invite link stays valid. Applied lazily (checked
# whenever a token is looked up) rather than via a scheduled sweep -- no
# background job needed, and a stale invite doc sitting around unflipped
# costs nothing until someone actually tries to use it.
INVITE_EXPIRY_DAYS = 30

# If the same person invites the same email again within this window,
# reuse the existing invite (and skip re-sending the email) instead of
# creating a second one -- guards against someone mashing "send" a few
# times in a row, not a hard anti-abuse measure on its own (that's what
# MAX_USER_INVITES_PER_DAY is for).
DUPLICATE_SEND_COOLDOWN_HOURS = 24


class InviteLimitError(Exception):
    """Raised when a user has hit MAX_USER_INVITES_PER_DAY -- callers turn
    this into a 429, same shape as rate_limit.py's own errors."""


def _firestore_client():
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    return firestore.client(app=app)


def _invites_collection():
    return _firestore_client().collection("invites")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _invites_sent_by(uid: str) -> list[dict]:
    """Single-field `where` (auto-indexed, no composite index needed) --
    same pattern as history_store.list_history: filter/sort the rest in
    Python rather than building a compound Firestore query for what's
    always a small, single-user result set."""
    return [doc.to_dict() for doc in _invites_collection().where("invited_by", "==", uid).stream()]


def list_all_invites() -> list[dict]:
    docs = [doc.to_dict() for doc in _invites_collection().stream()]
    docs.sort(key=lambda d: d.get("sent_at") or "", reverse=True)
    return docs


def list_invites_for_uid(uid: str) -> list[dict]:
    docs = _invites_sent_by(uid)
    docs.sort(key=lambda d: d.get("sent_at") or "", reverse=True)
    return docs


def get_invite_by_token(token: str) -> dict | None:
    query = _invites_collection().where("token", "==", token).limit(1).stream()
    doc = next(iter(query), None)
    if doc is None:
        return None
    invite = doc.to_dict()

    if invite["status"] == "pending":
        sent_at = _parse(invite["sent_at"])
        if datetime.now(timezone.utc) - sent_at > timedelta(days=INVITE_EXPIRY_DAYS):
            invite["status"] = "expired"
            _invites_collection().document(invite["invite_id"]).set({"status": "expired"}, merge=True)

    return invite


def create_invite(
    email: str,
    name: str | None,
    source: str,
    invited_by_uid: str,
    invited_by_email: str,
    inviter_label: str,
    admin_note: str | None = None,
) -> dict:
    """Creates (or reuses, see the cooldown check below) an invite record.
    Never sends anything itself -- returns the record and lets the caller
    (main.py) decide whether/how to email it, since that's where the actual
    Resend call and email-template choice already live for every other
    transactional email in this app."""
    normalized_email = email.strip().lower()

    if source == "user":
        if normalized_email == invited_by_email.strip().lower():
            raise ValueError("You can't invite yourself.")

        sent_by_this_user = _invites_sent_by(invited_by_uid)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent = [d for d in sent_by_this_user if _parse(d["sent_at"]) >= cutoff]
        if len(recent) >= MAX_USER_INVITES_PER_DAY:
            raise InviteLimitError(
                f"You can only send {MAX_USER_INVITES_PER_DAY} invites per day. Try again tomorrow."
            )

        dupe_cutoff = datetime.now(timezone.utc) - timedelta(hours=DUPLICATE_SEND_COOLDOWN_HOURS)
        existing = next(
            (
                d
                for d in sent_by_this_user
                if d["email"] == normalized_email
                and d["status"] == "pending"
                and _parse(d["sent_at"]) >= dupe_cutoff
            ),
            None,
        )
        if existing is not None:
            return existing

    # Recorded either way (for auditability -- an admin can see the invite
    # was created and why no email went out) but never actually emailed if
    # the address already has an account: sending "come join CratePrep!" to
    # an existing user is confusing at best, and answering "does this email
    # already have an account" at all is exactly the kind of oracle a
    # forgot-password/signup flow is normally careful not to expose.
    already_has_account = get_user_by_email(normalized_email) is not None

    invite_id = uuid.uuid4().hex
    record = {
        "invite_id": invite_id,
        "email": normalized_email,
        "name": (name or "").strip() or None,
        "source": source,
        "invited_by": invited_by_uid,
        "invited_by_email": invited_by_email,
        "inviter_label": inviter_label,
        "admin_note": (admin_note or "").strip() or None,
        "token": uuid.uuid4().hex,
        "status": "existing_user" if already_has_account else "pending",
        "sent_at": _now_iso(),
        "accepted_at": None,
        "accepted_uid": None,
    }
    _invites_collection().document(invite_id).set(record)
    return record


def revoke_invite(invite_id: str) -> dict:
    doc_ref = _invites_collection().document(invite_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise ValueError("Invite not found.")
    current = doc.to_dict()
    if current["status"] != "pending":
        raise ValueError(f"Can't revoke an invite that's already {current['status']}.")
    doc_ref.set({"status": "revoked"}, merge=True)
    return {**current, "status": "revoked"}


def redeem_invite(token: str, accepted_uid: str) -> dict | None:
    """Marks an invite accepted once the invited person actually completes
    signup -- this (not "email sent") is what makes `status` mean something.
    Only transitions from "pending"; expired/revoked/already-accepted/
    existing_user tokens redeem to nothing, and the caller treats None as a
    silent no-op (matches every other best-effort post-signup call in this
    app, e.g. sendWelcomeEmail)."""
    invite = get_invite_by_token(token)
    if invite is None or invite["status"] != "pending":
        return None

    update = {"status": "accepted", "accepted_at": _now_iso(), "accepted_uid": accepted_uid}
    _invites_collection().document(invite["invite_id"]).set(update, merge=True)
    return {**invite, **update}
