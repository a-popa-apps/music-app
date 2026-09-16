from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
import stripe

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


@pytest.fixture(autouse=True)
def _reset_billing_stats_cache():
    # get_billing_stats caches its result for BILLING_STATS_CACHE_SECONDS --
    # without resetting it, one test's cached stats could leak into the
    # next test's assertions regardless of what that test's own Stripe
    # mock returns.
    billing._billing_stats_cache = None
    billing._billing_stats_cache_time = 0.0


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


def test_safe_get_works_on_plain_dict():
    assert billing._safe_get({"a": 1}, "a") == 1
    assert billing._safe_get({"a": 1}, "missing", "default") == "default"


def test_safe_get_works_on_stripe_object_without_dict_get():
    # Regression test: this SDK version's StripeObject doesn't support
    # .get() (dict-style [] access only) -- _safe_get must work against the
    # real type webhook events actually deliver, not just a plain dict.
    from stripe._stripe_object import StripeObject

    obj = StripeObject.construct_from({"a": 1}, "sk_test_x")
    assert not hasattr(obj, "get")
    assert billing._safe_get(obj, "a") == 1
    assert billing._safe_get(obj, "missing", "default") == "default"


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


def test_create_checkout_session_replaces_stale_customer_from_a_different_stripe_mode(fake_users, fake_stripe):
    # Real incident this guards against: a customer id created under a test
    # key (or vice versa) is permanently stored on the profile doc, but
    # test/live are completely separate object spaces in Stripe -- Stripe
    # rejects any request using that id under a key from the other mode
    # with an InvalidRequestError, not a 404, and that used to bubble all
    # the way up and break checkout outright.
    profile_store.save_settings("uid-1", {})
    billing._users_collection().document("uid-1").set({"stripe_customer_id": "cus_stale_test_mode"}, merge=True)

    fake_stripe.Customer.retrieve.side_effect = stripe.error.InvalidRequestError(
        "No such customer: 'cus_stale_test_mode'; a similar object exists in test mode, but a live mode key was "
        "used to make this request.",
        param="id",
    )
    fake_stripe.Customer.create.return_value = MagicMock(id="cus_fresh_live")
    fake_stripe.checkout.Session.create.return_value = MagicMock(url="https://checkout.stripe.com/abc")

    url = billing.create_checkout_session("uid-1", "monthly", "https://x/success", "https://x/cancel")

    assert url == "https://checkout.stripe.com/abc"
    fake_stripe.Customer.create.assert_called_once()
    assert profile_store.get_settings("uid-1")["stripe_customer_id"] == "cus_fresh_live"


def test_create_checkout_session_reuses_customer_that_still_resolves(fake_users, fake_stripe):
    profile_store.save_settings("uid-1", {})
    billing._users_collection().document("uid-1").set({"stripe_customer_id": "cus_still_good"}, merge=True)
    fake_stripe.Customer.retrieve.return_value = MagicMock(id="cus_still_good")
    fake_stripe.checkout.Session.create.return_value = MagicMock(url="https://checkout.stripe.com/abc")

    billing.create_checkout_session("uid-1", "monthly", "https://x/success", "https://x/cancel")

    fake_stripe.Customer.create.assert_not_called()
    assert profile_store.get_settings("uid-1")["stripe_customer_id"] == "cus_still_good"


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
    subscription = MagicMock(status="active")
    subscription.to_dict.return_value = {"status": "active"}
    fake_stripe.Subscription.retrieve.return_value = subscription
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


def test_webhook_checkout_completed_sends_subscription_started_email(fake_users, fake_stripe, monkeypatch):
    subscription = MagicMock(status="active")
    subscription.to_dict.return_value = {"status": "active"}
    fake_stripe.Subscription.retrieve.return_value = subscription
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda to, subject, html: sent.append((to, subject, html)) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": _stripe_obj(
                {"metadata": {"uid": "uid-1"}, "customer": "cus_123", "subscription": "sub_123"}
            )
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert len(sent) == 1
    assert sent[0][0] == "test@example.com"
    assert "Pro" in sent[0][1]
    assert "trial" not in sent[0][2].lower()


