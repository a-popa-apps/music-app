from __future__ import annotations

import asyncio
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import Any, Callable

logger = logging.getLogger(__name__)

_pool: ProcessPoolExecutor | None = None
_pool_workers: int | None = None

# Recycles a worker after this many tasks -- a real, still-unexplained
# per-file memory creep was already flagged (via local simulation, before
# this pool existed) and never root-caused; now that the actual essentia
# work runs in a long-lived worker process instead of being torn down
# with each request, if that creep is inside essentia/ffmpeg's own native
# state rather than Python's, it would otherwise accumulate for as long
# as a single worker stays alive. Cheap insurance either way: a fresh
# worker (paying only the warm-up cost, not a whole request) periodically
# resets whatever's actually accumulating.
MAX_TASKS_PER_WORKER = 15


def _warm_up_worker() -> None:
    # Runs once per worker process, right when it starts -- pays essentia's
    # own import/model-loading cost upfront instead of on whichever real
    # file happens to land on a freshly-started worker first.
    from .detect_bpm import warm_up

    warm_up()


def _noop() -> None:
    pass


def _new_pool(max_workers: int) -> ProcessPoolExecutor:
    # "spawn", not the Linux default "fork": forking a process that
    # already has gRPC connections open (firebase-admin/Firestore uses
    # gRPC internally) is a real, documented hazard -- the forked child
    # can hang or crash outright. Spawn starts each worker completely
    # fresh instead, at the cost of each one re-importing the app (paid
    # once at pool startup, via the warm-up below, not per file).
    ctx = multiprocessing.get_context("spawn")
    return ProcessPoolExecutor(
        max_workers=max_workers,
        mp_context=ctx,
        initializer=_warm_up_worker,
        max_tasks_per_child=MAX_TASKS_PER_WORKER,
    )


async def ensure_started(max_workers: int) -> None:
    """Creates the worker pool and waits for every worker to actually
    start and warm up, so the first real upload after a deploy doesn't
    pay that cold-start cost. Call once at app startup."""
    global _pool, _pool_workers
    if _pool is not None and _pool_workers == max_workers:
        return
    _pool = _new_pool(max_workers)
    _pool_workers = max_workers
    loop = asyncio.get_running_loop()
    # One trivial task per worker slot -- forces that many workers to
    # actually spawn and run their initializer now, rather than trusting
    # the pool's own lazy worker-start timing.
    await asyncio.gather(*(loop.run_in_executor(_pool, _noop) for _ in range(max_workers)))


async def run_isolated(max_workers: int, func: Callable[..., Any], *args: Any) -> Any:
    """Runs func(*args) in a separate worker process rather than a thread.

    essentia/ffmpeg occasionally segfault outright on a real-world
    malformed or unusual file -- a segfault kills the whole OS process,
    every thread in it, which in a thread-pool model takes down the
    entire server: every other in-flight request, not just the one bad
    file (confirmed live: a single file crashed the whole backend mid
    batch, three times in a row, for every user, not just the one
    uploading it). Running the actual decode/analyze/tag/preview work in
    a separate process means a crash there only kills that one worker;
    the pool notices, gets recreated, and the rest of the app keeps
    running untouched.

    Retries once against a freshly-recreated pool -- a worker crash marks
    the *whole* pool broken (Python's own behavior, not a choice here),
    so a submission that merely happened to share a now-dead pool with
    the actual crash still deserves a real attempt rather than surfacing
    the pool's own bookkeeping as if it were that file's error."""
    global _pool, _pool_workers

    for attempt in range(2):
        if _pool is None or _pool_workers != max_workers:
            if _pool is not None:
                _pool.shutdown(wait=False)
            _pool = _new_pool(max_workers)
            _pool_workers = max_workers

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(_pool, func, *args)
        except BrokenProcessPool as e:
            logger.warning("analysis worker process crashed (%s) -- recreating pool", e)
            _pool.shutdown(wait=False)
            _pool = None
            if attempt == 1:
                raise
    raise AssertionError("unreachable")
