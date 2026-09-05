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

BRACKETED = re.compile(r"[\[\(][^\]\)]*[\]\)]")
URL = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
TELEGRAM = re.compile(r"(@[\w.]+|t\.me/\S+)", re.IGNORECASE)
JUNK_PHRASE = re.compile(
    "|".join(re.escape(k) for k in JUNK_KEYWORDS), re.IGNORECASE
)
WHITESPACE_RUN = re.compile(r"\s{2,}")
DASH_RUN = re.compile(r"-{2,}")
EDGE_SEPARATORS = re.compile(r"^[\s\-_.]+|[\s\-_.]+$")


def clean_filename(filename: str) -> str:
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        ext = "." + ext
    else:
        stem, ext = filename, ""

    def strip_bracketed_junk(match: re.Match) -> str:
        content = match.group(0)
        if JUNK_PHRASE.search(content):
            return " "
        return content

    stem = URL.sub(" ", stem)
    stem = TELEGRAM.sub(" ", stem)
    stem = BRACKETED.sub(strip_bracketed_junk, stem)
    stem = JUNK_PHRASE.sub(" ", stem)
    stem = stem.replace("_", " ")
    stem = DASH_RUN.sub("-", stem)
    stem = WHITESPACE_RUN.sub(" ", stem)
    stem = EDGE_SEPARATORS.sub("", stem).strip()

    if not stem:
        stem = "track"

    return stem + ext
