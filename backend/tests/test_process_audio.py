import asyncio
import io
import json
import math
import struct
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
