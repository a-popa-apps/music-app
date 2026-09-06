from __future__ import annotations

import os

import stripe
from firebase_admin import auth as firebase_auth

from .auth import get_app
from .profile_store import _users_collection, get_settings

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
