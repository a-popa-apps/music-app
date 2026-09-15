import json

import pytest

from app import detect_genre


class FakeResponse:
    def __init__(self, body: dict | bytes, content_type: str = "application/json"):
        self._body = json.dumps(body).encode("utf-8") if isinstance(body, dict) else body
        self.headers = _FakeHeaders(content_type)

    def read(self, n: int = -1) -> bytes:
        return self._body if n < 0 else self._body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeHeaders:
    def __init__(self, content_type: str):
        self._content_type = content_type

    def get_content_type(self):
        return self._content_type


def _routed_urlopen(routes: dict):
    """Maps a URL substring to a FakeResponse (or a callable returning one),
    checked in insertion order -- lets one test stub several sequential
    calls without depending on exact call order."""

    def fake(req, timeout=None):
        url = req.full_url
        for substr, response in routes.items():
            if substr in url:
                return response(req) if callable(response) else response
        raise AssertionError(f"unexpected URL: {url}")

    return fake


class TestItunesLookup:
    def test_finds_plausible_match_with_genre_and_artwork(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {
                    "results": [
                        {
                            "artistName": "Daft Punk",
                            "trackName": "One More Time",
                            "primaryGenreName": "Dance",
                            "artworkUrl100": "https://example.com/art/100x100bb.jpg",
                        }
                    ]
                }
            ),
        )

        result = detect_genre._itunes_track_lookup("daft punk one more time")
        assert result == {
            "artist": "Daft Punk",
            "title": "One More Time",
            "genre": "Dance",
            "artwork_url": "https://example.com/art/600x600bb.jpg",
        }

    def test_skips_implausible_results(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {"results": [{"artistName": "Totally Unrelated", "trackName": "Nothing Alike"}]}
            ),
        )
        assert detect_genre._itunes_track_lookup("daft punk one more time") is None

    def test_request_failure_returns_none(self, monkeypatch):
        def raise_error(req, timeout=None):
            raise OSError("boom")

        monkeypatch.setattr(detect_genre.urllib.request, "urlopen", raise_error)
        assert detect_genre._itunes_track_lookup("daft punk one more time") is None


class TestDeezerLookup:
    def test_finds_plausible_match_with_artwork_but_no_genre(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {
                    "data": [
                        {
                            "artist": {"name": "Daft Punk"},
                            "title": "One More Time",
                            "album": {
                                "cover_xl": "https://example.com/xl.jpg",
                                "cover_big": "https://example.com/big.jpg",
                            },
                        }
                    ]
                }
            ),
        )

        result = detect_genre._deezer_track_lookup("daft punk one more time")
        assert result == {
            "artist": "Daft Punk",
            "title": "One More Time",
            "genre": None,
            "artwork_url": "https://example.com/xl.jpg",
        }

    def test_falls_back_to_smaller_cover_when_xl_missing(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {
                    "data": [
                        {
                            "artist": {"name": "Daft Punk"},
                            "title": "One More Time",
                            "album": {"cover_medium": "https://example.com/medium.jpg"},
                        }
                    ]
                }
            ),
        )
        result = detect_genre._deezer_track_lookup("daft punk one more time")
        assert result["artwork_url"] == "https://example.com/medium.jpg"


