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
    key_tag: str | None = None,
    genre: str | None = None,
) -> bytes:
    """`key_tag` should be standard musical key notation ("Am", "F#"), not
    a Camelot code ("8A") -- TKEY/INITIALKEY's own convention, and what
    Rekordbox/Serato/Traktor actually expect there so a track's key shows
    up correctly without the DJ software re-analyzing it. Camelot is a
    DJ-friendly *display* convention on top of that; each of those apps
    already offers a "show keys as Camelot" preference of its own for
    users who want that view."""
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
            if key_tag:
                tags.setall("TKEY", [TKEY(encoding=3, text=key_tag)])
            if genre:
                tags.setall("TCON", [TCON(encoding=3, text=genre)])
            audio.save(tmp_path)
        else:
            audio = VORBIS_FORMATS[suffix](tmp_path)
            if bpm is not None:
                audio["BPM"] = str(round(bpm))
            if key_tag:
                audio["INITIALKEY"] = key_tag
            if genre:
                audio["GENRE"] = genre
            audio.save()

        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)
