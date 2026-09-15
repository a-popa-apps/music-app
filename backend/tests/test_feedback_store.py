import pytest

from app import feedback_store
from tests.fake_firestore import FakeCollection


@pytest.fixture
def fake_feedback(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(feedback_store, "_feedback_collection", lambda: collection)
    return collection


def test_create_feedback_stores_all_fields(fake_feedback):
    doc = feedback_store.create_feedback(
        "support", "Help, my export is broken", email="a@example.com", subject="Broken export"
    )
    assert doc["category"] == "support"
    assert doc["message"] == "Help, my export is broken"
    assert doc["subject"] == "Broken export"
    assert doc["email"] == "a@example.com"
    assert doc["read"] is False
    assert doc["feedback_id"]
    assert doc["submitted_at"]


def test_create_feedback_rejects_invalid_category(fake_feedback):
    with pytest.raises(ValueError):
        feedback_store.create_feedback("nonsense", "hello")


def test_create_feedback_rejects_empty_message(fake_feedback):
    with pytest.raises(ValueError):
        feedback_store.create_feedback("feedback", "   ")


def test_list_feedback_sorts_newest_first(fake_feedback):
    older = feedback_store.create_feedback("feedback", "older")
    older["submitted_at"] = "2000-01-01T00:00:00+00:00"
    fake_feedback.document(older["feedback_id"]).set(older)
    feedback_store.create_feedback("feedback", "newer")

    entries = feedback_store.list_feedback()
    assert [e["message"] for e in entries] == ["newer", "older"]


def test_mark_feedback_read_toggles(fake_feedback):
    doc = feedback_store.create_feedback("feedback", "hello")
    updated = feedback_store.mark_feedback_read(doc["feedback_id"], True)
    assert updated["read"] is True
    updated = feedback_store.mark_feedback_read(doc["feedback_id"], False)
    assert updated["read"] is False


def test_mark_feedback_read_rejects_unknown_id(fake_feedback):
    with pytest.raises(ValueError):
        feedback_store.mark_feedback_read("does-not-exist", True)


def test_delete_feedback_removes_entry(fake_feedback):
    doc = feedback_store.create_feedback("feedback", "hello")
    feedback_store.delete_feedback(doc["feedback_id"])
    assert feedback_store.list_feedback() == []


def test_delete_feedback_rejects_unknown_id(fake_feedback):
    with pytest.raises(ValueError):
        feedback_store.delete_feedback("does-not-exist")


def test_delete_feedback_batch_removes_all_listed(fake_feedback):
    a = feedback_store.create_feedback("feedback", "one")
    b = feedback_store.create_feedback("feedback", "two")
    c = feedback_store.create_feedback("feedback", "three")

    feedback_store.delete_feedback_batch([a["feedback_id"], b["feedback_id"]])

    remaining = feedback_store.list_feedback()
    assert [d["feedback_id"] for d in remaining] == [c["feedback_id"]]


def test_delete_feedback_batch_skips_unknown_ids(fake_feedback):
    doc = feedback_store.create_feedback("feedback", "hello")
    # Should not raise even though "does-not-exist" isn't a real id.
    feedback_store.delete_feedback_batch([doc["feedback_id"], "does-not-exist"])
    assert feedback_store.list_feedback() == []
