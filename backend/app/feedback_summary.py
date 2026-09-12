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
    "You triage a pile of unread user feedback/support submissions for a "
    "solo developer who doesn't have time to read every one individually. "
    "Write a short plain-language summary (a few sentences, not a long "
    "report) that groups the submissions by theme, calls out anything "
    "that reads like a bug report or urgent complaint by name so it isn't "
    "missed, and notes if several people are asking for the same thing. "
    "Don't restate every message -- summarize what a developer would "
    "actually want to know before opening the list. If the submissions "
    "don't have much in common, say that plainly instead of forcing a "
    "pattern that isn't there."
)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def generate_feedback_summary(entries: list[dict]) -> str | None:
    """Triage summary of a list of feedback/support submissions (each with
    category/subject/message). Requires ANTHROPIC_API_KEY; returns None
    (never raises) if that's unset, on any API error, or if there's
    nothing to summarize."""
    client = _get_client()
    if client is None or not entries:
        return None

    payload = [
        {
            "category": entry.get("category"),
            "subject": entry.get("subject"),
            "message": entry.get("message"),
        }
        for entry in entries
    ]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": SCHEMA},
            },
            messages=[{"role": "user", "content": json.dumps(payload)}],
        )
        text = next(b.text for b in response.content if b.type == "text")
        data = json.loads(text)
    except Exception:
        return None

    summary = data.get("summary")
    return summary.strip() if summary else None
