import io
import wave

import pytest

pytest.importorskip("essentia")

import numpy as np

from app.audio_io import SAMPLE_RATE, get_duration_seconds, load_audio


def _make_wav(duration: float, sr: int = 44100) -> bytes:
    buffer = io.BytesIO()
    n = int(sr * duration)
    samples = (0.2 * np.sin(2 * np.pi * 220 * np.arange(n) / sr)).astype(np.float32)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return buffer.getvalue()


def test_load_audio_full_decode_matches_file_length():
    content = _make_wav(2)
    audio = load_audio(content, ".wav")
    assert abs(len(audio) / SAMPLE_RATE - 2) < 0.05


def test_load_audio_truncates_to_max_seconds():
    content = _make_wav(5)
    audio = load_audio(content, ".wav", max_seconds=2)
    assert abs(len(audio) / SAMPLE_RATE - 2) < 0.05


def test_load_audio_max_seconds_beyond_file_length_returns_whole_file():
    content = _make_wav(2)
    audio = load_audio(content, ".wav", max_seconds=30)
    assert abs(len(audio) / SAMPLE_RATE - 2) < 0.05


def test_load_audio_truncated_matches_full_decode_sliced_the_same_way():
    # The actual speed-optimization guarantee: decoding only a window gives
    # the same samples as decoding in full and slicing -- not an
    # approximation.
    content = _make_wav(5)
    full = load_audio(content, ".wav")
    windowed = load_audio(content, ".wav", max_seconds=2)
    cutoff = len(windowed)
    assert np.allclose(full[:cutoff], windowed, atol=1e-4)


def test_get_duration_seconds_reads_full_length_without_decoding():
    content = _make_wav(5)
    assert abs(get_duration_seconds(content, ".wav") - 5) < 0.05


def test_get_duration_seconds_unaffected_by_a_truncated_decode_elsewhere():
    # The key guarantee this function exists for: even when load_audio only
    # decoded a short window (for speed), the reported duration must still
    # be the file's real, full length.
    content = _make_wav(5)
    load_audio(content, ".wav", max_seconds=1)
    assert abs(get_duration_seconds(content, ".wav") - 5) < 0.05


def test_get_duration_seconds_returns_none_for_garbage():
    assert get_duration_seconds(b"not audio", ".wav") is None
