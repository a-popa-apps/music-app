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
