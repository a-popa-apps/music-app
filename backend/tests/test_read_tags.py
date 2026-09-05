from __future__ import annotations

from unittest.mock import patch

from app.read_tags import read_embedded_tags


class _FakeTags(dict):
    """Mimics mutagen's EasyID3-style tags: values are lists of strings."""


class _FakeAudio:
    def __init__(self, tags: dict | None):
        self.tags = _FakeTags(tags) if tags is not None else None


def _mock_file(tags: dict | None):
    return patch("app.read_tags.mutagen.File", return_value=_FakeAudio(tags))


def test_no_tags_returns_empty():
    with _mock_file(None):
        assert read_embedded_tags(b"fake", ".mp3") == {}


def test_missing_artist_or_title_returns_empty():
    with _mock_file({"title": ["Some Title"]}):
        assert read_embedded_tags(b"fake", ".mp3") == {}
    with _mock_file({"artist": ["Some Artist"]}):
        assert read_embedded_tags(b"fake", ".mp3") == {}


def test_generic_genre_filtered_out():
    with _mock_file({"artist": ["Artist"], "title": ["Title"], "genre": ["Music"]}):
        result = read_embedded_tags(b"fake", ".mp3")
    assert result["genre"] is None


def test_real_genre_kept():
    with _mock_file({"artist": ["Artist"], "title": ["Title"], "genre": ["IDM"]}):
        result = read_embedded_tags(b"fake", ".mp3")
    assert result["genre"] == "IDM"


def test_thermal_line_case():
    with _mock_file(
        {
            "artist": ["Thermal Line"],
            "title": ["To End Twine (House D'arret - HD 004/99)"],
            "genre": ["Music"],
        }
    ):
        result = read_embedded_tags(b"fake", ".mp3")
    assert result == {
        "artist": "Thermal Line",
        "title": "To End Twine",
        "genre": None,
        "version_tag": None,
    }


def test_fly_high_label_credit_stripped():
    with _mock_file(
        {
            "artist": ["Dj GLC"],
            "title": ["Fly High  [Bosco058] - Bosconi Records"],
            "genre": ["Music"],
        }
    ):
        result = read_embedded_tags(b"fake", ".mp3")
    assert result["artist"] == "Dj GLC"
    assert result["title"] == "Fly High"


def test_load_error_returns_empty():
    with patch("app.read_tags.mutagen.File", side_effect=Exception("boom")):
        assert read_embedded_tags(b"fake", ".mp3") == {}
