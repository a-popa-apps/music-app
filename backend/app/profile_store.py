from __future__ import annotations

from datetime import datetime, timezone

from firebase_admin import firestore

from .auth import get_app

FREE_MONTHLY_TRACK_LIMIT = 10

# 80% of the monthly limit -- a heads-up before someone hits the wall
# outright, with enough runway left to actually act on it.
USAGE_WARNING_THRESHOLD = round(FREE_MONTHLY_TRACK_LIMIT * 0.8)

VALID_ROLES = {"dj", "producer", "dj_producer", "enthusiast"}
VALID_GENRES = {
    "Electronic music",
    "Hip-Hop / R&B",
    "Urban",
    "Latin",
    "Open Format / Multi-genre",
    "Other",
}

DEFAULT_SETTINGS = {
    "name": "",
    "country": "",
    "artist_name": "",
    "role": None,
    "primary_genres": [],
    "filename_template": None,
    "discogs_deep_search": False,
    "enhanced_detection": False,
    "ai_filename_cleanup": False,
    "auto_sort_by_energy": False,
    "plan": "free",
    "is_admin": False,
    "stripe_customer_id": None,
    "stripe_subscription_id": None,
    "subscription_status": None,
    "tracks_processed_this_period": 0,
    "usage_period_start": None,
    "welcome_email_sent": False,
    "usage_warning_period": None,
}

# Not user-editable via the regular PUT /profile endpoint -- "plan" and the
# stripe_*/subscription_status fields are only ever written by the billing
# webhook (billing.py) or admin endpoints, "is_admin" only by the admin-only
# endpoints in main.py, and the usage fields only by check_and_reserve_usage
# below -- so a user can never self-promote, forge their own subscription
# state, or reset their own usage counter.
READ_ONLY_FIELDS = {
    "plan",
    "is_admin",
    "stripe_customer_id",
    "stripe_subscription_id",
    "subscription_status",
    "tracks_processed_this_period",
    "usage_period_start",
    "welcome_email_sent",
    "usage_warning_period",
}


def _users_collection():
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    return firestore.client(app=app).collection("users")


def get_settings(uid: str) -> dict:
    doc = _users_collection().document(uid).get()
    if not doc.exists:
        return dict(DEFAULT_SETTINGS)
    return {**DEFAULT_SETTINGS, **doc.to_dict()}


def save_settings(uid: str, settings: dict) -> dict:
    role = settings.get("role")
    if role is not None and role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role!r}")

    genres = settings.get("primary_genres", [])
    if len(genres) > 3:
        raise ValueError("Max 3 primary genres")
    if any(g not in VALID_GENRES for g in genres):
        raise ValueError(f"Invalid genre in: {genres!r}")

    update = {
        k: v for k, v in settings.items() if k in DEFAULT_SETTINGS and k not in READ_ONLY_FIELDS
    }
    _users_collection().document(uid).set(update, merge=True)
    return get_settings(uid)


def delete_settings(uid: str) -> None:
    _users_collection().document(uid).delete()


def mark_welcome_email_sent(uid: str) -> None:
    _users_collection().document(uid).set({"welcome_email_sent": True}, merge=True)


def _current_period_key() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


def check_and_reserve_usage(
    uid: str, file_count: int, plan: str, settings: dict | None = None
) -> tuple[int, bool]:
    """Enforces the Free plan's monthly track quota. Pro is unlimited here
    (still bounded by the per-batch MAX_FILES_PRO cap elsewhere). Raises
    ValueError if this batch would exceed the quota; otherwise reserves the
    capacity by incrementing the counter, resetting it first if the
    calendar month has rolled over since the last reserved batch.

    Returns (tracks_used_after_this_batch, should_send_usage_warning) --
    should_send_usage_warning is True the first time usage reaches
    USAGE_WARNING_THRESHOLD within a billing period (never True twice for
    the same period). Pro always returns (0, False).

    Pass `settings` when the caller already fetched this user's settings
    (e.g. /process already needs plan/filename_template from it) to avoid
    reading the same document twice in one request; fetches its own
    otherwise."""
    if plan == "pro":
        return 0, False

    settings = settings if settings is not None else get_settings(uid)
    period = _current_period_key()
    used = settings["tracks_processed_this_period"] if settings["usage_period_start"] == period else 0
    new_used = used + file_count

    if new_used > FREE_MONTHLY_TRACK_LIMIT:
        raise ValueError(
            f"Monthly Free plan limit reached ({used}/{FREE_MONTHLY_TRACK_LIMIT} tracks used). "
            "Upgrade to Pro for more."
        )

    warning_already_sent = settings.get("usage_warning_period") == period
    should_warn = new_used >= USAGE_WARNING_THRESHOLD and not warning_already_sent

    update = {"tracks_processed_this_period": new_used, "usage_period_start": period}
    if should_warn:
        update["usage_warning_period"] = period
    _users_collection().document(uid).set(update, merge=True)

    return new_used, should_warn
