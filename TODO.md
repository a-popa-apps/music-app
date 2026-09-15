# TODO

## Credentials / environment variables

Backend (Render):
- [ ] `ANTHROPIC_API_KEY` — **confirmed missing** (`/health` → `ai_cleanup_configured: false`, checked 2026-09-14). Enables AI filename cleanup, AI batch summary, and feedback triage; all three currently no-op without it.
- [x] `FIREBASE_SERVICE_ACCOUNT_JSON` — **confirmed set** (`/health` → `firebase_configured: true`, checked 2026-09-14).
- [ ] `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRICE_MONTHLY` / `STRIPE_PRICE_ANNUAL` — not checkable via `/health` (no field for it); still needs a real test-mode purchase to confirm end-to-end (see below).
- [x] `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` — **confirmed set** (`/health` → `spotify_configured: true`, checked 2026-09-14).
- [ ] `DISCOGS_TOKEN` — optional, unconfirmed either way; works without it.

Frontend (Vercel):
- [x] `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, `VITE_FIREBASE_MESSAGING_SENDER_ID`, `VITE_FIREBASE_APP_ID` — **confirmed set with real-looking values** (inspected the built production JS bundle at `music-app-sage-sigma.vercel.app`, found a real Firebase API key and `a-popa-music-apps.firebaseapp.com` auth domain baked in, checked 2026-09-14). Not the same as a verified end-to-end sign-in (no test credentials used) but rules out "vars are empty/placeholder".
- [ ] `VITE_BACKEND_URL` — already defaults to the Render URL in `.env.example`; only needs setting if that URL changes

Backend (Render), error monitoring:
- [ ] `SENTRY_DSN` — optional, not yet set. Backend now initializes Sentry when present (`/health` → `sentry_configured`); without it, unhandled exceptions in production still fail silently (a request just 500s with nothing surfaced anywhere). Get a DSN from a Sentry project (free tier is enough) and set it on Render to close this gap.
- [ ] `SENTRY_ENVIRONMENT` — optional, defaults to `"production"`; only needed if you want staging/prod separated in Sentry.

Backend (Render), transactional email:
- [x] `RESEND_API_KEY` — **confirmed set** (`/health` → `email_configured: true`, checked 2026-09-15). Verification, password-reset, and payment-failed emails are all sent through CratePrep's own branded templates instead of Firebase/Stripe's default ones.
- [ ] `EMAIL_FROM` — optional, currently unset, so all three emails send from Resend's shared sandbox address (`onboarding@resend.dev`) rather than a `crateprep.app` address. To fix: verify `crateprep.app` as a sending domain in the Resend dashboard (DNS records they provide), then set this to something like `CratePrep <noreply@crateprep.app>`.
- [ ] Nobody has triggered a real signup or password-reset yet to confirm an email actually lands in an inbox and renders correctly end-to-end — the code path and the rendered HTML are both verified, real delivery through Resend isn't.
- [x] `ADMIN_EMAIL` — **confirmed set** to `popa472@gmail.com` on Render, checked 2026-09-15. Comma-separated list of addresses that get alerted when someone submits feedback/a support request via `POST /feedback`; add more addresses by separating with commas.

## Verify what's actually already set

This session's network access was restricted for most of this work (couldn't reach any external site, including the production backend); that got fixed 2026-09-14 by switching the environment to full network access, so the checks below could finally run for real:
- [x] Hit the deployed backend's `/health` endpoint — confirmed `firebase_configured: true`, `spotify_configured: true`, `ai_cleanup_configured: false`.
- [x] Confirmed the deployed frontend (`music-app-sage-sigma.vercel.app`) is reachable (HTTP 200) and its production JS bundle has real (non-empty, non-placeholder) `VITE_FIREBASE_*` values baked in, checked 2026-09-14. Still not a fully verified sign-in (would need real user credentials, which this session won't request or handle).
- [ ] Do a real test purchase in Stripe test mode to confirm billing end-to-end — still open, `/health` has no field for Stripe config status.

## Reliability

- [x] Cost ceiling on AI-powered features — `backend/app/ai_budget.py` adds a global daily call limit (`DAILY_AI_CALL_LIMIT`, default 500) shared across AI filename cleanup, batch summary, and feedback triage, on top of the existing per-IP rate limiting. Surfaced on `/health` (`ai_calls_today`, `ai_daily_limit`). Shipped 2026-09-14.
- [x] Error monitoring — Sentry wired into the backend (`sentry_sdk.init(...)` in `main.py`, gated on `SENTRY_DSN` being set, same no-op-if-unset pattern as every other integration). Shipped 2026-09-14; **still needs `SENTRY_DSN` set on Render** (see credentials section above) before it actually reports anything.
- [x] Custom-branded transactional email — verification and password-reset emails no longer rely on Firebase's default (unbranded, `firebaseapp.com`-sender) templates. The backend now generates the one-time action link via the Firebase Admin SDK (`backend/app/auth.py`) and sends CratePrep's own HTML email (`backend/app/email_templates.py`) through Resend (`backend/app/email_service.py`) — two new endpoints, `POST /auth/send-verification-email` (authenticated) and `POST /auth/forgot-password` (public, rate-limited, enumeration-safe — always responds the same whether or not the email is registered). Shipped 2026-09-15, `RESEND_API_KEY` set on Render the same day — live in production.
- [x] Payment-failed email — a Pro subscriber whose card gets declined now gets an email telling them to update their payment method, instead of silently losing Pro access with no idea why. Hooks into the existing Stripe webhook handler (`backend/app/billing.py`): fires only on the transition *into* `past_due`/`unpaid` (not on repeat webhook deliveries while already there, and not on a deliberate cancellation). Shipped 2026-09-15.
- [x] Admin alert on new feedback — `POST /feedback` now emails everyone listed in `ADMIN_EMAIL` (comma-separated) whenever a real (non-spam) submission comes in, with the category, subject, message, and submitter's email, plus a link into the admin panel. Submitter-controlled fields are HTML-escaped before going into the email. No-op if `ADMIN_EMAIL` isn't set. Shipped 2026-09-15; **needs `ADMIN_EMAIL` set on Render** (see credentials section above) to actually send anything.
- [x] Welcome email after verification — `AuthActionPage.tsx` now calls a new `POST /auth/welcome-email` endpoint right after a user completes email verification. The endpoint independently re-checks with Firebase that the account is actually verified and only sends once per account (tracked via a `welcome_email_sent` flag on the user's profile doc), so it can't be used to spam arbitrary or unverified addresses. Shipped 2026-09-15.
- [x] Subscription-started email — a new Pro subscriber gets a "Welcome to CratePrep Pro" email right after checkout completes (mentions the trial and when they'll be charged, if applicable), instead of the first billing email they ever see being the bad one. Hooks into `checkout.session.completed` in `backend/app/billing.py`; guarded against a retried webhook re-sending it to an already-Pro account. Shipped 2026-09-15.
- [x] Cancellation-confirmation email — hooks into the existing `customer.subscription.deleted` webhook: confirms the subscription has ended and the account is back on Free, with a resubscribe link. Skipped when the subscription ended via the payment-failure dunning process (Stripe's own `cancellation_details.reason`) since those users already got the payment-failed email, and guarded against resending on a retried webhook for an already-canceled account. Shipped 2026-09-15.
- [x] Approaching free-tier limit email — `POST /process` now emails a Free-plan user the first time their monthly usage reaches 80% of the 10-track limit (`USAGE_WARNING_THRESHOLD` in `backend/app/profile_store.py`), with an upgrade link. Sent at most once per billing period (tracked via a `usage_warning_period` flag, same pattern as `welcome_email_sent`). Shipped 2026-09-15.
- [x] Password-changed security notice — `AuthActionPage.tsx` calls a new `POST /auth/password-changed-notice` endpoint right after a password reset succeeds, so an account owner finds out immediately if someone else changed their password. Same exposure/rate-limiting as `/auth/forgot-password` (no stronger proof a reset just happened — a false positive is a mildly annoying email, not a security hole). Shipped 2026-09-15.

## Other loose ends noticed while working in this repo

- [ ] Connect the **Render** connector at claude.ai → Settings → Connectors (search "Render", authorize via OAuth) — lets Claude check deploys/logs/metrics and manage the web service directly
- [ ] Connect the **Vercel** connector the same way (search "Vercel") — lets Claude check deployments/projects directly
- [ ] After connecting both, enable them for future chat sessions (per-conversation connector toggle) so their tools actually load