class TestLookupTrackChain:
    def test_falls_through_spotify_discogs_to_itunes_then_deezer(self, monkeypatch):
        monkeypatch.setattr(detect_genre, "_spotify_track_lookup", lambda q: None)
        monkeypatch.setattr(detect_genre, "_discogs_track_lookup", lambda q: None)
        monkeypatch.setattr(detect_genre, "_itunes_track_lookup", lambda q: None)
        called = {}

        def fake_deezer(q):
            called["hit"] = True
            return {"artist": "A", "title": "B", "genre": "House", "artwork_url": None}

        monkeypatch.setattr(detect_genre, "_deezer_track_lookup", fake_deezer)

        result = detect_genre.lookup_track("some query")
        assert called["hit"] is True
        assert result["genre"] == "House"

    def test_stops_immediately_once_first_match_already_has_artwork(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre,
            "_spotify_track_lookup",
            lambda q: {"artist": "A", "title": "B", "genre": "Techno", "artwork_url": "https://x/1.jpg"},
        )
        never_called = []
        monkeypatch.setattr(detect_genre, "_discogs_track_lookup", lambda q: never_called.append(1))
        monkeypatch.setattr(detect_genre, "_itunes_track_lookup", lambda q: never_called.append(1))
        monkeypatch.setattr(detect_genre, "_deezer_track_lookup", lambda q: never_called.append(1))

        detect_genre.lookup_track("some query")
        assert never_called == []

    def test_keeps_trying_later_sources_for_artwork_when_first_match_lacks_it(self, monkeypatch):
        # Mirrors a real gap found live: Discogs without a token (or a
        # release with no scanned cover) returns a plausible match but no
        # cover_image -- iTunes/Deezer's artwork shouldn't be thrown away
        # just because Discogs already resolved artist/title/genre.
        monkeypatch.setattr(
            detect_genre,
            "_spotify_track_lookup",
            lambda q: None,
        )
        monkeypatch.setattr(
            detect_genre,
            "_discogs_track_lookup",
            lambda q: {"artist": "A", "title": "B", "genre": "House", "artwork_url": None},
        )
        monkeypatch.setattr(
            detect_genre,
            "_itunes_track_lookup",
            lambda q: {"artist": "A", "title": "B", "genre": "Dance", "artwork_url": "https://x/itunes.jpg"},
        )
        never_called = []
        monkeypatch.setattr(detect_genre, "_deezer_track_lookup", lambda q: never_called.append(1))

        result = detect_genre.lookup_track("some query")
        # Genre stays Discogs' (first match wins for genre/artist/title),
        # but artwork gets backfilled from iTunes.
        assert result == {"artist": "A", "title": "B", "genre": "House", "artwork_url": "https://x/itunes.jpg"}
        assert never_called == []  # artwork found -- Deezer never needed

    def test_returns_first_match_even_if_nobody_ever_has_artwork(self, monkeypatch):
        monkeypatch.setattr(detect_genre, "_spotify_track_lookup", lambda q: None)
        monkeypatch.setattr(
            detect_genre,
            "_discogs_track_lookup",
            lambda q: {"artist": "A", "title": "B", "genre": "House", "artwork_url": None},
        )
        monkeypatch.setattr(detect_genre, "_itunes_track_lookup", lambda q: None)
        monkeypatch.setattr(detect_genre, "_deezer_track_lookup", lambda q: None)

        result = detect_genre.lookup_track("some query")
        assert result == {"artist": "A", "title": "B", "genre": "House", "artwork_url": None}

    def test_empty_query_returns_none(self):
        assert detect_genre.lookup_track("") is None


class TestMusicBrainzGenreLookup:
    def test_finds_genre_inline_on_search_result(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {
                    "recordings": [
                        {
                            "id": "abc-123",
                            "title": "One More Time",
                            "artist-credit": [{"name": "Daft Punk"}],
                            "genres": [{"name": "house", "count": 5}, {"name": "disco", "count": 1}],
                        }
                    ]
                }
            ),
        )
        result = detect_genre._musicbrainz_genre_lookup("Daft Punk", "One More Time")
        assert result == {"genre": "house", "artwork_url": None}

    def test_fetches_genre_via_second_call_when_missing_from_search(self, monkeypatch):
        routes = {
            "/recording?query": FakeResponse(
                {
                    "recordings": [
                        {
                            "id": "abc-123",
                            "title": "One More Time",
                            "artist-credit": [{"name": "Daft Punk"}],
                        }
                    ]
                }
            ),
            "/recording/abc-123": FakeResponse({"genres": [{"name": "electronic", "count": 3}]}),
        }
        monkeypatch.setattr(detect_genre.urllib.request, "urlopen", _routed_urlopen(routes))
        result = detect_genre._musicbrainz_genre_lookup("Daft Punk", "One More Time")
        assert result == {"genre": "electronic", "artwork_url": None}

    def test_skips_implausible_recordings(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {
                    "recordings": [
                        {
                            "id": "xyz",
                            "title": "Completely Different Song",
                            "artist-credit": [{"name": "Some Cover Band"}],
                        }
                    ]
                }
            ),
        )
        assert detect_genre._musicbrainz_genre_lookup("Daft Punk", "One More Time") is None

    def test_request_failure_returns_none(self, monkeypatch):
        def raise_error(req, timeout=None):
            raise OSError("musicbrainz is busy")

        monkeypatch.setattr(detect_genre.urllib.request, "urlopen", raise_error)
        assert detect_genre._musicbrainz_genre_lookup("Daft Punk", "One More Time") is None


