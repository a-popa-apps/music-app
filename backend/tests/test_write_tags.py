import io
import wave

from app.write_tags import write_tags


def _make_wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 8000)  # 1 second of silence
    return buffer.getvalue()


def test_write_and_read_back_wav_tags():
    content = _make_wav_bytes()
    tagged = write_tags(content, ".wav", bpm=128.4, camelot="8A", genre="House")

    from mutagen.wave import WAVE
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(tagged)
        tmp.flush()
        audio = WAVE(tmp.name)
        assert str(audio.tags["TBPM"]) == "128"
        assert str(audio.tags["TKEY"]) == "8A"
        assert str(audio.tags["TCON"]) == "House"


def test_unsupported_extension_returns_unchanged():
    content = b"not really audio"
    assert write_tags(content, ".aac", bpm=128, camelot="8A", genre="House") == content


def test_no_values_leaves_no_tags_but_still_returns_valid_file():
    content = _make_wav_bytes()
    tagged = write_tags(content, ".wav")
    assert len(tagged) > 0
