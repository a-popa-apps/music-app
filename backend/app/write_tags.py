from __future__ import annotations

import os
import tempfile

from mutagen.aiff import AIFF
from mutagen.flac import FLAC
from mutagen.id3 import TBPM, TCON, TKEY
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

ID3_FORMATS = {
    ".mp3": MP3,
    ".wav": WAVE,
    ".aiff": AIFF,
    ".aif": AIFF,
}
VORBIS_FORMATS = {
    ".flac": FLAC,
    ".ogg": OggVorbis,
}


def write_tags(
    content: bytes,
    suffix: str,
    bpm: float | None = None,
    camelot: str | None = None,
    genre: str | None = None,
) -> bytes:
    suffix = suffix.lower()
    if suffix not in ID3_FORMATS and suffix not in VORBIS_FORMATS:
        # No reliable embedded-tag standard for this format (e.g. bare .aac)
        return content

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if suffix in ID3_FORMATS:
            audio = ID3_FORMATS[suffix](tmp_path)
            if audio.tags is None:
                audio.add_tags()
            tags = audio.tags
            if bpm is not None:
                tags.setall("TBPM", [TBPM(encoding=3, text=str(round(bpm)))])
            if camelot:
                tags.setall("TKEY", [TKEY(encoding=3, text=camelot)])
            if genre:
                tags.setall("TCON", [TCON(encoding=3, text=genre)])
            audio.save(tmp_path)
        else:
            audio = VORBIS_FORMATS[suffix](tmp_path)
            if bpm is not None:
                audio["BPM"] = str(round(bpm))
            if camelot:
                audio["INITIALKEY"] = camelot
            if genre:
                audio["GENRE"] = genre
            audio.save()

        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)
