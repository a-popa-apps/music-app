import json
import urllib.error

from app import ai_client

SCHEMA = {
    "type": "OBJECT",
    "properties": {"summary": {"type": "STRING"}},
    "required": ["summary"],
}


class FakeResponse:
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _gemini_response(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


class TestNoApiKey:
    def test_returns_none_without_api_key(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", None)
        assert ai_client.generate_json("system", "content", SCHEMA) is None


class TestBudget:
    def test_returns_none_when_budget_exhausted(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")
        monkeypatch.setattr(ai_client, "allow_ai_call", lambda: False)
        called = []
        monkeypatch.setattr(
            ai_client.urllib.request, "urlopen", lambda req, timeout=None: called.append(1)
        )

        assert ai_client.generate_json("system", "content", SCHEMA) is None
        assert called == []


class TestGeneration:
    def test_parses_json_response(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")
        monkeypatch.setattr(
            ai_client.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(_gemini_response('{"summary": "ok"}')),
        )

        assert ai_client.generate_json("system", "content", SCHEMA) == {"summary": "ok"}

    def test_posts_expected_request_shape(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["headers"] = {k.lower(): v for k, v in req.headers.items()}
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return FakeResponse(_gemini_response('{"summary": "ok"}'))

        monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)

        ai_client.generate_json("be terse", "the input", SCHEMA)

        assert captured["method"] == "POST"
        assert ai_client.GEMINI_MODEL in captured["url"]
        assert captured["headers"]["x-goog-api-key"] == "test-key"
        assert captured["body"]["contents"] == [{"role": "user", "parts": [{"text": "the input"}]}]
        assert captured["body"]["systemInstruction"] == {"parts": [{"text": "be terse"}]}
        assert captured["body"]["generationConfig"]["responseMimeType"] == "application/json"
        assert captured["body"]["generationConfig"]["responseSchema"] == SCHEMA

    def test_request_failure_returns_none(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")

        def raise_error(req, timeout=None):
            raise OSError("network down")

        monkeypatch.setattr(ai_client.urllib.request, "urlopen", raise_error)

        assert ai_client.generate_json("system", "content", SCHEMA) is None

    def test_malformed_json_returns_none(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")
        monkeypatch.setattr(
            ai_client.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(_gemini_response("not json")),
        )

        assert ai_client.generate_json("system", "content", SCHEMA) is None

    def test_unexpected_response_shape_returns_none(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")
        monkeypatch.setattr(
            ai_client.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse({"candidates": []}),
        )

        assert ai_client.generate_json("system", "content", SCHEMA) is None


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.com", code, "error", {}, None)


class TestRateLimitAlert:
    def test_alerts_admins_on_429(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")

        def raise_429(req, timeout=None):
            raise _http_error(429)

        monkeypatch.setattr(ai_client.urllib.request, "urlopen", raise_429)
        alerts = []
        monkeypatch.setattr(ai_client, "notify_admins", lambda subject, html: alerts.append(subject))

        assert ai_client.generate_json("system", "content", SCHEMA) is None
        assert len(alerts) == 1
        assert "rate limit" in alerts[0].lower()

    def test_does_not_alert_on_other_http_errors(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")

        def raise_500(req, timeout=None):
            raise _http_error(500)

        monkeypatch.setattr(ai_client.urllib.request, "urlopen", raise_500)
        alerts = []
        monkeypatch.setattr(ai_client, "notify_admins", lambda subject, html: alerts.append(subject))

        assert ai_client.generate_json("system", "content", SCHEMA) is None
        assert alerts == []

    def test_does_not_alert_twice_for_the_same_day(self, monkeypatch):
        monkeypatch.setattr(ai_client, "GEMINI_API_KEY", "test-key")

        def raise_429(req, timeout=None):
            raise _http_error(429)

        monkeypatch.setattr(ai_client.urllib.request, "urlopen", raise_429)
        alerts = []
        monkeypatch.setattr(ai_client, "notify_admins", lambda subject, html: alerts.append(subject))

        ai_client.generate_json("system", "content", SCHEMA)
        ai_client.generate_json("system", "content", SCHEMA)

        assert len(alerts) == 1
