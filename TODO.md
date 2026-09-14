# TODO

## Credentials / environment variables

Backend (Render):
- [ ] `ANTHROPIC_API_KEY` — **confirmed missing** (`/health` → `ai_cleanup_configured: false`, checked 2026-09-14). Enables AI filename cleanup, AI batch summary, and feedback triage; all three currently no-op without it.
- [x] `FIREBASE_SERVICE_ACCOUNT_JSON` — **confirmed set** (`/health` → `firebase_configured: true`, checked 2026-09-14).
- [ ] `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRICE_MONTHLY` / `STRIPE_PRICE_ANNUAL` — not checkable via `/health` (no field for it); still needs a real test-mode purchase to confirm end-to-end (see below).
- [x] `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` — **confirmed set** (`/health` → `spotify_configured: true`, checked 2026-09-14).
- [ ] `DISCOGS_TOKEN` — optional, unconfirmed either way; works without it.

Frontend (Vercel):
- [ ] `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, `VITE_FIREBASE_MESSAGING_SENDER_ID`, `VITE_FIREBASE_APP_ID` — client-side Firebase config (sign-in won't work without these)
- [ ] `VITE_BACKEND_URL` — already defaults to the Render URL in `.env.example`; only needs setting if that URL changes

## Verify what's actually already set

This session's network access was restricted for most of this work (couldn't reach any external site, including the production backend); that got fixed 2026-09-14 by switching the environment to full network access, so the checks below could finally run for real:
- [x] Hit the deployed backend's `/health` endpoint — confirmed `firebase_configured: true`, `spotify_configured: true`, `ai_cleanup_configured: false`.
- [x] Confirmed the deployed frontend (`music-app-sage-sigma.vercel.app`) is reachable (HTTP 200) — but reachability isn't the same as a verified working sign-in flow; still worth actually signing in once to be sure the `VITE_FIREBASE_*` vars are correct, not just present.
- [ ] Do a real test purchase in Stripe test mode to confirm billing end-to-end — still open, `/health` has no field for Stripe config status.

## Other loose ends noticed while working in this repo

- [ ] Connect the **Render** connector at claude.ai → Settings → Connectors (search "Render", authorize via OAuth) — lets Claude check deploys/logs/metrics and manage the web service directly
- [ ] Connect the **Vercel** connector the same way (search "Vercel") — lets Claude check deployments/projects directly
- [ ] After connecting both, enable them for future chat sessions (per-conversation connector toggle) so their tools actually load
