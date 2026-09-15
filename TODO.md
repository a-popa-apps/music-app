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
- [ ] `RESEND_API_KEY` — not yet set. Verification and password-reset emails are now sent through CratePrep's own branded templates instead of Firebase's default ones (`/health` → `email_configured`), but without this key nothing actually sends — signup/login still work, users just never get the email. Sign up at resend.com (free tier: 3,000 emails/month) and set this on Render.
- [ ] `EMAIL_FROM` — optional, defaults to Resend's own shared sandbox address (`onboarding@resend.dev`) so sending works immediately once `RESEND_API_KEY` is set. To send from a real `crateprep.app` address, verify that domain in the Resend dashboard (DNS records they provide) and set this to something like `CratePrep <noreply@crateprep.app>`.

## Verify what's actually already set

This session's network access was restricted for most of this work (couldn't reach any external site, including the production backend); that got fixed 2026-09-14 by switching the environment to full network access, so the checks below could finally run for real:
- [x] Hit the deployed backend's `/health` endpoint — confirmed `firebase_configured: true`, `spotify_configured: true`, `ai_cleanup_configured: false`.
- [x] Confirmed the deployed frontend (`music-app-sage-sigma.vercel.app`) is reachable (HTTP 200) and its production JS bundle has real (non-empty, non-placeholder) `VITE_FIREBASE_*` values baked in, checked 2026-09-14. Still not a fully verified sign-in (would need real user credentials, which this session won't request or handle).
- [ ] Do a real test purchase in Stripe test mode to confirm billing end-to-end — still open, `/health` has no field for Stripe config status.

## Reliability

- [x] Cost ceiling on AI-powered features — `backend/app/ai_budget.py` adds a global daily call limit (`DAILY_AI_CALL_LIMIT`, default 500) shared across AI filename cleanup, batch summary, and feedback triage, on top of the existing per-IP rate limiting. Surfaced on `/health` (`ai_calls_today`, `ai_daily_limit`). Shipped 2026-09-14.
- [x] Error monitoring — Sentry wired into the backend (`sentry_sdk.init(...)` in `main.py`, gated on `SENTRY_DSN` being set, same no-op-if-unset pattern as every other integration). Shipped 2026-09-14; **still needs `SENTRY_DSN` set on Render** (see credentials section above) before it actually reports anything.
- [x] Custom-branded transactional email — verification and password-reset emails no longer rely on Firebase's default (unbranded, `firebaseapp.com`-sender) templates. The backend now generates the one-time action link via the Firebase Admin SDK (`backend/app/auth.py`) and sends CratePrep's own HTML email (`backend/app/email_templates.py`) through Resend (`backend/app/email_service.py`) — two new endpoints, `POST /auth/send-verification-email` (authenticated) and `POST /auth/forgot-password` (public, rate-limited, enumeration-safe — always responds the same whether or not the email is registered). Shipped 2026-09-15; **still needs `RESEND_API_KEY` set on Render** before either email actually sends (see credentials section above).

## Other loose ends noticed while working in this repo

- [ ] Connect the **Render** connector at claude.ai → Settings → Connectors (search "Render", authorize via OAuth) — lets Claude check deploys/logs/metrics and manage the web service directly
- [ ] Connect the **Vercel** connector the same way (search "Vercel") — lets Claude check deployments/projects directly
- [ ] After connecting both, enable them for future chat sessions (per-conversation connector toggle) so their tools actually load
