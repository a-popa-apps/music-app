from __future__ import annotations

import struct
from unittest.mock import patch

from app.read_tags import read_embedded_tags


def _riff_chunk(chunk_id: bytes, data: bytes) -> bytes:
    padded = data + (b"\x00" if len(data) % 2 else b"")
    return chunk_id + struct.pack("<I", len(data)) + padded


def _build_wav_with_riff_info(info: dict[str, str]) -> bytes:
    """A minimal, real, valid WAV file tagged only via the native RIFF INFO
    LIST chunk (IART/INAM/IGNR) -- the convention mutagen's WAVE class
    doesn't read at all, unlike ID3-in-WAV. Used to test the fallback in
    read_embedded_tags without needing a real reported file."""
    fmt_chunk = _riff_chunk(b"fmt ", struct.pack("<HHIIHH", 1, 1, 44100, 88200, 2, 16))
    data_chunk = _riff_chunk(b"data", b"\x00\x00\x00\x00")
    info_body = b"INFO" + b"".join(
        _riff_chunk(key.encode("ascii"), value.encode("utf-8") + b"\x00") for key, value in info.items()
    )
    list_chunk = _riff_chunk(b"LIST", info_body)
    body = b"WAVE" + fmt_chunk + data_chunk + list_chunk
    return b"RIFF" + struct.pack("<I", len(body)) + body


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


def test_wav_riff_info_fallback_used_when_id3_read_is_empty():
    # Mirrors a real reported bug: a WAV tagged only via the native RIFF
    # INFO chunk (no ID3-in-WAV) showed correct artist/title in macOS's
    # Finder/Music.app, but mutagen's WAVE class -- which only reads
    # ID3v2-in-WAV -- saw no tags at all, so the file fell through to a
    # blind title-only catalog search that matched the wrong artist.
    wav_bytes = _build_wav_with_riff_info(
        {"IART": "Duowe, Picasso", "INAM": "Pink Dust", "IGNR": "Ambient"}
    )
    with _mock_file(None):
        result = read_embedded_tags(wav_bytes, ".wav")
    assert result["artist"] == "Duowe, Picasso"
    assert result["title"] == "Pink Dust"
    assert result["genre"] == "Ambient"


def test_wav_riff_info_fallback_not_used_for_other_formats():
    # The RIFF INFO chunk format is WAV-specific -- an .mp3 upload that
    # happens to contain similar-looking bytes should never trigger it.
    wav_bytes = _build_wav_with_riff_info({"IART": "Artist", "INAM": "Title"})
    with _mock_file(None):
        assert read_embedded_tags(wav_bytes, ".mp3") == {}


def test_wav_riff_info_fallback_only_fills_missing_fields():
    # A real ID3-in-WAV artist tag should win even if the RIFF INFO chunk
    # (from some earlier, stale tagging pass) disagrees -- ID3 is checked
    # first and only a genuinely missing field falls back to RIFF INFO.
    wav_bytes = _build_wav_with_riff_info({"IART": "Stale Artist", "INAM": "Pink Dust"})
    with _mock_file({"artist": ["Real Artist"]}):
        result = read_embedded_tags(wav_bytes, ".wav")
    assert result["artist"] == "Real Artist"
    assert result["title"] == "Pink Dust"


def test_wav_with_no_tags_at_all_returns_empty():
    wav_bytes = _build_wav_with_riff_info({})
    with _mock_file(None):
        assert read_embedded_tags(wav_bytes, ".wav") == {}
