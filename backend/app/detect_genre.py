from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.parse
import urllib.request

from .analysis_cache import get_genre_lookup, store_genre_lookup

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN")  # optional, raises the rate limit
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY")  # required -- no-ops if unset

# Shared public test key, same one TheAudioDB's own docs use for the free
# tier -- there's no per-app registration for the free API.
THEAUDIODB_API_KEY = os.environ.get("THEAUDIODB_API_KEY", "123")

_spotify_token_cache = {"token": None, "expires_at": 0.0}

# Cover art is typically 100KB-2MB even at 1000x1000 -- this is a sanity
# ceiling against a misbehaving/unexpected response, not a real limit.
MAX_ARTWORK_BYTES = 8 * 1024 * 1024


def _get_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, data: bytes, headers: dict) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_artwork(url: str | None) -> tuple[bytes, str] | None:
    """Downloads a catalog-supplied cover art URL, returning (bytes, mime)
    or None on any failure -- artwork is a nice-to-have, never worth
    failing a whole track's processing over."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CratePrepApp/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get_content_type() or "image/jpeg"
            if not content_type.startswith("image/"):
                return None
            data = resp.read(MAX_ARTWORK_BYTES + 1)
            if len(data) > MAX_ARTWORK_BYTES:
                return None
            return data, content_type
    except Exception:
        return None


def _get_spotify_token() -> str | None:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None

    if _spotify_token_cache["token"] and time.time() < _spotify_token_cache["expires_at"]:
        return _spotify_token_cache["token"]

    credentials = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    try:
        result = _post_json(
            "https://accounts.spotify.com/api/token",
            data=b"grant_type=client_credentials",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    except Exception:
        return None

    token = result.get("access_token")
    if token:
        _spotify_token_cache["token"] = token
        _spotify_token_cache["expires_at"] = time.time() + result.get("expires_in", 3600) - 30
    return token


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _is_plausible_match(query: str, artist: str, title: str) -> bool:
    """Catalog search engines rank loosely -- a query like "Bicep Glue" can
    return Bicep's self-titled album ahead of the actual "Glue" release, and
    a generic query like "Good Track" can match a totally unrelated release
    that merely contains both words somewhere in its own title. Jaccard
    similarity (vs. one-directional overlap) also penalizes a result
    stuffed with unrelated extra words."""
    query_words = _words(query)
    if len(query_words) < 2:
        return False  # too generic a query to trust any match

    result_words = _words(f"{artist} {title}")
    if not result_words:
        return False

    overlap = query_words & result_words
    union = query_words | result_words
    return len(overlap) / len(union) >= 0.6


def _spotify_track_lookup(query: str) -> dict | None:
    token = _get_spotify_token()
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    try:
        search = _get_json(
            f"https://api.spotify.com/v1/search?q={urllib.parse.quote(query)}&type=track&limit=5",
            headers,
        )
        for item in search.get("tracks", {}).get("items", []):
            artist_name = item["artists"][0]["name"]
            title = item["name"]
            if not _is_plausible_match(query, artist_name, title):
                continue

            genre = None
            try:
                artist_data = _get_json(
                    f"https://api.spotify.com/v1/artists/{item['artists'][0]['id']}", headers
                )
                genres = artist_data.get("genres", [])
                genre = genres[0] if genres else None
            except Exception:
                pass

            images = (item.get("album") or {}).get("images") or []
            artwork_url = images[0]["url"] if images else None  # largest first, per Spotify's API

            return {"artist": artist_name, "title": title, "genre": genre, "artwork_url": artwork_url}
        return None
    except Exception:
        return None


def _discogs_track_lookup(query: str) -> dict | None:
    url = f"https://api.discogs.com/database/search?q={urllib.parse.quote(query)}&type=release&per_page=5"
    if DISCOGS_TOKEN:
        url += f"&token={DISCOGS_TOKEN}"

    try:
        result = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
        for entry in result.get("results", []):
            title_field = entry.get("title", "")
            parts = title_field.split(" - ", 1)
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                continue

            artist, title = parts[0].strip(), parts[1].strip()
            if not _is_plausible_match(query, artist, title):
                continue

            styles = entry.get("style") or []
            genres = entry.get("genre") or []
            genre = styles[0] if styles else (genres[0] if genres else None)
            # Discogs only returns a real cover_image (vs. an empty string)
            # for token-authenticated requests -- harmless no-op without one.
            artwork_url = entry.get("cover_image") or None
            return {"artist": artist, "title": title, "genre": genre, "artwork_url": artwork_url}
        return None
    except Exception:
        return None


def _itunes_track_lookup(query: str) -> dict | None:
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&media=music&entity=song&limit=5"
    try:
        result = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
        for entry in result.get("results", []):
            artist = entry.get("artistName")
            title = entry.get("trackName")
            if not artist or not title or not _is_plausible_match(query, artist, title):
                continue

            genre = entry.get("primaryGenreName")
            # Comes back as a 100x100 thumbnail -- iTunes serves any size at
            # the same path, so upsize it rather than embedding a postage stamp.
            artwork_url = entry.get("artworkUrl100")
            if artwork_url:
                artwork_url = artwork_url.replace("100x100bb", "600x600bb")
            return {"artist": artist, "title": title, "genre": genre, "artwork_url": artwork_url}
        return None
    except Exception:
        return None


def _deezer_track_lookup(query: str) -> dict | None:
    url = f"https://api.deezer.com/search/track?q={urllib.parse.quote(query)}&limit=5"
    try:
        result = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
        for entry in result.get("data", []):
            artist = (entry.get("artist") or {}).get("name")
            title = entry.get("title")
            if not artist or not title or not _is_plausible_match(query, artist, title):
                continue

            # Deezer's search results don't include genre on the track
            # itself -- it lives on the album, one more call away. Skipped
            # here to keep this a single request; artwork is still useful
            # on its own even without genre from this particular source.
            album = entry.get("album") or {}
            artwork_url = album.get("cover_xl") or album.get("cover_big") or album.get("cover_medium")
            return {"artist": artist, "title": title, "genre": None, "artwork_url": artwork_url}
        return None
    except Exception:
        return None


def lookup_track(query: str) -> dict | None:
    """Search a chain of catalogs for a dash-less filename, returning the
    first plausible artist/title split (genre and artwork when available)
    instead of guessing. Spotify and Discogs first (best genre data); iTunes
    and Deezer as free, keyless fallbacks -- both handle a combined,
    not-yet-split "artist title" query well. (MusicBrainz/TheAudioDB/Last.fm
    need artist and title as separate, already-known fields to search
    reliably, so they live in detect_genre's genre-only fallback chain
    instead, not here.)

    Keeps trying later sources for artwork alone once artist/title/genre are
    already resolved -- Discogs without an API token (or a release Discogs
    simply has no cover scanned for) returns no cover_image at all, and
    stopping at the first plausible match would otherwise throw away decent
    artwork iTunes or Deezer had for the same track."""
    if not query:
        return None

    match = None
    for source in (_spotify_track_lookup, _discogs_track_lookup, _itunes_track_lookup, _deezer_track_lookup):
        result = source(query)
        if result is None:
            continue
        if match is None:
            match = result
        elif not match.get("artwork_url") and result.get("artwork_url"):
            match["artwork_url"] = result["artwork_url"]
        if match.get("artwork_url"):
            break

    return match


DEEP_SEARCH_MAX_RELEASES = 10


def _titles_match(target: str, candidate: str) -> bool:
    target_words = _words(target)
    candidate_words = _words(candidate)
    if not target_words or not candidate_words:
        return False
    if target_words == candidate_words:
        return True
    overlap = target_words & candidate_words
    union = target_words | candidate_words
    return len(overlap) / len(union) >= 0.7


def _discogs_artist_id(artist: str) -> int | None:
    """Picks the closest-matching candidate, not just the first one whose
    words happen to be a subset -- "A G" is a subset-match of both the
    correct "A:G" AND the wrong "A. G. Cook", and a naive first-match would
    have returned whichever ranked higher in Discogs' own search order."""
    url = f"https://api.discogs.com/database/search?q={urllib.parse.quote(artist)}&type=artist&per_page=15"
    if DISCOGS_TOKEN:
        url += f"&token={DISCOGS_TOKEN}"

    query_words = _words(artist)
    if not query_words:
        return None

    result = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
    best_id, best_score = None, 0.0
    for entry in result.get("results", []):
        name_words = _words(entry.get("title", ""))
        if not (query_words <= name_words):
            continue
        score = len(query_words) / len(name_words)  # 1.0 = exact match, penalizes extra words
        if score > best_score:
            best_id, best_score = entry.get("id"), score

    return best_id if best_score >= 0.5 else None


