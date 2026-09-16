from __future__ import annotations

import io
import tempfile

import mutagen
from mutagen._riff import RiffFile

from .clean_filename import _clean_text

GENERIC_GENRES = {"", "music", "other", "unknown", "genre"}


def _read_wav_riff_info(content: bytes) -> dict[str, str]:
    """Reads a WAV file's native RIFF INFO LIST chunk (IART=artist,
    INAM=title, IGNR=genre) -- an older, still-common WAV tagging
    convention that mutagen's WAVE class doesn't read at all (it only
    supports ID3v2-in-WAV, via _WaveID3). macOS's Finder/Music.app read
    this convention natively, so a file that shows correct tags there can
    still come back from mutagen alone as having no tags whatsoever.
    Best-effort: returns {} for anything that doesn't parse as valid RIFF,
    has no INFO list, or the INFO list has none of the fields we use."""
    try:
        riff = RiffFile(io.BytesIO(content))
        info_chunk = next(
            (c for c in riff.root.subchunks() if c.id == "LIST" and getattr(c, "name", None) == "INFO"),
            None,
        )
        if info_chunk is None:
            return {}
        result = {}
        for sub in info_chunk.subchunks():
            text = sub.read().split(b"\x00", 1)[0].decode("utf-8", errors="replace").strip()
            if text:
                result[sub.id] = text
        return result
    except Exception:
        return {}


def read_embedded_tags(content: bytes, ext: str) -> dict:
    """Best-effort read of artist/title/genre already embedded in the file's
    own tags, cleaned the same way filename text is cleaned. Lets a
    well-tagged upload skip filename guessing entirely; returns {} if the
    file has no readable tags or no useful artist/title."""
    try:
        with tempfile.NamedTemporaryFile(suffix=ext) as tmp:
            tmp.write(content)
            tmp.flush()
            audio = mutagen.File(tmp.name, easy=True)
    except Exception:
        audio = None

    def first(key: str) -> str | None:
        if audio is None or audio.tags is None:
            return None
        values = audio.tags.get(key)
        if not values:
            return None
        value = str(values[0]).strip()
        return value or None

    raw_artist = first("artist")
    raw_title = first("title")
    raw_genre = first("genre")

    # Only worth the extra parse when the ID3-based read came up short --
    # and only for WAV, since that's the only format here where mutagen's
    # tag support has this gap (MP3/FLAC/AIFF/OGG all have real ID3/native
    # tag support in mutagen already).
    if ext.lower() in (".wav", ".wave") and (not raw_artist or not raw_title):
        riff_info = _read_wav_riff_info(content)
        raw_artist = raw_artist or riff_info.get("IART")
        raw_title = raw_title or riff_info.get("INAM")
        raw_genre = raw_genre or riff_info.get("IGNR")

    if not raw_artist or not raw_title:
        return {}

    artist, _ = _clean_text(raw_artist)
    title, version_tag = _clean_text(raw_title)
    if not artist or not title:
        return {}

    genre = raw_genre if raw_genre and raw_genre.lower() not in GENERIC_GENRES else None

    return {"artist": artist, "title": title, "genre": genre, "version_tag": version_tag}
