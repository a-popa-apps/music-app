from __future__ import annotations

import asyncio
import gc
import io
import json
import os
import re
import zipfile

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from .ai_cleanup import ai_split_artist_title
from .audio_io import get_duration_seconds, load_audio
from .batch_summary import generate_batch_summary
from .clean_filename import compose_name, guess_split, local_dash_split, prepare_stem
from .detect_bpm import ANALYSIS_SECONDS, detect_bpm
from .detect_energy import detect_energy
from .detect_genre import detect_genre, fetch_artwork, lookup_track
from .detect_key import detect_key
from .playlist import build_playlist
from .read_tags import read_embedded_tags
from .write_tags import write_tags

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".ogg", ".aac"}
MAX_FILES_FREE = 10
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


def _normalized_artist(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _resolve_artist_title_genre(
    stem: str,
    deep_search: bool = False,
    embedded_tags: dict | None = None,
    ai_cleanup: bool = False,
) -> tuple[str | None, str | None, str | None, dict]:
    """Embedded file tags first, if the file already carries a usable
    artist/title (most reliable -- no guessing needed) *and* doesn't
    contradict an explicit "Artist - Title" filename. A filename already in
    that form is a deliberate, unambiguous signal, so if its artist
    disagrees with the tag's artist (a mistagged file -- tags copied from
    the wrong track, a bad auto-tagger, a re-rip that kept stale metadata)
    the filename wins instead of silently propagating the wrong tag. Else
    local dash split; else search Spotify/Discogs using the raw stem so a
    real catalog match beats guessing; else, if enabled, an LLM split
    (smarter than the word-count guess for filenames with no separator and
    no catalog match); else a best-effort word-count guess as the final
    fallback."""
    debug: dict = {}

    dash_split = local_dash_split(stem)
    tag_conflicts_with_filename = bool(
        embedded_tags
        and dash_split
        and _normalized_artist(dash_split[0]) != _normalized_artist(embedded_tags["artist"])
    )

    if embedded_tags and not tag_conflicts_with_filename:
        artist, title = embedded_tags["artist"], embedded_tags["title"]
        if embedded_tags["genre"]:
            genre = embedded_tags["genre"]
        else:
            lookup = detect_genre(artist, title, deep_search=deep_search)
            genre = lookup["genre"]
            debug["artwork_url"] = lookup["artwork_url"]
        debug["name_source"] = "embedded_tags"
        return artist, title, genre, debug

    if dash_split:
        artist, title = dash_split
        lookup = detect_genre(artist, title, deep_search=deep_search)
        debug["name_source"] = "local_dash_split"
        debug["artwork_url"] = lookup["artwork_url"]
        return artist, title, lookup["genre"], debug

    match = lookup_track(stem)
    if match:
        debug["name_source"] = "catalog_match"
        debug["artwork_url"] = match.get("artwork_url")
        return match["artist"], match["title"], match["genre"], debug

    if ai_cleanup:
        split = ai_split_artist_title(stem)
        if split:
            artist, title = split
            lookup = detect_genre(artist, title, deep_search=deep_search)
            debug["name_source"] = "ai_cleanup"
            debug["artwork_url"] = lookup["artwork_url"]
            return artist, title, lookup["genre"], debug

    split = guess_split(stem)
    if split:
        artist, title = split
        debug["name_source"] = "guessed"
        lookup = detect_genre(artist, title, deep_search=deep_search)
        debug["artwork_url"] = lookup["artwork_url"]
        return artist, title, lookup["genre"], debug

    return None, None, None, debug


def _analyze_and_tag(
    content: bytes,
    ext: str,
    stem: str,
    version_tag: str | None,
    filename_template: str | None = None,
    deep_search: bool = False,
    enhanced_detection: bool = False,
    ai_cleanup: bool = False,
) -> tuple[bytes, dict, str]:
    embedded_tags = read_embedded_tags(content, ext)
    artist, title, genre, name_debug = _resolve_artist_title_genre(
        stem, deep_search, embedded_tags=embedded_tags, ai_cleanup=ai_cleanup
    )
    # Internal-only -- used below to fetch and embed cover art, not meant
    # for the manifest/results table, so it doesn't ride along in name_debug.
    artwork_url = name_debug.pop("artwork_url", None)
    if embedded_tags and not version_tag:
        version_tag = embedded_tags["version_tag"]

    try:
        # Free/default mode only ever analyzes the first ANALYSIS_SECONDS
        # (BPM, key, energy all already fast-path to a short window) --
        # decoding just that slice instead of the whole track is the
        # single biggest speed win available, since decode cost scales
        # with track length. "Enhanced Detection" (Pro) still needs the
        # full track for its full-track BPM pass and low-confidence key
        # retry, so it decodes everything as before.
        audio = load_audio(
            content, ext, max_seconds=None if enhanced_detection else ANALYSIS_SECONDS
        )
    except Exception as e:
        entry = {
            "bpm": None,
            "key": None,
            "genre": genre,
            "artist": artist,
            "title": title,
            "load_error": f"{type(e).__name__}: {e}",
            **name_debug,
        }
        final_name = compose_name(artist, title, stem, version_tag, ext)
        return content, entry, final_name

    entry: dict = {
        # From the file's own header, not len(audio)/SAMPLE_RATE -- audio
        # may only be a truncated window above, but the track's real
        # duration (shown in the UI, written into the playlist) must not be.
        "duration_seconds": get_duration_seconds(content, ext),
        "artist": artist,
        "title": title,
        **name_debug,
    }
    bpm = None
    camelot = None
    tonality = None

    try:
        bpm = detect_bpm(audio, full_track=enhanced_detection)
        entry["bpm"] = bpm
    except Exception as e:
        entry["bpm"] = None
        entry["bpm_error"] = f"{type(e).__name__}: {e}"

    try:
        key_result = detect_key(audio, enhanced=enhanced_detection)
        entry.update(key_result)
        camelot = key_result["camelot"]
        tonality = key_result["tonality"]
    except Exception as e:
        entry["key"] = None
        entry["key_error"] = f"{type(e).__name__}: {e}"

    try:
        entry["energy"] = detect_energy(audio, full_track=enhanced_detection)
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

    artwork = fetch_artwork(artwork_url)

    try:
        tagged_content = write_tags(
            content,
            ext,
            bpm=bpm,
            key_tag=tonality,
            genre=genre,
            artist=artist,
            title=title,
            artwork=artwork[0] if artwork else None,
            artwork_mime=artwork[1] if artwork else "image/jpeg",
        )
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
    content: bytes,
    ext: str,
    stem: str,
    version_tag: str | None,
    original_name: str,
    filename_template: str | None,
    deep_search: bool,
    enhanced_detection: bool,
    ai_cleanup: bool,
) -> tuple[bytes, dict, str]:
    try:
        return await run_in_threadpool(
            _analyze_and_tag,
            content,
            ext,
            stem,
            version_tag,
            filename_template,
            deep_search,
            enhanced_detection,
            ai_cleanup,
        )
    except Exception as e:
        # One file misbehaving shouldn't lose the rest of the batch --
        # fall back to including it unprocessed, with the error noted.
        return content, {"error": f"Processing failed: {type(e).__name__}: {e}"}, original_name
    finally:
        gc.collect()


