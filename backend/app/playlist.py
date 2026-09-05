from __future__ import annotations


def build_playlist(tracks: list[tuple[str, float | None]]) -> str:
    """Build an extended M3U8 playlist. Duration -1 is the EXTM3U convention
    for "unknown length" (used when duration detection failed)."""
    lines = ["#EXTM3U"]
    for name, duration_seconds in tracks:
        duration = int(duration_seconds) if duration_seconds is not None else -1
        title = name.rsplit(".", 1)[0]
        lines.append(f"#EXTINF:{duration},{title}")
        lines.append(name)
    return "\n".join(lines) + "\n"
