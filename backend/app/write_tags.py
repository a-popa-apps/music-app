from __future__ import annotations

import base64
import os
import tempfile

from mutagen.aiff import AIFF
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, TBPM, TCON, TIT2, TKEY, TPE1
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


def _flac_picture(data: bytes, mime: str) -> Picture:
    pic = Picture()
    pic.type = 3  # id3.PictureType.COVER_FRONT -- same convention APIC uses
    pic.mime = mime
    pic.desc = "Cover"
    pic.data = data
    return pic


def write_tags(
    content: bytes,
    suffix: str,
    bpm: float | None = None,
    key_tag: str | None = None,
    genre: str | None = None,
    artist: str | None = None,
    title: str | None = None,
    artwork: bytes | None = None,
    artwork_mime: str = "image/jpeg",
) -> bytes:
    """`key_tag` should be standard musical key notation ("Am", "F#"), not
    a Camelot code ("8A") -- TKEY/INITIALKEY's own convention, and what
    Rekordbox/Serato/Traktor actually expect there so a track's key shows
    up correctly without the DJ software re-analyzing it. Camelot is a
    DJ-friendly *display* convention on top of that; each of those apps
    already offers a "show keys as Camelot" preference of its own for
    users who want that view.

    `artist`/`title` are the app's own resolved values (filename, catalog
    match, tags -- whichever _resolve_artist_title_genre trusted), written
    back into the file's own tags so a corrected artist/title isn't only
    cosmetic in the filename: DJ software reads embedded tags, not
    filenames, so a mistagged source file would otherwise still show the
    wrong artist once imported even after CratePrep renamed it.

    `artwork`, when supplied, replaces any existing embedded cover art with
    the catalog-sourced image -- same "detected value always wins" policy
    as every other field here, not a fill-only-if-missing merge."""
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
            if artist:
                tags.setall("TPE1", [TPE1(encoding=3, text=artist)])
            if title:
                tags.setall("TIT2", [TIT2(encoding=3, text=title)])
            if artwork:
                tags.setall(
                    "APIC",
                    [APIC(encoding=3, mime=artwork_mime, type=3, desc="Cover", data=artwork)],
                )
            audio.save(tmp_path)
        elif suffix == ".flac":
            audio = FLAC(tmp_path)
            if bpm is not None:
                audio["BPM"] = str(round(bpm))
            if key_tag:
                audio["INITIALKEY"] = key_tag
            if genre:
                audio["GENRE"] = genre
            if artist:
                audio["ARTIST"] = artist
            if title:
                audio["TITLE"] = title
            if artwork:
                audio.clear_pictures()
                audio.add_picture(_flac_picture(artwork, artwork_mime))
            audio.save()
        else:
            audio = VORBIS_FORMATS[suffix](tmp_path)
            if bpm is not None:
                audio["BPM"] = str(round(bpm))
            if key_tag:
                audio["INITIALKEY"] = key_tag
            if genre:
                audio["GENRE"] = genre
            if artist:
                audio["ARTIST"] = artist
            if title:
                audio["TITLE"] = title
            if artwork:
                # Ogg Vorbis has no native picture block like FLAC -- the
                # de facto standard (used by foobar2000, Picard, etc.) is a
                # base64-encoded FLAC-style Picture block in this comment field.
                encoded = base64.b64encode(_flac_picture(artwork, artwork_mime).write())
                audio["metadata_block_picture"] = [encoded.decode("ascii")]
            audio.save()

        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)
