import json

from app import batch_summary


def _manifest(*entries: dict) -> dict:
    return {f"track{i}.mp3": entry for i, entry in enumerate(entries)}


class TestTooFewTracks:
    def test_returns_none_for_single_track(self, monkeypatch):
        called = []
        monkeypatch.setattr(batch_summary, "generate_json", lambda *a, **k: called.append(1))
        manifest = _manifest({"bpm": 128, "camelot": "8A", "genre": "House", "energy": 6})
        assert batch_summary.generate_batch_summary(manifest) is None
        assert called == []  # never even calls out below the minimum

    def test_errored_tracks_dont_count_toward_minimum(self, monkeypatch):
        monkeypatch.setattr(batch_summary, "generate_json", lambda *a, **k: {"summary": "ok"})
        manifest = _manifest(
            {"bpm": 128, "camelot": "8A", "genre": "House", "energy": 6},
            {"error": "Processing failed: boom"},
        )
        assert batch_summary.generate_batch_summary(manifest) is None


class TestSummaryGeneration:
    def test_returns_summary_text(self, monkeypatch):
        monkeypatch.setattr(
            batch_summary,
            "generate_json",
            lambda *a, **k: {"summary": "Mostly house around 128 BPM, energy builds steadily."},
        )
        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
        )
        result = batch_summary.generate_batch_summary(manifest)
        assert result == "Mostly house around 128 BPM, energy builds steadily."

    def test_excludes_errored_tracks_from_payload(self, monkeypatch):
        captured = {}

        def fake_generate_json(system_prompt, content, schema):
            captured["content"] = content
            return {"summary": "ok"}

        monkeypatch.setattr(batch_summary, "generate_json", fake_generate_json)

        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
            {"error": "Processing failed: boom"},
        )
        batch_summary.generate_batch_summary(manifest)

        sent = json.loads(captured["content"])
        assert len(sent) == 2

    def test_empty_summary_returns_none(self, monkeypatch):
        monkeypatch.setattr(batch_summary, "generate_json", lambda *a, **k: {"summary": ""})
        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
        )
        assert batch_summary.generate_batch_summary(manifest) is None

    def test_no_result_from_provider_returns_none(self, monkeypatch):
        monkeypatch.setattr(batch_summary, "generate_json", lambda *a, **k: None)
        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
        )
        assert batch_summary.generate_batch_summary(manifest) is None