class TestTheAudioDbGenreLookup:
    def test_finds_genre_and_artwork(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {
                    "track": [
                        {
                            "strArtist": "Daft Punk",
                            "strTrack": "One More Time",
                            "strGenre": "House",
                            "strTrackThumb": "https://example.com/thumb.jpg",
                        }
                    ]
                }
            ),
        )
        result = detect_genre._theaudiodb_genre_lookup("Daft Punk", "One More Time")
        assert result == {"genre": "House", "artwork_url": "https://example.com/thumb.jpg"}

    def test_no_matches_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse({"track": None}),
        )
        assert detect_genre._theaudiodb_genre_lookup("Daft Punk", "One More Time") is None


class TestLastFmGenreLookup:
    def test_returns_none_without_api_key(self, monkeypatch):
        monkeypatch.setattr(detect_genre, "LASTFM_API_KEY", None)
        called = []
        monkeypatch.setattr(
            detect_genre.urllib.request, "urlopen", lambda req, timeout=None: called.append(1)
        )
        assert detect_genre._lastfm_genre_lookup("Daft Punk", "One More Time") is None
        assert called == []

    def test_returns_top_tag_as_genre(self, monkeypatch):
        monkeypatch.setattr(detect_genre, "LASTFM_API_KEY", "test-key")
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(
                {"toptags": {"tag": [{"name": "french house"}, {"name": "00s"}]}}
            ),
        )
        result = detect_genre._lastfm_genre_lookup("Daft Punk", "One More Time")
        assert result == {"genre": "french house", "artwork_url": None}

    def test_no_tags_returns_none(self, monkeypatch):
        monkeypatch.setattr(detect_genre, "LASTFM_API_KEY", "test-key")
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse({"toptags": {"tag": []}}),
        )
        assert detect_genre._lastfm_genre_lookup("Daft Punk", "One More Time") is None


class TestFetchArtwork:
    def test_downloads_image_bytes(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(b"\xff\xd8\xff\xe0fakejpeg", "image/jpeg"),
        )
        result = detect_genre.fetch_artwork("https://example.com/art.jpg")
        assert result == (b"\xff\xd8\xff\xe0fakejpeg", "image/jpeg")

    def test_none_url_returns_none(self):
        assert detect_genre.fetch_artwork(None) is None

    def test_non_image_content_type_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(b"<html>oops</html>", "text/html"),
        )
        assert detect_genre.fetch_artwork("https://example.com/not-an-image") is None

    def test_oversized_response_returns_none(self, monkeypatch):
        monkeypatch.setattr(detect_genre, "MAX_ARTWORK_BYTES", 10)
        monkeypatch.setattr(
            detect_genre.urllib.request,
            "urlopen",
            lambda req, timeout=None: FakeResponse(b"x" * 100, "image/jpeg"),
        )
        assert detect_genre.fetch_artwork("https://example.com/huge.jpg") is None

    def test_request_failure_returns_none(self, monkeypatch):
        def raise_error(req, timeout=None):
            raise OSError("boom")

        monkeypatch.setattr(detect_genre.urllib.request, "urlopen", raise_error)
        assert detect_genre.fetch_artwork("https://example.com/art.jpg") is None


