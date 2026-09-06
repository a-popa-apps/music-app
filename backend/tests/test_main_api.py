from types import SimpleNamespace

import pytest

pytest.importorskip("essentia")

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.process_audio import MAX_FILES_FREE, MAX_FILES_PRO, validate_files


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


def _fake_file(name="track.mp3", size=1000):
    return SimpleNamespace(filename=name, size=size)


def test_validate_files_free_tier_rejects_over_25():
    files = [_fake_file(f"track{i}.mp3") for i in range(26)]
    with pytest.raises(HTTPException) as exc_info:
        validate_files(files, max_files=MAX_FILES_FREE)
    assert exc_info.value.status_code == 400


def test_validate_files_free_tier_allows_up_to_25():
    files = [_fake_file(f"track{i}.mp3") for i in range(25)]
    validate_files(files, max_files=MAX_FILES_FREE)


def test_validate_files_pro_tier_allows_more_than_free_limit():
    files = [_fake_file(f"track{i}.mp3") for i in range(40)]
    validate_files(files, max_files=MAX_FILES_PRO)


def test_validate_files_pro_tier_rejects_over_50():
    files = [_fake_file(f"track{i}.mp3") for i in range(51)]
    with pytest.raises(HTTPException) as exc_info:
        validate_files(files, max_files=MAX_FILES_PRO)
    assert exc_info.value.status_code == 400
