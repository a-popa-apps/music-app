import essentia.standard as es
import numpy as np

from .audio_io import SAMPLE_RATE

ANALYSIS_SECONDS = 30


def _estimate_tempo(audio: np.ndarray, full_track: bool = False) -> float:
    window = audio if full_track else audio[: SAMPLE_RATE * ANALYSIS_SECONDS]
    rhythm_extractor = es.RhythmExtractor2013(method="degara")
    bpm, _beats, _confidence, _estimates, _intervals = rhythm_extractor(window)
    return round(float(bpm), 2)


def warm_up() -> None:
    noise = np.random.default_rng(0).standard_normal(SAMPLE_RATE * 5).astype(np.float32)
    _estimate_tempo(noise)


def detect_bpm(audio: np.ndarray, full_track: bool = False) -> float:
    """full_track=True (Pro's "enhanced" mode) analyzes the entire track
    instead of the first ANALYSIS_SECONDS -- catches tempo drift, tempo
    changes, and long differently-tempo'd intros/outros that a single 30s
    window can miss. Slower per track, more accurate on those cases."""
    return _estimate_tempo(audio, full_track=full_track)
