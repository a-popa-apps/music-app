import pytest

pytest.importorskip("essentia")

import numpy as np

from app.detect_key import detect_key, to_camelot, to_rekordbox_tonality
from app.audio_io import SAMPLE_RATE


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


def _tone(freq: float = 220, seconds: float = 8) -> np.ndarray:
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_detect_key_default_mode_returns_expected_shape():
    result = detect_key(_tone())
    assert set(result.keys()) == {"key", "camelot", "tonality", "strength"}
    assert 0 <= result["strength"] <= 1


def test_detect_key_enhanced_mode_on_low_confidence_signal_does_not_crash():
    # Noise is tonally ambiguous -- likely to score low enough to exercise
    # the enhanced second-pass branch, not just fall through unused.
    noise = (np.random.default_rng(0).standard_normal(SAMPLE_RATE * 10) * 0.1).astype(np.float32)
    result = detect_key(noise, enhanced=True)
    assert set(result.keys()) == {"key", "camelot", "tonality", "strength"}
    assert 0 <= result["strength"] <= 1


def test_detect_key_enhanced_mode_matches_shape_on_short_audio():
    # Shorter than a full "quarter" split still shouldn't error out.
    short = _tone(seconds=1)
    result = detect_key(short, enhanced=True)
    assert set(result.keys()) == {"key", "camelot", "tonality", "strength"}
