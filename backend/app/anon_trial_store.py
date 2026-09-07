from __future__ import annotations

import hashlib

from firebase_admin import firestore

from .auth import get_app

# A one-time trial, not a recurring allowance -- lets an anonymous visitor
# see real value before hitting a signup wall, without giving away the
# actual Free plan (25 tracks/month, requires an account).
ANON_TRIAL_LIMIT = 5


def _trials_collection():
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    return firestore.client(app=app).collection("anonymous_trials")


def _ip_key(ip: str) -> str:
    # Hash rather than store the raw IP -- we only need to recognize repeat
    # visitors, not retain their actual address.
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def check_and_reserve_trial(ip: str, file_count: int) -> None:
    """Enforces the lifetime anonymous-trial cap. Raises ValueError if this
    batch would exceed it; otherwise reserves the capacity by incrementing
    the counter. No period/reset logic -- unlike the Free plan's monthly
    quota, this never rolls over."""
    doc_ref = _trials_collection().document(_ip_key(ip))
    doc = doc_ref.get()
    used = doc.to_dict().get("tracks_used", 0) if doc.exists else 0

    if used + file_count > ANON_TRIAL_LIMIT:
        remaining = max(0, ANON_TRIAL_LIMIT - used)
        raise ValueError(
            f"Free trial used up ({used}/{ANON_TRIAL_LIMIT} tracks, {remaining} remaining). "
            "Sign up free for 25 tracks/month."
        )

    doc_ref.set({"tracks_used": used + file_count}, merge=True)
