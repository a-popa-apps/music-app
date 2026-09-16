import os

from app import preview_cache


def test_store_then_get_round_trips(monkeypatch, tmp_path):
    monkeypatch.setattr(preview_cache, "CACHE_DIR", str(tmp_path))
    preview_cache.store_preview("abc123", b"some wav bytes")
    assert preview_cache.get_cached_preview("abc123") == b"some wav bytes"


def test_get_miss_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(preview_cache, "CACHE_DIR", str(tmp_path))
    assert preview_cache.get_cached_preview("does-not-exist") is None


def test_eviction_keeps_total_size_under_cap(monkeypatch, tmp_path):
    monkeypatch.setattr(preview_cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(preview_cache, "MAX_CACHE_BYTES", 30)

    # Explicit, well-separated mtimes -- eviction order depends on mtime,
    # and two stores in quick succession can otherwise land within the same
    # filesystem mtime tick (observed flaky on tmpfs), making "oldest" ambiguous.
    preview_cache.store_preview("first", b"a" * 20)
    os.utime(tmp_path / "first.wav", (100, 100))
    preview_cache.store_preview("second", b"b" * 20)
    os.utime(tmp_path / "second.wav", (200, 200))

    # Storing "second" pushed the total to 40 bytes, over the 30-byte cap --
    # "first" is the oldest entry, so it should have been evicted to bring
    # the total back under the cap, while "second" survives.
    assert preview_cache.get_cached_preview("first") is None
    assert preview_cache.get_cached_preview("second") == b"b" * 20


def test_reading_an_entry_protects_it_from_eviction(monkeypatch, tmp_path):
    monkeypatch.setattr(preview_cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(preview_cache, "MAX_CACHE_BYTES", 50)

    preview_cache.store_preview("first", b"a" * 20)
    os.utime(tmp_path / "first.wav", (100, 100))
    preview_cache.store_preview("second", b"b" * 20)
    os.utime(tmp_path / "second.wav", (200, 200))

    preview_cache.get_cached_preview("first")
    os.utime(tmp_path / "first.wav", (300, 300))  # touched -- now newer than "second"

    preview_cache.store_preview("third", b"c" * 20)  # total now 60 > 50 -- evicts the oldest, "second"

    assert preview_cache.get_cached_preview("first") == b"a" * 20
    assert preview_cache.get_cached_preview("second") is None
    assert preview_cache.get_cached_preview("third") == b"c" * 20
