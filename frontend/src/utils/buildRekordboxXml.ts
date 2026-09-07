export interface RekordboxTrack {
  name: string
  artist: string | null
  title: string | null
  genre: string | null
  bpm: number | null
  tonality: string | null
  duration: number | null
  fileSizeBytes: number
}

const KIND_BY_EXTENSION: Record<string, string> = {
  mp3: "MP3 File",
  wav: "WAV File",
  flac: "FLAC File",
  aiff: "AIFF File",
  aif: "AIFF File",
  ogg: "Ogg Vorbis File",
  aac: "AAC File",
}

// Rekordbox's own required entity set for attribute values -- order matters,
// "&" must go first or it'll double-escape the entities produced below.
function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;")
}

function attr(name: string, value: string | number | null | undefined): string {
  if (value === null || value === undefined) return ""
  return ` ${name}="${escapeXml(String(value))}"`
}

function fileStem(name: string): string {
  return name.replace(/\.[^/.]+$/, "")
}

function extensionOf(name: string): string {
  const match = /\.([^/.]+)$/.exec(name)
  return match ? match[1].toLowerCase() : ""
}

/** Client-side Rekordbox library XML (the format Rekordbox itself calls
 * "rekordbox.xml" / an iTunes-style library export, extended by Pioneer).
 * Built entirely in the browser, from the current (possibly reordered)
 * results, the same way buildPlaylist.ts regenerates the .m3u8 -- no
 * backend round-trip needed at download time.
 *
 * Known limitation: Rekordbox's Location must be a file:// path, but we
 * can never know where the user will unzip the export. We write a
 * plausible placeholder; Rekordbox's own "Relocate" import feature matches
 * broken tracks by filename against a folder you point it at once, which
 * is the standard way tools in this space handle it. */
export function buildRekordboxXml(tracks: RekordboxTrack[]): string {
  const collectionEntries: string[] = []
  const playlistEntries: string[] = []

  tracks.forEach((track, i) => {
    const trackId = i + 1
    const ext = extensionOf(track.name)
    const name = track.title ?? fileStem(track.name)
    const artist = track.artist ?? ""
    const location = `file://localhost/CratePrep Export/${encodeURIComponent(track.name)}`
    const averageBpm = track.bpm !== null ? track.bpm.toFixed(2) : undefined
    const totalTime = track.duration !== null ? Math.round(track.duration) : 0

    collectionEntries.push(
      `    <TRACK TrackID="${trackId}"` +
        attr("Name", name) +
        attr("Artist", artist) +
        attr("Genre", track.genre) +
        attr("Kind", KIND_BY_EXTENSION[ext] ?? "Unknown File") +
        attr("Size", track.fileSizeBytes) +
        `${attr("TotalTime", totalTime)}` +
        attr("AverageBpm", averageBpm) +
        attr("Tonality", track.tonality) +
        attr("Location", location) +
        `/>`
    )

    playlistEntries.push(`        <TRACK Key="${trackId}"/>`)
  })

  return [
    `<?xml version="1.0" encoding="UTF-8"?>`,
    `<DJ_PLAYLISTS Version="1.0.0">`,
    `  <PRODUCT Name="CratePrep" Version="1.0" Company="CratePrep"/>`,
    `  <COLLECTION Entries="${tracks.length}">`,
    ...collectionEntries,
    `  </COLLECTION>`,
    `  <PLAYLISTS>`,
    `    <NODE Type="0" Name="ROOT" Count="1">`,
    `      <NODE Name="CratePrep" Type="1" KeyType="0" Entries="${tracks.length}">`,
    ...playlistEntries,
    `      </NODE>`,
    `    </NODE>`,
    `  </PLAYLISTS>`,
    `</DJ_PLAYLISTS>`,
    ``,
  ].join("\n")
}
