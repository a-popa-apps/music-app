from __future__ import annotations

import uuid
from datetime import datetime, timezone

from firebase_admin import firestore

from .auth import get_app


def _firestore_client():
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    return firestore.client(app=app)


def _history_collection():
    return _firestore_client().collection("history")


def add_history_entries(uid: str, manifest: dict) -> None:
    """Persists one doc per processed track (metadata only -- never the
    audio itself, consistent with the app's no-audio-retention policy).
    Best-effort from the caller's perspective: a failure here shouldn't
    block returning the processed zip to the user.

    Written as a single Firestore batch instead of one .set() per track --
    a 50-track Pro batch used to mean 50 sequential network round-trips."""
    processed_at = datetime.now(timezone.utc).isoformat()
    client = _firestore_client()
    collection = client.collection("history")
    batch = client.batch()

    for filename, entry in manifest.items():
        history_id = uuid.uuid4().hex
        batch.set(
            collection.document(history_id),
            {
                "history_id": history_id,
                "uid": uid,
                "filename": filename,
                "original_filename": entry.get("original_filename", filename),
                "bpm": entry.get("bpm"),
                "key": entry.get("key"),
                "camelot": entry.get("camelot"),
                "genre": entry.get("genre"),
                "energy": entry.get("energy"),
                "duration_seconds": entry.get("duration_seconds"),
                "failed": bool(entry.get("error")),
                "processed_at": processed_at,
            },
        )

    if manifest:
        batch.commit()


def list_history(uid: str, limit: int = 1000) -> list[dict]:
    # Filtered server-side (Firestore `where`) rather than streaming every
    # user's history and filtering in Python -- this used to cost reads
    # proportional to the whole system's history size on every call.
    docs = [doc.to_dict() for doc in _history_collection().where("uid", "==", uid).stream()]
    docs.sort(key=lambda d: d.get("processed_at") or "", reverse=True)
    return docs[:limit]


def clear_history(uid: str) -> int:
    collection = _history_collection()
    deleted = 0
    for doc in collection.where("uid", "==", uid).stream():
        data = doc.to_dict()
        collection.document(data["history_id"]).delete()
        deleted += 1
    return deleted
