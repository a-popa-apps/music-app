# Live integration smoke tests

`smoke_test.py` hits the **real deployed backend** (production Render
by default), a real Firebase project, and real Stripe **test-mode**
APIs. This is intentionally separate from `backend/tests/` (which is
mock-only and runs in CI on every push/PR) and is **not** wired into
CI -- it needs live credentials, makes real (test-mode) API calls, and
an external outage shouldn't fail your push/PR pipeline.

## Why this exists

Two real bugs this session -- a Stripe SDK param-shape mismatch in
`PromotionCode.create`, and a webhook handler that missed a discount
redemption because it only listened for one of two possible event
types -- were only catchable by hitting the real API. A mocked unit
test structurally cannot see a schema drift or an untested code path
against a live third party. This script formalizes the manual
curl-based verification already done by hand into something
repeatable.

## Running it

```bash
E2E_FIREBASE_API_KEY=<firebase web api key> python3 backend/e2e/smoke_test.py
```

### Env vars

| Variable | Required? | What |
|---|---|---|
| `E2E_FIREBASE_API_KEY` | yes | The public Firebase web API key (same one in `frontend/.env.local` as `VITE_FIREBASE_API_KEY` -- this is a public client identifier, not a secret). |
| `E2E_BACKEND_URL` | no | Defaults to the production Render URL. Override to test against a different deploy. |
| `E2E_ADMIN_EMAIL` / `E2E_ADMIN_PASSWORD` | no | A real admin account's credentials. Admin-only checks (users/stats/billing-stats/discount-codes) are **skipped**, not failed, if these aren't set. |

## What it checks

- Backend health and Firebase configuration.
- A fresh disposable account can sign up, has correct defaults, and is
  cleaned up (`DELETE /profile`) at the end regardless of pass/fail.
- Anonymous `/process` is rejected; an authenticated one actually
  processes a synthetic audio file into a real zip.
- History reflects a processed track and can be cleared.
- The Free-tier 25-tracks/month quota boundary triggers a 402 exactly
  at the 26th track (batched into few requests to stay under the
  separate per-request rate limit).
- Checkout/portal endpoints return real Stripe artifacts without
  needing to complete a hosted Checkout page.
- (Admin-only) Discount codes actually get created with real Stripe
  coupon/promotion-code ids, and deactivating one is reflected back.

## Adding a check

Follow the existing `check("name", condition, detail)` /
`skip("name", "reason")` pattern -- keep each check a single boolean
assertion with a clear name, and prefer extending an existing account
lifecycle over spinning up a new one, to keep runs fast and avoid
accumulating test data.
