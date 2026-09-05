import { describe, expect, it } from "vitest"
import { extractPlaceholders, previewFilename, unknownPlaceholders } from "./filenameTemplate"

describe("extractPlaceholders", () => {
  it("finds every placeholder in order", () => {
    expect(extractPlaceholders("{artist} - {title} [{bpm} - {key}]")).toEqual([
      "artist",
      "title",
      "bpm",
      "key",
    ])
  })

  it("returns an empty array when there are none", () => {
    expect(extractPlaceholders("Static Name")).toEqual([])
  })
})

describe("unknownPlaceholders", () => {
  it("returns nothing when all placeholders are known", () => {
    expect(unknownPlaceholders("{artist} - {title} [{bpm} - {key} - {genre}]")).toEqual([])
  })

  it("flags a typo'd placeholder", () => {
    expect(unknownPlaceholders("{artst} - {title}")).toEqual(["artst"])
  })

  it("de-duplicates a repeated unknown placeholder", () => {
    expect(unknownPlaceholders("{foo} {foo}")).toEqual(["foo"])
  })
})

describe("previewFilename", () => {
  it("falls back to the default example for a blank template", () => {
    expect(previewFilename("")).toBe("Daft Punk - One More Time (Remix).mp3")
    expect(previewFilename("   ")).toBe("Daft Punk - One More Time (Remix).mp3")
  })

  it("substitutes known placeholders with sample values", () => {
    expect(previewFilename("{artist} - {title} [{bpm} - {key}]")).toBe(
      "Daft Punk - One More Time [128 - 8A].mp3"
    )
  })

  it("leaves an unknown placeholder as-is so a typo is visible", () => {
    expect(previewFilename("{artst} - {title}")).toBe("{artst} - One More Time.mp3")
  })
})
