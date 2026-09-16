from __future__ import annotations

import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# Local disk, not Firebase Storage/Firestore -- deliberately. The case this
# actually needs to serve is a batch getting re-uploaded minutes later after
# a crash (the exact scenario that keeps happening this session), not "some
# other user uploads the same track next month". Local disk skips both the
# unbounded-growth question a permanent global cache would raise (nothing to
# evict on a schedule -- it's capped and self-evicts here) and needing a
# Storage bucket wired up at all. It's wiped on every deploy/restart, which
# is fine: it only ever needs to survive within one running instance's
# uptime.
CACHE_DIR = os.path.join(tempfile.gettempdir(), "crateprep_preview_cache")

# Conservative cap so this can never compete with the app for disk space --
# previews are full-length mono 16-bit WAVs (~5MB/minute of audio), so this
# comfortably holds a couple dozen tracks' worth at once.
MAX_CACHE_BYTES = 300 * 1024 * 1024


def _path(file_hash: str) -> str:
    return os.path.join(CACHE_DIR, f"{file_hash}.wav")


def get_cached_preview(file_hash: str) -> bytes | None:
    path = _path(file_hash)
    try:
        with open(path, "rb") as f:
            content = f.read()
    except FileNotFoundError:
        return None
    except OSError as e:
        logger.warning("preview cache read failed: %s", e)
        return None
    try:
        os.utime(path, None)  # mark as recently used so eviction picks the real LRU entry
    except OSError:
        pass
    return content


def store_preview(file_hash: str, content: bytes) -> None:
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(_path(file_hash), "wb") as f:
            f.write(content)
        _evict_oldest_until_under_cap()
    except OSError as e:
        logger.warning("preview cache write failed: %s", e)


def _evict_oldest_until_under_cap() -> None:
    try:
        entries = [(e.path, e.stat().st_mtime, e.stat().st_size) for e in os.scandir(CACHE_DIR)]
    except OSError:
        return

    total = sum(size for _, _, size in entries)
    if total <= MAX_CACHE_BYTES:
        return

    entries.sort(key=lambda entry: entry[1])  # oldest (least-recently-used) first
    for path, _, size in entries:
        if total <= MAX_CACHE_BYTES:
            break
        try:
            os.remove(path)
            total -= size
        except OSError:
            pass
