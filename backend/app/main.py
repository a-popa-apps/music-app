import essentia.standard as es
import mutagen
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .detect_bpm import warm_up
from .process_audio import build_zip, validate_files

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
    }


@app.post("/process")
async def process(files: list[UploadFile] = File(...)):
    validate_files(files)
    zip_bytes = await build_zip(files)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=quickie-export.zip"},
    )
