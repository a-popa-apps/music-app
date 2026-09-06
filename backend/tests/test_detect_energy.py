import pytest

pytest.importorskip("essentia")

import numpy as np

from app.detect_energy import detect_energy


def _tone(amplitude: float, seconds: float = 2, sr: int = 44100) -> np.ndarray:
    t = np.arange(int(sr * seconds)) / sr
    return (amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def test_energy_is_within_1_to_10():
    for amplitude in (0.01, 0.1, 0.5, 1.0):
        score = detect_energy(_tone(amplitude))
        assert 1 <= score <= 10


def test_energy_increases_with_loudness():
    quiet = detect_energy(_tone(0.02))
    loud = detect_energy(_tone(0.9))
    assert loud >= quiet


def test_energy_handles_silence_without_raising():
    silence = np.zeros(44100 * 2, dtype=np.float32)
    score = detect_energy(silence)
    assert score == 1
