from __future__ import annotations

import asyncio
import gc
import json
import logging
import os
import re
import tempfile
import zipfile

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from .ai_cleanup import ai_split_artist_title
from .analysis_cache import content_hash, get_exact_match, store_exact_match
from .analysis_process_pool import run_isolated
from .audio_io import NEEDS_BROWSER_PREVIEW, get_duration_seconds, load_audio, make_preview_wav
from .batch_summary import generate_batch_summary
from .clean_filename import compose_name, guess_split, local_dash_split, prepare_stem
from .detect_bpm import ANALYSIS_SECONDS, detect_bpm
from .detect_energy import detect_energy
from .detect_genre import detect_genre, fetch_artwork, lookup_track
from .detect_key import detect_key
from .playlist import build_playlist
from .preview_cache import get_cached_preview, store_preview
from .read_tags import read_embedded_tags
from .write_tags import write_tags

logger = logging.getLogger(__name__)

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


def _capitalize_first(text: str | None) -> str | None:
    # Only the first character -- filenames/catalog matches routinely come
    # back all-lowercase (a ripped-from-filename guess, a lowercase tag),
    # but forcing every word to title case would also mangle deliberate
    # stylization elsewhere in the string (DJ Q-Bert, will.i.am's later
    # letters, etc.), which this doesn't touch.
    return text[0].upper() + text[1:] if text else text


