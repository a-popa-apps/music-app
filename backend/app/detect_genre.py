from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.parse
import urllib.request

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN")  # optional, raises the rate limit

_spotify_token_cache = {"token": None, "expires_at": 0.0}


def _get_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, data: bytes, headers: dict) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


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

            return {"artist": artist_name, "title": title, "genre": genre}
        return None
    except Exception:
        return None


def _discogs_track_lookup(query: str) -> dict | None:
    url = f"https://api.discogs.com/database/search?q={urllib.parse.quote(query)}&type=release&per_page=5"
    if DISCOGS_TOKEN:
        url += f"&token={DISCOGS_TOKEN}"

    try:
        result = _get_json(url, headers={"User-Agent": "QuickieApp/1.0"})
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
            return {"artist": artist, "title": title, "genre": genre}
        return None
    except Exception:
        return None


def lookup_track(query: str) -> dict | None:
    """Search Spotify then Discogs for a dash-less filename, returning the
    catalog's own artist/title split (and genre) instead of guessing."""
    if not query:
        return None
    return _spotify_track_lookup(query) or _discogs_track_lookup(query)


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

    result = _get_json(url, headers={"User-Agent": "QuickieApp/1.0"})
    best_id, best_score = None, 0.0
    for entry in result.get("results", []):
        name_words = _words(entry.get("title", ""))
        if not (query_words <= name_words):
            continue
        score = len(query_words) / len(name_words)  # 1.0 = exact match, penalizes extra words
        if score > best_score:
            best_id, best_score = entry.get("id"), score

    return best_id if best_score >= 0.5 else None
    return None


def _discogs_artist_release_ids(artist_id: int, limit: int) -> list[int]:
    url = (
        f"https://api.discogs.com/artists/{artist_id}/releases"
        f"?sort=year&sort_order=desc&per_page={limit}"
    )
    if DISCOGS_TOKEN:
        url += f"&token={DISCOGS_TOKEN}"

    result = _get_json(url, headers={"User-Agent": "QuickieApp/1.0"})
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

    release = _get_json(url, headers={"User-Agent": "QuickieApp/1.0"})
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


def detect_genre(artist: str | None, title: str | None, deep_search: bool = False) -> str | None:
    """Genre-only lookup for when artist/title are already known (e.g. from
    a local dash split). Reuses lookup_track's plausibility-checked search
    rather than trusting a single top result; falls back to the slower
    deep_discogs_lookup when deep_search is enabled and the basic search
    finds nothing."""
    if not artist or not title:
        return None

    match = lookup_track(f"{artist} {title}")
    if match:
        return match["genre"]

    if deep_search:
        deep_match = deep_discogs_lookup(artist, title)
        if deep_match:
            return deep_match["genre"]

    return None
