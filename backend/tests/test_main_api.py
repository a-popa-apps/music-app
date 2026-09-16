import json
import os
import tempfile
from types import SimpleNamespace

import pytest

pytest.importorskip("essentia")

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.process_audio import MAX_FILES_FREE, MAX_FILES_PRO, validate_files


def _write_temp_zip(content: bytes) -> str:
    """build_zip/build_corrected_zip return a path to a temp file on disk
    (not bytes directly) -- see process_audio.py's own comment on why. Fakes
    standing in for them here need to produce a real file for FileResponse
    to actually serve."""
    fd, path = tempfile.mkstemp(suffix=".zip")
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return path


@pytest.fixture
def client():
    return TestClient(main.app)


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "essentia" in body
    assert "firebase_configured" in body


def test_health_does_not_leak_integration_config_or_ai_usage(client):
    # /health is public and unauthenticated -- this stuff belongs behind
    # /admin/stats instead, not handed to anyone who curls the URL.
    body = client.get("/health").json()
    for leaked_field in (
        "stripe_configured",
        "sentry_configured",
        "email_configured",
        "spotify_configured",
        "ai_cleanup_configured",
        "ai_calls_today",
        "ai_daily_limit",
    ):
        assert leaked_field not in body


def test_admin_stats_stripe_configured_requires_all_four_vars(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(
        main,
        "get_stats",
        lambda: {"total_users": 0, "by_plan": {}, "admin_count": 0, "recent_signups": []},
    )
    required = ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_MONTHLY", "STRIPE_PRICE_ANNUAL"]
    for var in required:
        monkeypatch.delenv(var, raising=False)
    assert client.get("/admin/stats").json()["stripe_configured"] is False

    for var in required:
        monkeypatch.setenv(var, "test-value")
    assert client.get("/admin/stats").json()["stripe_configured"] is True

    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    assert client.get("/admin/stats").json()["stripe_configured"] is False


def test_profile_requires_auth(client):
    assert client.get("/profile").status_code == 401
    assert client.put("/profile", json={}).status_code == 401
    assert client.delete("/profile").status_code == 401


def test_update_profile_forwards_toggle_fields(client, monkeypatch):
    # Regression test: ProfileUpdate previously had no `enhanced_detection`
    # field, so FastAPI/Pydantic silently dropped it from the request body
    # and the "Enhanced BPM & key detection" profile toggle could never
    # actually persist. Covers the same class of bug for the new
    # `ai_filename_cleanup` field added alongside it.
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    captured = {}

    def fake_save_settings(uid, payload):
        captured.update(payload)
        return payload

    monkeypatch.setattr(main, "save_settings", fake_save_settings)

    client.put(
        "/profile",
        json={
            "discogs_deep_search": True,
            "enhanced_detection": True,
            "ai_filename_cleanup": True,
            "auto_sort_by_energy": True,
        },
    )

    assert captured["discogs_deep_search"] is True
    assert captured["enhanced_detection"] is True
    assert captured["auto_sort_by_energy"] is True
    assert captured["ai_filename_cleanup"] is True


def test_history_requires_auth(client):
    assert client.get("/history").status_code == 401
    assert client.delete("/history").status_code == 401


def test_history_returns_list_for_authed_user(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "list_history", lambda uid: [{"filename": "a.mp3"}])
    res = client.get("/history")
    assert res.status_code == 200
    assert res.json() == [{"filename": "a.mp3"}]


def test_delete_history_clears_for_authed_user(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    calls = []
    monkeypatch.setattr(main, "clear_history", lambda uid: calls.append(uid))
    res = client.delete("/history")
    assert res.status_code == 200
    assert res.json() == {"status": "cleared"}
    assert calls == ["uid-1"]


def test_admin_endpoints_require_auth(client):
    assert client.get("/admin/users").status_code == 401
    assert client.get("/admin/stats").status_code == 401
    assert client.get("/admin/discount-codes").status_code == 401
    assert client.put("/admin/users/uid-1/plan", json={"plan": "pro"}).status_code == 401


def test_admin_forbidden_for_non_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": False})
    assert client.get("/admin/users").status_code == 403


def test_admin_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(main, "list_users", lambda: [{"uid": "u1"}])
    res = client.get("/admin/users")
    assert res.status_code == 200
    assert res.json() == [{"uid": "u1"}]


def test_admin_reset_usage_requires_auth(client):
    assert client.post("/admin/users/uid-1/reset-usage").status_code == 401


def test_admin_reset_usage_forbidden_for_non_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": False})
    assert client.post("/admin/users/uid-1/reset-usage").status_code == 403


def test_admin_reset_usage_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(
        main,
        "reset_usage",
        lambda uid: {"tracks_processed_this_period": 0, "usage_period_start": None},
    )
    res = client.post("/admin/users/target-uid/reset-usage")
    assert res.status_code == 200
    assert res.json()["tracks_processed_this_period"] == 0


def test_admin_read_user_history_requires_auth(client):
    assert client.get("/admin/users/target-uid/history").status_code == 401


def test_admin_read_user_history_forbidden_for_non_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": False})
    assert client.get("/admin/users/target-uid/history").status_code == 403


def test_admin_read_user_history_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(main, "list_history", lambda uid: [{"filename": "a.mp3", "uid": uid}])
    res = client.get("/admin/users/target-uid/history")
    assert res.status_code == 200
    assert res.json() == [{"filename": "a.mp3", "uid": "target-uid"}]


def test_submit_feedback_works_anonymously(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "create_feedback",
        lambda category, message, email=None, subject=None, uid=None: {
            "feedback_id": "f1",
            "category": category,
            "message": message,
            "read": False,
        },
    )
    res = client.post("/feedback", json={"category": "feedback", "message": "Love the app!"})
    assert res.status_code == 200
    assert res.json()["category"] == "feedback"
    assert res.json()["read"] is False


def test_submit_feedback_honeypot_filled_is_discarded(client, monkeypatch):
    calls = []
    monkeypatch.setattr(main, "create_feedback", lambda *a, **k: calls.append((a, k)))

    res = client.post(
        "/feedback",
        json={"category": "feedback", "message": "buy cheap watches", "website": "http://spam.example"},
    )
    assert res.status_code == 200
    assert calls == []  # never actually persisted


def test_submit_feedback_too_fast_is_discarded(client, monkeypatch):
    import time as time_module

    calls = []
    monkeypatch.setattr(main, "create_feedback", lambda *a, **k: calls.append((a, k)))

    res = client.post(
        "/feedback",
        json={
            "category": "feedback",
            "message": "hi",
            "form_rendered_at": time_module.time() * 1000,  # submitted "instantly"
        },
    )
    assert res.status_code == 200
    assert calls == []


def test_submit_feedback_normal_timing_is_not_discarded(client, monkeypatch):
    import time as time_module

    calls = []
    monkeypatch.setattr(
        main,
        "create_feedback",
        lambda *a, **k: calls.append((a, k)) or {"feedback_id": "f1", "read": False},
    )

    res = client.post(
        "/feedback",
        json={
            "category": "feedback",
            "message": "hi",
            "form_rendered_at": (time_module.time() - 5) * 1000,  # 5s ago, a real human pace
        },
    )
    assert res.status_code == 200
    assert len(calls) == 1


def test_submit_feedback_rejects_invalid_category(client):
    res = client.post("/feedback", json={"category": "nonsense", "message": "hi"})
    assert res.status_code == 400


def test_submit_feedback_sends_admin_alert(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "create_feedback",
        lambda *a, **k: {"feedback_id": "f1", "category": "support", "read": False},
    )
    captured = {}
    monkeypatch.setattr(
        main, "notify_admins", lambda subject, html: captured.update(subject=subject, html=html)
    )

    res = client.post("/feedback", json={"category": "support", "message": "it's broken"})

    assert res.status_code == 200
    assert "support" in captured["subject"].lower()
    assert "it&#x27;s broken" in captured["html"]


def test_submit_feedback_admin_alert_not_sent_when_discarded_as_spam(client, monkeypatch):
    monkeypatch.setattr(
        main, "create_feedback", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not persist"))
    )
    called = []
    monkeypatch.setattr(main, "notify_admins", lambda *a, **k: called.append(1))

    res = client.post(
        "/feedback",
        json={"category": "feedback", "message": "buy cheap watches", "website": "http://spam.example"},
    )

    assert res.status_code == 200
    assert called == []


def test_admin_feedback_requires_auth(client):
    assert client.get("/admin/feedback").status_code == 401
    assert client.patch("/admin/feedback/some-id", json={"read": True}).status_code == 401


def test_admin_feedback_forbidden_for_non_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": False})
    assert client.get("/admin/feedback").status_code == 403


def test_admin_feedback_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(main, "list_feedback", lambda: [{"feedback_id": "f1", "read": False}])
    res = client.get("/admin/feedback")
    assert res.status_code == 200
    assert res.json() == [{"feedback_id": "f1", "read": False}]


def test_admin_mark_feedback_read_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(
        main, "mark_feedback_read", lambda feedback_id, read: {"feedback_id": feedback_id, "read": read}
    )
    res = client.patch("/admin/feedback/f1", json={"read": True})
    assert res.status_code == 200
    assert res.json() == {"feedback_id": "f1", "read": True}


def test_admin_delete_feedback_requires_auth(client):
    assert client.delete("/admin/feedback/some-id").status_code == 401
    assert client.post("/admin/feedback/bulk-delete", json={"feedback_ids": ["a"]}).status_code == 401


def test_admin_delete_feedback_forbidden_for_non_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": False})
    assert client.delete("/admin/feedback/some-id").status_code == 403
    assert client.post("/admin/feedback/bulk-delete", json={"feedback_ids": ["a"]}).status_code == 403


def test_admin_delete_feedback_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    captured = {}
    monkeypatch.setattr(main, "delete_feedback", lambda feedback_id: captured.setdefault("id", feedback_id))

    res = client.delete("/admin/feedback/f1")

    assert res.status_code == 200
    assert res.json() == {"deleted": True}
    assert captured["id"] == "f1"


def test_admin_delete_feedback_404_for_unknown_id(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})

    def fake_delete(feedback_id):
        raise ValueError(f"No such feedback submission: {feedback_id!r}")

    monkeypatch.setattr(main, "delete_feedback", fake_delete)

    res = client.delete("/admin/feedback/does-not-exist")
    assert res.status_code == 404


def test_admin_bulk_delete_feedback_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    captured = {}
    monkeypatch.setattr(
        main, "delete_feedback_batch", lambda feedback_ids: captured.setdefault("ids", feedback_ids)
    )

    res = client.post("/admin/feedback/bulk-delete", json={"feedback_ids": ["f1", "f2"]})

    assert res.status_code == 200
    assert res.json() == {"deleted": 2}
    assert captured["ids"] == ["f1", "f2"]


def test_admin_summarize_feedback_requires_auth(client):
    assert client.post("/admin/feedback/summarize").status_code == 401


def test_admin_summarize_feedback_forbidden_for_non_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": False})
    assert client.post("/admin/feedback/summarize").status_code == 403


def test_admin_summarize_feedback_only_sends_unread(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(
        main,
        "list_feedback",
        lambda: [
            {"feedback_id": "f1", "read": False, "message": "unread one"},
            {"feedback_id": "f2", "read": True, "message": "already read"},
        ],
    )
    captured = {}

    def fake_generate(entries):
        captured["entries"] = entries
        return "summary text"

    monkeypatch.setattr(main, "generate_feedback_summary", fake_generate)

    res = client.post("/admin/feedback/summarize")

    assert res.status_code == 200
    assert res.json() == {"summary": "summary text"}
    assert [e["feedback_id"] for e in captured["entries"]] == ["f1"]


def test_admin_billing_stats_requires_auth(client):
    assert client.get("/admin/billing-stats").status_code == 401


def test_admin_billing_stats_forbidden_for_non_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": False})
    assert client.get("/admin/billing-stats").status_code == 403


def test_admin_billing_stats_allowed_for_admin(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})
    monkeypatch.setattr(main, "get_billing_stats", lambda: {"mrr_cents": 1300})
    res = client.get("/admin/billing-stats")
    assert res.status_code == 200
    assert res.json() == {"mrr_cents": 1300}


def test_admin_billing_stats_returns_503_when_stripe_unconfigured(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "admin-uid")
    monkeypatch.setattr(main, "get_settings", lambda uid: {"is_admin": True})

    def _raise():
        raise RuntimeError("Stripe is not configured")

    monkeypatch.setattr(main, "get_billing_stats", _raise)
    res = client.get("/admin/billing-stats")
    assert res.status_code == 503


def test_process_requires_files_field(client):
    res = client.post("/process")
    assert res.status_code == 422


async def _fake_build_zip(files, **kwargs):
    return _write_temp_zip(b"zip bytes"), {}


def test_process_allows_anonymous_trial_within_limit(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)
    monkeypatch.setattr(main, "check_and_reserve_trial", lambda ip, count: None)
    monkeypatch.setattr(main, "build_zip", _fake_build_zip)
    res = client.post(
        "/process",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
    )
    assert res.status_code == 200
    assert res.content == b"zip bytes"


def test_process_anonymous_batch_over_trial_limit_rejected(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)
    files = [("files", (f"track{i}.mp3", b"fake audio", "audio/mpeg")) for i in range(6)]
    res = client.post("/process", files=files)
    assert res.status_code == 400


def test_process_anonymous_trial_exhausted_returns_402(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)

    def _raise(ip, count):
        raise ValueError("Free trial used up (5/5 tracks, 0 remaining). Sign up free for 10 tracks/month.")

    monkeypatch.setattr(main, "check_and_reserve_trial", _raise)
    res = client.post(
        "/process",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
    )
    assert res.status_code == 402


def test_process_rejects_unsupported_extension(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda uid: {
            "plan": "free",
            "discogs_deep_search": False,
            "filename_template": None,
            "tracks_processed_this_period": 0,
            "usage_period_start": None,
        },
    )
    res = client.post(
        "/process",
        files=[("files", ("track.txt", b"not audio", "text/plain"))],
    )
    assert res.status_code == 400


def test_process_sends_usage_warning_email_when_threshold_crossed(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda uid: {"plan": "free", "discogs_deep_search": False, "filename_template": None},
    )
    monkeypatch.setattr(main, "check_and_reserve_usage", lambda uid, count, plan, settings=None: (8, True))
    monkeypatch.setattr(
        main, "get_user_record", lambda uid: SimpleNamespace(email="dj@example.com", email_verified=True)
    )
    monkeypatch.setattr(main, "build_zip", _fake_build_zip)
    captured = {}
    monkeypatch.setattr(
        main, "send_email", lambda to, subject, html: captured.update(to=to, subject=subject) or True
    )

    res = client.post(
        "/process",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
    )

    assert res.status_code == 200
    assert captured["to"] == "dj@example.com"
    assert "limit" in captured["subject"].lower()


def test_process_does_not_send_usage_warning_when_not_flagged(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda uid: {"plan": "free", "discogs_deep_search": False, "filename_template": None},
    )
    monkeypatch.setattr(main, "check_and_reserve_usage", lambda uid, count, plan, settings=None: (3, False))
    monkeypatch.setattr(main, "build_zip", _fake_build_zip)
    sent = []
    monkeypatch.setattr(main, "send_email", lambda *a, **k: sent.append(1) or True)

    res = client.post(
        "/process",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
    )

    assert res.status_code == 200
    assert sent == []


def _fake_file(name="track.mp3", size=1000):
    return SimpleNamespace(filename=name, size=size)


def test_validate_files_free_tier_rejects_over_limit():
    files = [_fake_file(f"track{i}.mp3") for i in range(MAX_FILES_FREE + 1)]
    with pytest.raises(HTTPException) as exc_info:
        validate_files(files, max_files=MAX_FILES_FREE)
    assert exc_info.value.status_code == 400


def test_validate_files_free_tier_allows_up_to_limit():
    files = [_fake_file(f"track{i}.mp3") for i in range(MAX_FILES_FREE)]
    validate_files(files, max_files=MAX_FILES_FREE)


def test_validate_files_pro_tier_allows_more_than_free_limit():
    files = [_fake_file(f"track{i}.mp3") for i in range(40)]
    validate_files(files, max_files=MAX_FILES_PRO)


def test_validate_files_pro_tier_rejects_over_50():
    files = [_fake_file(f"track{i}.mp3") for i in range(51)]
    with pytest.raises(HTTPException) as exc_info:
        validate_files(files, max_files=MAX_FILES_PRO)
    assert exc_info.value.status_code == 400


def test_send_verification_email_requires_auth(client):
    res = client.post("/auth/send-verification-email")
    assert res.status_code == 401


def test_send_verification_email_no_ops_when_already_verified(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(
        main,
        "get_user_record",
        lambda uid: SimpleNamespace(email="dj@example.com", email_verified=True),
    )
    called = []
    monkeypatch.setattr(main, "send_email", lambda *a, **k: called.append(1) or True)

    res = client.post("/auth/send-verification-email")

    assert res.status_code == 200
    assert res.json() == {"sent": False}
    assert called == []


def test_send_verification_email_sends_when_unverified(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(
        main,
        "get_user_record",
        lambda uid: SimpleNamespace(email="dj@example.com", email_verified=False),
    )
    monkeypatch.setattr(
        main, "generate_verification_link", lambda email, continue_url: "https://crateprep.app/verify"
    )
    captured = {}

    def fake_send_email(to, subject, html):
        captured["to"] = to
        captured["subject"] = subject
        return True

    monkeypatch.setattr(main, "send_email", fake_send_email)

    res = client.post("/auth/send-verification-email")

    assert res.status_code == 200
    assert res.json() == {"sent": True}
    assert captured["to"] == "dj@example.com"


def test_forgot_password_always_returns_sent_true(client, monkeypatch):
    # The enumeration-safety guarantee: whether or not the email is
    # registered, the response must look identical.
    monkeypatch.setattr(main, "generate_password_reset_link", lambda email, continue_url: None)
    called = []
    monkeypatch.setattr(main, "send_email", lambda *a, **k: called.append(1) or True)

    res = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": True}
    assert called == []  # no link generated -- nothing was sent, but the response doesn't reveal that


def test_forgot_password_sends_email_when_account_exists(client, monkeypatch):
    monkeypatch.setattr(
        main, "generate_password_reset_link", lambda email, continue_url: "https://crateprep.app/reset"
    )
    captured = {}

    def fake_send_email(to, subject, html):
        captured["to"] = to
        return True

    monkeypatch.setattr(main, "send_email", fake_send_email)

    res = client.post("/auth/forgot-password", json={"email": "dj@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": True}
    assert captured["to"] == "dj@example.com"


def test_welcome_email_no_ops_when_account_does_not_exist(client, monkeypatch):
    monkeypatch.setattr(main, "get_user_by_email", lambda email: None)
    sent = []
    monkeypatch.setattr(main, "send_email", lambda *a, **k: sent.append(1) or True)

    res = client.post("/auth/welcome-email", json={"email": "nobody@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": False}
    assert sent == []


def test_welcome_email_no_ops_when_not_verified(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_user_by_email",
        lambda email: SimpleNamespace(uid="uid-1", email="dj@example.com", email_verified=False),
    )
    sent = []
    monkeypatch.setattr(main, "send_email", lambda *a, **k: sent.append(1) or True)

    res = client.post("/auth/welcome-email", json={"email": "dj@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": False}
    assert sent == []


def test_welcome_email_no_ops_when_already_sent(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_user_by_email",
        lambda email: SimpleNamespace(uid="uid-1", email="dj@example.com", email_verified=True),
    )
    monkeypatch.setattr(main, "get_settings", lambda uid: {"welcome_email_sent": True})
    sent = []
    monkeypatch.setattr(main, "send_email", lambda *a, **k: sent.append(1) or True)

    res = client.post("/auth/welcome-email", json={"email": "dj@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": False}
    assert sent == []


def test_welcome_email_sends_and_marks_when_first_time_verified(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_user_by_email",
        lambda email: SimpleNamespace(uid="uid-1", email="dj@example.com", email_verified=True),
    )
    monkeypatch.setattr(main, "get_settings", lambda uid: {"welcome_email_sent": False})
    captured = {}
    monkeypatch.setattr(
        main, "send_email", lambda to, subject, html: captured.update(to=to, subject=subject) or True
    )
    marked = []
    monkeypatch.setattr(main, "mark_welcome_email_sent", lambda uid: marked.append(uid))

    res = client.post("/auth/welcome-email", json={"email": "dj@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": True}
    assert captured["to"] == "dj@example.com"
    assert marked == ["uid-1"]


def test_welcome_email_does_not_mark_sent_when_delivery_fails(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_user_by_email",
        lambda email: SimpleNamespace(uid="uid-1", email="dj@example.com", email_verified=True),
    )
    monkeypatch.setattr(main, "get_settings", lambda uid: {"welcome_email_sent": False})
    monkeypatch.setattr(main, "send_email", lambda *a, **k: False)
    marked = []
    monkeypatch.setattr(main, "mark_welcome_email_sent", lambda uid: marked.append(uid))

    res = client.post("/auth/welcome-email", json={"email": "dj@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": False}
    assert marked == []


def test_password_changed_notice_sends_when_account_exists(client, monkeypatch):
    monkeypatch.setattr(
        main, "get_user_by_email", lambda email: SimpleNamespace(uid="uid-1", email="dj@example.com")
    )
    captured = {}
    monkeypatch.setattr(
        main, "send_email", lambda to, subject, html: captured.update(to=to, subject=subject) or True
    )

    res = client.post("/auth/password-changed-notice", json={"email": "dj@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": True}
    assert captured["to"] == "dj@example.com"
    assert "changed" in captured["subject"].lower()


def test_password_changed_notice_always_returns_sent_true(client, monkeypatch):
    # Same enumeration-safety guarantee as forgot-password: whether or not
    # the account exists, the response looks identical.
    monkeypatch.setattr(main, "get_user_by_email", lambda email: None)
    sent = []
    monkeypatch.setattr(main, "send_email", lambda *a, **k: sent.append(1) or True)

    res = client.post("/auth/password-changed-notice", json={"email": "nobody@example.com"})

    assert res.status_code == 200
    assert res.json() == {"sent": True}
    assert sent == []


async def _fake_build_corrected_zip(files, corrections, filename_template=None):
    return _write_temp_zip(b"corrected zip bytes")


def test_retag_requires_files_field(client):
    res = client.post("/process/retag", data={"corrections": "[]"})
    assert res.status_code == 422


def test_retag_works_anonymously(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)
    monkeypatch.setattr(main, "build_corrected_zip", _fake_build_corrected_zip)

    res = client.post(
        "/process/retag",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
        data={"corrections": json.dumps([{"artist": "A", "title": "B"}])},
    )

    assert res.status_code == 200
    assert res.content == b"corrected zip bytes"


def test_retag_rejects_unsupported_extension(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)
    res = client.post(
        "/process/retag",
        files=[("files", ("track.txt", b"not audio", "text/plain"))],
        data={"corrections": json.dumps([{}])},
    )
    assert res.status_code == 400


def test_retag_rejects_invalid_json_corrections(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)
    res = client.post(
        "/process/retag",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
        data={"corrections": "not json"},
    )
    assert res.status_code == 400


def test_retag_rejects_corrections_length_mismatch(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)
    res = client.post(
        "/process/retag",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
        data={"corrections": json.dumps([{}, {}])},
    )
    assert res.status_code == 400


def test_retag_passes_corrections_through_to_build_corrected_zip(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: None)
    captured = {}

    async def fake_build(files, corrections, filename_template=None):
        captured["corrections"] = corrections
        captured["filename_template"] = filename_template
        return _write_temp_zip(b"zip")

    monkeypatch.setattr(main, "build_corrected_zip", fake_build)

    corrections = [{"artist": "Fixed Artist", "title": "Fixed Title", "bpm": 128.0}]
    res = client.post(
        "/process/retag",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
        data={"corrections": json.dumps(corrections)},
    )

    assert res.status_code == 200
    assert captured["corrections"] == corrections
    assert captured["filename_template"] is None  # anonymous -- no profile to read one from


def test_retag_uses_filename_template_for_pro_user(client, monkeypatch):
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(
        main, "get_settings", lambda uid: {"plan": "pro", "filename_template": "{artist} - {title}"}
    )
    captured = {}

    async def fake_build(files, corrections, filename_template=None):
        captured["filename_template"] = filename_template
        return _write_temp_zip(b"zip")

    monkeypatch.setattr(main, "build_corrected_zip", fake_build)

    res = client.post(
        "/process/retag",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
        data={"corrections": json.dumps([{"artist": "A", "title": "B"}])},
    )

    assert res.status_code == 200
    assert captured["filename_template"] == "{artist} - {title}"


def test_retag_ignores_filename_template_for_free_user(client, monkeypatch):
    # Same double-gating as /process itself -- a stored template only ever
    # applies for Pro, regardless of what's in the profile doc.
    monkeypatch.setattr(main, "get_current_user", lambda request: "uid-1")
    monkeypatch.setattr(
        main, "get_settings", lambda uid: {"plan": "free", "filename_template": "{artist} - {title}"}
    )
    captured = {}

    async def fake_build(files, corrections, filename_template=None):
        captured["filename_template"] = filename_template
        return _write_temp_zip(b"zip")

    monkeypatch.setattr(main, "build_corrected_zip", fake_build)

    res = client.post(
        "/process/retag",
        files=[("files", ("track.mp3", b"fake audio", "audio/mpeg"))],
        data={"corrections": json.dumps([{"artist": "A", "title": "B"}])},
    )

    assert res.status_code == 200
    assert captured["filename_template"] is None
