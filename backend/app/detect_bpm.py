import io

import librosa
import numpy as np
import soundfile as sf

ANALYSIS_DURATION = 30  # seconds
ANALYSIS_SR = 22050  # half of typical 44.1kHz; negligible accuracy loss for tempo


def _estimate_tempo(y: np.ndarray, sr: int) -> float:
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return round(float(np.atleast_1d(tempo)[0]), 2)


def warm_up() -> None:
    """Trigger numba's JIT compilation at startup instead of on a user's first request."""
    noise = np.random.default_rng(0).standard_normal(ANALYSIS_SR * 5).astype(np.float32)
    _estimate_tempo(noise, ANALYSIS_SR)


def detect_bpm(audio_bytes: bytes) -> float:
    info = sf.info(io.BytesIO(audio_bytes))
    total_duration = info.duration

    offset = 0.0
    if total_duration > ANALYSIS_DURATION:
        # skip a likely intro, but don't run past the end of the track
        offset = min(15.0, total_duration - ANALYSIS_DURATION)

    y, sr = librosa.load(
        io.BytesIO(audio_bytes),
        sr=ANALYSIS_SR,
        mono=True,
        offset=offset,
        duration=ANALYSIS_DURATION,
    )
    return _estimate_tempo(y, sr)
