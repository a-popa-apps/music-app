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
        # check_revoked=True so a token issued before an account was banned/
        # deleted stops working immediately instead of surviving until its
        # own (up to ~1hr) natural expiry -- costs one extra Firebase lookup
        # per request, worth it for admin bans to actually take effect.
        decoded = firebase_auth.verify_id_token(token, app=app, check_revoked=True)
        return decoded["uid"]
    except Exception:
        return None


def delete_user(uid: str) -> None:
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    firebase_auth.delete_user(uid, app=app)


def get_user_record(uid: str) -> firebase_auth.UserRecord | None:
    app = get_app()
    if app is None:
        return None
    try:
        return firebase_auth.get_user(uid, app=app)
    except firebase_auth.UserNotFoundError:
        return None


def _action_code_settings(continue_url: str) -> firebase_auth.ActionCodeSettings:
    # handle_code_in_app=True makes the generated link point directly at
    # continue_url with mode/oobCode as query params, instead of at
    # Firebase's own hosted action page -- AuthActionPage.tsx already reads
    # mode/oobCode itself and calls the client SDK to complete the action,
    # so this is required for that page to ever receive them.
    return firebase_auth.ActionCodeSettings(url=continue_url, handle_code_in_app=True)


def generate_verification_link(email: str, continue_url: str) -> str | None:
    """None if Firebase isn't configured. Doesn't send anything itself --
    just mints the one-time link; the caller decides how to deliver it."""
    app = get_app()
    if app is None:
        return None
    return firebase_auth.generate_email_verification_link(
        email, action_code_settings=_action_code_settings(continue_url), app=app
    )


def generate_password_reset_link(email: str, continue_url: str) -> str | None:
    """None if Firebase isn't configured *or* no account has this email --
    the two look identical to the caller on purpose, so a public "forgot
    password" endpoint built on this can't be used to enumerate which
    emails are registered."""
    app = get_app()
    if app is None:
        return None
    try:
        return firebase_auth.generate_password_reset_link(
            email, action_code_settings=_action_code_settings(continue_url), app=app
        )
    except firebase_auth.UserNotFoundError:
        return None
