from __future__ import annotations

import hashlib
import logging
import re

from firebase_admin import firestore

from .auth import get_app

logger = logging.getLogger(__name__)

# Two independent caches, global across all users (deliberately -- the
# whole point is that one user's upload can save the next user's, and
# none of what's cached is user-specific: audio-derived numbers and
# publicly-sourced catalog metadata).
#
# EXACT_COLLECTION: keyed by a SHA-256 of the raw uploaded bytes. A hit
# means literally the same file was already fully analyzed before, so
# every expensive step (essentia decode/analysis, genre catalog lookups)
# can be skipped outright. Exact-match only, deliberately: this never
# risks conflating two different tracks or reusing a subtly-wrong
# BPM/key from a different rip of the "same" song.
#
# METADATA_COLLECTION: keyed by a normalized "artist::title", used only
# for the genre/artwork catalog lookup (see detect_genre.py). This is
# what actually helps the common "same song, different rip/format"
# case an exact hash can't -- genre and artwork don't change between an
# MP3 and a FLAC of the same official release, so it's safe to share
# even when the audio bytes (and therefore BPM/key/energy, kept
# per-file always) don't match at all.
EXACT_COLLECTION = "track_analysis_cache"
METADATA_COLLECTION = "genre_lookup_cache"

EXACT_CACHE_FIELDS = (
    "bpm",
    "key",
    "camelot",
    "tonality",
    "energy",
    "genre",
    "artist",
    "title",
    "artwork_url",
    "name_source",
)


def _firestore_client():
    app = get_app()
    if app is None:
        return None
    return firestore.client(app=app)


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _metadata_key(artist: str, title: str) -> str:
    return f"{_normalize(artist)}::{_normalize(title)}"


def get_exact_match(hash_hex: str) -> dict | None:
    client = _firestore_client()
    if client is None:
        return None
    try:
        doc = client.collection(EXACT_COLLECTION).document(hash_hex).get()
    except Exception as e:
        logger.warning("analysis cache lookup failed: %s", e)
        return None
    return doc.to_dict() if doc.exists else None


def store_exact_match(hash_hex: str, entry: dict) -> None:
    client = _firestore_client()
    if client is None:
        return
    data = {field: entry[field] for field in EXACT_CACHE_FIELDS if entry.get(field) is not None}
    if not data:
        return
    try:
        client.collection(EXACT_COLLECTION).document(hash_hex).set(data)
    except Exception as e:
        logger.warning("analysis cache write failed: %s", e)


def get_genre_lookup(artist: str, title: str) -> dict | None:
    client = _firestore_client()
    if client is None:
        return None
    try:
        doc = client.collection(METADATA_COLLECTION).document(_metadata_key(artist, title)).get()
    except Exception as e:
        logger.warning("genre lookup cache read failed: %s", e)
        return None
    return doc.to_dict() if doc.exists else None


def store_genre_lookup(artist: str, title: str, genre: str | None, artwork_url: str | None) -> None:
    if genre is None and artwork_url is None:
        return  # nothing worth remembering -- would just freeze a future, deeper lookup out
    client = _firestore_client()
    if client is None:
        return
    try:
        client.collection(METADATA_COLLECTION).document(_metadata_key(artist, title)).set(
            {"genre": genre, "artwork_url": artwork_url}
        )
    except Exception as e:
        logger.warning("genre lookup cache write failed: %s", e)