def test_webhook_checkout_completed_mentions_trial_when_trialing(fake_users, fake_stripe, monkeypatch):
    subscription = MagicMock(status="trialing")
    subscription.to_dict.return_value = {"status": "trialing"}
    fake_stripe.Subscription.retrieve.return_value = subscription
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda to, subject, html: sent.append(html) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": _stripe_obj(
                {"metadata": {"uid": "uid-1"}, "customer": "cus_123", "subscription": "sub_123"}
            )
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert len(sent) == 1
    assert "trial" in sent[0].lower()


def test_webhook_checkout_completed_does_not_resend_when_already_pro(fake_users, fake_stripe, monkeypatch):
    # A retried webhook delivery for a checkout that already activated Pro
    # shouldn't re-send the "welcome to Pro" email.
    fake_users.document("uid-1").set({"plan": "pro", "subscription_status": "active"}, merge=True)
    subscription = MagicMock(status="active")
    subscription.to_dict.return_value = {"status": "active"}
    fake_stripe.Subscription.retrieve.return_value = subscription
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda *a, **k: sent.append(1) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": _stripe_obj(
                {"metadata": {"uid": "uid-1"}, "customer": "cus_123", "subscription": "sub_123"}
            )
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert sent == []


def test_webhook_subscription_deleted_sends_cancellation_email(fake_users, fake_stripe, monkeypatch):
    fake_users.document("uid-1").set({"plan": "pro", "subscription_status": "active"}, merge=True)
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda to, subject, html: sent.append((to, subject)) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {"object": _stripe_obj({"metadata": {"uid": "uid-1"}, "customer": "cus_123"})},
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert len(sent) == 1
    assert sent[0][0] == "test@example.com"
    assert "ended" in sent[0][1].lower()


def test_webhook_subscription_deleted_skips_cancellation_email_on_payment_failure(
    fake_users, fake_stripe, monkeypatch
):
    fake_users.document("uid-1").set({"plan": "pro", "subscription_status": "past_due"}, merge=True)
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda *a, **k: sent.append(1) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": _stripe_obj(
                {
                    "metadata": {"uid": "uid-1"},
                    "customer": "cus_123",
                    "cancellation_details": {"reason": "payment_failed"},
                }
            )
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert sent == []


def test_webhook_subscription_deleted_does_not_resend_cancellation_email_when_already_canceled(
    fake_users, fake_stripe, monkeypatch
):
    fake_users.document("uid-1").set({"plan": "free", "subscription_status": "canceled"}, merge=True)
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda *a, **k: sent.append(1) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {"object": _stripe_obj({"metadata": {"uid": "uid-1"}, "customer": "cus_123"})},
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert sent == []


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


def test_webhook_sends_payment_failed_email_on_transition_to_past_due(fake_users, fake_stripe, monkeypatch):
    fake_users.document("uid-1").set({"plan": "pro", "subscription_status": "active"}, merge=True)
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda to, subject, html: sent.append((to, subject)) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": _stripe_obj({"metadata": {"uid": "uid-1"}, "customer": "cus_123", "status": "past_due"}),
            "previous_attributes": {"status": "active"},
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert len(sent) == 1
    assert sent[0][0] == "test@example.com"
    assert "payment" in sent[0][1].lower()


def test_webhook_does_not_resend_payment_failed_email_while_already_past_due(
    fake_users, fake_stripe, monkeypatch
):
    # Stripe can re-deliver the same event, or send further updates while a
    # subscription sits in past_due -- only the *transition into* the state
    # should trigger the email, not every update while already there.
    fake_users.document("uid-1").set({"plan": "free", "subscription_status": "past_due"}, merge=True)
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda *a, **k: sent.append(1) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": _stripe_obj({"metadata": {"uid": "uid-1"}, "customer": "cus_123", "status": "past_due"}),
            "previous_attributes": {"status": "past_due"},
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert sent == []


def test_webhook_does_not_send_payment_failed_email_on_deliberate_cancellation(
    fake_users, fake_stripe, monkeypatch
):
    # A deliberate cancellation still sends the cancellation-confirmation
    # email (see test_webhook_subscription_deleted_sends_cancellation_email)
    # -- this test only guards against the *payment-failed* email firing too.
    fake_users.document("uid-1").set({"plan": "pro", "subscription_status": "active"}, merge=True)
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda to, subject, html: sent.append(subject) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {"object": _stripe_obj({"metadata": {"uid": "uid-1"}, "customer": "cus_123"})},
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert sent == ["Your CratePrep Pro subscription has ended"]


