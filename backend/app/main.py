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
    set_admin_flag,
    set_discount_code_active,
    set_user_plan,
)
from .auth import delete_user, get_app, get_current_user
from .detect_bpm import warm_up
from .process_audio import build_zip, validate_files
from .profile_store import delete_settings, get_settings, save_settings
from .rate_limit import enforce_rate_limit

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


@app.patch("/admin/discount-codes/{code}")
def admin_set_discount_code_active(code: str, body: DiscountCodeActiveUpdate, request: Request):
    _require_admin(request)
    try:
        return set_discount_code_active(code, body.active)
    except ValueError as e:
        raise HTTPException(400, str(e))


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
    delete_settings(uid)
    delete_user(uid)
    return {"status": "deleted"}


@app.post("/process")
async def process(request: Request, files: list[UploadFile] = File(...)):
    enforce_rate_limit(request)
    validate_files(files)

    filename_template = None
    deep_search = False
    uid = get_current_user(request)
    if uid is not None:
        try:
            settings = get_settings(uid)
            filename_template = settings.get("filename_template")
            deep_search = bool(settings.get("discogs_deep_search"))
        except Exception:
            filename_template = None  # don't let a profile lookup failure block processing
            deep_search = False

    zip_bytes = await build_zip(files, filename_template=filename_template, deep_search=deep_search)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=crateprep-export.zip"},
    )
