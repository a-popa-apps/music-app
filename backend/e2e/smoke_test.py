#!/usr/bin/env python3
"""Live integration smoke tests against the real deployed backend.

This is deliberately NOT part of backend/tests/ (which stays mock-only
and CI-gated) -- it hits the actual production Render backend, a real
Firebase project, and real Stripe test-mode APIs. Run it on demand,
never automatically in CI: it needs live credentials, costs real
(test-mode) API calls, and an external outage shouldn't fail your
push/PR pipeline.

Why this exists: two real bugs this session (a Stripe SDK param-shape
mismatch, a webhook event that missed a redemption path) were only
catchable by hitting the real API -- a mocked unit test structurally
cannot see a schema drift or an untested webhook event type. This
script formalizes the manual curl-based verification already done by
hand into something repeatable.

Usage:
    E2E_FIREBASE_API_KEY=... python3 backend/e2e/smoke_test.py

Env vars:
    E2E_BACKEND_URL      optional, defaults to the production Render URL
    E2E_FIREBASE_API_KEY required -- the public Firebase web API key
                         (same one in frontend/.env.local, not a secret)
    E2E_ADMIN_EMAIL      optional -- a real admin account's email
    E2E_ADMIN_PASSWORD   optional -- that account's password
                         (admin-only checks are skipped, not failed,
                         if these two aren't provided)
"""

from __future__ import annotations

import io
import math
import os
import struct
import sys
import uuid
import wave

import httpx

BACKEND_URL = os.environ.get("E2E_BACKEND_URL", "https://music-app-backend-eo2m.onrender.com")
FIREBASE_API_KEY = os.environ.get("E2E_FIREBASE_API_KEY")
ADMIN_EMAIL = os.environ.get("E2E_ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("E2E_ADMIN_PASSWORD")

IDENTITY_TOOLKIT_URL = "https://identitytoolkit.googleapis.com/v1/accounts"

results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))
    status = "PASS" if condition else "FAIL"
    line = f"[{status}] {name}"
    if detail and not condition:
        line += f" -- {detail}"
    print(line)


def skip(name: str, reason: str) -> None:
    print(f"[SKIP] {name} -- {reason}")


def make_wav(freq: float, bpm_pulse: float, duration: float = 4, sr: int = 22050) -> bytes:
    """A short synthetic tone with a rhythmic amplitude pulse, so BPM/key
    detection has something real to work with (same approach used manually
    earlier this session)."""
    n = int(sr * duration)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = bytearray()
        beat_period = 60.0 / bpm_pulse
        for i in range(n):
            t = i / sr
            phase = (t % beat_period) / beat_period
            amp = 0.5 * (0.3 + 0.7 * max(0, 1 - phase * 6))
            sample = amp * math.sin(2 * math.pi * freq * t)
            frames += struct.pack("<h", int(max(-1, min(1, sample)) * 32767))
        w.writeframes(bytes(frames))
    return buffer.getvalue()


def firebase_sign_up(client: httpx.Client, email: str, password: str) -> str:
    res = client.post(
        f"{IDENTITY_TOOLKIT_URL}:signUp?key={FIREBASE_API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
    )
    res.raise_for_status()
    return res.json()["idToken"]


