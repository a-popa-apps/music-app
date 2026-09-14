import io
import tempfile
import wave

import pytest

from app.write_tags import write_tags


def _make_wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 8000)  # 1 second of silence
    return buffer.getvalue()


def _make_flac_bytes() -> bytes:
    pytest.importorskip("essentia")
    import essentia.standard as es
    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as tmp:
        path = tmp.name
    try:
        es.MonoWriter(filename=path, format="flac", sampleRate=8000)(
            np.zeros(8000, dtype=np.float32)
        )
        with open(path, "rb") as f:
            return f.read()
    finally:
        import os

        os.unlink(path)


def test_write_and_read_back_wav_tags():
    content = _make_wav_bytes()
    tagged = write_tags(
        content, ".wav", bpm=128.4, key_tag="Am", genre="House", artist="Slam", title="Life Between Life"
    )

    from mutagen.wave import WAVE

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(tagged)
        tmp.flush()
        audio = WAVE(tmp.name)
        assert str(audio.tags["TBPM"]) == "128"
        assert str(audio.tags["TKEY"]) == "Am"
        assert str(audio.tags["TCON"]) == "House"
        assert str(audio.tags["TPE1"]) == "Slam"
        assert str(audio.tags["TIT2"]) == "Life Between Life"


def test_write_and_read_back_flac_tags():
    # The reported bug: a file's own embedded artist/title tags were wrong
    # (e.g. "Lady Aïda" from a DJ mix-compilation credit) and the app only
    # ever fixed the *filename*, never the file's own tags -- so software
    # that reads embedded tags (Rekordbox, Serato, VOX, QuickLook) still
    # showed the wrong artist even after CratePrep renamed the file.
    content = _make_flac_bytes()
    tagged = write_tags(content, ".flac", genre="House", artist="Slam", title="Life Between Life")

    from mutagen.flac import FLAC

    with tempfile.NamedTemporaryFile(suffix=".flac") as tmp:
        tmp.write(tagged)
        tmp.flush()
        audio = FLAC(tmp.name)
        assert audio["ARTIST"][0] == "Slam"
        assert audio["TITLE"][0] == "Life Between Life"
        assert audio["GENRE"][0] == "House"


def test_artist_and_title_omitted_when_not_provided():
    content = _make_wav_bytes()
    tagged = write_tags(content, ".wav", bpm=128)

    from mutagen.wave import WAVE

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(tagged)
        tmp.flush()
        audio = WAVE(tmp.name)
        assert "TPE1" not in audio.tags
        assert "TIT2" not in audio.tags


def test_unsupported_extension_returns_unchanged():
    content = b"not really audio"
    assert write_tags(content, ".aac", bpm=128, key_tag="Am", genre="House") == content


def test_no_values_leaves_no_tags_but_still_returns_valid_file():
    content = _make_wav_bytes()
    tagged = write_tags(content, ".wav")
    assert len(tagged) > 0
