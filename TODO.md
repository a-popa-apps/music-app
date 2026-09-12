# TODO

## Credentials / environment variables

Backend (Render):
- [ ] `ANTHROPIC_API_KEY` — enables the new AI filename cleanup feature; currently no-ops without it
- [ ] `FIREBASE_SERVICE_ACCOUNT_JSON` — service-account JSON for `firebase-admin`; without it, auth/Firestore-backed features (profiles, history, admin) silently disable rather than error (check `/health` → `firebase_configured`)
- [ ] `STRIPE_SECRET_KEY` — required for billing/checkout to work at all
- [ ] `STRIPE_WEBHOOK_SECRET` — required for Stripe webhook signature verification (plan upgrades/downgrades won't sync without it)
- [ ] `STRIPE_PRICE_MONTHLY` / `STRIPE_PRICE_ANNUAL` — Stripe Price IDs for the Pro plan
- [ ] `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` — genre lookup; without these it silently falls back to Discogs only (check `/health` → `spotify_configured`)
- [ ] `DISCOGS_TOKEN` — optional, just raises Discogs' rate limit; works without it

Frontend (Vercel):
- [ ] `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, `VITE_FIREBASE_MESSAGING_SENDER_ID`, `VITE_FIREBASE_APP_ID` — client-side Firebase config (sign-in won't work without these)
- [ ] `VITE_BACKEND_URL` — already defaults to the Render URL in `.env.example`; only needs setting if that URL changes

## Verify what's actually already set

I can't read Render/Vercel's env var dashboards from here, so I don't know which of the above are already configured vs. missing — only that the *code* expects them. Worth doing:
- [ ] Hit the deployed backend's `/health` endpoint and check `firebase_configured` / `spotify_configured` / `ai_cleanup_configured`
- [ ] Confirm sign-in actually works on the deployed frontend (validates the `VITE_FIREBASE_*` vars)
- [ ] Do a real test purchase in Stripe test mode to confirm billing end-to-end

## Other loose ends noticed while working in this repo

- [ ] Give Claude (this session's GitHub App) write access on Render/Vercel if you want direct deploy/log access — not needed for normal code work, only for live debugging or triggering deploys directly
