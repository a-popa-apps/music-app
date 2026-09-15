import asyncio
import io
import json
import math
import struct
import tempfile
import wave
import zipfile

import pytest

pytest.importorskip("essentia")

from fastapi import UploadFile

from app import process_audio


def _make_wav(freq: float = 220, duration: float = 1, sr: int = 22050) -> bytes:
    buffer = io.BytesIO()
    n = int(sr * duration)
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = bytearray()
        for i in range(n):
            sample = 0.5 * math.sin(2 * math.pi * freq * i / sr)
            frames += struct.pack("<h", int(sample * 32767))
        w.writeframes(bytes(frames))
    return buffer.getvalue()


class _UnclosableBytesIO(io.BytesIO):
    """aifc.Aifc_write.close() closes the underlying file object it was
    given (unlike wave.Wave_write, which only closes files it opened
    itself) -- it also writes the real frame count into the header at
    close time, so the bytes aren't valid until after that call. Silencing
    close() is the only way to get both: a fully-finalized AIFF and access
    to the buffer afterward."""

    def close(self):
        pass


def _make_aiff(freq: float = 220, duration: float = 1, sr: int = 22050) -> bytes:
    import aifc

    buffer = _UnclosableBytesIO()
    n = int(sr * duration)
    with aifc.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = bytearray()
        for i in range(n):
            sample = 0.5 * math.sin(2 * math.pi * freq * i / sr)
            frames += struct.pack(">h", int(sample * 32767))
        w.writeframes(bytes(frames))
    return buffer.getvalue()


def _upload(name: str, content: bytes) -> UploadFile:
    return UploadFile(io.BytesIO(content), filename=name)


def test_build_zip_processes_multiple_files_in_order():
    files = [_upload(f"Artist{i} - Title{i}.wav", _make_wav(200 + i * 10)) for i in range(3)]

    zip_bytes, manifest = asyncio.run(process_audio.build_zip(files))

    assert len(manifest) == 3
    original_filenames = {entry.get("original_filename") for entry in manifest.values()}
    assert original_filenames == {"Artist0 - Title0.wav", "Artist1 - Title1.wav", "Artist2 - Title2.wav"}
    for entry in manifest.values():
        assert 1 <= entry["energy"] <= 10
        assert entry["artist"] and entry["title"]
        # "Artist0 - Title0.wav" resolves via a clean local dash split --
        # name_source must be set here too (previously only set on the
        # embedded-tags/catalog-match/guessed branches), since the frontend's
        # post-batch quality summary depends on it always being present.
        assert entry["name_source"] == "local_dash_split"

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
    # 3 processed tracks + the manifest + the playlist
    assert len(names) == 5


def test_build_zip_spans_multiple_chunks_correctly(monkeypatch):
    # PROCESS_CONCURRENCY governs chunk size in build_zip -- with 5 files and
    # a chunk size of 2, this spans three chunks (2 + 2 + 1). Every file must
    # still be processed, in order, with none lost or duplicated across the
    # chunk boundary.
    monkeypatch.setattr(process_audio, "PROCESS_CONCURRENCY", 2)
    files = [_upload(f"Artist{i} - Title{i}.wav", _make_wav(200 + i * 10)) for i in range(5)]

    _, manifest = asyncio.run(process_audio.build_zip(files))

    assert len(manifest) == 5
    original_filenames = [entry.get("original_filename") for entry in manifest.values()]
    assert original_filenames == [f"Artist{i} - Title{i}.wav" for i in range(5)]


