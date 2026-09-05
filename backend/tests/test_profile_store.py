import pytest

from app import profile_store
from tests.fake_firestore import FakeCollection


@pytest.fixture
def fake_collection(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(profile_store, "_users_collection", lambda: collection)
    return collection


def test_get_settings_returns_defaults_for_unknown_user(fake_collection):
    settings = profile_store.get_settings("new-uid")
    assert settings == profile_store.DEFAULT_SETTINGS


def test_save_and_get_roundtrip(fake_collection):
    profile_store.save_settings("uid-1", {"name": "Andrei", "country": "RO"})
    settings = profile_store.get_settings("uid-1")
    assert settings["name"] == "Andrei"
    assert settings["country"] == "RO"
    # untouched fields keep their defaults
    assert settings["plan"] == "free"


def test_invalid_role_rejected(fake_collection):
    with pytest.raises(ValueError):
        profile_store.save_settings("uid-1", {"role": "not_a_real_role"})


def test_valid_role_accepted(fake_collection):
    profile_store.save_settings("uid-1", {"role": "dj"})
    assert profile_store.get_settings("uid-1")["role"] == "dj"


def test_too_many_genres_rejected(fake_collection):
    with pytest.raises(ValueError):
        profile_store.save_settings(
            "uid-1",
            {"primary_genres": ["Electronic music", "Hip-Hop / R&B", "Urban", "Latin"]},
        )


def test_invalid_genre_rejected(fake_collection):
    with pytest.raises(ValueError):
        profile_store.save_settings("uid-1", {"primary_genres": ["Not A Real Genre"]})


def test_plan_is_read_only_via_regular_save(fake_collection):
    profile_store.save_settings("uid-1", {"plan": "pro"})
    assert profile_store.get_settings("uid-1")["plan"] == "free"


def test_is_admin_is_read_only_via_regular_save(fake_collection):
    profile_store.save_settings("uid-1", {"is_admin": True})
    assert profile_store.get_settings("uid-1")["is_admin"] is False


def test_delete_settings_removes_doc(fake_collection):
    profile_store.save_settings("uid-1", {"name": "Andrei"})
    profile_store.delete_settings("uid-1")
    assert profile_store.get_settings("uid-1") == profile_store.DEFAULT_SETTINGS
