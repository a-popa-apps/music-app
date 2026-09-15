from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "CratePrep <onboarding@resend.dev>")


def send_email(to: str, subject: str, html: str) -> bool:
    """Sends a transactional email via Resend. Returns False (never raises)
    if RESEND_API_KEY isn't set or the request fails -- same no-op-if-
    unconfigured pattern as every other optional integration in this
    codebase (Stripe, Spotify, Sentry). A failed send should never break
    the request that triggered it: signup/login/reset flows already work
    without a working inbox on the other end, this is a nice-to-have on
    top, not a dependency."""
    if not RESEND_API_KEY:
        return False

    payload = json.dumps({"from": EMAIL_FROM, "to": [to], "subject": subject, "html": html}).encode(
        "utf-8"
    )
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False
