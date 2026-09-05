from __future__ import annotations

import json
import os

import firebase_admin
from fastapi import Request
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

_app = None


def get_app():
    """Lazily initializes the Firebase Admin SDK. Returns None (rather than
    raising) if FIREBASE_SERVICE_ACCOUNT_JSON isn't set, so the rest of the
    app can keep working without Firebase configured (e.g. local dev)."""
    global _app
    if _app is not None:
        return _app

    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not raw:
        return None

    cred = credentials.Certificate(json.loads(raw))
    _app = firebase_admin.initialize_app(cred)
    return _app


def get_current_user(request: Request) -> str | None:
    """Verified Firebase uid, or None for anonymous/invalid/missing tokens.
    Never raises -- anonymous requests must keep working everywhere this
    is used."""
    app = get_app()
    if app is None:
        return None

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None

    token = header.removeprefix("Bearer ")
    try:
        decoded = firebase_auth.verify_id_token(token, app=app)
        return decoded["uid"]
    except Exception:
        return None


def delete_user(uid: str) -> None:
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    firebase_auth.delete_user(uid, app=app)
