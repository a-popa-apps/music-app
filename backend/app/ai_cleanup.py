from __future__ import annotations

import json
import os

import anthropic

MODEL = "claude-opus-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "artist": {"type": ["string", "null"]},
        "title": {"type": ["string", "null"]},
        "confident": {"type": "boolean"},
    },
    "required": ["artist", "title", "confident"],
    "additionalProperties": False,
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

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def ai_split_artist_title(stem: str) -> tuple[str, str] | None:
    """Last-resort artist/title split for filenames the free local/catalog
    paths in clean_filename.py and detect_genre.py couldn't resolve.
    Requires ANTHROPIC_API_KEY; returns None (never raises) if that's unset,
    on any API error, or when the model itself isn't confident -- callers
    already have guess_split as a fallback for that case."""
    client = _get_client()
    stem = stem.strip()
    if client is None or not stem:
        return None

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": SCHEMA},
            },
            messages=[{"role": "user", "content": stem}],
        )
        text = next(b.text for b in response.content if b.type == "text")
        data = json.loads(text)
    except Exception:
        return None

    if not data.get("confident"):
        return None

    artist, title = data.get("artist"), data.get("title")
    if not artist or not title:
        return None

    return artist.strip(), title.strip()
