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


# Extensions the app accepts but that Chrome/Firefox's <audio> element and
# Web Audio API have no native decoder for at all (confirmed directly:
# canPlayType("audio/aiff") returns "", and decodeAudioData throws
# EncodingError, even on a perfectly valid file) -- only Safari can play
# these natively. Browser playback needs a transcoded stand-in; the
# original bytes are untouched and still what gets exported/downloaded.
NEEDS_BROWSER_PREVIEW = {".aiff", ".aif"}


def make_preview_wav(content: bytes, suffix: str) -> bytes:
    """Decodes the full track and re-encodes it as a WAV every browser can
    play, for in-app playback/waveform purposes only. Uses essentia's own
    FFmpeg-backed writer -- already a hard runtime dependency (it's what
    decodes these same files for BPM/key/energy), so this adds no new
    dependency. Mono output matches TrackWaveform's own peak extraction
    (channel 0 only), so there's no fidelity loss for what this is used for."""
    audio = load_audio(content, suffix, max_seconds=None)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        es.MonoWriter(filename=tmp_path, format="wav", sampleRate=SAMPLE_RATE)(audio)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


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
