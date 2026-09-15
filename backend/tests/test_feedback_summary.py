import json

from app import feedback_summary


class TestEmptyInput:
    def test_returns_none_for_no_entries(self, monkeypatch):
        called = []
        monkeypatch.setattr(feedback_summary, "generate_json", lambda *a, **k: called.append(1))
        assert feedback_summary.generate_feedback_summary([]) is None
        assert called == []  # never even calls out with nothing to summarize


class TestSummaryGeneration:
    def test_returns_summary_text(self, monkeypatch):
        monkeypatch.setattr(
            feedback_summary,
            "generate_json",
            lambda *a, **k: {"summary": "Two people report the export button doing nothing."},
        )
        entries = [
            {"category": "support", "subject": "Export broken", "message": "Nothing happens"},
            {"category": "support", "subject": None, "message": "Export button is dead for me too"},
        ]
        result = feedback_summary.generate_feedback_summary(entries)
        assert result == "Two people report the export button doing nothing."

    def test_only_sends_category_subject_message(self, monkeypatch):
        captured = {}

        def fake_generate_json(system_prompt, content, schema):
            captured["content"] = content
            return {"summary": "ok"}

        monkeypatch.setattr(feedback_summary, "generate_json", fake_generate_json)

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

        sent = json.loads(captured["content"])
        assert sent == [{"category": "feedback", "subject": "Idea", "message": "Add dark mode"}]

    def test_empty_summary_returns_none(self, monkeypatch):
        monkeypatch.setattr(feedback_summary, "generate_json", lambda *a, **k: {"summary": ""})
        entries = [{"category": "support", "subject": "Bug", "message": "It crashed"}]
        assert feedback_summary.generate_feedback_summary(entries) is None

    def test_no_result_from_provider_returns_none(self, monkeypatch):
        monkeypatch.setattr(feedback_summary, "generate_json", lambda *a, **k: None)
        entries = [{"category": "support", "subject": "Bug", "message": "It crashed"}]
        assert feedback_summary.generate_feedback_summary(entries) is None
