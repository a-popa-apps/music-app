import essentia.standard as es
import numpy as np

from .audio_io import SAMPLE_RATE
from .detect_bpm import ANALYSIS_SECONDS

# Mixed In Key-style 1-10 "energy" rating. Loudness alone is a weak proxy
# for perceived energy in the streaming-loudness-war era -- a dark, mellow
# track can be mastered just as loud as a bright, percussive one -- so this
# blends RMS loudness with spectral centroid (brightness), the standard
# proxy for timbral brightness: bright/harsh mixes read as more energetic,
# dark/bassy mixes read as calmer, independent of raw loudness. Both
# ranges are starting guesses (typical masters run -30 to -6 dBFS RMS;
# full-mix spectral centroids for calm/dark material vs. bright/percussive
# material roughly span 500Hz-4000Hz); expect to retune after seeing real
# tracks' ratings live, same as PROCESS_CONCURRENCY was left tunable
# rather than assumed correct the first time.
MIN_DB = -30.0
MAX_DB = -6.0
MIN_CENTROID_HZ = 500.0
MAX_CENTROID_HZ = 4000.0

# Loudness is the more reliable single signal; brightness mainly corrects
# the "loud but dark" case rather than driving the score on its own.
LOUDNESS_WEIGHT = 0.7
BRIGHTNESS_WEIGHT = 0.3


def _scaled(value: float, lo: float, hi: float) -> float:
    clamped = max(lo, min(hi, value))
    return (clamped - lo) / (hi - lo)


def detect_energy(audio: np.ndarray, full_track: bool = False) -> int:
    """full_track=True (Pro's "enhanced" mode, same flag detect_bpm/
    detect_key take) analyzes the entire available audio instead of just
    the first ANALYSIS_SECONDS. A DJ track's intro is usually its
    quietest, sparsest section, so windowing to just that consistently
    understated energy for tracks with a build-up intro."""
    window = audio if full_track else audio[: SAMPLE_RATE * ANALYSIS_SECONDS]
    if len(window) == 0:
        return 1

    rms = float(es.RMS()(window))
    db = 20 * np.log10(rms) if rms > 0 else MIN_DB
    loudness_score = _scaled(db, MIN_DB, MAX_DB)

    centroid = float(es.SpectralCentroidTime(sampleRate=SAMPLE_RATE)(window))
    brightness_score = _scaled(centroid, MIN_CENTROID_HZ, MAX_CENTROID_HZ)

    blended = LOUDNESS_WEIGHT * loudness_score + BRIGHTNESS_WEIGHT * brightness_score
    return round(blended * 9 + 1)
