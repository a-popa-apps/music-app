from __future__ import annotations

import secrets
import string

from firebase_admin import auth as firebase_auth
from firebase_admin import firestore

from .auth import get_app
from .profile_store import _users_collection, delete_settings, get_settings

VALID_PLANS = {"free", "pro"}
VALID_PERCENTS = {25, 50, 75, 100}


def list_users() -> list[dict]:
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")

    users = []
    for record in firebase_auth.list_users(app=app).iterate_all():
        settings = get_settings(record.uid)
        users.append(
            {
                "uid": record.uid,
                "email": record.email,
                "disabled": record.disabled,
                "created_at": record.user_metadata.creation_timestamp,
                "name": settings["name"],
                "artist_name": settings["artist_name"],
                "plan": settings["plan"],
                "is_admin": settings["is_admin"],
            }
        )
    return users


def set_user_plan(uid: str, plan: str) -> dict:
    if plan not in VALID_PLANS:
        raise ValueError(f"Invalid plan: {plan!r}")
    _users_collection().document(uid).set({"plan": plan}, merge=True)
    return get_settings(uid)


def set_admin_flag(uid: str, is_admin: bool) -> dict:
    _users_collection().document(uid).set({"is_admin": bool(is_admin)}, merge=True)
    return get_settings(uid)


def reset_usage(uid: str) -> dict:
    _users_collection().document(uid).set(
        {"tracks_processed_this_period": 0, "usage_period_start": None}, merge=True
    )
    return get_settings(uid)


def delete_user_account(uid: str) -> None:
    delete_settings(uid)
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    firebase_auth.delete_user(uid, app=app)


def get_stats() -> dict:
    users = list_users()
    by_plan: dict[str, int] = {}
    for u in users:
        by_plan[u["plan"]] = by_plan.get(u["plan"], 0) + 1

    recent = sorted(users, key=lambda u: u["created_at"] or 0, reverse=True)[:10]

    return {
        "total_users": len(users),
        "by_plan": by_plan,
        "admin_count": sum(1 for u in users if u["is_admin"]),
        "recent_signups": recent,
    }


def _discount_codes_collection():
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    return firestore.client(app=app).collection("discount_codes")


def _generate_code(percent_off: int) -> str:
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"SAVE{percent_off}-{suffix}"


def create_discount_code(percent_off: int, uid: str, max_uses: int = 1) -> dict:
    if percent_off not in VALID_PERCENTS:
        raise ValueError(f"Invalid percent_off: {percent_off!r}")
    if max_uses < 1:
        raise ValueError("max_uses must be at least 1")

    code = _generate_code(percent_off)
    ref = _discount_codes_collection().document(code)
    ref.set(
        {
            "code": code,
            "percent_off": percent_off,
            "active": True,
            "max_uses": max_uses,
            "used_count": 0,
            "created_by": uid,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return ref.get().to_dict()


def list_discount_codes() -> list[dict]:
    return [doc.to_dict() for doc in _discount_codes_collection().stream()]


def set_discount_code_active(code: str, active: bool) -> dict:
    ref = _discount_codes_collection().document(code)
    if not ref.get().exists:
        raise ValueError(f"No such discount code: {code!r}")
    ref.set({"active": bool(active)}, merge=True)
    return ref.get().to_dict()
