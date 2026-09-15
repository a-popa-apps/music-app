from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from .ai_budget import allow_ai_call
from .email_service import notify_admins
from .email_templates import ai_limit_alert_email_html

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# gemini-3.5-flash-lite -- Google's cheapest/fastest multimodal model,
# comfortably within the Gemini API's free tier for tasks this small
# (structured single-field extraction, short summaries). gemini-2.5-flash-
# lite (the prior default) turned out to be a 404 for new API keys --
# Google's own error message pointed here. Never append a dated snapshot
# suffix, same reasoning as pinning any other provider's model id to a
# moving target instead of a fixed release.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://crateprep.app")

_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Same in-memory, once-per-day dedup as ai_budget.py's own exhaustion
# alert -- can re-fire once after a redeploy, but never spams every call
# while Gemini keeps rejecting requests.
_rate_limit_alerted_day: str | None = None


def _alert_rate_limited() -> None:
    global _rate_limit_alerted_day
    day = time.strftime("%Y-%m-%d", time.gmtime())
    if _rate_limit_alerted_day == day:
        return
    _rate_limit_alerted_day = day
    notify_admins(
        "CratePrep: Gemini API rate limit hit",
        ai_limit_alert_email_html(
            "Gemini API rate limit hit",
            (
                "CratePrep's Gemini API key just got rate-limited (HTTP 429). This usually "
                "means the free tier's request-per-day or request-per-minute ceiling has "
                "been reached -- AI-assisted features (filename cleanup, batch summaries, "
                "feedback triage) will keep silently skipping until Gemini's limit resets. "
                "If this keeps happening, consider upgrading to a paid Gemini tier."
            ),
            f"{FRONTEND_URL}/admin",
        ),
    )


def generate_json(system_prompt: str, content: str, schema: dict) -> dict | None:
    """Shared entry point for all three AI-powered features (filename
    cleanup, feedback triage, batch summary): a JSON-schema-constrained
    call to Gemini via raw HTTP -- same no-SDK-for-one-endpoint style as
    email_service.py's Resend integration, and it sidesteps a real
    dependency conflict (the Google SDK pulls in an httpx version
    incompatible with this app's pinned FastAPI/Starlette test client).
    Returns None (never raises) if GEMINI_API_KEY is unset, the daily call
    budget is exhausted, or on any API error -- every caller already
    treats "no result" as "skip this AI-assisted extra", the same as any
    other optional integration in this app.

    Callers are responsible for checking their own preconditions (e.g. a
    non-empty input) before calling this, so the daily budget is only
    spent on calls that would actually run. `schema` must be in Gemini's
    OpenAPI-subset schema format (uppercase type names, `nullable: true`
    for optional fields) -- not standard JSON Schema."""
    if not GEMINI_API_KEY or not allow_ai_call():
        return None

    payload = json.dumps(
        {
            "contents": [{"role": "user", "parts": [{"text": content}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        _API_URL.format(model=GEMINI_MODEL),
        data=payload,
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            _alert_rate_limited()
        return None
    except Exception:
        return None
