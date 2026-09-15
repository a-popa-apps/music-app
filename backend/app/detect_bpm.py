from typing import Callable

import essentia.standard as es
import numpy as np

from .audio_io import SAMPLE_RATE

ANALYSIS_SECONDS = 30

# essentia's "multifeature" confidence for RhythmExtractor2013 runs roughly
# 0-5.3; below this, a reading isn't trustworthy enough to use as-is.
# Confirmed against a real track with a ~40s beatless spoken-word intro: its
# opening 30 seconds (the default analysis window) scored 0.3 confidence and
# read 172 BPM -- 45 BPM off the independently-verified tempo -- while a
# full-track read of the same file scored 2.1 and matched it exactly.
LOW_CONFIDENCE_THRESHOLD = 1.0


def _estimate_tempo(audio: np.ndarray) -> tuple[float, float]:
    # "degara" (the previous method here) never reports a usable confidence
    # -- it always returns 0 regardless of how reliable the read actually
    # is -- so there was no way to detect the failure mode below at all.
    # "multifeature" costs a bit more per call but gives a real confidence
    # score, which is what makes the retry in detect_bpm possible.
    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    bpm, _beats, confidence, _estimates, _intervals = rhythm_extractor(audio)
    return round(float(bpm), 2), float(confidence)


def warm_up() -> None:
    noise = np.random.default_rng(0).standard_normal(SAMPLE_RATE * 5).astype(np.float32)
    _estimate_tempo(noise)


def detect_bpm(
    audio: np.ndarray,
    full_track: bool = False,
    full_audio_loader: Callable[[], np.ndarray] | None = None,
) -> float:
    """full_track=True (Pro's "enhanced" mode) analyzes the entire track
    instead of the first ANALYSIS_SECONDS -- catches tempo drift, tempo
    changes, and long differently-tempo'd intros/outros that a single 30s
    window can miss. Slower per track, more accurate on those cases.

    `full_audio_loader`, when given, is called (only) if the fast window's
    read comes back low-confidence -- e.g. a window that lands entirely
    inside a quiet/beatless intro (spoken word, ambient pads, slow rubato)
    can lock onto a false, faster pulse instead of the track's real tempo.
    Retrying against the full track easily outweighs a short bad intro with
    everything that comes after it, at the cost of a full decode -- worth
    paying only for the rare track that actually needs it."""
    window = audio if full_track else audio[: SAMPLE_RATE * ANALYSIS_SECONDS]
    bpm, confidence = _estimate_tempo(window)

    if not full_track and confidence < LOW_CONFIDENCE_THRESHOLD and full_audio_loader is not None:
        full_bpm, full_confidence = _estimate_tempo(full_audio_loader())
        if full_confidence > confidence:
            return full_bpm

    return bpm
