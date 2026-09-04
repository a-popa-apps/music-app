import io

import librosa
import numpy as np


def detect_bpm(audio_bytes: bytes) -> float:
    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return round(float(np.atleast_1d(tempo)[0]), 2)
