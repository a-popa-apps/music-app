from fastapi import Request

from app import auth


def _request(header: str | None) -> Request:
    headers = [(b"authorization", header.encode())] if header else []
    return Request({"type": "http", "headers": headers})


def test_get_current_user_returns_none_when_firebase_not_configured(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: None)
    assert auth.get_current_user(_request("Bearer sometoken")) is None


def test_get_current_user_returns_none_without_bearer_header(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: "fake-app")
    assert auth.get_current_user(_request(None)) is None
    assert auth.get_current_user(_request("Basic sometoken")) is None


def test_get_current_user_passes_check_revoked(monkeypatch):
    # Regression test: verify_id_token must be called with check_revoked=True
    # so a token issued before an account was banned/deleted stops working
    # immediately, instead of remaining valid until its own natural expiry.
    monkeypatch.setattr(auth, "get_app", lambda: "fake-app")
    captured = {}

    def fake_verify(token, app=None, check_revoked=False):
        captured["token"] = token
        captured["check_revoked"] = check_revoked
        return {"uid": "uid-1"}

    monkeypatch.setattr(auth.firebase_auth, "verify_id_token", fake_verify)

    uid = auth.get_current_user(_request("Bearer sometoken"))

    assert uid == "uid-1"
    assert captured["token"] == "sometoken"
    assert captured["check_revoked"] is True


def test_get_current_user_returns_none_on_revoked_or_invalid_token(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: "fake-app")

    def raise_error(token, app=None, check_revoked=False):
        raise ValueError("token revoked or invalid")

    monkeypatch.setattr(auth.firebase_auth, "verify_id_token", raise_error)

    assert auth.get_current_user(_request("Bearer sometoken")) is None


def test_generate_verification_link_returns_none_when_firebase_not_configured(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: None)
    assert auth.generate_verification_link("dj@example.com", "https://crateprep.app/auth/action") is None


def test_generate_verification_link_uses_handle_code_in_app(monkeypatch):
    # Regression test: without handle_code_in_app=True the generated link
    # points at Firebase's own hosted action page instead of continue_url,
    # and AuthActionPage.tsx (which reads mode/oobCode directly) would never
    # receive them.
    monkeypatch.setattr(auth, "get_app", lambda: "fake-app")
    captured = {}

    def fake_generate(email, action_code_settings=None, app=None):
        captured["email"] = email
        captured["settings"] = action_code_settings
        return "https://crateprep.app/auth/action?mode=verifyEmail&oobCode=abc"

    monkeypatch.setattr(auth.firebase_auth, "generate_email_verification_link", fake_generate)

    link = auth.generate_verification_link("dj@example.com", "https://crateprep.app/auth/action")

    assert link == "https://crateprep.app/auth/action?mode=verifyEmail&oobCode=abc"
    assert captured["email"] == "dj@example.com"
    assert captured["settings"].handle_code_in_app is True
    assert captured["settings"].url == "https://crateprep.app/auth/action"


def test_generate_password_reset_link_returns_none_when_firebase_not_configured(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: None)
    assert auth.generate_password_reset_link("dj@example.com", "https://crateprep.app/auth/action") is None


def test_generate_password_reset_link_returns_none_for_unknown_email(monkeypatch):
    # This is the enumeration-safety guarantee a public forgot-password
    # endpoint relies on: "not configured" and "no such account" must be
    # indistinguishable to the caller.
    monkeypatch.setattr(auth, "get_app", lambda: "fake-app")

    def raise_not_found(email, action_code_settings=None, app=None):
        raise auth.firebase_auth.UserNotFoundError("no user")

    monkeypatch.setattr(auth.firebase_auth, "generate_password_reset_link", raise_not_found)

    assert auth.generate_password_reset_link("nobody@example.com", "https://crateprep.app/auth/action") is None


def test_get_user_record_returns_none_when_firebase_not_configured(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: None)
    assert auth.get_user_record("uid-1") is None


def test_get_user_record_returns_none_for_unknown_uid(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: "fake-app")

    def raise_not_found(uid, app=None):
        raise auth.firebase_auth.UserNotFoundError("no user")

    monkeypatch.setattr(auth.firebase_auth, "get_user", raise_not_found)

    assert auth.get_user_record("uid-1") is None


def test_get_user_record_returns_the_record(monkeypatch):
    monkeypatch.setattr(auth, "get_app", lambda: "fake-app")
    sentinel = object()
    monkeypatch.setattr(auth.firebase_auth, "get_user", lambda uid, app=None: sentinel)

    assert auth.get_user_record("uid-1") is sentinel