def _discogs_artist_release_ids(artist_id: int, limit: int) -> list[int]:
    url = (
        f"https://api.discogs.com/artists/{artist_id}/releases"
        f"?sort=year&sort_order=desc&per_page={limit}"
    )
    if DISCOGS_TOKEN:
        url += f"&token={DISCOGS_TOKEN}"

    result = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
    return [
        r["id"]
        for r in result.get("releases", [])
        if r.get("type") == "release"  # skip "master" entries -- would need an
        # extra lookup to resolve to a concrete release, not worth it here
    ][:limit]


def _discogs_release_track_match(release_id: int, title: str) -> dict | None:
    url = f"https://api.discogs.com/releases/{release_id}"
    if DISCOGS_TOKEN:
        url += f"?token={DISCOGS_TOKEN}"

    release = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
    for track in release.get("tracklist", []):
        track_title = track.get("title", "")
        if track_title and _titles_match(title, track_title):
            styles = release.get("styles") or []
            genres = release.get("genres") or []
            genre = styles[0] if styles else (genres[0] if genres else None)
            return {"title": track_title, "genre": genre}
    return None


def deep_discogs_lookup(artist: str, title: str) -> dict | None:
    """Slower, more thorough fallback: searches the artist's own Discogs page
    and scans their release tracklists directly, catching tracks the basic
    release-title search misses (e.g. a track named "Catharsis" on a release
    titled "Algobub" -- searching "Catharsis" alone would never surface it).
    Opt-in only, since this can be several sequential API calls per track."""
    try:
        artist_id = _discogs_artist_id(artist)
        if artist_id is None:
            return None

        for release_id in _discogs_artist_release_ids(artist_id, DEEP_SEARCH_MAX_RELEASES):
            try:
                match = _discogs_release_track_match(release_id, title)
            except Exception:
                continue
            if match:
                return {"artist": artist, "title": match["title"], "genre": match["genre"]}
        return None
    except Exception:
        return None


