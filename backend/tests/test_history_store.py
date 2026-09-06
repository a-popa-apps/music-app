import pytest

from app import history_store
from tests.fake_firestore import FakeCollection


@pytest.fixture
def fake_history(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(history_store, "_history_collection", lambda: collection)
    return collection


def _manifest_entry(**overrides):
    entry = {
        "bpm": 128.0,
        "key": "C major",
        "camelot": "8B",
        "genre": "Electronic music",
        "duration_seconds": 210.5,
        "original_filename": "raw_track.mp3",
    }
    entry.update(overrides)
    return entry


def test_add_history_entries_writes_one_doc_per_track(fake_history):
    manifest = {
        "Artist - Title.mp3": _manifest_entry(),
        "Artist2 - Title2.mp3": _manifest_entry(bpm=140.0, original_filename="raw2.mp3"),
    }
    history_store.add_history_entries("uid-1", manifest)

    entries = history_store.list_history("uid-1")
    assert len(entries) == 2
    filenames = {e["filename"] for e in entries}
    assert filenames == {"Artist - Title.mp3", "Artist2 - Title2.mp3"}
    for e in entries:
        assert e["uid"] == "uid-1"
        assert e["failed"] is False
        assert e["history_id"]
        assert e["processed_at"]


def test_add_history_entries_marks_failed_tracks(fake_history):
    manifest = {"broken.mp3": {"error": "Failed to read file: OSError: boom"}}
    history_store.add_history_entries("uid-1", manifest)

    entries = history_store.list_history("uid-1")
    assert len(entries) == 1
    assert entries[0]["failed"] is True
    # the read-failure path never sets original_filename -- falls back to the key
    assert entries[0]["original_filename"] == "broken.mp3"


def test_list_history_only_returns_matching_uid(fake_history):
    history_store.add_history_entries("uid-1", {"a.mp3": _manifest_entry()})
    history_store.add_history_entries("uid-2", {"b.mp3": _manifest_entry()})

    entries = history_store.list_history("uid-1")
    assert len(entries) == 1
    assert entries[0]["filename"] == "a.mp3"


def test_list_history_sorts_newest_first(fake_history):
    history_store.add_history_entries("uid-1", {"older.mp3": _manifest_entry()})
    entries = history_store.list_history("uid-1")
    entries[0]["processed_at"] = "2000-01-01T00:00:00+00:00"
    fake_history.document(entries[0]["history_id"]).set(entries[0])

    history_store.add_history_entries("uid-1", {"newer.mp3": _manifest_entry()})

    entries = history_store.list_history("uid-1")
    assert [e["filename"] for e in entries] == ["newer.mp3", "older.mp3"]


def test_list_history_respects_limit(fake_history):
    for i in range(5):
        history_store.add_history_entries("uid-1", {f"track{i}.mp3": _manifest_entry()})

    entries = history_store.list_history("uid-1", limit=2)
    assert len(entries) == 2


def test_clear_history_removes_only_target_uid(fake_history):
    history_store.add_history_entries("uid-1", {"a.mp3": _manifest_entry()})
    history_store.add_history_entries("uid-2", {"b.mp3": _manifest_entry()})

    deleted = history_store.clear_history("uid-1")
    assert deleted == 1
    assert history_store.list_history("uid-1") == []
    assert len(history_store.list_history("uid-2")) == 1
