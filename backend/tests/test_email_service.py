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


def test_notify_admins_does_nothing_when_unset(monkeypatch):
    monkeypatch.setattr(email_service, "ADMIN_EMAIL", "")
    sent = []
    monkeypatch.setattr(email_service, "send_email", lambda *a, **k: sent.append(1) or True)

    email_service.notify_admins("Subject", "<p>Hi</p>")

    assert sent == []


def test_notify_admins_sends_to_every_comma_separated_address(monkeypatch):
    monkeypatch.setattr(email_service, "ADMIN_EMAIL", "one@crateprep.app, two@crateprep.app")
    sent = []
    monkeypatch.setattr(email_service, "send_email", lambda to, subject, html: sent.append(to) or True)

    email_service.notify_admins("Subject", "<p>Hi</p>")

    assert sent == ["one@crateprep.app", "two@crateprep.app"]


def test_notify_admins_passes_subject_and_html_through(monkeypatch):
    monkeypatch.setattr(email_service, "ADMIN_EMAIL", "admin@crateprep.app")
    captured = {}
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda to, subject, html: captured.update(to=to, subject=subject, html=html) or True,
    )

    email_service.notify_admins("Alert!", "<p>Details</p>")

    assert captured == {"to": "admin@crateprep.app", "subject": "Alert!", "html": "<p>Details</p>"}
