from app import ai_cleanup


class TestEmptyInput:
    def test_returns_none_for_empty_stem(self, monkeypatch):
        called = []
        monkeypatch.setattr(ai_cleanup, "generate_json", lambda *a, **k: called.append(1))
        assert ai_cleanup.ai_split_artist_title("   ") is None
        assert called == []  # never even calls out for an empty stem


class TestSplitting:
    def test_confident_response_is_parsed(self, monkeypatch):
        monkeypatch.setattr(
            ai_cleanup,
            "generate_json",
            lambda *a, **k: {"artist": "Bicep", "title": "Glue", "confident": True},
        )
        result = ai_cleanup.ai_split_artist_title("bicepgluefinalmasterv2")
        assert result == ("Bicep", "Glue")

    def test_not_confident_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            ai_cleanup,
            "generate_json",
            lambda *a, **k: {"artist": None, "title": None, "confident": False},
        )
        assert ai_cleanup.ai_split_artist_title("track1") is None

    def test_missing_artist_or_title_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            ai_cleanup,
            "generate_json",
            lambda *a, **k: {"artist": "Someone", "title": None, "confident": True},
        )
        assert ai_cleanup.ai_split_artist_title("ambiguous") is None

    def test_no_result_from_provider_returns_none(self, monkeypatch):
        # Covers an unset API key, an API error, or a budget cap -- all
        # collapsed into generate_json returning None.
        monkeypatch.setattr(ai_cleanup, "generate_json", lambda *a, **k: None)
        assert ai_cleanup.ai_split_artist_title("whatever") is None

    def test_strips_whitespace_from_stem_before_calling(self, monkeypatch):
        captured = {}

        def fake_generate_json(system_prompt, content, schema):
            captured["content"] = content
            return {"artist": "A", "title": "B", "confident": True}

        monkeypatch.setattr(ai_cleanup, "generate_json", fake_generate_json)
        ai_cleanup.ai_split_artist_title("  messy stem  ")
        assert captured["content"] == "messy stem"
