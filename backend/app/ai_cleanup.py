from __future__ import annotations

from .ai_client import generate_json

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "artist": {"type": "STRING", "nullable": True},
        "title": {"type": "STRING", "nullable": True},
        "confident": {"type": "BOOLEAN"},
    },
    "required": ["artist", "title", "confident"],
}

SYSTEM_PROMPT = (
    "You clean up messy DJ track filenames into an artist and a title. "
    "Filenames often have inconsistent word order, missing separators, or "
    "extra junk that simpler cleanup steps couldn't fully remove. Split the "
    "given text into the artist name and the track title the way a DJ "
    "would recognize them. If the text is too ambiguous to confidently "
    "split (e.g. it's a single generic word, a catalog code, or clearly "
    "not a track name), set artist and title to null and confident to "
    "false rather than guessing."
)


def ai_split_artist_title(stem: str) -> tuple[str, str] | None:
    """Last-resort artist/title split for filenames the free local/catalog
    paths in clean_filename.py and detect_genre.py couldn't resolve.
    Requires GEMINI_API_KEY; returns None (never raises) if that's unset,
    on any API error, or when the model itself isn't confident -- callers
    already have guess_split as a fallback for that case."""
    stem = stem.strip()
    if not stem:
        return None

    data = generate_json(SYSTEM_PROMPT, stem, SCHEMA)
    if data is None or not data.get("confident"):
        return None

    artist, title = data.get("artist"), data.get("title")
    if not artist or not title:
        return None

    return artist.strip(), title.strip()