async def _resolve_artist_title_genre(
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
            lookup = await detect_genre(artist, title, deep_search=deep_search)
            genre = lookup["genre"]
            debug["artwork_url"] = lookup["artwork_url"]
        debug["name_source"] = "embedded_tags"
        return artist, title, genre, debug

    if dash_split:
        artist, title = dash_split
        lookup = await detect_genre(artist, title, deep_search=deep_search)
        debug["name_source"] = "local_dash_split"
        debug["artwork_url"] = lookup["artwork_url"]
        return artist, title, lookup["genre"], debug

    match = await lookup_track(stem)
    if match:
        debug["name_source"] = "catalog_match"
        debug["artwork_url"] = match.get("artwork_url")
        return match["artist"], match["title"], match["genre"], debug

    if ai_cleanup:
        split = ai_split_artist_title(stem)
        if split:
            artist, title = split
            lookup = await detect_genre(artist, title, deep_search=deep_search)
            debug["name_source"] = "ai_cleanup"
            debug["artwork_url"] = lookup["artwork_url"]
            return artist, title, lookup["genre"], debug

    split = guess_split(stem)
    if split:
        artist, title = split
        debug["name_source"] = "guessed"
        lookup = await detect_genre(artist, title, deep_search=deep_search)
        debug["artwork_url"] = lookup["artwork_url"]
        return artist, title, lookup["genre"], debug

    return None, None, None, debug


def _run_essentia_analysis(content: bytes, ext: str, enhanced_detection: bool, needs_preview: bool) -> dict:
    """BPM/key/energy analysis, plus (if needs_preview) the browser-preview
    WAV generation -- the only parts of this pipeline that touch essentia/
    ffmpeg's native code, which is why this one function (not the whole
    analyze-and-tag pipeline) is what runs in an isolated worker process
    (see analysis_process_pool.py): a crash here would otherwise take the
    whole server down, but tag-writing below is pure Python/mutagen and has
    no such risk. Bundled into one call, not two, so `content` -- which can
    be tens of MB -- only crosses the process boundary once per file, not
    once per isolated step. Returns a plain dict; the only large value in
    it is `preview_content` when present, which is unavoidable -- it's the
    actual audio data a browser will play."""
    try:
        # Free/default mode only ever analyzes the first ANALYSIS_SECONDS
        # (BPM, key, energy all already fast-path to a short window) --
        # decoding just that slice instead of the whole track is the
        # single biggest speed win available, since decode cost scales
        # with track length. "Enhanced Detection" (Pro) still needs the
        # full track for its full-track BPM pass and low-confidence key
        # retry, so it decodes everything as before.
        audio = load_audio(content, ext, max_seconds=None if enhanced_detection else ANALYSIS_SECONDS)
    except Exception as e:
        result = {"bpm": None, "key": None, "load_error": f"{type(e).__name__}: {e}"}
    else:
        result = {}

        try:
            result["bpm"] = detect_bpm(
                audio,
                full_track=enhanced_detection,
                # Lets detect_bpm retry against the full track (only if its
                # fast windowed read comes back low-confidence) without
                # paying for a full decode upfront -- enhanced_detection
                # already decoded the full track above, so there's nothing
                # to retry with there.
                full_audio_loader=(
                    None if enhanced_detection else lambda: load_audio(content, ext, max_seconds=None)
                ),
            )
        except Exception as e:
            result["bpm"] = None
            result["bpm_error"] = f"{type(e).__name__}: {e}"

        try:
            result.update(detect_key(audio, enhanced=enhanced_detection))
        except Exception as e:
            result["key"] = None
            result["key_error"] = f"{type(e).__name__}: {e}"

        try:
            result["energy"] = detect_energy(audio, full_track=enhanced_detection)
        except Exception as e:
            result["energy"] = None
            result["energy_error"] = f"{type(e).__name__}: {e}"

    if needs_preview:
        try:
            result["preview_content"] = make_preview_wav(content, ext)
        except Exception as e:
            result["preview_error"] = f"{type(e).__name__}: {e}"

    return result


def _run_preview_only(content: bytes, ext: str) -> dict:
    """Just the browser-preview WAV generation, for an exact-match cache
    hit -- BPM/key/energy are already known, but the preview is never
    cached (it would need blob storage, not Firestore, for files this
    size), so it still needs regenerating from the real bytes."""
    try:
        return {"preview_content": make_preview_wav(content, ext)}
    except Exception as e:
        return {"preview_error": f"{type(e).__name__}: {e}"}


async def _analyze_and_tag(
    content: bytes,
    ext: str,
    stem: str,
    version_tag: str | None,
    filename_template: str | None = None,
    deep_search: bool = False,
    enhanced_detection: bool = False,
    ai_cleanup: bool = False,
) -> tuple[bytes, dict, str, bytes | None]:
    embedded_tags = read_embedded_tags(content, ext)
    if embedded_tags and not version_tag:
        version_tag = embedded_tags["version_tag"]

    # A file with these exact bytes (anyone's upload, not just this user's)
    # has already been fully analyzed before -- reuse that result and skip
    # both the essentia decode/analysis and the genre catalog lookups, the
    # two genuinely expensive steps. Exact-match only: this never risks
    # reusing a subtly-wrong BPM/key from a different rip of the "same"
    # song (see detect_genre's own cache for that case instead, which only
    # shares genre/artwork -- safe across different rips -- never BPM/key).
    file_hash = content_hash(content)
    cached = get_exact_match(file_hash)

    needs_preview = ext in NEEDS_BROWSER_PREVIEW
    preview_content: bytes | None = None

    if cached:
        # WARNING level purely so this shows up in Render's default log
        # filtering without needing a logging-config change -- this is a
        # confirmation line, not an actual problem.
        logger.warning(
            "CACHE HIT (exact) [%s]: %s - %s, bpm=%s",
            file_hash[:12],
            cached.get("artist"),
            cached.get("title"),
            cached.get("bpm"),
        )
        entry: dict = {
            # _capitalize_first here too, not just on the cache-miss path --
            # an entry cached before this fix shipped can still have a
            # lowercase artist/title, and there's no cache expiry to
            # otherwise correct it.
            "duration_seconds": get_duration_seconds(content, ext),
            "artist": _capitalize_first(cached.get("artist")),
            "title": _capitalize_first(cached.get("title")),
            "name_source": cached.get("name_source"),
            "bpm": cached.get("bpm"),
            "key": cached.get("key"),
            "camelot": cached.get("camelot"),
            "tonality": cached.get("tonality"),
            "energy": cached.get("energy"),
            "genre": cached.get("genre"),
        }
        artist, title, genre = entry["artist"], entry["title"], entry["genre"]
        bpm, camelot, tonality = entry["bpm"], entry["camelot"], entry["tonality"]
        artwork_url = cached.get("artwork_url")

        if needs_preview:
            # The exact-match cache above only ever covers BPM/key/energy/
            # genre -- it never skips this, since a preview is regenerated
            # from scratch (full decode + ffmpeg re-encode) on every request
            # regardless of that cache. This local-disk cache is what
            # actually makes a same-file retry (e.g. re-uploading a batch
            # right after a crash) fast for AIFF files, which otherwise pay
            # this full cost again even on an exact-match hit.
            preview_content = get_cached_preview(file_hash)
            if preview_content is None:
                preview_result = await run_isolated(PROCESS_CONCURRENCY, _run_preview_only, content, ext)
                preview_content = preview_result.get("preview_content")
                if "preview_error" in preview_result:
                    entry["preview_error"] = preview_result["preview_error"]
                elif preview_content is not None:
                    store_preview(file_hash, preview_content)
    else:
        artist, title, genre, name_debug = await _resolve_artist_title_genre(
            stem, deep_search, embedded_tags=embedded_tags, ai_cleanup=ai_cleanup
        )
        artist, title = _capitalize_first(artist), _capitalize_first(title)
        # Internal-only -- used below to fetch and embed cover art, not
        # meant for the manifest/results table, so it doesn't ride along
        # in name_debug.
        artwork_url = name_debug.pop("artwork_url", None)

        # Analysis and preview generation are bundled into one isolated
        # call (see _run_essentia_analysis) rather than two, so `content`
        # -- which can be tens of MB -- only crosses the process boundary
        # once here, not once per essentia-touching step.
        analysis = await run_isolated(
            PROCESS_CONCURRENCY, _run_essentia_analysis, content, ext, enhanced_detection, needs_preview
        )

        if "load_error" in analysis:
            entry = {
                "bpm": None,
                "key": None,
                "genre": genre,
                "artist": artist,
                "title": title,
                "load_error": analysis["load_error"],
                **name_debug,
            }
            final_name = compose_name(artist, title, stem, version_tag, ext)
            return content, entry, final_name, None

        preview_content = analysis.pop("preview_content", None)
        preview_error = analysis.pop("preview_error", None)

        entry = {
            # From the file's own header, not len(audio)/SAMPLE_RATE -- audio
            # may only be a truncated window above, but the track's real
            # duration (shown in the UI, written into the playlist) must not be.
            "duration_seconds": get_duration_seconds(content, ext),
            "artist": artist,
            "title": title,
            **name_debug,
            **analysis,
        }
        if preview_error:
            entry["preview_error"] = preview_error
        elif preview_content is not None:
            store_preview(file_hash, preview_content)
        bpm = analysis.get("bpm")
        camelot = analysis.get("camelot")
        tonality = analysis.get("tonality")
        entry["genre"] = genre

        logger.warning(
            "CACHE MISS (exact) [%s]: analyzed and cached %s - %s, bpm=%s",
            file_hash[:12],
            artist,
            title,
            bpm,
        )
        store_exact_match(file_hash, {**entry, "artwork_url": artwork_url})

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

    return tagged_content, entry, final_name, preview_content


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
) -> tuple[bytes, dict, str, bytes | None]:
    try:
        # _analyze_and_tag itself isolates the specific essentia/ffmpeg
        # calls that can crash the whole process (see run_isolated calls
        # inside it) -- everything else here (cache lookups, genre
        # lookups, tag-writing) is safe to run directly.
        return await _analyze_and_tag(
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
        return content, {"error": f"Processing failed: {type(e).__name__}: {e}"}, original_name, None
    finally:
        gc.collect()


async def build_corrected_zip(
    files: list[UploadFile],
    corrections: list[dict],
    filename_template: str | None = None,
) -> str:
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
    # Disk-backed for the same reason as build_zip -- see its own comment.
    fd, zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)

    seen_names: set[str] = set()
    playlist_tracks: list[tuple[str, float | None]] = []
    manifest = {}

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
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

                entry = {
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
                if ext in NEEDS_BROWSER_PREVIEW:
                    # Isolated the same way as build_zip's own preview
                    # generation -- this touches essentia/ffmpeg's native
                    # code too, so a crash here must only kill one worker,
                    # not the whole server (a direct make_preview_wav() call
                    # here previously bypassed that protection entirely).
                    preview_result = await run_isolated(PROCESS_CONCURRENCY, _run_preview_only, content, ext)
                    preview_content = preview_result.get("preview_content")
                    if preview_content is not None:
                        preview_name = f"{name}.preview.wav"
                        zip_file.writestr(preview_name, preview_content)
                        entry["preview_filename"] = preview_name
                manifest[name] = entry
                playlist_tracks.append((name, duration))
            except Exception as e:
                name = _dedupe(original_name, seen_names)
                manifest[name] = {
                    "error": f"Re-tagging failed: {type(e).__name__}: {e}",
                    "original_filename": original_name,
                }

        zip_file.writestr("crateprep-manifest.json", json.dumps(manifest, indent=2))
        zip_file.writestr("crateprep-playlist.m3u8", build_playlist(playlist_tracks))

    return zip_path


async def build_zip(
    files: list[UploadFile],
    filename_template: str | None = None,
    deep_search: bool = False,
    enhanced_detection: bool = False,
    ai_cleanup: bool = False,
) -> tuple[str, dict]:
    # Written straight to a temp file on disk, not an in-memory io.BytesIO --
    # confirmed via real production crashes that persisted even after
    # concurrent-decode work was serialized down to one file at a time: the
    # growing zip itself (original lossless files plus their uncompressed
    # browser-preview WAVs) is what was actually accumulating, since nothing
    # was ever written out until the *entire* batch's zip was built. A
    # 30-track lossless batch can easily add up to gigabytes held in RAM for
    # the whole request; the same bytes on disk cost nothing the OS can't
    # absorb. Returns the temp file's path -- the caller is responsible for
    # streaming it back to the client and deleting it afterward.
    fd, zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)

    manifest = {}
    seen_names: set[str] = set()
    playlist_tracks: list[tuple[str, float | None]] = []

    # Still processed in fixed-size chunks (PROCESS_CONCURRENCY files at a
    # time) rather than reading and analyzing the whole batch up front --
    # that would hold every file's raw bytes *and* already-tagged bytes in
    # memory simultaneously before any of it could be written to the zip
    # above, so peak memory would still scale with total batch size rather
    # than with how many files are actually being worked on at once.
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
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

                tagged_content, entry, resolved_name, preview_content = next(results_iter)
                name = _dedupe(resolved_name, seen_names)
                zip_file.writestr(name, tagged_content)

                if preview_content is not None:
                    preview_name = f"{name}.preview.wav"
                    zip_file.writestr(preview_name, preview_content)
                    entry["preview_filename"] = preview_name

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

    return zip_path, manifest
