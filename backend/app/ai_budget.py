from __future__ import annotations

import os
import time
from collections import defaultdict

from .email_service import notify_admins
from .email_templates import ai_limit_alert_email_html

# A coarse global circuit breaker across all three AI-powered features
# combined (ai_cleanup, batch_summary, feedback_summary) -- not a per-user
# quota. Free/Pro track quotas and the per-account rate limiter already
# bound normal usage reasonably well; this exists purely to cap worst-case
# spend if something goes wrong (a bug causing retries, a single batch of
# many unresolvable filenames each triggering ai_split_artist_title, or
# outright abuse) rather than to shape any legitimate user's experience.
#
# In-memory, so it resets on redeploy/restart -- same tradeoff as
# rate_limit.py's own in-memory store; would need a shared store (Redis,
# Firestore) to hold a real ceiling across multiple instances or restarts.
DAILY_AI_CALL_LIMIT = int(os.environ.get("DAILY_AI_CALL_LIMIT", "500"))

# Stripe webhooks/background triggers have no browser Origin to derive a
# frontend URL from -- same fixed fallback billing.py already uses for
# links embedded in a webhook-triggered email.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://music-app-sage-sigma.vercel.app")

_calls: dict[str, int] = defaultdict(int)

# Tracks which day an exhaustion alert was already sent for -- in-memory,
# so (like _calls above) it can re-fire once after a redeploy, but never
# spams on every call once the budget is already exhausted for the day.
_alerted_day: str | None = None


def _today_key() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def calls_used_today() -> int:
    """Read-only -- for surfacing budget status (e.g. on /health) without
    reserving a slot or mutating the underlying dict."""
    return _calls.get(_today_key(), 0)


def allow_ai_call() -> bool:
    """Reserves and returns True if today's global AI-call budget has room;
    returns False (reserving nothing) once DAILY_AI_CALL_LIMIT is reached
    for the day. Call this immediately before any Gemini API call -- every
    caller already treats "no" as "skip gracefully", the same as a missing
    API key or a request error, so exhausting the budget just means the
    AI-assisted extras silently sit out for the rest of the day rather than
    breaking anything."""
    key = _today_key()
    if _calls[key] >= DAILY_AI_CALL_LIMIT:
        _alert_budget_exhausted(key)
        return False
    _calls[key] += 1
    return True


def _alert_budget_exhausted(day: str) -> None:
    global _alerted_day
    if _alerted_day == day:
        return
    _alerted_day = day
    notify_admins(
        "CratePrep: daily AI call budget exhausted",
        ai_limit_alert_email_html(
            "Daily AI call budget exhausted",
            (
                f"CratePrep hit its self-imposed cap of {DAILY_AI_CALL_LIMIT} AI calls "
                "today, combined across filename cleanup, batch summaries, and feedback "
                "triage. Every AI-assisted feature is sitting out gracefully for the rest "
                "of the day rather than breaking anything -- but this is worth a look if "
                "it wasn't expected, since it usually means either real growth in usage "
                "or a bug causing repeated calls."
            ),
            f"{FRONTEND_URL}/admin",
        ),
    )