def firebase_sign_in(client: httpx.Client, email: str, password: str) -> str:
    res = client.post(
        f"{IDENTITY_TOOLKIT_URL}:signInWithPassword?key={FIREBASE_API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
    )
    res.raise_for_status()
    return res.json()["idToken"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def run() -> int:
    if not FIREBASE_API_KEY:
        print("E2E_FIREBASE_API_KEY is required. See this file's docstring.")
        return 1

    client = httpx.Client(timeout=60)
    test_uid_token: str | None = None

    try:
        # 1. Health -- retried, since Render's free-tier backend cold-starts
        # after being idle and a single request can time out during that.
        res = None
        for attempt in range(3):
            try:
                res = client.get(f"{BACKEND_URL}/health")
                break
            except httpx.TransportError as e:
                print(f"  (health check attempt {attempt + 1} failed: {e}, retrying...)")
        body = res.json() if res is not None and res.status_code == 200 else {}
        check(
            "GET /health",
            res is not None and res.status_code == 200 and body.get("essentia") is True,
            res.text if res is not None else "no response after retries",
        )
        check("firebase_configured", body.get("firebase_configured") is True)

        # 2. Fresh disposable account + profile defaults
        email = f"e2e-smoke-{uuid.uuid4().hex[:10]}@example.com"
        password = uuid.uuid4().hex
        test_uid_token = firebase_sign_up(client, email, password)
        res = client.get(f"{BACKEND_URL}/profile", headers=auth_headers(test_uid_token))
        profile = res.json() if res.status_code == 200 else {}
        check("GET /profile defaults", res.status_code == 200 and profile.get("plan") == "free")
        check("new account is not admin", profile.get("is_admin") is False)

        # 3. Anonymous /process requires auth (a real file, so this hits the
        # auth check and not FastAPI's earlier "files field missing" 422)
        res = client.post(
            f"{BACKEND_URL}/process",
            files={"files": ("t.wav", make_wav(200, 120, duration=1), "audio/wav")},
        )
        check("anonymous POST /process -> 401", res.status_code == 401, f"got {res.status_code}")

        # 4. Authenticated /process with a real synthetic track
        wav_bytes = make_wav(220, 128)
        res = client.post(
            f"{BACKEND_URL}/process",
            headers=auth_headers(test_uid_token),
            files={"files": ("smoke-test.wav", wav_bytes, "audio/wav")},
        )
        check(
            "authenticated POST /process -> 200 zip",
            res.status_code == 200 and res.content[:2] == b"PK",
            f"status={res.status_code} body={res.text[:200]}",
        )

        # 5. History reflects the processed track, then clears
        res = client.get(f"{BACKEND_URL}/history", headers=auth_headers(test_uid_token))
        history = res.json() if res.status_code == 200 else []
        check("GET /history includes processed track", len(history) == 1, str(history))

        res = client.delete(f"{BACKEND_URL}/history", headers=auth_headers(test_uid_token))
        check("DELETE /history -> 200", res.status_code == 200)

        res = client.get(f"{BACKEND_URL}/history", headers=auth_headers(test_uid_token))
        check("GET /history empty after clear", res.json() == [])

        # 6. Free-tier monthly quota boundary (25 tracks/month). One batch
        # request for the remaining 24 tracks -- not 24 separate requests --
        # to stay under the free tier's 5-requests-per-5-minutes rate limit
        # (MAX_REQUESTS_FREE), which is a separate, tighter limit from the
        # 25-tracks/month quota this step is actually testing.
        tiny_wav = make_wav(200, 120, duration=1)
        res = client.post(
            f"{BACKEND_URL}/process",
            headers=auth_headers(test_uid_token),
            files=[("files", (f"t{i}.wav", tiny_wav, "audio/wav")) for i in range(24)],
        )
        check("batch of 24 tracks -> 200", res.status_code == 200, f"status={res.status_code} body={res.text[:200]}")

        res = client.get(f"{BACKEND_URL}/profile", headers=auth_headers(test_uid_token))
        used = res.json().get("tracks_processed_this_period")
        check("quota counter reached 25", used == 25, f"got {used}")

        res = client.post(
            f"{BACKEND_URL}/process",
            headers=auth_headers(test_uid_token),
            files={"files": ("over-limit.wav", make_wav(200, 120, duration=1), "audio/wav")},
        )
        check(
            "26th track -> 402 quota exceeded",
            res.status_code == 402,
            f"status={res.status_code} body={res.text[:200]}",
        )

        # 7. Billing endpoints without completing a real Checkout page.
        # Portal is checked FIRST -- checkout creates a Stripe Customer as a
        # side effect (_get_or_create_customer), so this account would no
        # longer have "no billing account" once checkout has been called.
        res = client.post(f"{BACKEND_URL}/billing/portal", headers=auth_headers(test_uid_token))
        check(
            "POST /billing/portal with no billing account -> 400",
            res.status_code == 400,
            f"got {res.status_code}",
        )

        res = client.post(
            f"{BACKEND_URL}/billing/checkout",
            headers=auth_headers(test_uid_token),
            json={"billing_cycle": "monthly"},
        )
        checkout_url = res.json().get("url", "") if res.status_code == 200 else ""
        check(
            "POST /billing/checkout returns a Stripe URL",
            res.status_code == 200 and checkout_url.startswith("https://checkout.stripe.com/"),
            f"status={res.status_code} body={res.text[:200]}",
        )

        # 8. Admin-only checks (skipped without credentials)
        if ADMIN_EMAIL and ADMIN_PASSWORD:
            admin_token = firebase_sign_in(client, ADMIN_EMAIL, ADMIN_PASSWORD)

            res = client.get(f"{BACKEND_URL}/admin/users", headers=auth_headers(admin_token))
            check("GET /admin/users -> 200 list", res.status_code == 200 and isinstance(res.json(), list))

            res = client.get(f"{BACKEND_URL}/admin/stats", headers=auth_headers(admin_token))
            check("GET /admin/stats -> 200 w/ total_users", res.status_code == 200 and "total_users" in res.json())

            res = client.get(
                f"{BACKEND_URL}/admin/billing-stats", headers=auth_headers(admin_token)
            )
            check(
                "GET /admin/billing-stats -> 200 w/ mrr_cents",
                res.status_code == 200 and "mrr_cents" in res.json(),
                f"status={res.status_code} body={res.text[:200]}",
            )

            # The exact check that would have caught the PromotionCode.create
            # param-shape bug: this only passes if Stripe actually accepted
            # the Coupon + PromotionCode creation calls.
            res = client.post(
                f"{BACKEND_URL}/admin/discount-codes",
                headers=auth_headers(admin_token),
                json={"percent_off": 25, "max_uses": 1},
            )
            code_doc = res.json() if res.status_code == 200 else {}
            check(
                "POST /admin/discount-codes creates real Stripe coupon+promo",
                res.status_code == 200
                and bool(code_doc.get("stripe_coupon_id"))
                and bool(code_doc.get("stripe_promotion_code_id")),
                f"status={res.status_code} body={res.text[:300]}",
            )

            code = code_doc.get("code")
            if code:
                res = client.patch(
                    f"{BACKEND_URL}/admin/discount-codes/{code}",
                    headers=auth_headers(admin_token),
                    json={"active": False},
                )
                check("PATCH discount code deactivates", res.status_code == 200 and res.json().get("active") is False)

                res = client.get(
                    f"{BACKEND_URL}/admin/discount-codes", headers=auth_headers(admin_token)
                )
                codes = res.json() if res.status_code == 200 else []
                matching = next((c for c in codes if c.get("code") == code), None)
                check(
                    "GET /admin/discount-codes reflects deactivation",
                    matching is not None and matching.get("active") is False,
                )
        else:
            skip("admin-only checks", "E2E_ADMIN_EMAIL/E2E_ADMIN_PASSWORD not set")

    finally:
        # 9. Cleanup -- always delete the disposable account, pass or fail.
        # httpx doesn't raise on a non-2xx response by default, so this must
        # check the status explicitly or a failed delete goes unnoticed and
        # silently leaves the account behind.
        if test_uid_token:
            try:
                res = client.delete(f"{BACKEND_URL}/profile", headers=auth_headers(test_uid_token))
                if res.status_code != 200:
                    print(f"cleanup warning: DELETE /profile returned {res.status_code}: {res.text}")
            except Exception as e:
                print(f"cleanup warning: couldn't delete test account: {e}")
        client.close()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run())
