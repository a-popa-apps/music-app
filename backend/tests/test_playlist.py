from app.playlist import build_playlist


def test_header_present():
    assert build_playlist([]).startswith("#EXTM3U\n")


def test_single_track_format():
    result = build_playlist([("Artist - Title.mp3", 245.7)])
    assert result == "#EXTM3U\n#EXTINF:245,Artist - Title\nArtist - Title.mp3\n"


def test_unknown_duration_uses_minus_one():
    result = build_playlist([("Track.mp3", None)])
    assert "#EXTINF:-1,Track\n" in result


def test_preserves_order_for_multiple_tracks():
    result = build_playlist([("A.mp3", 10.0), ("B.mp3", 20.0)])
    lines = result.strip().split("\n")
    assert lines == [
        "#EXTM3U",
        "#EXTINF:10,A",
        "A.mp3",
        "#EXTINF:20,B",
        "B.mp3",
    ]
