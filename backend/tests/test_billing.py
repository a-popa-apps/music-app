from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app import billing, profile_store
from tests.fake_firestore import FakeCollection


def _stripe_obj(data: dict) -> MagicMock:
    """Mimics a real Stripe object: dict-style [] access plus .to_dict(),
    matching how billing.py actually reads webhook payloads (stripe-python
    15.x's StripeObject doesn't support .get() directly -- see the bug this
    guards against, caught by a real live webhook test)."""
    obj = MagicMock()
    obj.__getitem__.side_effect = data.__getitem__
    obj.to_dict.return_value = data
    return obj


@pytest.fixture
def fake_users(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(profile_store, "_users_collection", lambda: collection)
    monkeypatch.setattr(billing, "_users_collection", lambda: collection)
    return collection


@pytest.fixture
def fake_stripe(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(billing, "get_stripe", lambda: client)
    monkeypatch.setattr(billing, "_user_email", lambda uid: "test@example.com")
    monkeypatch.setattr(billing, "PRICE_IDS", {"monthly": "price_monthly", "annual": "price_annual"})
    return client


def test_plan_for_status():
    assert billing._plan_for_status("active") == "pro"
    assert billing._plan_for_status("trialing") == "pro"
    assert billing._plan_for_status("canceled") == "free"
    assert billing._plan_for_status(None) == "free"


def test_create_checkout_session_rejects_invalid_cycle(fake_users, fake_stripe):
    with pytest.raises(ValueError):
        billing.create_checkout_session("uid-1", "weekly", "https://x/success", "https://x/cancel")


def test_create_checkout_session_creates_customer_once(fake_users, fake_stripe):
    fake_stripe.Customer.create.return_value = MagicMock(id="cus_123")
    fake_stripe.checkout.Session.create.return_value = MagicMock(url="https://checkout.stripe.com/abc")

    url = billing.create_checkout_session("uid-1", "monthly", "https://x/success", "https://x/cancel")

    assert url == "https://checkout.stripe.com/abc"
    fake_stripe.Customer.create.assert_called_once()
    assert profile_store.get_settings("uid-1")["stripe_customer_id"] == "cus_123"

    # second call reuses the stored customer id instead of creating another
    billing.create_checkout_session("uid-1", "annual", "https://x/success", "https://x/cancel")
    fake_stripe.Customer.create.assert_called_once()


def test_create_billing_portal_session_requires_customer(fake_users, fake_stripe):
    with pytest.raises(ValueError):
        billing.create_billing_portal_session("uid-1", "https://x/profile")


def test_create_billing_portal_session_returns_url(fake_users, fake_stripe):
    profile_store.save_settings("uid-1", {})
    fake_users.document("uid-1").set({"stripe_customer_id": "cus_123"}, merge=True)
    fake_stripe.billing_portal.Session.create.return_value = MagicMock(url="https://billing.stripe.com/xyz")

    url = billing.create_billing_portal_session("uid-1", "https://x/profile")
    assert url == "https://billing.stripe.com/xyz"


def test_webhook_checkout_completed_activates_plan(fake_users, fake_stripe):
    fake_stripe.Subscription.retrieve.return_value = MagicMock(status="active")
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": _stripe_obj(
                {
                    "metadata": {"uid": "uid-1"},
                    "customer": "cus_123",
                    "subscription": "sub_123",
                }
            )
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    settings = profile_store.get_settings("uid-1")
    assert settings["plan"] == "pro"
    assert settings["stripe_customer_id"] == "cus_123"
    assert settings["stripe_subscription_id"] == "sub_123"
    assert settings["subscription_status"] == "active"


def test_webhook_subscription_deleted_reverts_to_free(fake_users, fake_stripe):
    fake_users.document("uid-1").set({"plan": "pro", "subscription_status": "active"}, merge=True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {"object": _stripe_obj({"metadata": {"uid": "uid-1"}, "customer": "cus_123"})},
    }

    billing.handle_webhook_event(b"payload", "sig")

    settings = profile_store.get_settings("uid-1")
    assert settings["plan"] == "free"
    assert settings["subscription_status"] == "canceled"


def test_webhook_falls_back_to_customer_lookup_for_uid(fake_users, fake_stripe):
    fake_stripe.Customer.retrieve.return_value = _stripe_obj({"metadata": {"uid": "uid-2"}})
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": _stripe_obj({"metadata": {}, "customer": "cus_456", "status": "past_due"})
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    settings = profile_store.get_settings("uid-2")
    assert settings["plan"] == "free"
    assert settings["subscription_status"] == "past_due"
