import io
import zipfile

from fastapi import HTTPException, UploadFile

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


async def build_zip(files: list[UploadFile]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            content = await file.read()
            zip_file.writestr(file.filename or "track", content)

    buffer.seek(0)
    return buffer.read()
