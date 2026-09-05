from app.clean_filename import (
    _clean_text,
    apply_template,
    clean_filename,
    compose_name,
    guess_split,
    local_dash_split,
    prepare_stem,
)


class TestPrepareStem:
    def test_splits_extension(self):
        stem, ext, version_tag = prepare_stem("Artist - Title.mp3")
        assert stem == "Artist - Title"
        assert ext == ".mp3"
        assert version_tag is None

    def test_no_extension(self):
        stem, ext, _ = prepare_stem("Artist - Title")
        assert stem == "Artist - Title"
        assert ext == ""

    def test_strips_leading_vinyl_code(self):
        stem, _, _ = prepare_stem("A1. Artist - Title.mp3")
        assert stem == "Artist - Title"

    def test_strips_url(self):
        stem, _, _ = prepare_stem("Artist - Title https://example.com/x.mp3")
        assert "http" not in stem

    def test_strips_telegram_handle(self):
        stem, _, _ = prepare_stem("Artist - Title @some_channel.mp3")
        assert "@some_channel" not in stem

    def test_strips_junk_phrase(self):
        stem, _, _ = prepare_stem("Artist - Title (Free Download).mp3")
        assert "free download" not in stem.lower()

    def test_strips_catalog_code_at_end(self):
        stem, _, _ = prepare_stem("Artist Title CAT123.mp3")
        assert stem == "Artist Title"

    def test_extracts_version_tag_from_brackets(self):
        stem, _, version_tag = prepare_stem("Artist - Title (Extended Mix).mp3")
        assert stem == "Artist - Title"
        assert version_tag == "Extended Mix"

    def test_non_version_bracket_removed_without_becoming_tag(self):
        stem, _, version_tag = prepare_stem("Artist - Title [Cool Label].mp3")
        assert version_tag is None
        assert "Cool Label" not in stem


class TestTrailingLabelCredit:
    def test_strips_trailing_records_credit(self):
        cleaned, _ = _clean_text("Fly High  [Bosco058] - Bosconi Records")
        assert cleaned == "Fly High"

    def test_strips_trailing_recordings_credit(self):
        cleaned, _ = _clean_text("Some Title - Cool Recordings")
        assert cleaned == "Some Title"

    def test_does_not_strip_legitimate_dash_title(self):
        cleaned, _ = _clean_text("Love - Interlude")
        assert cleaned == "Love - Interlude"


class TestLocalDashSplit:
    def test_splits_on_dash(self):
        assert local_dash_split("Artist - Title") == ("Artist", "Title")

    def test_splits_on_en_dash(self):
        assert local_dash_split("Artist – Title") == ("Artist", "Title")

    def test_no_dash_returns_none(self):
        assert local_dash_split("Artist Title") is None

    def test_empty_side_returns_none(self):
        assert local_dash_split("- Title") is None


class TestGuessSplit:
    def test_two_words(self):
        assert guess_split("Artist Title") == ("Artist", "Title")

    def test_three_plus_words(self):
        assert guess_split("Artist Name Title Words") == ("Artist Name", "Title Words")

    def test_single_word_returns_none(self):
        assert guess_split("Track") is None


class TestApplyTemplate:
    def test_substitutes_known_placeholders(self):
        result = apply_template(
            "{artist} - {title} [{bpm} - {key}]",
            artist="Artist",
            title="Title",
            bpm=128.4,
            key="8A",
            genre="House",
        )
        assert result == "Artist - Title [128 - 8A]"

    def test_missing_values_render_empty(self):
        result = apply_template(
            "{artist} - {title} [{bpm}]", artist="Artist", title="Title", bpm=None, key=None, genre=None
        )
        assert result == "Artist - Title []"

    def test_unknown_placeholder_left_as_is(self):
        result = apply_template(
            "{artist} - {typo}", artist="Artist", title="Title", bpm=None, key=None, genre=None
        )
        assert result == "Artist - {typo}"


class TestComposeName:
    def test_default_format_without_template(self):
        name = compose_name("Artist", "Title", "fallback", None, ".mp3")
        assert name == "Artist - Title.mp3"

    def test_falls_back_to_stem_without_artist_title(self):
        name = compose_name(None, None, "Original Stem", None, ".mp3")
        assert name == "Original Stem.mp3"

    def test_appends_version_tag(self):
        name = compose_name("Artist", "Title", "fallback", "Extended Mix", ".mp3")
        assert name == "Artist - Title (Extended Mix).mp3"

    def test_uses_template_when_artist_and_title_present(self):
        name = compose_name(
            "Artist",
            "Title",
            "fallback",
            None,
            ".mp3",
            filename_template="{artist} - {title} [{bpm}]",
            bpm=128,
            key="8A",
            genre="House",
        )
        assert name == "Artist - Title [128].mp3"

    def test_ignores_template_without_artist_title(self):
        name = compose_name(
            None, None, "fallback", None, ".mp3", filename_template="{artist} - {title}"
        )
        assert name == "fallback.mp3"


class TestCleanFilename:
    def test_dash_split_end_to_end(self):
        assert clean_filename("Artist - Title.mp3") == "Artist - Title.mp3"

    def test_guess_split_end_to_end(self):
        assert clean_filename("Artist Title.mp3") == "Artist - Title.mp3"

    def test_single_word_falls_back_to_stem(self):
        assert clean_filename("99.mp3") == "99.mp3"
