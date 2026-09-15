from __future__ import annotations

import uuid
from datetime import datetime, timezone

from firebase_admin import firestore

from .auth import get_app

VALID_CATEGORIES = {"support", "feedback"}


def _firestore_client():
    app = get_app()
    if app is None:
        raise RuntimeError("Firebase is not configured")
    return firestore.client(app=app)


def _feedback_collection():
    return _firestore_client().collection("feedback_submissions")


def create_feedback(
    category: str,
    message: str,
    email: str | None = None,
    subject: str | None = None,
    uid: str | None = None,
) -> dict:
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {category!r}")
    if not message or not message.strip():
        raise ValueError("message is required")

    feedback_id = uuid.uuid4().hex
    doc = {
        "feedback_id": feedback_id,
        "category": category,
        "subject": subject,
        "message": message.strip(),
        "email": email,
        "uid": uid,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }
    _feedback_collection().document(feedback_id).set(doc)
    return doc


def list_feedback() -> list[dict]:
    docs = [doc.to_dict() for doc in _feedback_collection().stream()]
    docs.sort(key=lambda d: d.get("submitted_at") or "", reverse=True)
    return docs


def mark_feedback_read(feedback_id: str, read: bool) -> dict:
    ref = _feedback_collection().document(feedback_id)
    if not ref.get().exists:
        raise ValueError(f"No such feedback submission: {feedback_id!r}")
    ref.set({"read": bool(read)}, merge=True)
    return ref.get().to_dict()


def delete_feedback(feedback_id: str) -> None:
    ref = _feedback_collection().document(feedback_id)
    if not ref.get().exists:
        raise ValueError(f"No such feedback submission: {feedback_id!r}")
    ref.delete()


def delete_feedback_batch(feedback_ids: list[str]) -> None:
    """Deletes multiple submissions (a "select all and delete" from the
    admin UI). Unknown ids are skipped rather than raising -- by the time a
    bulk delete lands, another admin tab or click may have already removed
    one of the selected rows, and that's not a reason to fail the rest."""
    collection = _feedback_collection()
    for feedback_id in feedback_ids:
        collection.document(feedback_id).delete()
