import pytest

from app import admin_store, profile_store
from tests.fake_firestore import FakeCollection


@pytest.fixture
def fake_users(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(profile_store, "_users_collection", lambda: collection)
    monkeypatch.setattr(admin_store, "_users_collection", lambda: collection)
    return collection


@pytest.fixture
def fake_discount_codes(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(admin_store, "_discount_codes_collection", lambda: collection)
    return collection


def test_set_user_plan_updates_settings(fake_users):
    updated = admin_store.set_user_plan("uid-1", "pro")
    assert updated["plan"] == "pro"


def test_set_user_plan_rejects_invalid_plan(fake_users):
    with pytest.raises(ValueError):
        admin_store.set_user_plan("uid-1", "enterprise")


def test_set_admin_flag_promotes_and_demotes(fake_users):
    updated = admin_store.set_admin_flag("uid-1", True)
    assert updated["is_admin"] is True
    updated = admin_store.set_admin_flag("uid-1", False)
    assert updated["is_admin"] is False


def test_reset_usage_clears_counter_and_period(fake_users):
    profile_store.check_and_reserve_usage("uid-1", 20, "free")
    assert profile_store.get_settings("uid-1")["tracks_processed_this_period"] == 20

    updated = admin_store.reset_usage("uid-1")
    assert updated["tracks_processed_this_period"] == 0
    assert updated["usage_period_start"] is None

    # a subsequent batch starts counting from zero again, not from the old period
    profile_store.check_and_reserve_usage("uid-1", 25, "free")
    assert profile_store.get_settings("uid-1")["tracks_processed_this_period"] == 25


def test_create_discount_code_valid_percent(fake_discount_codes):
    doc = admin_store.create_discount_code(25, "admin-uid")
    assert doc["percent_off"] == 25
    assert doc["active"] is True
    assert doc["used_count"] == 0
    assert doc["created_by"] == "admin-uid"
    assert doc["code"].startswith("SAVE25-")


@pytest.mark.parametrize("percent_off", [10, 33, 0, 101])
def test_create_discount_code_rejects_invalid_percent(fake_discount_codes, percent_off):
    with pytest.raises(ValueError):
        admin_store.create_discount_code(percent_off, "admin-uid")


def test_create_discount_code_rejects_zero_max_uses(fake_discount_codes):
    with pytest.raises(ValueError):
        admin_store.create_discount_code(25, "admin-uid", max_uses=0)


def test_list_discount_codes_returns_created_codes(fake_discount_codes):
    admin_store.create_discount_code(50, "admin-uid")
    codes = admin_store.list_discount_codes()
    assert len(codes) == 1
    assert codes[0]["percent_off"] == 50


def test_set_discount_code_active_toggles(fake_discount_codes):
    doc = admin_store.create_discount_code(75, "admin-uid")
    updated = admin_store.set_discount_code_active(doc["code"], False)
    assert updated["active"] is False


def test_set_discount_code_active_rejects_unknown_code(fake_discount_codes):
    with pytest.raises(ValueError):
        admin_store.set_discount_code_active("NOPE", False)
