from __future__ import annotations

import os
import time

import stripe
from firebase_admin import auth as firebase_auth

from .auth import get_app
from .email_service import send_email
from .email_templates import (
    payment_failed_email_html,
    subscription_canceled_email_html,
    subscription_started_email_html,
)
from .profile_store import _users_collection, get_settings

REVENUE_WINDOW_DAYS = 30

# Stripe webhooks arrive with no browser Origin to derive a frontend URL
# from (unlike every other endpoint here, which reads it off the request --
# see main.py's _frontend_base_url) -- this is the one place that needs a
# fixed fallback for links embedded in a webhook-triggered email.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://crateprep.app")

# A payment failure, not a deliberate cancellation -- worth a heads-up email
# so a Pro subscriber doesn't silently lose access without knowing why.
PAYMENT_FAILED_STATUSES = {"past_due", "unpaid"}

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
        try:
            client.Customer.retrieve(customer_id)
            return customer_id
        except stripe.error.InvalidRequestError:
            # Stale id from a different Stripe mode -- e.g. this account's
            # customer was created back when STRIPE_SECRET_KEY was a test
            # key, and test/live are completely separate object spaces, so
            # it will never resolve under a live key (or vice versa). Fall
            # through and mint a fresh one instead of failing checkout.
            pass

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
        subscription_data={"metadata": {"uid": uid}},
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


# The admin dashboard's Stats tab hits this on every page load, and it was
# re-listing *all* subscriptions and *all* paid invoices from Stripe (one API
# call per page of 100) every single time -- wasteful today, and scales
# linearly with total subscriber/invoice count as the business grows. A
# short TTL cache means at most one real Stripe scan every 5 minutes,
# regardless of how often the dashboard is reloaded.
BILLING_STATS_CACHE_SECONDS = 300

_billing_stats_cache: dict | None = None
_billing_stats_cache_time: float = 0.0


def get_billing_stats() -> dict:
    global _billing_stats_cache, _billing_stats_cache_time

    now = time.time()
    if _billing_stats_cache is not None and now - _billing_stats_cache_time < BILLING_STATS_CACHE_SECONDS:
        return _billing_stats_cache

    client = get_stripe()
    if client is None:
        raise RuntimeError("Stripe is not configured")

    mrr_cents = 0
    active_subscribers = 0
    trialing_subscribers = 0
    canceling_subscribers = 0
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
            # Canceling from the Stripe-hosted billing portal (what
            # create_billing_portal_session sends users to) schedules the
            # cancellation for the end of the current period by default --
            # the subscription's status stays "active"/"trialing" the whole
            # time, so without this it looks identical to a healthy,
            # renewing subscriber right up until it actually ends.
            if sub_data.get("cancel_at_period_end"):
                canceling_subscribers += 1
        elif status == "canceled":
            canceled_at = sub_data.get("canceled_at")
            if canceled_at and canceled_at >= cutoff:
                canceled_last_30_days += 1

    revenue_last_30_days_cents = 0
    invoices = client.Invoice.list(status="paid", created={"gte": int(cutoff)}, limit=100)
    for invoice in invoices.auto_paging_iter():
        revenue_last_30_days_cents += invoice.to_dict().get("amount_paid") or 0

    stats = {
        "mrr_cents": mrr_cents,
        "active_subscribers": active_subscribers,
        "trialing_subscribers": trialing_subscribers,
        "canceling_subscribers": canceling_subscribers,
        "canceled_last_30_days": canceled_last_30_days,
        "revenue_last_30_days_cents": revenue_last_30_days_cents,
    }
    _billing_stats_cache = stats
    _billing_stats_cache_time = now
    return stats


def _stripe_dashboard_url(kind: str, object_id: str, livemode: bool) -> str:
    prefix = "https://dashboard.stripe.com/" if livemode else "https://dashboard.stripe.com/test/"
    return f"{prefix}{kind}/{object_id}"


