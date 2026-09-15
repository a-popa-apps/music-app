import pytest

pytest.importorskip("essentia")

import numpy as np

from app.detect_bpm import ANALYSIS_SECONDS
from app.detect_energy import detect_energy


def _tone(amplitude: float, freq: float = 220, seconds: float = 2, sr: int = 44100) -> np.ndarray:
    t = np.arange(int(sr * seconds)) / sr
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_energy_is_within_1_to_10():
    for amplitude in (0.01, 0.1, 0.5, 1.0):
        score = detect_energy(_tone(amplitude))
        assert 1 <= score <= 10


def test_energy_increases_with_loudness():
    quiet = detect_energy(_tone(0.02))
    loud = detect_energy(_tone(0.9))
    assert loud > quiet


def test_energy_increases_with_brightness_at_equal_loudness():
    # Same amplitude, only the frequency (and so spectral centroid)
    # differs -- a bright tone should read as more energetic than a dark
    # one even though they're equally loud, since loudness alone can't
    # distinguish a dark/bassy mix from a bright/percussive one.
    dark = detect_energy(_tone(0.5, freq=80))
    bright = detect_energy(_tone(0.5, freq=3000))
    assert bright > dark


def test_energy_handles_silence_without_raising():
    silence = np.zeros(44100 * 2, dtype=np.float32)
    score = detect_energy(silence)
    assert score == 1


def test_energy_handles_empty_array_without_raising():
    assert detect_energy(np.array([], dtype=np.float32)) == 1


def test_full_track_analyzes_beyond_the_default_window():
    # A quiet "intro" for the first ANALYSIS_SECONDS, then a loud, bright
    # tail -- the default (non-enhanced) window only ever sees the quiet
    # intro, but full_track=True should pick up the louder tail and score
    # noticeably higher, the same way detect_bpm's full_track catches a
    # tempo change a 30s window would miss.
    quiet_intro = _tone(0.01, freq=100, seconds=ANALYSIS_SECONDS + 1)
    loud_tail = _tone(0.9, freq=3000, seconds=5)
    audio = np.concatenate([quiet_intro, loud_tail])

    windowed_score = detect_energy(audio, full_track=False)
    full_track_score = detect_energy(audio, full_track=True)

    assert full_track_score > windowed_score


def test_default_window_is_capped_at_analysis_seconds():
    quiet_intro = _tone(0.01, freq=100, seconds=ANALYSIS_SECONDS + 1)
    loud_tail = _tone(0.9, freq=3000, seconds=5)
    audio = np.concatenate([quiet_intro, loud_tail])

    only_intro_score = detect_energy(quiet_intro)
    windowed_score = detect_energy(audio, full_track=False)

    # The default window shouldn't see the loud tail at all, so scoring
    # the full array without full_track should match scoring the intro
    # alone.
    assert windowed_score == only_intro_score