class TestDetectGenre:
    def test_missing_artist_or_title_returns_empty_result(self):
        assert detect_genre.detect_genre(None, "Title") == {"genre": None, "artwork_url": None}
        assert detect_genre.detect_genre("Artist", None) == {"genre": None, "artwork_url": None}

    def test_uses_lookup_track_result_when_it_has_genre(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre,
            "lookup_track",
            lambda q: {"artist": "A", "title": "B", "genre": "Techno", "artwork_url": "https://x/1.jpg"},
        )
        result = detect_genre.detect_genre("A", "B")
        assert result == {"genre": "Techno", "artwork_url": "https://x/1.jpg"}

    def test_falls_through_to_secondary_sources_when_no_genre_found(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre,
            "lookup_track",
            lambda q: {"artist": "A", "title": "B", "genre": None, "artwork_url": "https://x/1.jpg"},
        )
        monkeypatch.setattr(detect_genre, "_musicbrainz_genre_lookup", lambda a, t: None)
        monkeypatch.setattr(
            detect_genre, "_theaudiodb_genre_lookup", lambda a, t: {"genre": "House", "artwork_url": None}
        )
        called_lastfm = []
        monkeypatch.setattr(
            detect_genre, "_lastfm_genre_lookup", lambda a, t: called_lastfm.append(1)
        )

        result = detect_genre.detect_genre("A", "B")
        # Genre comes from TheAudioDB, but the earlier lookup_track artwork
        # is preserved since TheAudioDB didn't supply its own here.
        assert result == {"genre": "House", "artwork_url": "https://x/1.jpg"}
        assert called_lastfm == []  # never reached -- TheAudioDB already succeeded

    def test_keeps_first_artwork_seen_even_if_later_source_has_none(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre, "lookup_track", lambda q: {"artist": "A", "title": "B", "genre": None, "artwork_url": None}
        )
        monkeypatch.setattr(
            detect_genre,
            "_musicbrainz_genre_lookup",
            lambda a, t: {"genre": None, "artwork_url": "https://mb/art.jpg"},
        )
        monkeypatch.setattr(
            detect_genre, "_theaudiodb_genre_lookup", lambda a, t: {"genre": "House", "artwork_url": None}
        )
        result = detect_genre.detect_genre("A", "B")
        assert result == {"genre": "House", "artwork_url": "https://mb/art.jpg"}

    def test_deep_search_used_as_last_resort(self, monkeypatch):
        monkeypatch.setattr(
            detect_genre, "lookup_track", lambda q: None
        )
        monkeypatch.setattr(detect_genre, "_musicbrainz_genre_lookup", lambda a, t: None)
        monkeypatch.setattr(detect_genre, "_theaudiodb_genre_lookup", lambda a, t: None)
        monkeypatch.setattr(detect_genre, "_lastfm_genre_lookup", lambda a, t: None)
        monkeypatch.setattr(
            detect_genre, "deep_discogs_lookup", lambda a, t: {"artist": a, "title": t, "genre": "Deep House"}
        )

        assert detect_genre.detect_genre("A", "B", deep_search=False) == {"genre": None, "artwork_url": None}
        assert detect_genre.detect_genre("A", "B", deep_search=True) == {
            "genre": "Deep House",
            "artwork_url": None,
        }

    def test_nothing_found_anywhere_returns_none_genre(self, monkeypatch):
        monkeypatch.setattr(detect_genre, "lookup_track", lambda q: None)
        monkeypatch.setattr(detect_genre, "_musicbrainz_genre_lookup", lambda a, t: None)
        monkeypatch.setattr(detect_genre, "_theaudiodb_genre_lookup", lambda a, t: None)
        monkeypatch.setattr(detect_genre, "_lastfm_genre_lookup", lambda a, t: None)

        assert detect_genre.detect_genre("A", "B") == {"genre": None, "artwork_url": None}