def test_build_zip_generates_browser_preview_for_aiff_but_not_wav():
    # Chrome/Firefox have no native AIFF decoder at all -- confirmed directly
    # against a real browser (canPlayType empty, decodeAudioData throws) even
    # on a perfectly valid file. build_zip must ship a browser-playable WAV
    # transcode alongside any AIFF track for in-app playback, referenced via
    # the manifest, while leaving formats browsers already support alone.
    files = [
        _upload("Artist - Title.aiff", _make_aiff(200)),
        _upload("Artist2 - Title2.wav", _make_wav(200)),
    ]

    zip_bytes, manifest = asyncio.run(process_audio.build_zip(files))

    by_original = {entry["original_filename"]: (name, entry) for name, entry in manifest.items()}
    aiff_name, aiff_entry = by_original["Artist - Title.aiff"]
    wav_name, wav_entry = by_original["Artist2 - Title2.wav"]

    assert aiff_entry.get("preview_filename") == f"{aiff_name}.preview.wav"
    assert "preview_filename" not in wav_entry

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert aiff_entry["preview_filename"] in names
        preview_bytes = zf.read(aiff_entry["preview_filename"])

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(preview_bytes)
        tmp.flush()
        with wave.open(tmp.name, "rb") as w:
            assert w.getnframes() > 0


def test_build_zip_enhanced_detection_threads_through_without_error():
    files = [_upload("Artist - Title.wav", _make_wav(200))]
    zip_bytes, manifest = asyncio.run(process_audio.build_zip(files, enhanced_detection=True))
    entry = next(iter(manifest.values()))
    assert entry["bpm"] is not None
    assert entry["key"] is not None
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
    assert "crateprep-manifest.json" in names
    assert "crateprep-playlist.m3u8" in names


def test_build_zip_ai_cleanup_used_when_local_paths_fail(monkeypatch):
    # No dash, single ambiguous word that guess_split can't split and that
    # lookup_track (mocked here to simulate no catalog match) can't resolve
    # -- ai_cleanup should be consulted before falling back to guess_split.
    monkeypatch.setattr(process_audio, "lookup_track", lambda stem: None)
    monkeypatch.setattr(
        process_audio, "ai_split_artist_title", lambda stem: ("Bicep", "Glue")
    )

    files = [_upload("bicepgluefinalmasterv2.wav", _make_wav(200))]
    _, manifest = asyncio.run(process_audio.build_zip(files, ai_cleanup=True))

    entry = next(iter(manifest.values()))
    assert (entry["artist"], entry["title"]) == ("Bicep", "Glue")
    assert entry["name_source"] == "ai_cleanup"


