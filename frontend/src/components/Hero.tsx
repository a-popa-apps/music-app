import { unzipSync } from "fflate"
import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { useAuth } from "../hooks/useAuth"
import { uploadAndProcess } from "../services/api"

interface ManifestEntry {
  bpm?: number | null
  camelot?: string | null
  genre?: string | null
  duration_seconds?: number | null
  original_filename?: string
  error?: string
}

interface ProcessedTrack {
  name: string
  originalFilename?: string
  bpm: number | null
  key: string | null
  genre: string | null
  failed: boolean
}

type Phase = "idle" | "processing" | "done" | "error"

async function parseManifest(blob: Blob): Promise<ProcessedTrack[]> {
  const bytes = new Uint8Array(await blob.arrayBuffer())
  const files = unzipSync(bytes)
  const manifestBytes = files["quickie-manifest.json"]
  if (!manifestBytes) return []

  const manifest: Record<string, ManifestEntry> = JSON.parse(
    new TextDecoder().decode(manifestBytes)
  )

  return Object.entries(manifest).map(([name, entry]) => ({
    name,
    originalFilename: entry.original_filename,
    bpm: entry.bpm ?? null,
    key: entry.camelot ?? null,
    genre: entry.genre ?? null,
    failed: Boolean(entry.error),
  }))
}

