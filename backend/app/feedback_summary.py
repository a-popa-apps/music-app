from __future__ import annotations

import json

from .ai_client import generate_json

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
    },
    "required": ["summary"],
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


def generate_feedback_summary(entries: list[dict]) -> str | None:
    """Triage summary of a list of feedback/support submissions (each with
    category/subject/message). Requires GEMINI_API_KEY; returns None
    (never raises) if that's unset, on any API error, or if there's
    nothing to summarize."""
    if not entries:
        return None

    payload = [
        {
            "category": entry.get("category"),
            "subject": entry.get("subject"),
            "message": entry.get("message"),
        }
        for entry in entries
    ]

    data = generate_json(SYSTEM_PROMPT, json.dumps(payload), SCHEMA)
    if data is None:
        return None

    summary = data.get("summary")
    return summary.strip() if summary else None