def get_recent_transactions(limit: int = 10) -> list[dict]:
    """Latest paid-or-attempted invoices, newest first (Stripe's default
    list order), for the admin dashboard's "recent transactions" table --
    each links back to the real record in the Stripe dashboard rather than
    duplicating Stripe's own UI for anything beyond a quick glance."""
    client = get_stripe()
    if client is None:
        raise RuntimeError("Stripe is not configured")

    transactions = []
    for invoice in client.Invoice.list(limit=limit).auto_paging_iter():
        inv = invoice.to_dict()
        transactions.append(
            {
                "id": inv.get("id"),
                "amount_cents": inv.get("amount_paid") or inv.get("amount_due") or 0,
                "currency": inv.get("currency"),
                "customer_email": inv.get("customer_email"),
                "status": inv.get("status"),
                "created": inv.get("created"),
                "stripe_url": _stripe_dashboard_url("invoices", inv["id"], inv.get("livemode", False)),
            }
        )
        if len(transactions) >= limit:
            break
    return transactions


def _safe_get(obj, key: str, default=None):
    """This stripe-python version's StripeObject doesn't support .get()
    (dict-style [] access only -- see _stripe_obj's docstring in
    tests/test_billing.py for the live-webhook bug this class of mistake
    already caused once). `in` + [] works on both a real StripeObject and a
    plain dict, so this is safe for production events and for test
    fixtures that mock event["data"] as a plain dict."""
    return obj[key] if key in obj else default


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

        was_pro_already = get_settings(uid).get("plan") == "pro"

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

        # Guards against a retried webhook delivery re-sending this on an
        # already-Pro account -- checkout.session.completed should only
        # ever fire once per new subscription, but Stripe retries on any
        # non-2xx response.
        if not was_pro_already and _plan_for_status(status) == "pro":
            email = _user_email(uid)
            if email:
                send_email(
                    email,
                    "You're on CratePrep Pro!",
                    subscription_started_email_html(
                        TRIAL_DAYS if status == "trialing" else None, f"{FRONTEND_URL}/profile"
                    ),
                )

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        uid = data.get("metadata", {}).get("uid") or _uid_from_customer(client, data.get("customer"))
        if not uid:
            return

        # Only relevant (and only fetched) for a deleted subscription --
        # guards against a retried webhook delivery re-sending the
        # cancellation email for a subscription that's already canceled.
        previously_canceled = (
            event_type == "customer.subscription.deleted"
            and get_settings(uid).get("subscription_status") == "canceled"
        )

        status = "canceled" if event_type == "customer.subscription.deleted" else data.get("status")
        _users_collection().document(uid).set(
            {"plan": _plan_for_status(status), "subscription_status": status},
            merge=True,
        )

        if event_type == "customer.subscription.deleted":
            # Skip the "sorry to see you go" email when the dunning process
            # (repeated failed payments), not a deliberate cancellation, is
            # what ended the subscription -- those users already got the
            # payment-failed email and know why.
            cancellation_reason = (data.get("cancellation_details") or {}).get("reason")
            if not previously_canceled and cancellation_reason != "payment_failed":
                email = _user_email(uid)
                if email:
                    send_email(
                        email,
                        "Your CratePrep Pro subscription has ended",
                        subscription_canceled_email_html(f"{FRONTEND_URL}/pricing"),
                    )

        # Only on the transition *into* a failed-payment state -- not on
        # every subsequent webhook delivery while already there (Stripe
        # retries/re-sends events), and not on a deliberate cancellation.
        previous_attributes = _safe_get(event["data"], "previous_attributes", {})
        previous_status = _safe_get(previous_attributes, "status")
        if status in PAYMENT_FAILED_STATUSES and previous_status not in PAYMENT_FAILED_STATUSES:
            email = _user_email(uid)
            if email:
                send_email(
                    email,
                    "Action needed: update your CratePrep payment method",
                    payment_failed_email_html(f"{FRONTEND_URL}/profile"),
                )