def test_build_zip_ai_cleanup_disabled_by_default(monkeypatch):
    monkeypatch.setattr(process_audio, "lookup_track", lambda stem: None)
    monkeypatch.setattr(
        process_audio,
        "ai_split_artist_title",
        lambda stem: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    files = [_upload("Two Words.wav", _make_wav(200))]
    _, manifest = asyncio.run(process_audio.build_zip(files))

    entry = next(iter(manifest.values()))
    assert entry["name_source"] == "guessed"


def test_build_zip_includes_batch_summary_when_available(monkeypatch):
    monkeypatch.setattr(
        process_audio, "generate_batch_summary", lambda manifest: "Mostly house, energy builds."
    )
    files = [_upload(f"Artist{i} - Title{i}.wav", _make_wav(200 + i * 10)) for i in range(2)]

    zip_bytes, _ = asyncio.run(process_audio.build_zip(files))

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        assert "crateprep-summary.json" in zf.namelist()
        summary = json.loads(zf.read("crateprep-summary.json"))
    assert summary == {"summary": "Mostly house, energy builds."}


def test_build_zip_omits_summary_file_when_none_returned(monkeypatch):
    monkeypatch.setattr(process_audio, "generate_batch_summary", lambda manifest: None)
    files = [_upload("Artist - Title.wav", _make_wav(200))]

    zip_bytes, _ = asyncio.run(process_audio.build_zip(files))

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        assert "crateprep-summary.json" not in zf.namelist()


def test_build_zip_one_failure_does_not_lose_others(monkeypatch):
    real_analyze = process_audio._analyze_and_tag

    def flaky(
        content,
        ext,
        stem,
        version_tag,
        filename_template=None,
        deep_search=False,
        enhanced_detection=False,
        ai_cleanup=False,
    ):
        if stem == "bad":
            raise RuntimeError("boom")
        return real_analyze(
            content, ext, stem, version_tag, filename_template, deep_search, enhanced_detection, ai_cleanup
        )

    monkeypatch.setattr(process_audio, "_analyze_and_tag", flaky)

    files = [
        _upload("good1.wav", _make_wav(200)),
        _upload("bad.wav", _make_wav(210)),
        _upload("good2.wav", _make_wav(220)),
    ]

    _, manifest = asyncio.run(process_audio.build_zip(files))

    assert len(manifest) == 3
    by_original = {entry["original_filename"]: entry for entry in manifest.values()}
    assert "error" in by_original["bad.wav"]
    assert "error" not in by_original["good1.wav"]
    assert "error" not in by_original["good2.wav"]


def test_duration_reflects_full_track_even_though_default_mode_only_decodes_a_window():
    # Default (non-enhanced) mode only decodes/analyzes the first
    # ANALYSIS_SECONDS for speed -- duration must still reflect the
    # track's real, full length, not however much was actually decoded.
    files = [_upload("Artist - Title.wav", _make_wav(duration=35))]
    _, manifest = asyncio.run(process_audio.build_zip(files))
    entry = next(iter(manifest.values()))
    assert entry["duration_seconds"] is not None
    assert abs(entry["duration_seconds"] - 35) < 0.5


def test_default_mode_only_decodes_the_analysis_window(monkeypatch):
    # detect_bpm itself is responsible for deciding whether its windowed
    # read needs a full-track retry (covered directly in test_detect_bpm.py)
    # -- this test only checks build_zip's own wiring: when detect_bpm
    # doesn't call full_audio_loader, no second decode happens.
    real_load_audio = process_audio.load_audio
    calls = []

    def spy(content, ext, max_seconds=None):
        calls.append(max_seconds)
        return real_load_audio(content, ext, max_seconds=max_seconds)

    monkeypatch.setattr(process_audio, "load_audio", spy)
    monkeypatch.setattr(
        process_audio, "detect_bpm", lambda audio, full_track=False, full_audio_loader=None: 128.0
    )

    files = [_upload("Artist - Title.wav", _make_wav(duration=2))]
    asyncio.run(process_audio.build_zip(files))

    assert calls == [process_audio.ANALYSIS_SECONDS]


def test_default_mode_escalates_to_full_decode_on_low_confidence_bpm(monkeypatch):
    # When detect_bpm decides it needs the full track (simulated here by
    # actually calling the loader it's given, standing in for its own
    # low-confidence retry), build_zip must decode the full track for it --
    # a second, full decode for this track specifically.
    real_load_audio = process_audio.load_audio
    calls = []

    def spy(content, ext, max_seconds=None):
        calls.append(max_seconds)
        return real_load_audio(content, ext, max_seconds=max_seconds)

    monkeypatch.setattr(process_audio, "load_audio", spy)

    def fake_detect_bpm(audio, full_track=False, full_audio_loader=None):
        if full_audio_loader is not None:
            full_audio_loader()
        return 128.0

    monkeypatch.setattr(process_audio, "detect_bpm", fake_detect_bpm)

    files = [_upload("Artist - Title.wav", _make_wav(duration=2))]
    asyncio.run(process_audio.build_zip(files))

    assert calls == [process_audio.ANALYSIS_SECONDS, None]


def test_enhanced_detection_decodes_the_full_track(monkeypatch):
    real_load_audio = process_audio.load_audio
    calls = []

    def spy(content, ext, max_seconds=None):
        calls.append(max_seconds)
        return real_load_audio(content, ext, max_seconds=max_seconds)

    monkeypatch.setattr(process_audio, "load_audio", spy)

    files = [_upload("Artist - Title.wav", _make_wav(duration=2))]
    asyncio.run(process_audio.build_zip(files, enhanced_detection=True))

    assert calls == [None]


def test_resolve_artist_title_prefers_filename_when_tags_conflict(monkeypatch):
    # The file's own ID3 tags say "Wrong Artist", but the filename is an
    # unambiguous "Artist - Title" split naming the real artist -- the
    # filename should win rather than silently propagating a mistagged
    # artist (e.g. from a re-rip or a bad auto-tagger).
    monkeypatch.setattr(
        process_audio,
        "detect_genre",
        lambda artist, title, deep_search=False: {"genre": None, "artwork_url": None},
    )

    artist, title, genre, debug = process_audio._resolve_artist_title_genre(
        "Real Artist - Real Title",
        embedded_tags={"artist": "Wrong Artist", "title": "Real Title", "genre": None, "version_tag": None},
    )

    assert (artist, title) == ("Real Artist", "Real Title")
    assert debug["name_source"] == "local_dash_split"


def test_resolve_artist_title_trusts_tags_when_they_agree_with_filename(monkeypatch):
    monkeypatch.setattr(
        process_audio,
        "detect_genre",
        lambda artist, title, deep_search=False: {"genre": None, "artwork_url": None},
    )

    artist, title, genre, debug = process_audio._resolve_artist_title_genre(
        "real artist - Real Title",
        embedded_tags={"artist": "Real Artist", "title": "Real Title", "genre": "House", "version_tag": None},
    )

    # Formatting differs (case) but it's the same artist -- no conflict, so
    # the tag's own (better-formatted) artist casing is kept.
    assert (artist, title) == ("Real Artist", "Real Title")
    assert genre == "House"
    assert debug["name_source"] == "embedded_tags"


def test_resolve_artist_title_prefers_filename_with_comma_separator_and_track_number(monkeypatch):
    # The exact real-world case this was reported from: a ripped-CD-style
    # filename with a leading zero-padded track number and a comma
    # separator, plus tags mistagged with the wrong artist.
    monkeypatch.setattr(
        process_audio,
        "detect_genre",
        lambda artist, title, deep_search=False: {"genre": None, "artwork_url": None},
    )

    stem, _, _ = process_audio.prepare_stem("09 Slam , Life Between Life.mp3")
    artist, title, genre, debug = process_audio._resolve_artist_title_genre(
        stem,
        embedded_tags={
            "artist": "Wrong Tagged Artist",
            "title": "Life Between Life",
            "genre": None,
            "version_tag": None,
        },
    )

    assert (artist, title) == ("Slam", "Life Between Life")
    assert debug["name_source"] == "local_dash_split"


def test_resolve_artist_title_trusts_tags_when_filename_has_no_dash_split(monkeypatch):
    # No explicit "Artist - Title" filename to compare against -- tags stay
    # authoritative, matching the app's primary use case (messy filename,
    # trustworthy tags).
    monkeypatch.setattr(
        process_audio,
        "detect_genre",
        lambda artist, title, deep_search=False: {"genre": None, "artwork_url": None},
    )

    artist, title, genre, debug = process_audio._resolve_artist_title_genre(
        "messydownloadfilenamev2final",
        embedded_tags={"artist": "Real Artist", "title": "Real Title", "genre": None, "version_tag": None},
    )

    assert (artist, title) == ("Real Artist", "Real Title")
    assert debug["name_source"] == "embedded_tags"


def test_build_corrected_zip_writes_supplied_values_not_detected_ones():
    # No detection at all should run here -- these values are exactly what
    # should land in the output, whether or not they'd match what
    # detection would have guessed for this audio.
    files = [_upload("track.wav", _make_wav(200))]
    corrections = [
        {
            "artist": "Corrected Artist",
            "title": "Corrected Title",
            "genre": "Corrected Genre",
            "bpm": 128.0,
            "camelot": "8A",
            "tonality": "Am",
            "duration_seconds": 12.3,
        }
    ]

    zip_bytes = asyncio.run(process_audio.build_corrected_zip(files, corrections))

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        manifest = json.loads(zf.read("crateprep-manifest.json"))
        [name] = [n for n in zf.namelist() if n.endswith(".wav")]
        tagged_content = zf.read(name)

    assert "Corrected Artist" in name
    assert "Corrected Title" in name
    entry = manifest[name]
    assert entry["artist"] == "Corrected Artist"
    assert entry["title"] == "Corrected Title"
    assert entry["genre"] == "Corrected Genre"
    assert entry["bpm"] == 128.0
    assert entry["camelot"] == "8A"
    assert entry["original_filename"] == "track.wav"

    from mutagen.wave import WAVE

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(tagged_content)
        tmp.flush()
        audio = WAVE(tmp.name)
        assert str(audio.tags["TPE1"]) == "Corrected Artist"
        assert str(audio.tags["TIT2"]) == "Corrected Title"
        assert str(audio.tags["TCON"]) == "Corrected Genre"
        assert str(audio.tags["TBPM"]) == "128"
        assert str(audio.tags["TKEY"]) == "Am"


def test_build_corrected_zip_matches_files_to_corrections_positionally():
    files = [_upload("a.wav", _make_wav(200)), _upload("b.wav", _make_wav(210))]
    corrections = [
        {"artist": "Artist A", "title": "Title A"},
        {"artist": "Artist B", "title": "Title B"},
    ]

    zip_bytes = asyncio.run(process_audio.build_corrected_zip(files, corrections))

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        manifest = json.loads(zf.read("crateprep-manifest.json"))

    original_filenames = {entry["original_filename"] for entry in manifest.values()}
    assert original_filenames == {"a.wav", "b.wav"}
    by_original = {entry["original_filename"]: entry for entry in manifest.values()}
    assert by_original["a.wav"]["artist"] == "Artist A"
    assert by_original["b.wav"]["artist"] == "Artist B"


def test_build_corrected_zip_applies_filename_template():
    files = [_upload("track.wav", _make_wav(200))]
    corrections = [{"artist": "The Artist", "title": "The Title", "bpm": 128.0, "camelot": "8A"}]

    zip_bytes = asyncio.run(
        process_audio.build_corrected_zip(
            files, corrections, filename_template="{bpm} - {artist} - {title}"
        )
    )

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        [name] = [n for n in zf.namelist() if n.endswith(".wav")]

    assert name.startswith("128 - The Artist - The Title")


def test_build_corrected_zip_dedupes_names_that_collide():
    files = [_upload("a.wav", _make_wav(200)), _upload("b.wav", _make_wav(210))]
    corrections = [
        {"artist": "Same Artist", "title": "Same Title"},
        {"artist": "Same Artist", "title": "Same Title"},
    ]

    zip_bytes = asyncio.run(process_audio.build_corrected_zip(files, corrections))

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = [n for n in zf.namelist() if n.endswith(".wav")]

    assert len(names) == 2
    assert len(set(names)) == 2


_FAKE_ARTWORK = (b"\xff\xd8\xff\xe0" + b"\x00" * 32 + b"\xff\xd9", "image/jpeg")


def test_build_zip_embeds_catalog_artwork_when_found(monkeypatch):
    monkeypatch.setattr(
        process_audio,
        "detect_genre",
        lambda artist, title, deep_search=False: {
            "genre": "House",
            "artwork_url": "https://example.com/cover.jpg",
        },
    )
    monkeypatch.setattr(
        process_audio, "fetch_artwork", lambda url: _FAKE_ARTWORK if url else None
    )

    files = [_upload("Real Artist - Real Title.wav", _make_wav(200))]
    zip_bytes, manifest = asyncio.run(process_audio.build_zip(files))

    # Not a manifest field -- internal-only, used to embed the tag itself.
    [entry] = manifest.values()
    assert "artwork_url" not in entry

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        [wav_name] = [n for n in zf.namelist() if n.endswith(".wav")]
        tagged_bytes = zf.read(wav_name)

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(tagged_bytes)
        tmp.flush()
        from mutagen.wave import WAVE

        audio = WAVE(tmp.name)
        apic = audio.tags["APIC:Cover"]
        assert apic.data == _FAKE_ARTWORK[0]
        assert apic.mime == _FAKE_ARTWORK[1]


def test_build_zip_has_no_artwork_tag_when_none_found(monkeypatch):
    monkeypatch.setattr(
        process_audio,
        "detect_genre",
        lambda artist, title, deep_search=False: {"genre": None, "artwork_url": None},
    )

    files = [_upload("Real Artist - Real Title.wav", _make_wav(200))]
    zip_bytes, _ = asyncio.run(process_audio.build_zip(files))

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        [wav_name] = [n for n in zf.namelist() if n.endswith(".wav")]
        tagged_bytes = zf.read(wav_name)

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(tagged_bytes)
        tmp.flush()
        from mutagen.wave import WAVE

        audio = WAVE(tmp.name)
        assert "APIC:Cover" not in audio.tags
