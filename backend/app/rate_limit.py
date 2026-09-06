from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

WINDOW_SECONDS = 300  # 5 minutes
MAX_REQUESTS_FREE = 5
MAX_REQUESTS_PRO = 25

# In-memory is fine for a single Render instance; would need a shared store
# (e.g. Redis) if this ever runs across multiple instances.
_requests: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(
    request: Request, key: str | None = None, max_requests: int = MAX_REQUESTS_FREE
) -> None:
    """Raises 429 if this bucket has exceeded max_requests in WINDOW_SECONDS.
    /process is CPU-heavy -- this bounds the cost of abuse.

    Pass `key` (the authenticated uid) so each account gets its own bucket
    sized to its plan, rather than sharing a limit with everyone on the same
    IP/NAT -- falls back to client IP when no key is given (e.g. for a route
    that doesn't require auth)."""
    bucket_key = key or _client_ip(request)
    now = time.time()
    timestamps = _requests[bucket_key]

    cutoff = now - WINDOW_SECONDS
    while timestamps and timestamps[0] < cutoff:
        timestamps.pop(0)

    if len(timestamps) >= max_requests:
        retry_after = int(WINDOW_SECONDS - (now - timestamps[0])) + 1
        raise HTTPException(
            429,
            f"Too many requests. Try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    timestamps.append(now)
