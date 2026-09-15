"""A minimal in-memory stand-in for a Firestore collection, just enough to
exercise profile_store/admin_store without touching real Firebase."""

from __future__ import annotations


class _FakeSnapshot:
    def __init__(self, data: dict | None):
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict:
        return dict(self._data) if self._data else {}


class _FakeDocRef:
    def __init__(self, store: dict, doc_id: str):
        self._store = store
        self._doc_id = doc_id

    def get(self) -> _FakeSnapshot:
        return _FakeSnapshot(self._store.get(self._doc_id))

    def set(self, data: dict, merge: bool = False) -> None:
        if merge and self._doc_id in self._store:
            self._store[self._doc_id] = {**self._store[self._doc_id], **data}
        else:
            self._store[self._doc_id] = dict(data)

    def delete(self) -> None:
        self._store.pop(self._doc_id, None)


class _FakeQuery:
    """A filtered view over a FakeCollection's docs -- just enough of
    Firestore's query builder interface (.where().stream()) to test code
    that filters server-side instead of streaming everything."""

    def __init__(self, docs: list[dict]):
        self._docs = docs

    def where(self, field: str, op: str, value) -> "_FakeQuery":
        if op not in ("==", "eq"):
            raise NotImplementedError(f"FakeCollection.where only supports '==', got {op!r}")
        return _FakeQuery([d for d in self._docs if d.get(field) == value])

    def stream(self):
        return [_FakeSnapshot(data) for data in self._docs]


class FakeCollection:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def document(self, doc_id: str) -> _FakeDocRef:
        return _FakeDocRef(self._store, doc_id)

    def stream(self):
        return [_FakeSnapshot(data) for data in self._store.values()]

    def where(self, field: str, op: str, value) -> _FakeQuery:
        return _FakeQuery(list(self._store.values())).where(field, op, value)


class _FakeBatch:
    """Just enough of Firestore's WriteBatch to test code that batches
    several .set() calls into one commit instead of one round-trip each."""

    def __init__(self):
        self._writes: list[tuple[_FakeDocRef, dict]] = []

    def set(self, doc_ref: _FakeDocRef, data: dict) -> None:
        self._writes.append((doc_ref, data))

    def commit(self) -> None:
        for doc_ref, data in self._writes:
            doc_ref.set(data)
        self._writes = []


class FakeClient:
    """Stands in for firestore.client() -- hands out the same FakeCollection
    instance per name (so state persists across calls) and a fresh batch."""

    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def collection(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection())

    def batch(self) -> _FakeBatch:
        return _FakeBatch()
