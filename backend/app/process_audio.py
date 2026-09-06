from __future__ import annotations

import asyncio
import gc
import io
import json
import os
import zipfile

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from .audio_io import SAMPLE_RATE, load_audio
from .clean_filename import compose_name, guess_split, local_dash_split, prepare_stem
from .detect_bpm import detect_bpm
from .detect_energy import detect_energy
from .detect_genre import detect_genre, lookup_track
from .detect_key import detect_key
from .playlist import build_playlist
from .read_tags import read_embedded_tags
from .write_tags import write_tags

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".ogg", ".aac"}
MAX_FILES_FREE = 25
MAX_FILES_PRO = 50
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB per file
MAX_TOTAL_SIZE = 2 * 1024 * 1024 * 1024  # 2GB per upload

# Files in a batch are independent, so analyzing them concurrently instead of
# one at a time is a real speedup -- both the essentia decode/BPM/key work
# (releases the GIL, benefits from multiple cores) and the Spotify/Discogs
# genre lookups (I/O-bound, mostly just waiting on the network) parallelize
# well. Kept conservative and tunable rather than guessing high: each
# concurrent slot holds a full decoded audio array in memory (roughly 50MB
# for a 5-minute track) plus essentia's own working memory, and the actual
# Render plan's RAM headroom isn't known -- raise via the env var once real
# memory behavior has been observed live, not preemptively.
PROCESS_CONCURRENCY = int(os.environ.get("PROCESS_CONCURRENCY", "3"))


def validate_files(files: list[UploadFile], max_files: int = MAX_FILES_FREE) -> None:
    if len(files) == 0:
        raise HTTPException(400, "No files uploaded.")

    if len(files) > max_files:
        raise HTTPException(
            400, f"Too many files ({len(files)}). Max: {max_files} per upload."
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

    try:
        entry["energy"] = detect_energy(audio)
    except Exception as e:
        entry["energy"] = None
        entry["energy_error"] = f"{type(e).__name__}: {e}"

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


async def _analyze_one(
    semaphore: asyncio.Semaphore,
    content: bytes,
    ext: str,
    stem: str,
    version_tag: str | None,
    original_name: str,
    filename_template: str | None,
    deep_search: bool,
) -> tuple[bytes, dict, str]:
    async with semaphore:
        try:
            return await run_in_threadpool(
                _analyze_and_tag, content, ext, stem, version_tag, filename_template, deep_search
            )
        except Exception as e:
            # One file misbehaving shouldn't lose the rest of the batch --
            # fall back to including it unprocessed, with the error noted.
            return content, {"error": f"Processing failed: {type(e).__name__}: {e}"}, original_name
        finally:
            gc.collect()


async def build_zip(
    files: list[UploadFile],
    filename_template: str | None = None,
    deep_search: bool = False,
) -> tuple[bytes, dict]:
    buffer = io.BytesIO()
    manifest = {}
    seen_names: set[str] = set()
    playlist_tracks: list[tuple[str, float | None]] = []

    # Phase 1: read every upload sequentially -- this is Starlette's async
    # file I/O tied to each UploadFile, cheap, and not worth parallelizing.
    reads: list[tuple[str, dict | None]] = []
    for file in files:
        original_name = file.filename or "track"
        try:
            stem, ext, version_tag = prepare_stem(original_name)
            content = await file.read()
            reads.append(
                (original_name, {"stem": stem, "ext": ext, "version_tag": version_tag, "content": content})
            )
        except Exception as e:
            reads.append((original_name, {"error": f"Failed to read file: {type(e).__name__}: {e}"}))

    # Phase 2: analyze the successfully-read files concurrently (bounded by
    # PROCESS_CONCURRENCY) -- this is the expensive, genuinely independent
    # part (decode + BPM/key detection + optional genre network lookup).
    semaphore = asyncio.Semaphore(PROCESS_CONCURRENCY)
    results = await asyncio.gather(
        *(
            _analyze_one(
                semaphore,
                data["content"],
                data["ext"],
                data["stem"],
                data["version_tag"],
                original_name,
                filename_template,
                deep_search,
            )
            for original_name, data in reads
            if "error" not in data
        )
    )
    results_iter = iter(results)

    # Phase 3: write the zip/manifest/playlist sequentially, in original
    # upload order, from the already-computed results -- dedup and the zip
    # file itself stay single-threaded, so nothing here needs a lock.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for original_name, data in reads:
            if "error" in data:
                manifest[original_name] = data
                continue

            tagged_content, entry, resolved_name = next(results_iter)
            name = _dedupe(resolved_name, seen_names)
            zip_file.writestr(name, tagged_content)

            entry["original_filename"] = original_name
            manifest[name] = entry
            playlist_tracks.append((name, entry.get("duration_seconds")))

        zip_file.writestr("crateprep-manifest.json", json.dumps(manifest, indent=2))
        zip_file.writestr("crateprep-playlist.m3u8", build_playlist(playlist_tracks))

    buffer.seek(0)
    return buffer.read(), manifest
