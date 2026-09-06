from __future__ import annotations

import os
import time

import stripe
from firebase_admin import auth as firebase_auth

from .auth import get_app
from .profile_store import _users_collection, get_settings

REVENUE_WINDOW_DAYS = 30

PRICE_IDS = {
    "monthly": os.environ.get("STRIPE_PRICE_MONTHLY"),
    "annual": os.environ.get("STRIPE_PRICE_ANNUAL"),
}

TRIAL_DAYS = 7

_configured_key: str | None = None


def get_stripe():
    """Lazily configures the Stripe SDK from STRIPE_SECRET_KEY. Returns None
    if unset, mirroring auth.py's get_app() -- the rest of the app should
    keep working (e.g. local dev) without Stripe configured."""
    global _configured_key
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        return None
    if _configured_key != key:
        stripe.api_key = key
        _configured_key = key
    return stripe


def _user_email(uid: str) -> str | None:
    app = get_app()
    if app is None:
        return None
    try:
        return firebase_auth.get_user(uid, app=app).email
    except Exception:
        return None


def _get_or_create_customer(client, uid: str) -> str:
    customer_id = get_settings(uid).get("stripe_customer_id")
    if customer_id:
        return customer_id

    customer = client.Customer.create(email=_user_email(uid), metadata={"uid": uid})
    _users_collection().document(uid).set({"stripe_customer_id": customer.id}, merge=True)
    return customer.id


def create_checkout_session(uid: str, billing_cycle: str, success_url: str, cancel_url: str) -> str:
    price_id = PRICE_IDS.get(billing_cycle)
    if not price_id:
        raise ValueError(f"Invalid billing_cycle: {billing_cycle!r}")

    client = get_stripe()
    if client is None:
        raise RuntimeError("Stripe is not configured")

    customer_id = _get_or_create_customer(client, uid)

    session = client.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        allow_promotion_codes=True,
        subscription_data={"trial_period_days": TRIAL_DAYS, "metadata": {"uid": uid}},
        metadata={"uid": uid},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def create_billing_portal_session(uid: str, return_url: str) -> str:
    customer_id = get_settings(uid).get("stripe_customer_id")
    if not customer_id:
        raise ValueError("No billing account found for this user.")

    client = get_stripe()
    if client is None:
        raise RuntimeError("Stripe is not configured")

    session = client.billing_portal.Session.create(customer=customer_id, return_url=return_url)
    return session.url


def _plan_for_status(status: str | None) -> str:
    return "pro" if status in ("active", "trialing") else "free"


def _monthly_equivalent_cents(price: dict) -> int:
    """Normalizes a Price's unit_amount to a monthly-equivalent, derived
    from its actual recurring interval rather than hardcoding known price
    amounts a second time (already hardcoded once in Pricing.tsx) -- so this
    can't silently drift out of sync with a real price change made in the
    Stripe dashboard."""
    amount = price.get("unit_amount") or 0
    recurring = price.get("recurring") or {}
    interval = recurring.get("interval")
    interval_count = recurring.get("interval_count") or 1

    if interval == "year":
        return round(amount / (12 * interval_count))
    if interval == "month":
        return round(amount / interval_count)
    if interval == "week":
        return round(amount * 4.345 / interval_count)
    if interval == "day":
        return round(amount * 30.44 / interval_count)
    return amount  # unknown interval -- best effort, don't crash


def get_billing_stats() -> dict:
    client = get_stripe()
    if client is None:
        raise RuntimeError("Stripe is not configured")

    mrr_cents = 0
    active_subscribers = 0
    trialing_subscribers = 0
    canceled_last_30_days = 0
    cutoff = time.time() - REVENUE_WINDOW_DAYS * 86400

    for sub in client.Subscription.list(status="all", limit=100).auto_paging_iter():
        sub_data = sub.to_dict()
        status = sub_data.get("status")

        if status in ("active", "trialing"):
            for item in sub_data.get("items", {}).get("data", []):
                price = item.get("price") or {}
                mrr_cents += _monthly_equivalent_cents(price)
            if status == "active":
                active_subscribers += 1
            else:
                trialing_subscribers += 1
        elif status == "canceled":
            canceled_at = sub_data.get("canceled_at")
            if canceled_at and canceled_at >= cutoff:
                canceled_last_30_days += 1

    revenue_last_30_days_cents = 0
    invoices = client.Invoice.list(status="paid", created={"gte": int(cutoff)}, limit=100)
    for invoice in invoices.auto_paging_iter():
        revenue_last_30_days_cents += invoice.to_dict().get("amount_paid") or 0

    return {
        "mrr_cents": mrr_cents,
        "active_subscribers": active_subscribers,
        "trialing_subscribers": trialing_subscribers,
        "canceled_last_30_days": canceled_last_30_days,
        "revenue_last_30_days_cents": revenue_last_30_days_cents,
    }


def _uid_from_customer(client, customer_id: str | None) -> str | None:
    if not customer_id:
        return None
    try:
        customer = client.Customer.retrieve(customer_id)
        return customer.to_dict().get("metadata", {}).get("uid")
    except Exception:
        return None


def handle_webhook_event(payload: bytes, sig_header: str) -> None:
    client = get_stripe()
    if client is None:
        raise RuntimeError("Stripe is not configured")

    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    event = client.Webhook.construct_event(payload, sig_header, webhook_secret)

    event_type = event["type"]
    data = event["data"]["object"].to_dict()

    if event_type == "checkout.session.completed":
        uid = data.get("metadata", {}).get("uid")
        if not uid:
            return

        subscription_id = data.get("subscription")
        status = "active"
        if subscription_id:
            subscription = client.Subscription.retrieve(subscription_id)
            status = subscription.status

        _users_collection().document(uid).set(
            {
                "plan": _plan_for_status(status),
                "stripe_customer_id": data.get("customer"),
                "stripe_subscription_id": subscription_id,
                "subscription_status": status,
            },
            merge=True,
        )

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        uid = data.get("metadata", {}).get("uid") or _uid_from_customer(client, data.get("customer"))
        if not uid:
            return

        status = "canceled" if event_type == "customer.subscription.deleted" else data.get("status")
        _users_collection().document(uid).set(
            {"plan": _plan_for_status(status), "subscription_status": status},
            merge=True,
        )
