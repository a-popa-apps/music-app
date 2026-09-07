import essentia.standard as es
import numpy as np

NOTE_SEMITONES = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}

# Camelot number for each major-key tonic, indexed by semitone (C=0)
MAJOR_CAMELOT_NUMBER = {
    0: 8, 1: 3, 2: 10, 3: 5, 4: 12, 5: 7,
    6: 2, 7: 9, 8: 4, 9: 11, 10: 6, 11: 1,
}


def to_camelot(key: str, scale: str) -> str:
    semitone = NOTE_SEMITONES[key]
    if scale == "major":
        return f"{MAJOR_CAMELOT_NUMBER[semitone]}B"
    relative_major_semitone = (semitone + 3) % 12
    return f"{MAJOR_CAMELOT_NUMBER[relative_major_semitone]}A"


def to_rekordbox_tonality(key: str, scale: str) -> str:
    """Pioneer's Tonality field: bare note for major ("C", "F#"), note + "m"
    for minor ("Am", "F#m") -- reuses whatever sharp/flat spelling essentia
    returned rather than renormalizing, since Rekordbox accepts either."""
    return key if scale == "major" else f"{key}m"


# Below this confidence, KeyExtractor's own single-pass result is
# considered unreliable enough to be worth a second opinion in "enhanced"
# mode. First guess, not measured against real tracks yet -- same class of
# unverified starting constant as Energy's MIN_DB/MAX_DB was.
ENHANCED_CONFIDENCE_THRESHOLD = 0.7


def detect_key(audio: np.ndarray, enhanced: bool = False) -> dict:
    """KeyExtractor already analyzes the entire track by default, so
    "enhanced" mode can't get a second opinion by just re-running on the
    same audio. Instead, when the first pass's confidence is below
    ENHANCED_CONFIDENCE_THRESHOLD, it re-runs on just the middle ~50% of
    the track (skipping likely intro/outro ambiguity) and keeps whichever
    pass scored higher -- a genuinely different analysis, not a repeat."""
    key, scale, strength = es.KeyExtractor()(audio)

    if enhanced and strength < ENHANCED_CONFIDENCE_THRESHOLD:
        quarter = len(audio) // 4
        middle = audio[quarter : len(audio) - quarter]
        if len(middle) > 0:
            alt_key, alt_scale, alt_strength = es.KeyExtractor()(middle)
            if alt_strength > strength:
                key, scale, strength = alt_key, alt_scale, alt_strength

    return {
        "key": f"{key} {scale}",
        "camelot": to_camelot(key, scale),
        "tonality": to_rekordbox_tonality(key, scale),
        "strength": round(float(strength), 2),
    }
