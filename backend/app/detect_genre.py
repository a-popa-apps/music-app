from __future__ import annotations

import base64
import json
import os
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


def _spotify_genre(artist: str, title: str) -> str | None:
    token = _get_spotify_token()
    if not token:
        return None

    query = urllib.parse.quote(f"artist:{artist} track:{title}")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        search = _get_json(
            f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1", headers
        )
        items = search.get("tracks", {}).get("items", [])
        if not items:
            return None

        artist_id = items[0]["artists"][0]["id"]
        artist_data = _get_json(f"https://api.spotify.com/v1/artists/{artist_id}", headers)
        genres = artist_data.get("genres", [])
        return genres[0] if genres else None
    except Exception:
        return None


def _discogs_genre(artist: str, title: str) -> str | None:
    query = urllib.parse.quote(f"{artist} {title}")
    url = f"https://api.discogs.com/database/search?q={query}&type=release&per_page=1"
    if DISCOGS_TOKEN:
        url += f"&token={DISCOGS_TOKEN}"

    try:
        result = _get_json(url, headers={"User-Agent": "QuickieApp/1.0"})
        results = result.get("results", [])
        if not results:
            return None

        styles = results[0].get("style") or []
        genres = results[0].get("genre") or []
        if styles:
            return styles[0]
        if genres:
            return genres[0]
        return None
    except Exception:
        return None


def detect_genre(artist: str | None, title: str | None) -> str | None:
    if not artist or not title:
        return None
    return _spotify_genre(artist, title) or _discogs_genre(artist, title)