def _musicbrainz_genre_lookup(artist: str, title: str) -> dict | None:
    """MusicBrainz's plain-text search ranks loosely enough that a query
    like "daft punk one more time" can surface an unrelated track whose
    *title* happens to contain those words (a cover/tribute recording,
    for instance) ahead of the real one -- unlike Spotify/Discogs/iTunes/
    Deezer's search, it isn't reliable for combined artist+title queries.
    With artist and title already known and passed as separate structured
    fields, it's a solid fallback purely for genre/tag data. Genre isn't on
    the recording-search response itself -- needs a second call to fetch
    the matched recording's own genre/tag list."""
    query = f'artist:"{artist}" AND recording:"{title}"'
    try:
        search = _get_json(
            f"https://musicbrainz.org/ws/2/recording?query={urllib.parse.quote(query)}&fmt=json&limit=5",
            headers={"User-Agent": "CratePrepApp/1.0 ( https://crateprep.app )"},
        )
        for recording in search.get("recordings", []):
            credit = recording.get("artist-credit") or [{}]
            candidate_artist = credit[0].get("name", "")
            candidate_title = recording.get("title", "")
            if not _is_plausible_match(f"{artist} {title}", candidate_artist, candidate_title):
                continue

            genres = recording.get("genres") or []
            if not genres:
                detail = _get_json(
                    f"https://musicbrainz.org/ws/2/recording/{recording['id']}?inc=genres&fmt=json",
                    headers={"User-Agent": "CratePrepApp/1.0 ( https://crateprep.app )"},
                )
                genres = detail.get("genres") or []

            top_genre = max(genres, key=lambda g: g.get("count", 0))["name"] if genres else None
            return {"genre": top_genre, "artwork_url": None}
        return None
    except Exception:
        return None