export function Hero() {
  const { user, isVerified } = useAuth()
  const [phase, setPhase] = useState<Phase>("idle")
  const [fileCount, setFileCount] = useState(0)
  const [results, setResults] = useState<ProcessedTrack[]>([])
  const [zipBlob, setZipBlob] = useState<Blob | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    void processFiles(acceptedFiles)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: phase === "processing",
    accept: {
      "audio/*": [".mp3", ".wav", ".aiff", ".flac"],
    },
  })

  async function processFiles(files: File[]) {
    setFileCount(files.length)
    setPhase("processing")
    try {
      const idToken = user && isVerified ? await user.getIdToken() : undefined
      const blob = await uploadAndProcess(files, idToken)
      const parsed = await parseManifest(blob)
      setZipBlob(blob)
      setResults(parsed)
      setPhase("done")
    } catch {
      setPhase("error")
    }
  }

  function handleDownload() {
    if (!zipBlob) return
    const url = URL.createObjectURL(zipBlob)
    const link = document.createElement("a")
    link.href = url
    link.download = "quickie-export.zip"
    link.click()
    URL.revokeObjectURL(url)
  }

  function reset() {
    setPhase("idle")
    setFileCount(0)
    setResults([])
    setZipBlob(null)
  }

  return (
    <section id="demo" className="w-full bg-surface-container-lowest px-4 pb-16 pt-12 lg:px-12">
      <div className="mx-auto flex max-w-7xl flex-col items-center text-center">
        <div className="mb-6 inline-flex items-center gap-1 rounded-full bg-surface-container-low px-4 py-1 shadow-sm">
          <span className="h-2 w-2 animate-ping rounded-full bg-secondary-container" />
          <span className="font-mono text-meta-badge uppercase tracking-wider text-on-surface-variant">
            DJ Utility 1.0 &middot; Rekordbox Ready
          </span>
        </div>

        <h1 className="mb-4 max-w-4xl text-display-hero-mobile tracking-tighter text-on-surface lg:text-display-hero">
          Let's do it quick.
        </h1>

        <p className="mb-10 max-w-2xl text-body-lg text-on-surface-variant">
          Drop your messy download folder. Get back clean filenames, verified
          BPM and Camelot keys, genre playlists, and ready-to-gig Rekordbox
          exports in seconds.
        </p>

        <div className="w-full text-left">
          {phase === "idle" && (
            <div
              {...getRootProps()}
              className={`flex w-full cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-outline-variant bg-surface-container-low p-12 text-center shadow-sm transition-all hover:bg-surface-container ${
                isDragActive ? "border-secondary-container ring-2 ring-secondary-container" : ""
              }`}
            >
              <input {...getInputProps()} />
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-secondary-container">
                <span className="material-symbols-outlined text-[36px] text-on-secondary">
                  graphic_eq
                </span>
              </div>
              <h3 className="mb-1 text-headline-sm text-on-surface">
                Drag your track folder here
              </h3>
              <p className="mb-4 text-body-md text-on-surface-variant">
                Drop .WAV, .MP3, .AIFF, or .FLAC directly from Finder or Explorer
              </p>
              <span className="rounded-full bg-secondary-container px-4 py-1 font-mono text-meta-badge uppercase tracking-wider text-on-secondary">
                Lossless Supported
              </span>
            </div>
          )}

          {phase === "processing" && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-outline-variant bg-surface-container-low p-12 text-center shadow-sm">
              <span className="material-symbols-outlined animate-spin text-[36px] text-secondary-container">
                progress_activity
              </span>
              <h3 className="text-headline-sm text-on-surface">
                Processing {fileCount} file{fileCount === 1 ? "" : "s"}...
              </h3>
              <p className="text-body-md text-on-surface-variant">
                Detecting BPM, key, and genre for each track.
              </p>
              <div className="h-2 w-full max-w-md overflow-hidden rounded-full bg-surface-container">
                <div className="h-full w-1/3 animate-indeterminate rounded-full bg-secondary-container" />
              </div>
            </div>
          )}

          {phase === "error" && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-red-200 bg-red-50 p-12 text-center shadow-sm">
              <span className="material-symbols-outlined text-[36px] text-red-600">error</span>
              <h3 className="text-headline-sm text-red-700">Processing failed</h3>
              <p className="text-body-md text-red-700/80">
                The backend didn't respond. Check that it's awake and try again.
              </p>
              <button
                onClick={reset}
                className="rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
              >
                Try again
              </button>
            </div>
          )}

          {phase === "done" && (
            <div className="w-full overflow-hidden rounded bg-surface-container-lowest shadow-md">
              <div className="grid grid-cols-12 items-center bg-surface-container-low px-6 py-2 font-mono text-meta-badge uppercase tracking-wider text-on-surface-variant">
                <div className="col-span-1 text-center">#</div>
                <div className="col-span-4">Track Title &amp; Artist</div>
                <div className="col-span-2 text-center">BPM</div>
                <div className="col-span-2 text-center">Key</div>
                <div className="col-span-2 hidden lg:block">Genre Tag</div>
                <div className="col-span-3 text-right lg:col-span-1">Status</div>
              </div>

              {results.map((track, i) => (
                <div
                  key={track.name + i}
                  className="grid grid-cols-12 items-center border-t border-outline-variant px-6 py-4 transition-colors hover:bg-surface-container-low"
                >
                  <div className="col-span-1 text-center font-mono text-meta-numeric text-on-surface-variant">
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div className="col-span-4 flex min-w-0 flex-col pr-2">
                    <span className="truncate text-body-md font-bold text-on-surface">
                      {track.name}
                    </span>
                    {track.originalFilename && (
                      <span className="truncate text-body-sm text-on-surface-variant">
                        was: {track.originalFilename}
                      </span>
                    )}
                  </div>
                  <div className="col-span-2 text-center font-mono text-meta-numeric font-bold text-secondary-container">
                    {track.bpm !== null ? Math.round(track.bpm) : "—"}
                  </div>
                  <div className="col-span-2 text-center">
                    {track.key ? (
                      <span className="rounded bg-surface-container-low px-2 py-px font-mono text-meta-numeric text-on-surface">
                        {track.key}
                      </span>
                    ) : (
                      <span className="font-mono text-meta-numeric text-on-surface-variant">—</span>
                    )}
                  </div>
                  <div className="col-span-2 hidden items-center lg:flex">
                    {track.genre && (
                      <span className="rounded-full bg-inverse-surface px-2 py-px text-body-sm text-inverse-on-surface">
                        {track.genre}
                      </span>
                    )}
                  </div>
                  <div className="col-span-3 text-right lg:col-span-1">
                    <span
                      className={`inline-flex items-center gap-1 font-mono text-meta-badge font-bold uppercase ${
                        track.failed ? "text-red-600" : "text-secondary-container"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          track.failed ? "bg-red-600" : "bg-secondary-container"
                        }`}
                      />
                      {track.failed ? "Error" : "Done"}
                    </span>
                  </div>
                </div>
              ))}

              <div className="flex flex-col items-center justify-between gap-4 border-t border-outline-variant bg-surface-container-low p-6 sm:flex-row">
                <div className="flex items-center gap-4 font-mono text-meta-numeric text-on-surface-variant">
                  <span className="flex items-center gap-1 text-on-surface">
                    <span className="material-symbols-outlined text-[18px] text-secondary-container">
                      verified
                    </span>
                    {results.length} track{results.length === 1 ? "" : "s"} processed
                  </span>
                  <button
                    onClick={reset}
                    className="text-body-sm font-semibold text-on-surface-variant underline hover:text-on-surface"
                  >
                    Process another folder
                  </button>
                </div>
                <button
                  onClick={handleDownload}
                  className="inline-flex w-full items-center justify-center gap-1 rounded-full bg-secondary-container px-6 py-2 text-headline-sm font-semibold text-on-primary transition-all hover:opacity-90 sm:w-auto"
                >
                  <span className="material-symbols-outlined text-[18px]">folder_zip</span>
                  Download processed files
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
