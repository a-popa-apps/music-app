import pytest

from app import anon_trial_store
from tests.fake_firestore import FakeCollection


@pytest.fixture
def fake_collection(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(anon_trial_store, "_trials_collection", lambda: collection)
    return collection


def test_first_request_within_limit_succeeds(fake_collection):
    anon_trial_store.check_and_reserve_trial("1.2.3.4", 3)  # should not raise


def test_reserves_capacity_across_requests(fake_collection):
    anon_trial_store.check_and_reserve_trial("1.2.3.4", 3)
    anon_trial_store.check_and_reserve_trial("1.2.3.4", 2)  # 3 + 2 == limit, still fine


def test_exceeding_lifetime_limit_raises(fake_collection):
    anon_trial_store.check_and_reserve_trial("1.2.3.4", 3)
    with pytest.raises(ValueError, match="2 remaining"):
        anon_trial_store.check_and_reserve_trial("1.2.3.4", 3)


def test_different_ips_get_independent_allowances(fake_collection):
    anon_trial_store.check_and_reserve_trial("1.1.1.1", 5)
    anon_trial_store.check_and_reserve_trial("2.2.2.2", 5)  # independent bucket, should not raise


def test_ip_is_not_stored_in_plaintext(fake_collection):
    anon_trial_store.check_and_reserve_trial("1.2.3.4", 1)
    assert "1.2.3.4" not in fake_collection._store
