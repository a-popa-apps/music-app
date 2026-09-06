import { describe, expect, it } from "vitest"
import { buildPlaylist } from "./buildPlaylist"

describe("buildPlaylist", () => {
  it("includes the header even when empty", () => {
    expect(buildPlaylist([])).toBe("#EXTM3U\n")
  })

  it("formats a single track", () => {
    const result = buildPlaylist([{ name: "Artist - Title.mp3", duration: 245.7 }])
    expect(result).toBe("#EXTM3U\n#EXTINF:245,Artist - Title\nArtist - Title.mp3\n")
  })

  it("uses -1 for unknown duration", () => {
    const result = buildPlaylist([{ name: "Track.mp3", duration: null }])
    expect(result).toContain("#EXTINF:-1,Track\n")
  })

  it("preserves order for multiple tracks", () => {
    const result = buildPlaylist([
      { name: "A.mp3", duration: 10 },
      { name: "B.mp3", duration: 20 },
    ])
    expect(result.trim().split("\n")).toEqual([
      "#EXTM3U",
      "#EXTINF:10,A",
      "A.mp3",
      "#EXTINF:20,B",
      "B.mp3",
    ])
  })
})
