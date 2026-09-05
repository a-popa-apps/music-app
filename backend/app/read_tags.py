from __future__ import annotations

import tempfile

import mutagen

from .clean_filename import _clean_text

GENERIC_GENRES = {"", "music", "other", "unknown", "genre"}


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
        return {}

    if audio is None or audio.tags is None:
        return {}

    def first(key: str) -> str | None:
        values = audio.tags.get(key)
        if not values:
            return None
        value = str(values[0]).strip()
        return value or None

    raw_artist = first("artist")
    raw_title = first("title")
    raw_genre = first("genre")

    if not raw_artist or not raw_title:
        return {}

    artist, _ = _clean_text(raw_artist)
    title, version_tag = _clean_text(raw_title)
    if not artist or not title:
        return {}

    genre = raw_genre if raw_genre and raw_genre.lower() not in GENERIC_GENRES else None

    return {"artist": artist, "title": title, "genre": genre, "version_tag": version_tag}
