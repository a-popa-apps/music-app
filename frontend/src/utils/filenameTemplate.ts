export const KNOWN_PLACEHOLDERS = ["artist", "title", "bpm", "key", "genre", "duration"] as const

const SAMPLE_VALUES: Record<string, string> = {
  artist: "Daft Punk",
  title: "One More Time",
  bpm: "128",
  key: "8A",
  genre: "House",
  duration: "3:44",
}

const PLACEHOLDER_PATTERN = /\{(\w+)\}/g

export function extractPlaceholders(template: string): string[] {
  return [...template.matchAll(PLACEHOLDER_PATTERN)].map((m) => m[1])
}

export function unknownPlaceholders(template: string): string[] {
  const found = extractPlaceholders(template)
  return [...new Set(found.filter((p) => !KNOWN_PLACEHOLDERS.includes(p as never)))]
}

/** Renders a preview using sample track data. Unknown placeholders are left
 * as-is (e.g. "{artst}") so a typo is visible rather than silently dropped --
 * this matches how the real substitution will behave once wired into
 * processing, so the preview is an honest representation. */
export function previewFilename(template: string): string {
  if (!template.trim()) return "Daft Punk - One More Time (Remix).mp3"
  return (
    template.replace(PLACEHOLDER_PATTERN, (match, name) => SAMPLE_VALUES[name] ?? match) +
    ".mp3"
  )
}
