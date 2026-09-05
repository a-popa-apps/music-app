from __future__ import annotations

import re

JUNK_KEYWORDS = [
    "free download",
    "free dl",
    "buy on beatport",
    "buy on traxsource",
    "buy on juno",
    "buy full track",
    "out now",
    "click buy",
    "support the artist",
    "preview only",
    "preview clip",
    "snippet",
    "promo only",
    "promo copy",
    "promo use only",
    "not for sale",
    "download link in bio",
    "repost",
    "telegram",
    "leak",
    "ripped by",
    "rip by",
]

VERSION_KEYWORDS = re.compile(
    r"remix|rework|mashup|bootleg|\bflip\b|\bdub\b|\bvip\b|\bedit\b|\bmix\b|version",
    re.IGNORECASE,
)

BRACKETED = re.compile(r"[\[\(]([^\]\)]*)[\]\)]")
URL = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
TELEGRAM = re.compile(r"(@[\w.]+|t\.me/\S+)", re.IGNORECASE)
JUNK_PHRASE = re.compile(
    "|".join(re.escape(k) for k in JUNK_KEYWORDS), re.IGNORECASE
)
DASH_SPLIT = re.compile(r"\s*[-–—]\s*")
WHITESPACE_RUN = re.compile(r"\s{2,}")
EDGE_JUNK = re.compile(r"^[\s\-_.,]+|[\s\-_.,]+$")
CATALOG_CODE_AT_END = re.compile(r"\s+[A-Za-z]{2,6}\d{2,5}$")
LEADING_VINYL_CODE = re.compile(r"^[A-Da-d]{1,2}\d{1,2}[\s.\-_]+")
TEMPLATE_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def _extract_version_tag(stem: str) -> tuple[str, str | None]:
    """Remove all bracketed groups from stem; keep the first one that looks
    like a version/remix credit (e.g. "Foo Remix", "Extended Mix")."""
    version_tag = None

    def handle(match: re.Match) -> str:
        nonlocal version_tag
        content = match.group(1).strip()
        if version_tag is None and VERSION_KEYWORDS.search(content):
            version_tag = content
        return " "

    return BRACKETED.sub(handle, stem), version_tag


def _tidy(text: str) -> str:
    text = WHITESPACE_RUN.sub(" ", text)
    return EDGE_JUNK.sub("", text).strip()


def prepare_stem(filename: str) -> tuple[str, str, str | None]:
    """Strip junk (URLs, Telegram handles, vinyl position codes, promo
    phrases, catalog codes) and pull out any version/remix credit.
    Returns (tidied_stem, ext, version_tag) with no artist/title split yet."""
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        ext = "." + ext
    else:
        stem, ext = filename, ""

    stem = LEADING_VINYL_CODE.sub("", stem)
    stem = URL.sub(" ", stem)
    stem = TELEGRAM.sub(" ", stem)
    stem, version_tag = _extract_version_tag(stem)
    stem = JUNK_PHRASE.sub(" ", stem)
    stem = CATALOG_CODE_AT_END.sub("", stem)
    stem = stem.replace("_", " ")
    stem = _tidy(stem)

    return stem, ext, version_tag


def local_dash_split(stem: str) -> tuple[str, str] | None:
    """Split on an explicit dash separator, e.g. "Artist - Title"."""
    parts = DASH_SPLIT.split(stem, maxsplit=1)
    if len(parts) == 2 and parts[0] and parts[1]:
        return _tidy(parts[0]), _tidy(parts[1])
    return None


def guess_split(stem: str) -> tuple[str, str] | None:
    """Last-resort artist/title guess for a dash-less name with no external
    catalog match: assume the first word (or two, if there are enough words)
    is the artist. Unreliable for compilations/one-off titles, but better
    than leaving most real-world dash-less filenames untouched."""
    words = stem.split(" ")
    if len(words) >= 3:
        return " ".join(words[:2]), " ".join(words[2:])
    if len(words) == 2:
        return words[0], words[1]
    return None


def apply_template(
    template: str,
    *,
    artist: str,
    title: str,
    bpm: float | None,
    key: str | None,
    genre: str | None,
) -> str:
    """Substitutes {artist} {title} {bpm} {key} {genre}. A known placeholder
    whose value wasn't detected renders as an empty string; an unrecognized
    placeholder (typo) is left literally in place, matching the frontend
    preview's behavior so what the user saw is what they get."""
    values = {
        "artist": artist,
        "title": title,
        "bpm": str(round(bpm)) if bpm is not None else "",
        "key": key or "",
        "genre": genre or "",
    }

    def replace(match: re.Match) -> str:
        name = match.group(1)
        return values[name] if name in values else match.group(0)

    return TEMPLATE_PLACEHOLDER.sub(replace, template)


def compose_name(
    artist: str | None,
    title: str | None,
    fallback_stem: str,
    version_tag: str | None,
    ext: str,
    *,
    filename_template: str | None = None,
    bpm: float | None = None,
    key: str | None = None,
    genre: str | None = None,
) -> str:
    if filename_template and artist and title:
        result = apply_template(
            filename_template, artist=artist, title=title, bpm=bpm, key=key, genre=genre
        )
    elif artist and title:
        result = f"{artist} - {title}"
    else:
        result = fallback_stem or "track"

    if version_tag:
        result = f"{result} ({version_tag})"

    return result + ext


def clean_filename(filename: str) -> str:
    """Local-only cleanup with no external lookups: dash split if present,
    else a best-effort word-count guess. See process_audio.py for the
    network-lookup-assisted version used in the actual pipeline."""
    stem, ext, version_tag = prepare_stem(filename)
    split = local_dash_split(stem) or guess_split(stem)
    artist, title = split if split else (None, None)
    return compose_name(artist, title, stem, version_tag, ext)
