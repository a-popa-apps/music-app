import pytest

pytest.importorskip("essentia")

from app.detect_key import to_camelot, to_rekordbox_tonality


def test_to_rekordbox_tonality_major_is_bare_note():
    assert to_rekordbox_tonality("C", "major") == "C"
    assert to_rekordbox_tonality("F#", "major") == "F#"


def test_to_rekordbox_tonality_minor_appends_m():
    assert to_rekordbox_tonality("A", "minor") == "Am"
    assert to_rekordbox_tonality("F#", "minor") == "F#m"


def test_to_camelot_matches_known_pairs():
    # C major / A minor are relative keys -- both land on Camelot 8.
    assert to_camelot("C", "major") == "8B"
    assert to_camelot("A", "minor") == "8A"
