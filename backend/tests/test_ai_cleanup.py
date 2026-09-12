import json
from types import SimpleNamespace

import pytest

from app import ai_cleanup


@pytest.fixture(autouse=True)
def _reset_client_cache(monkeypatch):
    # Each test controls ANTHROPIC_API_KEY explicitly; make sure a client
    # cached by an earlier test doesn't leak in and short-circuit _get_client.
    monkeypatch.setattr(ai_cleanup, "_client", None)


def _fake_response(payload: dict):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps(payload))]
    )


class TestNoApiKey:
    def test_returns_none_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert ai_cleanup.ai_split_artist_title("some messy filename") is None


class TestEmptyInput:
    def test_returns_none_for_empty_stem(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        assert ai_cleanup.ai_split_artist_title("   ") is None


class TestSplitting:
    def test_confident_response_is_parsed(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _fake_response(
                    {"artist": "Bicep", "title": "Glue", "confident": True}
                )
            )
        )
        monkeypatch.setattr(ai_cleanup, "_get_client", lambda: fake_client)

        result = ai_cleanup.ai_split_artist_title("bicepgluefinalmasterv2")

        assert result == ("Bicep", "Glue")

    def test_not_confident_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _fake_response(
                    {"artist": None, "title": None, "confident": False}
                )
            )
        )
        monkeypatch.setattr(ai_cleanup, "_get_client", lambda: fake_client)

        assert ai_cleanup.ai_split_artist_title("track1") is None

    def test_missing_artist_or_title_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: _fake_response(
                    {"artist": "Someone", "title": None, "confident": True}
                )
            )
        )
        monkeypatch.setattr(ai_cleanup, "_get_client", lambda: fake_client)

        assert ai_cleanup.ai_split_artist_title("ambiguous") is None

    def test_api_error_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def raise_error(**kwargs):
            raise RuntimeError("network down")

        fake_client = SimpleNamespace(messages=SimpleNamespace(create=raise_error))
        monkeypatch.setattr(ai_cleanup, "_get_client", lambda: fake_client)

        assert ai_cleanup.ai_split_artist_title("whatever") is None

    def test_malformed_json_returns_none(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        fake_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    content=[SimpleNamespace(type="text", text="not json")]
                )
            )
        )
        monkeypatch.setattr(ai_cleanup, "_get_client", lambda: fake_client)

        assert ai_cleanup.ai_split_artist_title("whatever") is None
