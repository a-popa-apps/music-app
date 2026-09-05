import pytest

pytest.importorskip("essentia")

from fastapi.testclient import TestClient

from app import main


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


def test_profile_requires_auth(client):
    assert client.get("/profile").status_code == 401
    assert client.put("/profile", json={}).status_code == 401
    assert client.delete("/profile").status_code == 401


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


def test_process_requires_files_field(client):
    res = client.post("/process")
    assert res.status_code == 422


def test_process_rejects_unsupported_extension(client):
    res = client.post(
        "/process",
        files=[("files", ("track.txt", b"not audio", "text/plain"))],
    )
    assert res.status_code == 400