async def build_corrected_zip(
    files: list[UploadFile],
    corrections: list[dict],
    filename_template: str | None = None,
) -> bytes:
    """Re-tags an already-processed batch with user-supplied final values
    instead of running detection again -- used when someone corrects a
    wrong artist/title/genre/BPM in the results table before downloading.
    `corrections` is positional (one dict per file, same order as
    `files`), each with the same shape as a manifest entry from
    build_zip: artist/title/genre/bpm/camelot/tonality/energy/
    duration_seconds -- callers should pass through every field for a
    track even if only correcting one of them, or the others silently
    disappear from the result (energy has no detection fallback here,
    unlike build_zip). No usage-quota check here -- these are files the
    caller already spent their quota processing once; this only fixes
    what gets written. One file's failure doesn't lose the rest of the
    batch, mirroring build_zip's own resilience."""
    buffer = io.BytesIO()
    seen_names: set[str] = set()
    playlist_tracks: list[tuple[str, float | None]] = []
    manifest = {}

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file, correction in zip(files, corrections):
            original_name = file.filename or "track"
            try:
                content = await file.read()
                stem, ext, version_tag = prepare_stem(original_name)

                artist = correction.get("artist")
                title = correction.get("title")
                genre = correction.get("genre")
                bpm = correction.get("bpm")
                camelot = correction.get("camelot")
                tonality = correction.get("tonality")
                energy = correction.get("energy")
                duration = correction.get("duration_seconds")

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
                    duration=duration,
                )
                name = _dedupe(final_name, seen_names)

                try:
                    tagged_content = write_tags(
                        content, ext, bpm=bpm, key_tag=tonality, genre=genre, artist=artist, title=title
                    )
                except Exception:
                    tagged_content = content

                zip_file.writestr(name, tagged_content)
                manifest[name] = {
                    "artist": artist,
                    "title": title,
                    "genre": genre,
                    "bpm": bpm,
                    "camelot": camelot,
                    "tonality": tonality,
                    "energy": energy,
                    "duration_seconds": duration,
                    "original_filename": original_name,
                }
                playlist_tracks.append((name, duration))
            except Exception as e:
                name = _dedupe(original_name, seen_names)
                manifest[name] = {
                    "error": f"Re-tagging failed: {type(e).__name__}: {e}",
                    "original_filename": original_name,
                }

        zip_file.writestr("crateprep-manifest.json", json.dumps(manifest, indent=2))
        zip_file.writestr("crateprep-playlist.m3u8", build_playlist(playlist_tracks))

    buffer.seek(0)
    return buffer.read()


