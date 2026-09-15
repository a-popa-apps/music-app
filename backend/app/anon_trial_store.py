from __future__ import annotations

import hashlib

from firebase_admin import firestore

from .auth import get_app

# A one-time trial, not a recurring allowance -- lets an anonymous visitor
# see real value before hitting a signup wall, without giving away the
# actual Free plan (10 tracks/month, requires an account).
ANON_TRIAL_LIMIT = 5


def _firestore_client():
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    return firestore.client(app=app)


def _trials_collection():
    return _firestore_client().collection("anonymous_trials")


def _run_transaction(client, update_fn):
    """Executes update_fn(transaction) as a real Firestore transaction --
    see profile_store._run_transaction for why this matters: without it,
    two concurrent requests from the same IP could both read "under limit"
    before either write landed."""
    transaction = client.transaction()
    return firestore.transactional(update_fn)(transaction)


def _ip_key(ip: str) -> str:
    # Hash rather than store the raw IP -- we only need to recognize repeat
    # visitors, not retain their actual address.
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def check_and_reserve_trial(ip: str, file_count: int) -> None:
    """Enforces the lifetime anonymous-trial cap. Raises ValueError if this
    batch would exceed it; otherwise reserves the capacity by incrementing
    the counter. No period/reset logic -- unlike the Free plan's monthly
    quota, this never rolls over.

    Runs as a Firestore transaction so two concurrent requests from the
    same IP (e.g. two tabs, or two visitors behind the same NAT) can't
    both read "under limit" and both proceed."""
    client = _firestore_client()
    doc_ref = client.collection("anonymous_trials").document(_ip_key(ip))

    def _reserve(transaction):
        snapshot = doc_ref.get(transaction=transaction)
        used = snapshot.to_dict().get("tracks_used", 0) if snapshot.exists else 0

        if used + file_count > ANON_TRIAL_LIMIT:
            remaining = max(0, ANON_TRIAL_LIMIT - used)
            raise ValueError(
                f"Free trial used up ({used}/{ANON_TRIAL_LIMIT} tracks, {remaining} remaining). "
                "Sign up free for 10 tracks/month."
            )

        transaction.set(doc_ref, {"tracks_used": used + file_count}, merge=True)

    _run_transaction(client, _reserve)
