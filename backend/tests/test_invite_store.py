from datetime import datetime, timedelta, timezone

import pytest

from app import invite_store
from tests.fake_firestore import FakeCollection


@pytest.fixture
def fake_invites(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(invite_store, "_invites_collection", lambda: collection)
    monkeypatch.setattr(invite_store, "get_user_by_email", lambda email: None)
    # Real DNS validation is tested separately (test_validate_email_or_raise_*
    # below, with dns.resolver mocked) -- every other test here is about the
    # Firestore/rate-limit/status logic and shouldn't depend on, or be slowed
    # down by, a real network lookup for "example.com".
    monkeypatch.setattr(invite_store, "_validate_email_or_raise", lambda email: None)
    return collection


def test_create_invite_admin_source_stores_all_fields(fake_invites):
    invite = invite_store.create_invite(
        "  Friend@Example.com  ",
        "Sam",
        source="admin",
        invited_by_uid="admin-uid",
        invited_by_email="admin@example.com",
        inviter_label="The CratePrep team",
        admin_note="Thought of you!",
    )
    assert invite["email"] == "friend@example.com"  # trimmed + lowercased
    assert invite["name"] == "Sam"
    assert invite["source"] == "admin"
    assert invite["invited_by"] == "admin-uid"
    assert invite["invited_by_email"] == "admin@example.com"
    assert invite["inviter_label"] == "The CratePrep team"
    assert invite["admin_note"] == "Thought of you!"
    assert invite["status"] == "pending"
    assert invite["token"]
    assert invite["invite_id"]
    assert invite["accepted_at"] is None
    assert invite["accepted_uid"] is None


def test_create_invite_generates_unique_token_and_id_per_invite(fake_invites):
    first = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    second = invite_store.create_invite(
        "b@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    assert first["token"] != second["token"]
    assert first["invite_id"] != second["invite_id"]


def test_create_invite_blank_name_stored_as_none(fake_invites):
    invite = invite_store.create_invite(
        "a@example.com", "   ", source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    assert invite["name"] is None


def test_create_invite_user_source_rejects_self_invite(fake_invites):
    with pytest.raises(ValueError):
        invite_store.create_invite(
            "me@example.com",
            None,
            source="user",
            invited_by_uid="uid-1",
            invited_by_email="me@example.com",
            inviter_label="Me",
        )


def test_create_invite_user_source_case_insensitive_self_invite(fake_invites):
    with pytest.raises(ValueError):
        invite_store.create_invite(
            "ME@Example.com",
            None,
            source="user",
            invited_by_uid="uid-1",
            invited_by_email="me@example.com",
            inviter_label="Me",
        )


def test_create_invite_user_source_enforces_daily_limit(fake_invites):
    for i in range(invite_store.MAX_USER_INVITES_PER_DAY):
        invite_store.create_invite(
            f"friend{i}@example.com",
            None,
            source="user",
            invited_by_uid="uid-1",
            invited_by_email="me@example.com",
            inviter_label="Me",
        )
    with pytest.raises(invite_store.InviteLimitError):
        invite_store.create_invite(
            "onemore@example.com",
            None,
            source="user",
            invited_by_uid="uid-1",
            invited_by_email="me@example.com",
            inviter_label="Me",
        )


def test_create_invite_daily_limit_is_per_sender(fake_invites):
    for i in range(invite_store.MAX_USER_INVITES_PER_DAY):
        invite_store.create_invite(
            f"friend{i}@example.com",
            None,
            source="user",
            invited_by_uid="uid-1",
            invited_by_email="me@example.com",
            inviter_label="Me",
        )
    # A different sender isn't affected by uid-1's limit.
    invite = invite_store.create_invite(
        "another@example.com",
        None,
        source="user",
        invited_by_uid="uid-2",
        invited_by_email="other@example.com",
        inviter_label="Other",
    )
    assert invite["status"] == "pending"


def test_create_invite_reuses_existing_pending_invite_within_cooldown(fake_invites):
    first = invite_store.create_invite(
        "friend@example.com",
        None,
        source="user",
        invited_by_uid="uid-1",
        invited_by_email="me@example.com",
        inviter_label="Me",
    )
    second = invite_store.create_invite(
        "friend@example.com",
        None,
        source="user",
        invited_by_uid="uid-1",
        invited_by_email="me@example.com",
        inviter_label="Me",
    )
    assert second["invite_id"] == first["invite_id"]
    assert len(invite_store.list_all_invites()) == 1


def test_create_invite_does_not_reuse_across_different_senders(fake_invites):
    invite_store.create_invite(
        "friend@example.com", None, source="user", invited_by_uid="uid-1", invited_by_email="a@x.com", inviter_label="A"
    )
    second = invite_store.create_invite(
        "friend@example.com", None, source="user", invited_by_uid="uid-2", invited_by_email="b@x.com", inviter_label="B"
    )
    assert len(invite_store.list_all_invites()) == 2
    assert second["invited_by"] == "uid-2"


def test_create_invite_marks_existing_user_status(fake_invites, monkeypatch):
    monkeypatch.setattr(invite_store, "get_user_by_email", lambda email: object())
    invite = invite_store.create_invite(
        "already@example.com",
        None,
        source="admin",
        invited_by_uid="admin-uid",
        invited_by_email="admin@example.com",
        inviter_label="The CratePrep team",
    )
    assert invite["status"] == "existing_user"


def test_list_all_invites_sorts_newest_first(fake_invites):
    older = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    older["sent_at"] = "2000-01-01T00:00:00+00:00"
    fake_invites.document(older["invite_id"]).set(older)
    invite_store.create_invite(
        "b@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )

    entries = invite_store.list_all_invites()
    assert [e["email"] for e in entries] == ["b@example.com", "a@example.com"]


def test_list_invites_for_uid_only_returns_that_senders_invites(fake_invites):
    invite_store.create_invite(
        "a@example.com", None, source="user", invited_by_uid="uid-1", invited_by_email="1@x.com", inviter_label="1"
    )
    invite_store.create_invite(
        "b@example.com", None, source="user", invited_by_uid="uid-2", invited_by_email="2@x.com", inviter_label="2"
    )
    entries = invite_store.list_invites_for_uid("uid-1")
    assert [e["email"] for e in entries] == ["a@example.com"]


def test_get_invite_by_token_returns_none_for_unknown_token(fake_invites):
    assert invite_store.get_invite_by_token("does-not-exist") is None


def test_get_invite_by_token_returns_matching_invite(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    fetched = invite_store.get_invite_by_token(created["token"])
    assert fetched["invite_id"] == created["invite_id"]


def test_get_invite_by_token_marks_stale_pending_invite_expired(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    stale_sent_at = (
        datetime.now(timezone.utc) - timedelta(days=invite_store.INVITE_EXPIRY_DAYS + 1)
    ).isoformat()
    fake_invites.document(created["invite_id"]).set({"sent_at": stale_sent_at}, merge=True)

    fetched = invite_store.get_invite_by_token(created["token"])
    assert fetched["status"] == "expired"
    # Persisted, not just returned -- a second lookup sees the same result.
    assert invite_store.get_invite_by_token(created["token"])["status"] == "expired"


def test_get_invite_by_token_does_not_expire_recent_invite(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    assert invite_store.get_invite_by_token(created["token"])["status"] == "pending"


def test_revoke_invite_transitions_pending_to_revoked(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    revoked = invite_store.revoke_invite(created["invite_id"])
    assert revoked["status"] == "revoked"
    assert invite_store.get_invite_by_token(created["token"])["status"] == "revoked"


def test_revoke_invite_rejects_unknown_id(fake_invites):
    with pytest.raises(ValueError):
        invite_store.revoke_invite("does-not-exist")


def test_revoke_invite_rejects_already_revoked(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    invite_store.revoke_invite(created["invite_id"])
    with pytest.raises(ValueError):
        invite_store.revoke_invite(created["invite_id"])


def test_redeem_invite_transitions_pending_to_accepted(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    redeemed = invite_store.redeem_invite(created["token"], "new-user-uid")
    assert redeemed["status"] == "accepted"
    assert redeemed["accepted_uid"] == "new-user-uid"
    assert redeemed["accepted_at"]


def test_redeem_invite_unknown_token_returns_none(fake_invites):
    assert invite_store.redeem_invite("does-not-exist", "uid") is None


def test_redeem_invite_is_not_double_countable(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    first = invite_store.redeem_invite(created["token"], "uid-1")
    assert first is not None
    # A page refresh/duplicate call shouldn't re-accept under a different uid.
    second = invite_store.redeem_invite(created["token"], "uid-2")
    assert second is None
    assert invite_store.get_invite_by_token(created["token"])["accepted_uid"] == "uid-1"


def test_redeem_invite_rejects_revoked_invite(fake_invites):
    created = invite_store.create_invite(
        "a@example.com", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
    )
    invite_store.revoke_invite(created["invite_id"])
    assert invite_store.redeem_invite(created["token"], "uid-1") is None


class _FakeAnswer:
    def __init__(self, exchange: str):
        self.exchange = exchange

    def __str__(self):
        return self.exchange


class _FakeResolver:
    """Stands in for invite_store._resolver -- lets tests control exactly
    what each record-type lookup returns/raises without touching real DNS."""

    def __init__(self, mx=None, mx_raises=None, a=None, a_raises=None):
        self.mx = mx
        self.mx_raises = mx_raises
        self.a = a
        self.a_raises = a_raises
        self.calls: list[tuple[str, str]] = []

    def resolve(self, domain: str, rtype: str):
        self.calls.append((domain, rtype))
        if rtype == "MX":
            if self.mx_raises:
                raise self.mx_raises
            return [_FakeAnswer(e) for e in self.mx]
        if rtype == "A":
            if self.a_raises:
                raise self.a_raises
            return self.a
        raise AssertionError(f"unexpected record type: {rtype}")


@pytest.fixture
def fresh_domain_cache(monkeypatch):
    """Each validation test uses its own resolver behavior -- without a
    fresh cache, an earlier test's cached result for the same domain would
    silently short-circuit a later test that expects different behavior."""
    monkeypatch.setattr(invite_store, "_domain_cache", {})


def test_email_format_rejects_missing_at(fresh_domain_cache):
    with pytest.raises(ValueError):
        invite_store._validate_email_or_raise("not-an-email")


def test_email_format_rejects_missing_domain_dot(fresh_domain_cache):
    with pytest.raises(ValueError):
        invite_store._validate_email_or_raise("person@localhost")


def test_email_format_rejects_embedded_whitespace(fresh_domain_cache):
    with pytest.raises(ValueError):
        invite_store._validate_email_or_raise("person @example.com")


def test_validate_email_accepts_domain_with_mx_record(fresh_domain_cache, monkeypatch):
    fake = _FakeResolver(mx=["mail.realcompany.test"])
    monkeypatch.setattr(invite_store, "_resolver", fake)
    invite_store._validate_email_or_raise("person@realcompany.test")  # does not raise


def test_validate_email_falls_back_to_a_record_when_no_mx(fresh_domain_cache, monkeypatch):
    fake = _FakeResolver(mx_raises=invite_store.dns.resolver.NXDOMAIN(), a=["1.2.3.4"])
    monkeypatch.setattr(invite_store, "_resolver", fake)
    invite_store._validate_email_or_raise("person@webonly.test")  # does not raise
    assert ("webonly.test", "MX") in fake.calls
    assert ("webonly.test", "A") in fake.calls


def test_validate_email_rejects_domain_with_no_mx_or_a(fresh_domain_cache, monkeypatch):
    fake = _FakeResolver(mx_raises=invite_store.dns.resolver.NXDOMAIN(), a_raises=invite_store.dns.resolver.NXDOMAIN())
    monkeypatch.setattr(invite_store, "_resolver", fake)
    with pytest.raises(ValueError):
        invite_store._validate_email_or_raise("person@totally-fake-domain-xyz.test")


def test_validate_email_treats_null_mx_as_no_mail_but_still_checks_a(fresh_domain_cache, monkeypatch):
    # RFC 7505 null MX -- explicitly "this domain accepts no mail" -- should
    # not be treated the same as "has a working mail server".
    fake = _FakeResolver(mx=["."], a=["1.2.3.4"])
    monkeypatch.setattr(invite_store, "_resolver", fake)
    invite_store._validate_email_or_raise("person@nomail.test")
    assert ("nomail.test", "A") in fake.calls


def test_validate_email_null_mx_and_no_a_record_is_rejected(fresh_domain_cache, monkeypatch):
    fake = _FakeResolver(mx=["."], a_raises=invite_store.dns.resolver.NXDOMAIN())
    monkeypatch.setattr(invite_store, "_resolver", fake)
    with pytest.raises(ValueError):
        invite_store._validate_email_or_raise("person@nomail-noweb.test")


def test_validate_email_fails_open_on_inconclusive_dns_error(fresh_domain_cache, monkeypatch):
    # A resolver-level hiccup (not a definitive NXDOMAIN/NoAnswer) shouldn't
    # block a real invite over what's likely infrastructure flakiness on
    # this end, not evidence the address is fake.
    fake = _FakeResolver(mx_raises=invite_store.dns.exception.Timeout())
    monkeypatch.setattr(invite_store, "_resolver", fake)
    invite_store._validate_email_or_raise("person@slow-dns.test")  # does not raise


def test_validate_email_caches_dns_result_per_domain(fresh_domain_cache, monkeypatch):
    fake = _FakeResolver(mx=["mail.realcompany.test"])
    monkeypatch.setattr(invite_store, "_resolver", fake)
    invite_store._validate_email_or_raise("first@realcompany.test")
    invite_store._validate_email_or_raise("second@realcompany.test")
    assert len(fake.calls) == 1


def test_create_invite_rejects_invalid_email_format(fresh_domain_cache):
    # No fake_invites fixture (which stubs out validation) here on purpose --
    # format validation raises before create_invite ever touches Firestore.
    with pytest.raises(ValueError):
        invite_store.create_invite(
            "not-an-email", None, source="admin", invited_by_uid="u", invited_by_email="u@x.com", inviter_label="u"
        )