async def build_zip(
    files: list[UploadFile],
    filename_template: str | None = None,
    deep_search: bool = False,
    enhanced_detection: bool = False,
    ai_cleanup: bool = False,
) -> tuple[bytes, dict]:
    buffer = io.BytesIO()
    manifest = {}
    seen_names: set[str] = set()
    playlist_tracks: list[tuple[str, float | None]] = []

    # Processed in fixed-size chunks (PROCESS_CONCURRENCY files at a time)
    # rather than reading and analyzing the whole batch before writing
    # anything -- that used to hold every file's raw bytes *and* every
    # file's already-tagged bytes in memory simultaneously (on top of the
    # growing zip buffer below) before the first byte was written out, so
    # peak memory scaled with the size of the batch instead of with how
    # many files are actually being worked on at once. A 50-track lossless
    # batch could need gigabytes just for that; a chunk of
    # PROCESS_CONCURRENCY files needs only a small, constant amount
    # regardless of total batch size, while still analyzing that many
    # files concurrently for throughput.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for chunk_start in range(0, len(files), PROCESS_CONCURRENCY):
            chunk = files[chunk_start : chunk_start + PROCESS_CONCURRENCY]

            reads: list[tuple[str, dict | None]] = []
            for file in chunk:
                original_name = file.filename or "track"
                try:
                    stem, ext, version_tag = prepare_stem(original_name)
                    content = await file.read()
                    reads.append(
                        (
                            original_name,
                            {"stem": stem, "ext": ext, "version_tag": version_tag, "content": content},
                        )
                    )
                except Exception as e:
                    reads.append((original_name, {"error": f"Failed to read file: {type(e).__name__}: {e}"}))

            results = await asyncio.gather(
                *(
                    _analyze_one(
                        data["content"],
                        data["ext"],
                        data["stem"],
                        data["version_tag"],
                        original_name,
                        filename_template,
                        deep_search,
                        enhanced_detection,
                        ai_cleanup,
                    )
                    for original_name, data in reads
                    if "error" not in data
                )
            )
            results_iter = iter(results)

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

        # One call for the whole batch, not per track -- cheap regardless of
        # batch size, so this runs for every user, free or Pro. Off the event
        # loop: this is a blocking HTTP call to Gemini (up to a 15s timeout)
        # and would otherwise stall every other concurrent request.
        summary = await run_in_threadpool(generate_batch_summary, manifest)
        if summary:
            zip_file.writestr("crateprep-summary.json", json.dumps({"summary": summary}))

    buffer.seek(0)
    return buffer.read(), manifest
