import json
from types import SimpleNamespace

import pytest

from app import batch_summary


@pytest.fixture(autouse=True)
def _reset_client_cache(monkeypatch):
    monkeypatch.setattr(batch_summary, "_client", None)


def _fake_response(payload: dict):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps(payload))]
    )


def _manifest(*entries: dict) -> dict:
    return {f"track{i}.mp3": entry for i, entry in enumerate(entries)}


class TestNoApiKey:
    def test_returns_none_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        manifest = _manifest(
            {"bpm": 128, "camelot": "8A", "genre": "House", "energy": 6},
            {"bpm": 130, "camelot": "9A", "genre": "House", "energy": 7},
        )
        assert batch_summary.generate_batch_summary(manifest) is None


class TestTooFewTracks:
    def test_returns_none_for_single_track(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        manifest = _manifest({"bpm": 128, "camelot": "8A", "genre": "House", "energy": 6})
        assert batch_summary.generate_batch_summary(manifest) is None

    def test_errored_tracks_dont_count_toward_minimum(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        manifest = _manifest(
            {"bpm": 128, "camelot": "8A", "genre": "House", "energy": 6},
            {"error": "Processing failed: boom"},
        )
        assert batch_summary.generate_batch_summary(manifest) is None


class TestSummaryGeneration:
    def test_returns_summary_text(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _fake_response(
                    {"summary": "Mostly house around 128 BPM, energy builds steadily."}
                )
            )
        )
        monkeypatch.setattr(batch_summary, "_get_client", lambda: fake_client)

        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
        )
        result = batch_summary.generate_batch_summary(manifest)

        assert result == "Mostly house around 128 BPM, energy builds steadily."

    def test_excludes_errored_tracks_from_payload(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        captured = {}

        def fake_create(**kwargs):
            captured["messages"] = kwargs["messages"]
            return _fake_response({"summary": "ok"})

        fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
        monkeypatch.setattr(batch_summary, "_get_client", lambda: fake_client)

        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
            {"error": "Processing failed: boom"},
        )
        batch_summary.generate_batch_summary(manifest)

        sent = json.loads(captured["messages"][0]["content"])
        assert len(sent) == 2

    def test_empty_summary_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(create=lambda **kwargs: _fake_response({"summary": ""}))
        )
        monkeypatch.setattr(batch_summary, "_get_client", lambda: fake_client)

        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
        )
        assert batch_summary.generate_batch_summary(manifest) is None

    def test_api_error_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def raise_error(**kwargs):
            raise RuntimeError("network down")

        fake_client = SimpleNamespace(messages=SimpleNamespace(create=raise_error))
        monkeypatch.setattr(batch_summary, "_get_client", lambda: fake_client)

        manifest = _manifest(
            {"bpm": 126, "camelot": "8A", "genre": "House", "energy": 5},
            {"bpm": 128, "camelot": "9A", "genre": "House", "energy": 7},
        )
        assert batch_summary.generate_batch_summary(manifest) is None
