from __future__ import annotations

import gc
import io
import json
import zipfile

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from .audio_io import SAMPLE_RATE, load_audio
from .clean_filename import compose_name, guess_split, local_dash_split, prepare_stem
from .detect_bpm import detect_bpm
from .detect_genre import detect_genre, lookup_track
from .detect_key import detect_key
from .playlist import build_playlist
from .read_tags import read_embedded_tags
from .write_tags import write_tags

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".ogg", ".aac"}
MAX_FILES = 50
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB per file
MAX_TOTAL_SIZE = 2 * 1024 * 1024 * 1024  # 2GB per upload


def validate_files(files: list[UploadFile]) -> None:
    if len(files) == 0:
        raise HTTPException(400, "No files uploaded.")

    if len(files) > MAX_FILES:
        raise HTTPException(
            400, f"Too many files ({len(files)}). Max: {MAX_FILES} per upload."
        )

    total_size = 0
    for file in files:
        name = file.filename or ""
        ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                400,
                f"'{name}' is not a supported audio format. "
                f"Try: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
            )

        if file.size is not None:
            if file.size > MAX_FILE_SIZE:
                size_mb = file.size / (1024**2)
                raise HTTPException(
                    400,
                    f"'{name}' is too large ({size_mb:.0f}MB). Max: 100MB per file.",
                )
            total_size += file.size

    if total_size > MAX_TOTAL_SIZE:
        total_gb = total_size / (1024**3)
        raise HTTPException(
            400,
            f"Upload is too large ({total_gb:.1f}GB total). Max: 2GB per upload.",
        )


def _resolve_artist_title_genre(
    stem: str, deep_search: bool = False, embedded_tags: dict | None = None
) -> tuple[str | None, str | None, str | None, dict]:
    """Embedded file tags first, if the file already carries a usable
    artist/title (most reliable -- no guessing needed); else local dash
    split; else search Spotify/Discogs using the raw stem so a real catalog
    match beats guessing; else a best-effort word-count guess as a last
    resort."""
    debug: dict = {}

    if embedded_tags:
        artist, title = embedded_tags["artist"], embedded_tags["title"]
        genre = embedded_tags["genre"] or detect_genre(artist, title, deep_search=deep_search)
        debug["name_source"] = "embedded_tags"
        return artist, title, genre, debug

    split = local_dash_split(stem)
    if split:
        artist, title = split
        genre = detect_genre(artist, title, deep_search=deep_search)
        return artist, title, genre, debug

    match = lookup_track(stem)
    if match:
        debug["name_source"] = "catalog_match"
        return match["artist"], match["title"], match["genre"], debug

    split = guess_split(stem)
    if split:
        artist, title = split
        debug["name_source"] = "guessed"
        genre = detect_genre(artist, title, deep_search=deep_search)
        return artist, title, genre, debug

    return None, None, None, debug


def _analyze_and_tag(
    content: bytes,
    ext: str,
    stem: str,
    version_tag: str | None,
    filename_template: str | None = None,
    deep_search: bool = False,
) -> tuple[bytes, dict, str]:
    embedded_tags = read_embedded_tags(content, ext)
    artist, title, genre, name_debug = _resolve_artist_title_genre(
        stem, deep_search, embedded_tags=embedded_tags
    )
    if embedded_tags and not version_tag:
        version_tag = embedded_tags["version_tag"]

    try:
        audio = load_audio(content, ext)
    except Exception as e:
        entry = {
            "bpm": None,
            "key": None,
            "genre": genre,
            "load_error": f"{type(e).__name__}: {e}",
            **name_debug,
        }
        final_name = compose_name(artist, title, stem, version_tag, ext)
        return content, entry, final_name

    entry: dict = {"duration_seconds": round(len(audio) / SAMPLE_RATE, 2), **name_debug}
    bpm = None
    camelot = None

    try:
        bpm = detect_bpm(audio)
        entry["bpm"] = bpm
    except Exception as e:
        entry["bpm"] = None
        entry["bpm_error"] = f"{type(e).__name__}: {e}"

    try:
        key_result = detect_key(audio)
        entry.update(key_result)
        camelot = key_result["camelot"]
    except Exception as e:
        entry["key"] = None
        entry["key_error"] = f"{type(e).__name__}: {e}"

    del audio
    entry["genre"] = genre

    final_name = compose_name(
        artist,
        title,
        stem,
        version_tag,
        ext,
        filename_template=filename_template,
        bpm=bpm,
        key=camelot,
        genre=genre,
        duration=entry["duration_seconds"],
    )

    try:
        tagged_content = write_tags(content, ext, bpm=bpm, camelot=camelot, genre=genre)
    except Exception as e:
        tagged_content = content
        entry["tag_error"] = f"{type(e).__name__}: {e}"

    return tagged_content, entry, final_name


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


async def build_zip(
    files: list[UploadFile],
    filename_template: str | None = None,
    deep_search: bool = False,
) -> bytes:
    buffer = io.BytesIO()
    manifest = {}
    seen_names: set[str] = set()
    playlist_tracks: list[tuple[str, float | None]] = []

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            original_name = file.filename or "track"

            try:
                stem, ext, version_tag = prepare_stem(original_name)
                content = await file.read()
            except Exception as e:
                manifest[original_name] = {
                    "error": f"Failed to read file: {type(e).__name__}: {e}"
                }
                continue

            try:
                tagged_content, entry, resolved_name = await run_in_threadpool(
                    _analyze_and_tag,
                    content,
                    ext,
                    stem,
                    version_tag,
                    filename_template,
                    deep_search,
                )
            except Exception as e:
                # One file misbehaving shouldn't lose the rest of the batch --
                # fall back to including it unprocessed, with the error noted.
                tagged_content, resolved_name = content, original_name
                entry = {"error": f"Processing failed: {type(e).__name__}: {e}"}

            name = _dedupe(resolved_name, seen_names)
            zip_file.writestr(name, tagged_content)

            entry["original_filename"] = original_name
            manifest[name] = entry
            playlist_tracks.append((name, entry.get("duration_seconds")))
            gc.collect()

        zip_file.writestr("crateprep-manifest.json", json.dumps(manifest, indent=2))
        zip_file.writestr("crateprep-playlist.m3u8", build_playlist(playlist_tracks))

    buffer.seek(0)
    return buffer.read()
