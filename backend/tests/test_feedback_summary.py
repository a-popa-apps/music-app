import json
from types import SimpleNamespace

import pytest

from app import feedback_summary


@pytest.fixture(autouse=True)
def _reset_client_cache(monkeypatch):
    monkeypatch.setattr(feedback_summary, "_client", None)


def _fake_response(payload: dict):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps(payload))]
    )


class TestNoApiKey:
    def test_returns_none_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        entries = [{"category": "support", "subject": "Bug", "message": "It crashed"}]
        assert feedback_summary.generate_feedback_summary(entries) is None


class TestEmptyInput:
    def test_returns_none_for_no_entries(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        assert feedback_summary.generate_feedback_summary([]) is None


class TestSummaryGeneration:
    def test_returns_summary_text(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _fake_response(
                    {"summary": "Two people report the export button doing nothing."}
                )
            )
        )
        monkeypatch.setattr(feedback_summary, "_get_client", lambda: fake_client)

        entries = [
            {"category": "support", "subject": "Export broken", "message": "Nothing happens"},
            {"category": "support", "subject": None, "message": "Export button is dead for me too"},
        ]
        result = feedback_summary.generate_feedback_summary(entries)

        assert result == "Two people report the export button doing nothing."

    def test_only_sends_category_subject_message(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        captured = {}

        def fake_create(**kwargs):
            captured["messages"] = kwargs["messages"]
            return _fake_response({"summary": "ok"})

        fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
        monkeypatch.setattr(feedback_summary, "_get_client", lambda: fake_client)

        entries = [
            {
                "category": "feedback",
                "subject": "Idea",
                "message": "Add dark mode",
                "email": "user@example.com",
                "uid": "uid-123",
                "feedback_id": "f1",
            }
        ]
        feedback_summary.generate_feedback_summary(entries)

        sent = json.loads(captured["messages"][0]["content"])
        assert sent == [{"category": "feedback", "subject": "Idea", "message": "Add dark mode"}]

    def test_empty_summary_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(create=lambda **kwargs: _fake_response({"summary": ""}))
        )
        monkeypatch.setattr(feedback_summary, "_get_client", lambda: fake_client)

        entries = [{"category": "support", "subject": "Bug", "message": "It crashed"}]
        assert feedback_summary.generate_feedback_summary(entries) is None

    def test_api_error_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def raise_error(**kwargs):
            raise RuntimeError("network down")

        fake_client = SimpleNamespace(messages=SimpleNamespace(create=raise_error))
        monkeypatch.setattr(feedback_summary, "_get_client", lambda: fake_client)

        entries = [{"category": "support", "subject": "Bug", "message": "It crashed"}]
        assert feedback_summary.generate_feedback_summary(entries) is None
