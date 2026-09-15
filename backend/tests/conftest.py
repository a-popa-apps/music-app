from __future__ import annotations

import pytest

from app import ai_budget, ai_client, process_audio, rate_limit


@pytest.fixture(autouse=True)
def _run_analysis_inline(monkeypatch):
    """run_isolated normally hands work to a real worker process (see
    analysis_process_pool.py) so an essentia/ffmpeg segfault on one file
    can't take the whole server down -- a real production concern, not a
    testing one. A spawned worker re-imports process_audio fresh, so it
    never sees a test's monkeypatch.setattr(process_audio, ...) calls on
    functions like detect_bpm/_resolve_artist_title_genre. Bypassing the
    pool here keeps tests fast and lets that monkeypatching work as
    written, while production still gets real crash isolation."""

    async def _inline(max_workers, func, *args):
        return func(*args)

    monkeypatch.setattr(process_audio, "run_isolated", _inline)


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


@pytest.fixture(autouse=True)
def _reset_ai_budget_state():
    """Same leakage risk as rate_limit._requests above -- ai_budget._calls is
    a module-level dict, so any test anywhere that triggers an AI-powered
    feature (ai_cleanup/batch_summary/feedback_summary) consumes from the
    same global counter unless this resets between every test."""
    ai_budget._calls.clear()
    ai_budget._alerted_day = None
    ai_client._rate_limit_alerted_day = None
    yield
    ai_budget._calls.clear()
    ai_budget._alerted_day = None
    ai_client._rate_limit_alerted_day = None