def _theaudiodb_genre_lookup(artist: str, title: str) -> dict | None:
    url = (
        "https://www.theaudiodb.com/api/v1/json/"
        f"{THEAUDIODB_API_KEY}/searchtrack.php?s={urllib.parse.quote(artist)}&t={urllib.parse.quote(title)}"
    )
    try:
        result = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
        tracks = result.get("track") or []
        for entry in tracks:
            candidate_artist = entry.get("strArtist", "")
            candidate_title = entry.get("strTrack", "")
            if not _is_plausible_match(f"{artist} {title}", candidate_artist, candidate_title):
                continue
            return {
                "genre": entry.get("strGenre") or None,
                "artwork_url": entry.get("strTrackThumb") or None,
            }
        return None
    except Exception:
        return None


def _lastfm_genre_lookup(artist: str, title: str) -> dict | None:
    """No-op until LASTFM_API_KEY is set (free key, registered at
    last.fm/api/account/create) -- same optional-integration pattern as
    every other credential in this app. Tags are crowd-sourced, not a
    strict genre taxonomy, so noisier than Spotify/Discogs -- last resort,
    not tried first."""
    if not LASTFM_API_KEY:
        return None

    url = (
        "https://ws.audioscrobbler.com/2.0/?method=track.gettoptags"
        f"&artist={urllib.parse.quote(artist)}&track={urllib.parse.quote(title)}"
        f"&api_key={LASTFM_API_KEY}&format=json"
    )
    try:
        result = _get_json(url, headers={"User-Agent": "CratePrepApp/1.0"})
        tags = (result.get("toptags") or {}).get("tag") or []
        if not tags:
            return None
        # Tags are freeform ("banger", "2020s") as often as they're genres --
        # take the top one anyway, same trust level as Discogs' style field.
        return {"genre": tags[0].get("name"), "artwork_url": None}
    except Exception:
        return None


def detect_genre(artist: str | None, title: str | None, deep_search: bool = False) -> dict:
    """Genre (and artwork, when found) lookup for when artist/title are
    already known (e.g. from a local dash split). Checks a global cache
    (keyed by normalized artist+title, not the audio itself) first --
    genre and artwork don't change between an MP3 and a FLAC of the same
    official release, so this is what actually saves the network calls
    below the next time anyone uploads a different rip of a track that's
    already been looked up, not just an identical file."""
    if not artist or not title:
        return {"genre": None, "artwork_url": None}

    cached = get_genre_lookup(artist, title)
    if cached is not None:
        return cached

    result = _lookup_genre(artist, title, deep_search)
    store_genre_lookup(artist, title, result["genre"], result["artwork_url"])
    return result


def _lookup_genre(artist: str, title: str, deep_search: bool) -> dict:
    """Reuses lookup_track's plausibility-checked search first
    (Spotify/Discogs/iTunes/Deezer), then MusicBrainz/TheAudioDB/Last.fm
    (cheap, single-call fallbacks) if still no genre, then the slower
    deep_discogs_lookup last, only when deep_search is enabled and
    everything else found nothing.

    Returns {"genre": str | None, "artwork_url": str | None} -- artwork
    is kept from the first source that had it even if a later source ends
    up supplying the genre instead."""
    artwork_url = None

    match = lookup_track(f"{artist} {title}")
    if match:
        artwork_url = match.get("artwork_url")
        if match.get("genre"):
            return {"genre": match["genre"], "artwork_url": artwork_url}

    for fallback in (_musicbrainz_genre_lookup, _theaudiodb_genre_lookup, _lastfm_genre_lookup):
        result = fallback(artist, title)
        if result:
            artwork_url = artwork_url or result.get("artwork_url")
            if result.get("genre"):
                return {"genre": result["genre"], "artwork_url": artwork_url}

    if deep_search:
        deep_match = deep_discogs_lookup(artist, title)
        if deep_match:
            return {"genre": deep_match["genre"], "artwork_url": artwork_url}

    return {"genre": None, "artwork_url": artwork_url}
