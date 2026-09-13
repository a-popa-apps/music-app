import { describe, expect, it } from "vitest"
import { suggestSetOrder, type MixableTrack } from "./suggestSetOrder"

function track(name: string, bpm: number | null, key: string | null, energy: number | null): MixableTrack {
  return { name, bpm, key, energy }
}

describe("suggestSetOrder", () => {
  it("leaves the batch unchanged when fewer than 3 tracks have usable data", () => {
    const tracks = [track("A", 128, "8A", 5), track("B", 126, "8A", 4)]
    expect(suggestSetOrder(tracks)).toEqual(tracks)
  })

  it("orders by lowest energy first as the opener", () => {
    const tracks = [
      track("High", 128, "8A", 9),
      track("Low", 128, "8A", 2),
      track("Mid", 128, "8A", 5),
    ]
    const result = suggestSetOrder(tracks)
    expect(result[0].name).toBe("Low")
  })

  it("prefers a harmonically compatible key over a clashing one", () => {
    const tracks = [
      track("Start", 128, "8A", 3),
      track("Clash", 128, "3B", 5), // far on the wheel, opposite letter
      track("Compatible", 128, "9A", 5), // adjacent on the wheel
    ]
    const result = suggestSetOrder(tracks)
    // Start -> Compatible should come before Start -> Clash
    expect(result.map((t) => t.name)).toEqual(["Start", "Compatible", "Clash"])
  })

  it("treats half/double-time BPM as compatible", () => {
    const tracks = [
      track("Start", 70, "8A", 3),
      track("Far", 90, "3B", 5),
      track("DoubleTime", 140, "3B", 5), // same key as Far, but BPM-compatible via 2x
    ]
    const result = suggestSetOrder(tracks)
    expect(result[0].name).toBe("Start")
    expect(result[1].name).toBe("DoubleTime")
  })

  it("doesn't penalize missing bpm/key on either side", () => {
    const tracks = [
      track("Start", 128, "8A", 3),
      track("NoData", null, null, 5),
      track("Compatible", 129, "8A", 5),
    ]
    const result = suggestSetOrder(tracks)
    expect(result.map((t) => t.name).sort()).toEqual(["Compatible", "NoData", "Start"])
  })

  it("appends tracks with no bpm and no key at the end, order preserved", () => {
    const tracks = [
      track("A", 128, "8A", 3),
      track("Failed1", null, null, null),
      track("B", 130, "9A", 5),
      track("Failed2", null, null, null),
      track("C", 132, "10A", 7),
    ]
    const result = suggestSetOrder(tracks)
    expect(result.slice(-2).map((t) => t.name)).toEqual(["Failed1", "Failed2"])
  })

  it("keeps every track exactly once", () => {
    const tracks = [
      track("A", 128, "8A", 3),
      track("B", 122, "6A", 8),
      track("C", 140, "3B", 2),
      track("D", 128, "8B", 5),
    ]
    const result = suggestSetOrder(tracks)
    expect(result.map((t) => t.name).sort()).toEqual(["A", "B", "C", "D"])
  })
})
