from __future__ import annotations

import pytest

from app import rate_limit


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    """Global, not just test_rate_limit.py's own fixture -- rate_limit._requests
    is a module-level dict shared across the whole test process, so any test
    anywhere that exercises a rate-limited endpoint (e.g. /process) leaks
    state into every other test that shares its bucket key (same fake client
    IP, same uid) unless this resets between every test, not just within one
    file."""
    rate_limit._requests.clear()
    yield
    rate_limit._requests.clear()
