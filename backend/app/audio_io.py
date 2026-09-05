import os
import tempfile

import essentia.standard as es

SAMPLE_RATE = 44100


def load_audio(audio_bytes: bytes, suffix: str = ".wav"):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        audio = es.MonoLoader(filename=tmp_path, sampleRate=SAMPLE_RATE)()
    finally:
        os.unlink(tmp_path)

    return audio
