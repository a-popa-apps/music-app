from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

WINDOW_SECONDS = 300  # 5 minutes
MAX_REQUESTS = 5

# In-memory is fine for a single Render instance; would need a shared store
# (e.g. Redis) if this ever runs across multiple instances.
_requests: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request) -> None:
    """Raises 429 if this client has exceeded MAX_REQUESTS in WINDOW_SECONDS.
    /process is CPU-heavy and currently open to anyone -- this bounds the
    cost of abuse without requiring an account."""
    ip = _client_ip(request)
    now = time.time()
    timestamps = _requests[ip]

    cutoff = now - WINDOW_SECONDS
    while timestamps and timestamps[0] < cutoff:
        timestamps.pop(0)

    if len(timestamps) >= MAX_REQUESTS:
        retry_after = int(WINDOW_SECONDS - (now - timestamps[0])) + 1
        raise HTTPException(
            429,
            f"Too many requests. Try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    timestamps.append(now)
