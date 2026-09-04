import os
import tempfile

import essentia.standard as es

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


def detect_key(audio_bytes: bytes, suffix: str = ".wav") -> dict:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        audio = es.MonoLoader(filename=tmp_path)()
        key, scale, strength = es.KeyExtractor()(audio)
    finally:
        os.unlink(tmp_path)

    return {
        "key": f"{key} {scale}",
        "camelot": to_camelot(key, scale),
        "strength": round(float(strength), 2),
    }