def test_webhook_skips_payment_failed_email_when_no_email_on_file(fake_users, fake_stripe, monkeypatch):
    monkeypatch.setattr(billing, "_user_email", lambda uid: None)
    sent = []
    monkeypatch.setattr(billing, "send_email", lambda *a, **k: sent.append(1) or True)
    fake_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": _stripe_obj({"metadata": {"uid": "uid-1"}, "customer": "cus_123", "status": "unpaid"}),
            "previous_attributes": {"status": "active"},
        },
    }

    billing.handle_webhook_event(b"payload", "sig")

    assert sent == []


def test_get_billing_stats_requires_stripe_configured(monkeypatch):
    monkeypatch.setattr(billing, "get_stripe", lambda: None)
    with pytest.raises(RuntimeError):
        billing.get_billing_stats()


def test_get_billing_stats_sums_mrr_and_counts(fake_stripe):
    now = time.time()
    subs = [
        _stripe_obj(
            {
                "status": "active",
                "items": {
                    "data": [
                        {
                            "price": {
                                "unit_amount": 800,
                                "recurring": {"interval": "month", "interval_count": 1},
                            }
                        }
                    ]
                },
            }
        ),
        _stripe_obj(
            {
                "status": "active",
                "items": {
                    "data": [
                        {
                            "price": {
                                "unit_amount": 6000,
                                "recurring": {"interval": "year", "interval_count": 1},
                            }
                        }
                    ]
                },
            }
        ),
        _stripe_obj({"status": "trialing", "items": {"data": []}}),
        _stripe_obj({"status": "canceled", "items": {"data": []}, "canceled_at": now - 86400}),
        _stripe_obj(
            {"status": "canceled", "items": {"data": []}, "canceled_at": now - 86400 * 90}
        ),
    ]
    fake_stripe.Subscription.list.return_value.auto_paging_iter.return_value = subs

    invoices = [_stripe_obj({"amount_paid": 800}), _stripe_obj({"amount_paid": 500})]
    fake_stripe.Invoice.list.return_value.auto_paging_iter.return_value = invoices

    stats = billing.get_billing_stats()

    assert stats["mrr_cents"] == 800 + 500  # $8/mo as-is, $60/yr -> $5/mo equivalent
    assert stats["active_subscribers"] == 2
    assert stats["trialing_subscribers"] == 1
    assert stats["canceled_last_30_days"] == 1
    assert stats["revenue_last_30_days_cents"] == 1300


def test_get_billing_stats_is_cached_across_calls(fake_stripe, monkeypatch):
    fake_stripe.Subscription.list.return_value.auto_paging_iter.return_value = []
    fake_stripe.Invoice.list.return_value.auto_paging_iter.return_value = []

    first = billing.get_billing_stats()
    second = billing.get_billing_stats()

    assert first == second
    # A cache hit shouldn't re-list from Stripe at all.
    assert fake_stripe.Subscription.list.call_count == 1
    assert fake_stripe.Invoice.list.call_count == 1


def test_get_billing_stats_recomputes_after_cache_expires(fake_stripe, monkeypatch):
    fake_stripe.Subscription.list.return_value.auto_paging_iter.return_value = []
    fake_stripe.Invoice.list.return_value.auto_paging_iter.return_value = []

    billing.get_billing_stats()

    monkeypatch.setattr(
        billing, "_billing_stats_cache_time", time.time() - billing.BILLING_STATS_CACHE_SECONDS - 1
    )
    billing.get_billing_stats()

    assert fake_stripe.Subscription.list.call_count == 2


def test_monthly_equivalent_cents_handles_all_intervals():
    assert billing._monthly_equivalent_cents({"unit_amount": 1200, "recurring": {"interval": "month", "interval_count": 1}}) == 1200
    assert billing._monthly_equivalent_cents({"unit_amount": 12000, "recurring": {"interval": "year", "interval_count": 1}}) == 1000
    assert billing._monthly_equivalent_cents({"unit_amount": 100, "recurring": {"interval": "week", "interval_count": 1}}) == round(100 * 4.345)
    assert billing._monthly_equivalent_cents({"unit_amount": 100, "recurring": {"interval": "day", "interval_count": 1}}) == round(100 * 30.44)
    assert billing._monthly_equivalent_cents({"unit_amount": 500, "recurring": {}}) == 500
