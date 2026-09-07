import pytest

pytest.importorskip("essentia")

import numpy as np

from app.audio_io import SAMPLE_RATE
from app.detect_bpm import ANALYSIS_SECONDS, detect_bpm


def _click_track(bpm: float, seconds: float) -> np.ndarray:
    """A simple percussive click train at a fixed tempo -- RhythmExtractor
    needs beat-like transients, not a pure tone, to lock onto a tempo."""
    n = int(SAMPLE_RATE * seconds)
    audio = np.zeros(n, dtype=np.float32)
    interval = int(SAMPLE_RATE * 60 / bpm)
    click_len = 200
    for start in range(0, n - click_len, interval):
        audio[start : start + click_len] = np.linspace(1.0, 0.0, click_len, dtype=np.float32)
    return audio


def test_default_mode_estimates_a_plausible_bpm():
    audio = _click_track(128, seconds=10)
    bpm = detect_bpm(audio)
    assert 60 <= bpm <= 200


def test_full_track_mode_handles_audio_longer_than_the_default_window():
    # Longer than ANALYSIS_SECONDS -- the default (windowed) mode would only
    # ever see the first slice of this; full_track must not error out on
    # analyzing the rest of it too.
    audio = _click_track(128, seconds=ANALYSIS_SECONDS + 20)
    bpm = detect_bpm(audio, full_track=True)
    assert 60 <= bpm <= 200


def test_full_track_mode_does_not_crash_on_short_audio():
    # Shorter than ANALYSIS_SECONDS -- full_track and windowed mode should
    # both just analyze the whole (short) clip without special-casing.
    audio = _click_track(128, seconds=5)
    bpm = detect_bpm(audio, full_track=True)
    assert 60 <= bpm <= 200
