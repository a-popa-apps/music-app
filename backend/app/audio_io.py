import os
import tempfile

import essentia.standard as es
import mutagen

SAMPLE_RATE = 44100


def load_audio(audio_bytes: bytes, suffix: str = ".wav", max_seconds: float | None = None):
    """`max_seconds` decodes only a leading slice of the file (via
    EasyLoader's endTime) instead of the whole thing -- bit-identical to
    decoding in full and truncating the array, confirmed empirically, but
    far cheaper for a long track when only a short window is needed (the
    default, non-"enhanced" BPM/key/energy pass). EasyLoader's default
    replayGain (-6dB) is also confirmed to produce identical samples to the
    plain MonoLoader this replaced, so full decodes (max_seconds=None) are
    unaffected -- no retuning needed for anything calibrated against the
    old loader (e.g. detect_energy's MIN_DB/MAX_DB)."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        kwargs = {"filename": tmp_path, "sampleRate": SAMPLE_RATE}
        if max_seconds is not None:
            kwargs["endTime"] = max_seconds
        audio = es.EasyLoader(**kwargs)()
    finally:
        os.unlink(tmp_path)

    return audio


def get_duration_seconds(content: bytes, suffix: str) -> float | None:
    """True file duration read from its own header via mutagen -- no audio
    decoding, so it stays accurate even when load_audio only decodes a
    truncated window for speed."""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
            tmp.write(content)
            tmp.flush()
            audio = mutagen.File(tmp.name)
    except Exception:
        return None

    if audio is None or audio.info is None:
        return None
    return round(float(audio.info.length), 2)
