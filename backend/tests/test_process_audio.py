import asyncio
import io
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

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
    # 3 processed tracks + the manifest + the playlist
    assert len(names) == 5
    assert "crateprep-manifest.json" in names
    assert "crateprep-playlist.m3u8" in names


def test_build_zip_one_failure_does_not_lose_others(monkeypatch):
    real_analyze = process_audio._analyze_and_tag

    def flaky(content, ext, stem, version_tag, filename_template=None, deep_search=False):
        if stem == "bad":
            raise RuntimeError("boom")
        return real_analyze(content, ext, stem, version_tag, filename_template, deep_search)

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
