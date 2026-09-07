import { describe, expect, it } from "vitest"
import { buildRekordboxXml, type RekordboxTrack } from "./buildRekordboxXml"

function track(overrides: Partial<RekordboxTrack> = {}): RekordboxTrack {
  return {
    name: "Artist - Title.mp3",
    artist: "Artist",
    title: "Title",
    genre: "Techno",
    bpm: 128,
    tonality: "Am",
    duration: 245.7,
    fileSizeBytes: 4_200_000,
    ...overrides,
  }
}

describe("buildRekordboxXml", () => {
  it("includes the DJ_PLAYLISTS/COLLECTION/PLAYLISTS structure", () => {
    const xml = buildRekordboxXml([track()])
    expect(xml).toContain("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    expect(xml).toContain("<DJ_PLAYLISTS Version=\"1.0.0\">")
    expect(xml).toContain('<COLLECTION Entries="1">')
    expect(xml).toContain("<PLAYLISTS>")
    expect(xml).toContain('<NODE Name="CratePrep" Type="1" KeyType="0" Entries="1">')
  })

  it("writes track attributes correctly", () => {
    const xml = buildRekordboxXml([track()])
    expect(xml).toContain('TrackID="1"')
    expect(xml).toContain('Name="Title"')
    expect(xml).toContain('Artist="Artist"')
    expect(xml).toContain('Genre="Techno"')
    expect(xml).toContain('Kind="MP3 File"')
    expect(xml).toContain('Size="4200000"')
    expect(xml).toContain('TotalTime="246"')
    expect(xml).toContain('AverageBpm="128.00"')
    expect(xml).toContain('Tonality="Am"')
    expect(xml).toContain(
      'Location="file://localhost/CratePrep Export/Artist%20-%20Title.mp3"'
    )
  })

  it("falls back to the filename stem when title is unresolved", () => {
    const xml = buildRekordboxXml([
      track({ name: "Bad Rip.wav", artist: null, title: null }),
    ])
    expect(xml).toContain('Name="Bad Rip"')
    expect(xml).toContain('Artist=""')
  })

  it("omits AverageBpm/Tonality when not detected, defaults TotalTime to 0", () => {
    const xml = buildRekordboxXml([track({ bpm: null, tonality: null, duration: null })])
    expect(xml).not.toContain("AverageBpm=")
    expect(xml).not.toContain("Tonality=")
    expect(xml).toContain('TotalTime="0"')
  })

  it("preserves track order in both the collection and the playlist node", () => {
    const xml = buildRekordboxXml([
      track({ name: "A.mp3", title: "A" }),
      track({ name: "B.mp3", title: "B" }),
    ])
    const trackIdA = xml.indexOf('TrackID="1"')
    const trackIdB = xml.indexOf('TrackID="2"')
    expect(trackIdA).toBeGreaterThan(-1)
    expect(trackIdB).toBeGreaterThan(trackIdA)

    const keyA = xml.indexOf('<TRACK Key="1"/>')
    const keyB = xml.indexOf('<TRACK Key="2"/>')
    expect(keyA).toBeGreaterThan(-1)
    expect(keyB).toBeGreaterThan(keyA)
  })

  it("escapes XML-special characters in artist/title", () => {
    const xml = buildRekordboxXml([
      track({ artist: 'Artists & "Friends"', title: "Rock <n> Roll" }),
    ])
    expect(xml).toContain('Artist="Artists &amp; &quot;Friends&quot;"')
    expect(xml).toContain('Name="Rock &lt;n&gt; Roll"')
  })

  it("handles an empty track list", () => {
    const xml = buildRekordboxXml([])
    expect(xml).toContain('<COLLECTION Entries="0">')
    expect(xml).toContain('Entries="0">')
  })
})
