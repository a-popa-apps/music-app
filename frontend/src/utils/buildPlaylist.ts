export interface PlaylistTrack {
  name: string
  duration: number | null
}

/** Client-side port of backend/app/playlist.py's build_playlist -- same
 * #EXTM3U/#EXTINF format, same -1 "unknown duration" convention, same
 * unconditional inclusion of every track regardless of failed status.
 * Exists so drag-reordering the results table can regenerate the playlist
 * entry at download time without a server round-trip. */
export function buildPlaylist(tracks: PlaylistTrack[]): string {
  const lines = ["#EXTM3U"]
  for (const { name, duration } of tracks) {
    const durationSeconds = duration !== null ? Math.trunc(duration) : -1
    const title = name.replace(/\.[^/.]+$/, "")
    lines.push(`#EXTINF:${durationSeconds},${title}`)
    lines.push(name)
  }
  return lines.join("\n") + "\n"
}
