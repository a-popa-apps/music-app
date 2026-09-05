import essentia.standard as es
import mutagen
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from .auth import delete_user, get_app, get_current_user
from .detect_bpm import warm_up
from .process_audio import build_zip, validate_files
from .profile_store import delete_settings, get_settings, save_settings
from .rate_limit import enforce_rate_limit

app = FastAPI(title="Quickie Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the Vercel domain once it's live
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
    uid = get_current_user(request)
    if uid is not None:
        try:
            filename_template = get_settings(uid).get("filename_template")
        except Exception:
            filename_template = None  # don't let a profile lookup failure block processing

    zip_bytes = await build_zip(files, filename_template=filename_template)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=quickie-export.zip"},
    )
