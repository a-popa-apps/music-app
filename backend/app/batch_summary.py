from __future__ import annotations

import json
import os

import anthropic

MODEL = "claude-opus-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
    },
    "required": ["summary"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You write a short, DJ-facing summary of a batch of just-processed "
    "tracks -- 1-2 sentences, plain language, no bullet points or numbered "
    "lists. Describe the batch's genre mix, BPM range, and how energy "
    "trends across the tracks (e.g. builds, drops, stays flat). Call out "
    "anything that stands out from the rest of the batch (a much higher "
    "or lower BPM, an outlier genre). Summarize the overall shape rather "
    "than restating every track's exact numbers. If there isn't enough "
    "usable data (e.g. most tracks have no genre or BPM), say so briefly "
    "instead of inventing detail."
)

MIN_TRACKS_FOR_SUMMARY = 2

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _track_facts(manifest: dict) -> list[dict]:
    """Numeric/categorical facts only -- no filenames, artist, or title --
    this summary is about the batch's musical shape, not track identity."""
    facts = []
    for entry in manifest.values():
        if entry.get("error"):
            continue
        facts.append(
            {
                "bpm": entry.get("bpm"),
                "key": entry.get("camelot"),
                "genre": entry.get("genre"),
                "energy": entry.get("energy"),
            }
        )
    return facts


def generate_batch_summary(manifest: dict) -> str | None:
    """One-shot, per-batch (not per-track) natural-language summary of the
    batch's musical shape -- genre mix, BPM range, energy arc. Requires
    ANTHROPIC_API_KEY; returns None (never raises) if unset, on any API
    error, or if too few tracks processed successfully to say anything
    meaningful about the batch as a whole."""
    client = _get_client()
    facts = _track_facts(manifest)
    if client is None or len(facts) < MIN_TRACKS_FOR_SUMMARY:
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
            messages=[{"role": "user", "content": json.dumps(facts)}],
        )
        text = next(b.text for b in response.content if b.type == "text")
        data = json.loads(text)
    except Exception:
        return None

    summary = data.get("summary")
    return summary.strip() if summary else None
