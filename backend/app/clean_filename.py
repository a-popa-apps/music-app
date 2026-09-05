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


def clean_filename(filename: str) -> str:
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        ext = "." + ext
    else:
        stem, ext = filename, ""

    stem = URL.sub(" ", stem)
    stem = TELEGRAM.sub(" ", stem)
    stem, version_tag = _extract_version_tag(stem)
    stem = JUNK_PHRASE.sub(" ", stem)
    stem = stem.replace("_", " ")
    stem = _tidy(stem)

    parts = DASH_SPLIT.split(stem, maxsplit=1)
    if len(parts) == 2 and parts[0] and parts[1]:
        artist, title = (_tidy(parts[0]), _tidy(parts[1]))
        result = f"{artist} - {title}" if artist and title else stem
    else:
        result = stem

    if not result:
        result = "track"

    if version_tag:
        result = f"{result} ({version_tag})"

    return result + ext
