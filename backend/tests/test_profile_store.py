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


def test_check_and_reserve_usage_pro_is_unlimited(fake_collection):
    profile_store.check_and_reserve_usage("uid-1", 999, "pro")
    # no-op: doesn't even create a doc
    assert profile_store.get_settings("uid-1") == profile_store.DEFAULT_SETTINGS


def test_check_and_reserve_usage_free_tracks_usage(fake_collection):
    profile_store.check_and_reserve_usage("uid-1", 10, "free")
    settings = profile_store.get_settings("uid-1")
    assert settings["tracks_processed_this_period"] == 10
    assert settings["usage_period_start"] == profile_store._current_period_key()

    profile_store.check_and_reserve_usage("uid-1", 10, "free")
    assert profile_store.get_settings("uid-1")["tracks_processed_this_period"] == 20


def test_check_and_reserve_usage_free_rejects_over_limit(fake_collection):
    profile_store.check_and_reserve_usage("uid-1", 25, "free")
    with pytest.raises(ValueError):
        profile_store.check_and_reserve_usage("uid-1", 1, "free")
    # rejection doesn't mutate the stored count
    assert profile_store.get_settings("uid-1")["tracks_processed_this_period"] == 25


def test_check_and_reserve_usage_resets_on_period_rollover(fake_collection):
    profile_store.check_and_reserve_usage("uid-1", 25, "free")
    with pytest.raises(ValueError):
        profile_store.check_and_reserve_usage("uid-1", 1, "free")

    fake_collection.document("uid-1").set({"usage_period_start": "2000-01"}, merge=True)
    # a new period: the old count no longer applies
    profile_store.check_and_reserve_usage("uid-1", 5, "free")
    settings = profile_store.get_settings("uid-1")
    assert settings["tracks_processed_this_period"] == 5
    assert settings["usage_period_start"] == profile_store._current_period_key()
