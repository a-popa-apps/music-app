from __future__ import annotations

from firebase_admin import firestore

from .auth import get_app

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
    "plan": "free",
    "is_admin": False,
}

# Not user-editable via the regular PUT /profile endpoint -- "plan" has no
# billing flow yet, and "is_admin" is only ever set via the admin-only
# endpoints in main.py so a user can never self-promote.
READ_ONLY_FIELDS = {"plan", "is_admin"}


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
