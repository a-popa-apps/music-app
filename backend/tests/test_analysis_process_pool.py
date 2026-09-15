"""Exercises the real process pool (not mocked) -- these are slower than
the rest of the suite (each spawns real OS processes) but this module's
entire reason to exist is the crash-isolation guarantee, which can't be
verified through mocking. conftest.py's autouse fixture only bypasses
process_audio's own reference to run_isolated, not this module's real one,
so these tests get the genuine thing."""

import asyncio
import os

import pytest

pytest.importorskip("essentia")

from app.analysis_process_pool import run_isolated


def _double(x: int) -> int:
    return x * 2


def _get_pid() -> int:
    return os.getpid()


def _crash(x: int) -> int:
    # Simulates a genuine native-level crash (segfault) -- os._exit bypasses
    # Python's exception handling entirely, exactly like a real segfault,
    # without needing to actually corrupt memory to test it.
    os._exit(1)


def test_run_isolated_executes_in_a_separate_process():
    worker_pid = asyncio.run(run_isolated(2, _get_pid))
    assert worker_pid != os.getpid()


def test_run_isolated_returns_the_real_result():
    result = asyncio.run(run_isolated(2, _double, 21))
    assert result == 42


def test_run_isolated_survives_a_worker_crash():
    async def scenario():
        # The crash must not take down this test process, and the pool
        # must recover -- both are the entire point of isolating this
        # work at all.
        with pytest.raises(Exception):
            await run_isolated(2, _crash, 1)

        # Work submitted right after a crash must still succeed -- proves
        # the pool was actually recreated, not left broken.
        return await run_isolated(2, _double, 5)

    assert asyncio.run(scenario()) == 10
