import gc
import io
import json
import zipfile

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from .audio_io import load_audio
from .clean_filename import clean_filename
from .detect_bpm import detect_bpm
from .detect_key import detect_key

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".ogg", ".aac"}
MAX_FILES = 25
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB per file


def validate_files(files: list[UploadFile]) -> None:
    if len(files) == 0:
        raise HTTPException(400, "No files uploaded.")

    if len(files) > MAX_FILES:
        raise HTTPException(
            400, f"Too many files ({len(files)}). Max: {MAX_FILES} per upload."
        )

    for file in files:
        name = file.filename or ""
        ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                400,
                f"'{name}' has an unsupported format. "
                f"Try: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
            )

        if file.size is not None and file.size > MAX_FILE_SIZE:
            size_gb = file.size / (1024**3)
            raise HTTPException(
                400,
                f"'{name}' is too large ({size_gb:.1f}GB). Max: 2GB per file.",
            )


def _analyze(content: bytes, suffix: str) -> dict:
    try:
        audio = load_audio(content, suffix)
    except Exception as e:
        return {"bpm": None, "key": None, "load_error": f"{type(e).__name__}: {e}"}

    entry: dict = {}
    try:
        entry["bpm"] = detect_bpm(audio)
    except Exception as e:
        entry["bpm"] = None
        entry["bpm_error"] = f"{type(e).__name__}: {e}"

    try:
        entry.update(detect_key(audio))
    except Exception as e:
        entry["key"] = None
        entry["key_error"] = f"{type(e).__name__}: {e}"

    del audio
    return entry


def _dedupe(name: str, seen: set[str]) -> str:
    if name not in seen:
        seen.add(name)
        return name

    stem, ext = (name.rsplit(".", 1) + [""])[:2]
    ext = f".{ext}" if ext else ""
    counter = 2
    while (candidate := f"{stem} ({counter}){ext}") in seen:
        counter += 1
    seen.add(candidate)
    return candidate


async def build_zip(files: list[UploadFile]) -> bytes:
    buffer = io.BytesIO()
    manifest = {}
    seen_names: set[str] = set()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            original_name = file.filename or "track"
            name = _dedupe(clean_filename(original_name), seen_names)
            suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
            content = await file.read()
            zip_file.writestr(name, content)

            entry = await run_in_threadpool(_analyze, content, suffix)
            entry["original_filename"] = original_name
            manifest[name] = entry
            gc.collect()

        zip_file.writestr("quickie-manifest.json", json.dumps(manifest, indent=2))

    buffer.seek(0)
    return buffer.read()
