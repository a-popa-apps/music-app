import json

from app import email_service


def test_send_email_returns_false_when_not_configured(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", None)
    assert email_service.send_email("dj@example.com", "Subject", "<p>Hi</p>") is False


def test_send_email_posts_to_resend_with_expected_payload(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(email_service, "EMAIL_FROM", "CratePrep <noreply@crateprep.app>")
    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["headers"] = {k.lower(): v for k, v in req.headers.items()}
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(email_service.urllib.request, "urlopen", fake_urlopen)

    result = email_service.send_email("dj@example.com", "Verify your email", "<p>Hi</p>")

    assert result is True
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["method"] == "POST"
    assert captured["headers"]["authorization"] == "Bearer test-key"
    assert captured["body"] == {
        "from": "CratePrep <noreply@crateprep.app>",
        "to": ["dj@example.com"],
        "subject": "Verify your email",
        "html": "<p>Hi</p>",
    }


def test_send_email_returns_false_on_request_failure(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "test-key")

    def raise_error(req, timeout=None):
        raise OSError("network down")

    monkeypatch.setattr(email_service.urllib.request, "urlopen", raise_error)

    assert email_service.send_email("dj@example.com", "Subject", "<p>Hi</p>") is False


def test_send_email_returns_false_on_non_2xx_status(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "test-key")

    class FakeResponse:
        status = 500

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(email_service.urllib.request, "urlopen", lambda req, timeout=None: FakeResponse())

    assert email_service.send_email("dj@example.com", "Subject", "<p>Hi</p>") is False
