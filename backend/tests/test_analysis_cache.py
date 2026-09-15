from tests.fake_firestore import FakeClient

from app import analysis_cache


def _use_fake_client(monkeypatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr(analysis_cache, "_firestore_client", lambda: client)
    return client


class TestExactMatchCache:
    def test_miss_when_nothing_stored(self, monkeypatch):
        _use_fake_client(monkeypatch)
        assert analysis_cache.get_exact_match("deadbeef") is None

    def test_stores_and_retrieves_the_analyzed_fields(self, monkeypatch):
        _use_fake_client(monkeypatch)
        entry = {
            "bpm": 127.0,
            "key": "Eb minor",
            "camelot": "2A",
            "tonality": "Ebm",
            "energy": 1,
            "genre": "Downtempo",
            "artist": "Ursula Rucker",
            "title": "Circe",
            "name_source": "embedded_tags",
            "artwork_url": "https://x/cover.jpg",
            # Fields that shouldn't ride along into the cache document.
            "duration_seconds": 384.0,
            "bpm_error": None,
        }

        analysis_cache.store_exact_match("hash1", entry)
        cached = analysis_cache.get_exact_match("hash1")

        assert cached == {
            "bpm": 127.0,
            "key": "Eb minor",
            "camelot": "2A",
            "tonality": "Ebm",
            "energy": 1,
            "genre": "Downtempo",
            "artist": "Ursula Rucker",
            "title": "Circe",
            "name_source": "embedded_tags",
            "artwork_url": "https://x/cover.jpg",
        }

    def test_none_fields_are_not_stored(self, monkeypatch):
        _use_fake_client(monkeypatch)
        analysis_cache.store_exact_match("hash2", {"bpm": 128.0, "key": None, "genre": None})
        assert analysis_cache.get_exact_match("hash2") == {"bpm": 128.0}

    def test_storing_nothing_useful_leaves_no_document(self, monkeypatch):
        client = _use_fake_client(monkeypatch)
        analysis_cache.store_exact_match("hash3", {"bpm": None, "key": None})
        assert analysis_cache.get_exact_match("hash3") is None
        assert client.collection(analysis_cache.EXACT_COLLECTION)._store == {}

    def test_no_firebase_configured_is_a_silent_no_op(self, monkeypatch):
        monkeypatch.setattr(analysis_cache, "_firestore_client", lambda: None)
        analysis_cache.store_exact_match("hash4", {"bpm": 128.0})  # must not raise
        assert analysis_cache.get_exact_match("hash4") is None


class TestGenreLookupCache:
    def test_miss_when_nothing_stored(self, monkeypatch):
        _use_fake_client(monkeypatch)
        assert analysis_cache.get_genre_lookup("Rob Yancey", "Circe") is None

    def test_stores_and_retrieves_by_normalized_artist_and_title(self, monkeypatch):
        _use_fake_client(monkeypatch)
        analysis_cache.store_genre_lookup("Rob Yancey", "Circe", "Downtempo", "https://x/cover.jpg")

        # Case/punctuation differences shouldn't matter -- two rips of the
        # same song rarely have identically-formatted tags.
        cached = analysis_cache.get_genre_lookup("rob-yancey", "CIRCE!!")

        assert cached == {"genre": "Downtempo", "artwork_url": "https://x/cover.jpg"}

    def test_a_result_with_neither_genre_nor_artwork_is_not_cached(self, monkeypatch):
        client = _use_fake_client(monkeypatch)
        analysis_cache.store_genre_lookup("A", "B", None, None)
        assert analysis_cache.get_genre_lookup("A", "B") is None
        assert client.collection(analysis_cache.METADATA_COLLECTION)._store == {}

    def test_different_titles_do_not_collide(self, monkeypatch):
        _use_fake_client(monkeypatch)
        analysis_cache.store_genre_lookup("Artist", "Song One", "House", None)
        assert analysis_cache.get_genre_lookup("Artist", "Song Two") is None
