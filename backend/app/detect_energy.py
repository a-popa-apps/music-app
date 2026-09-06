import essentia.standard as es
import numpy as np

from .audio_io import SAMPLE_RATE
from .detect_bpm import ANALYSIS_SECONDS

# Mixed In Key-style 1-10 "energy" rating, derived from loudness rather
# than a single canonical algorithm -- essentia has no built-in "DJ energy"
# descriptor. This dB range is a starting guess (typical masters run
# somewhere in -30 to -6 dBFS RMS); expect to retune after seeing real
# tracks' ratings live, same as PROCESS_CONCURRENCY was left tunable rather
# than assumed correct the first time.
MIN_DB = -30.0
MAX_DB = -6.0


def detect_energy(audio: np.ndarray) -> int:
    window = audio[: SAMPLE_RATE * ANALYSIS_SECONDS]
    rms = float(es.RMS()(window))
    db = 20 * np.log10(rms) if rms > 0 else MIN_DB

    clamped = max(MIN_DB, min(MAX_DB, db))
    scaled = (clamped - MIN_DB) / (MAX_DB - MIN_DB) * 9 + 1
    return round(scaled)
