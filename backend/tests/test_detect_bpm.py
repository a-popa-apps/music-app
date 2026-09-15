import pytest

pytest.importorskip("essentia")

import numpy as np

from app import detect_bpm as detect_bpm_module
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


def test_low_confidence_window_retries_and_uses_full_track_result(monkeypatch):
    # Mirrors a real track with a ~40s beatless spoken-word intro: its
    # opening 30s read 172 BPM at confidence 0.3, while the full track read
    # 127 BPM (the independently-verified tempo) at confidence 2.1. Mocked
    # rather than reproduced with synthetic audio -- essentia's confidence
    # score is too sensitive to the exact signal to hand-tune reliably.
    responses = iter([(172.0, 0.3), (127.0, 2.1)])
    monkeypatch.setattr(detect_bpm_module, "_estimate_tempo", lambda audio: next(responses))

    window = np.zeros(SAMPLE_RATE * ANALYSIS_SECONDS, dtype=np.float32)
    bpm = detect_bpm(window, full_audio_loader=lambda: np.zeros(SAMPLE_RATE * 60, dtype=np.float32))

    assert bpm == 127.0


def test_low_confidence_window_keeps_original_if_full_track_is_not_better(monkeypatch):
    # The full-track retry isn't automatically trusted just for being a
    # retry -- if it comes back even less confident than the original
    # (short-audio edge cases, corrupt regions, etc.), the original reading
    # wins rather than trading it for a worse one.
    responses = iter([(172.0, 0.5), (200.0, 0.2)])
    monkeypatch.setattr(detect_bpm_module, "_estimate_tempo", lambda audio: next(responses))

    window = np.zeros(SAMPLE_RATE * ANALYSIS_SECONDS, dtype=np.float32)
    bpm = detect_bpm(window, full_audio_loader=lambda: np.zeros(SAMPLE_RATE * 60, dtype=np.float32))

    assert bpm == 172.0


def test_high_confidence_window_never_calls_full_audio_loader():
    audio = _click_track(128, seconds=10)
    calls = []

    def loader():
        calls.append(True)
        raise AssertionError("should not be called for a confident read")

    detect_bpm(audio, full_audio_loader=loader)

    assert calls == []
