import { unzipSync, zipSync, type Unzipped } from "fflate"
import { useCallback, useRef, useState } from "react"
import { useDropzone } from "react-dropzone"
import { useNavigate } from "react-router-dom"
import heroBg from "../assets/hero-bg.jpg"
import { useAuth } from "../hooks/useAuth"
import { ApiError, uploadAndProcess } from "../services/api"
import { buildPlaylist } from "../utils/buildPlaylist"

interface ManifestEntry {
  bpm?: number | null
  camelot?: string | null
  genre?: string | null
  energy?: number | null
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
  energy: number | null
  duration: number | null
  failed: boolean
}

type Phase = "idle" | "auth-required" | "processing" | "done" | "error"

function parseManifest(files: Unzipped): ProcessedTrack[] {
  const manifestBytes = files["crateprep-manifest.json"]
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
    energy: entry.energy ?? null,
    duration: entry.duration_seconds ?? null,
    failed: Boolean(entry.error),
  }))
}

export function Hero() {
  const { user, isVerified } = useAuth()
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>("idle")
  const [fileCount, setFileCount] = useState(0)
  const [results, setResults] = useState<ProcessedTrack[]>([])
  const [zipFiles, setZipFiles] = useState<Unzipped | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const dragIndex = useRef<number | null>(null)
  const [draggingIndex, setDraggingIndex] = useState<number | null>(null)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return
      if (!user || !isVerified) {
        setFileCount(acceptedFiles.length)
        setPhase("auth-required")
        return
      }
      void processFiles(acceptedFiles)
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [user, isVerified]
  )

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
      const idToken = await user!.getIdToken()
      const blob = await uploadAndProcess(files, idToken)
      const bytes = new Uint8Array(await blob.arrayBuffer())
      const unzipped = unzipSync(bytes)
      const parsed = parseManifest(unzipped)
      setZipFiles(unzipped)
      setResults(parsed)
      setPhase("done")
    } catch (err) {
      if (err instanceof ApiError && err.status === 402) {
        setErrorMessage(err.message)
      } else {
        setErrorMessage(null)
      }
      setPhase("error")
    }
  }

  function handleDownload() {
    if (!zipFiles) return
    const playlist = buildPlaylist(
      results.map((track) => ({ name: track.name, duration: track.duration }))
    )
    const rebuilt: Unzipped = {
      ...zipFiles,
      "crateprep-playlist.m3u8": new TextEncoder().encode(playlist),
    }
    const zipped = zipSync(rebuilt, { level: 0 })
    const blob = new Blob([zipped], { type: "application/zip" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "crateprep-export.zip"
    link.click()
    URL.revokeObjectURL(url)
  }

  function reset() {
    setPhase("idle")
    setFileCount(0)
    setResults([])
    setZipFiles(null)
    setErrorMessage(null)
  }

  function handleRowDragStart(index: number) {
    dragIndex.current = index
    setDraggingIndex(index)
  }

  function handleRowDragOver(e: React.DragEvent, index: number) {
    e.preventDefault()
    if (dragIndex.current === null || dragIndex.current === index) return
    const from = dragIndex.current
    setResults((prev) => {
      const next = [...prev]
      const [moved] = next.splice(from, 1)
      next.splice(index, 0, moved)
      return next
    })
    dragIndex.current = index
  }

  function handleRowDragEnd() {
    dragIndex.current = null
    setDraggingIndex(null)
  }

  return (
    <section
      id="demo"
      className="relative -mt-16 flex min-h-screen w-full flex-col items-center justify-center overflow-hidden bg-cover bg-center px-4 py-12 lg:px-12"
      style={{ backgroundImage: `url(${heroBg})` }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/40 to-black" />

      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col items-center text-center">
        <div className="mb-6 inline-flex items-center gap-1 rounded-full bg-white/10 px-4 py-1 backdrop-blur-sm">
          <span className="h-2 w-2 animate-ping rounded-full bg-secondary-container" />
          <span className="font-mono text-meta-badge uppercase tracking-wider text-white/90">
            DJ Utility 1.0 &middot; Rekordbox Ready
          </span>
        </div>

        <h1 className="mb-4 max-w-4xl text-display-hero-mobile tracking-tighter text-white lg:text-display-hero">
          Your crate. Ready in seconds.
        </h1>

        <p className="mb-10 max-w-2xl text-body-lg text-white/80">
          Drop your messy download folder. Get back clean filenames, verified
          BPM and Camelot keys, genre playlists, and ready-to-gig Rekordbox
          exports in seconds.
        </p>

        <div className="w-full text-left">
          {phase === "idle" && (
            <div
              {...getRootProps()}
              className={`flex w-full cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-white/30 bg-white/10 p-12 text-center backdrop-blur-md transition-all hover:bg-white/15 ${
                isDragActive ? "border-secondary-container bg-white/20 ring-2 ring-secondary-container" : ""
              }`}
            >
              <input {...getInputProps()} />
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-secondary-container">
                <span className="material-symbols-outlined text-[36px] text-on-secondary">
                  graphic_eq
                </span>
              </div>
              <h3 className="mb-1 text-headline-sm text-white">
                Drag your track folder here
              </h3>
              <p className="mb-4 text-body-md text-white/70">
                Drop .WAV, .MP3, .AIFF, or .FLAC directly from Finder or Explorer
              </p>
              <span className="rounded-full bg-secondary-container px-4 py-1 font-mono text-meta-badge uppercase tracking-wider text-on-secondary">
                Lossless Supported
              </span>
            </div>
          )}

          {phase === "processing" && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-white/20 bg-white/10 p-12 text-center backdrop-blur-md">
              <span className="material-symbols-outlined animate-spin text-[36px] text-secondary-container">
                progress_activity
              </span>
              <h3 className="text-headline-sm text-white">
                Processing {fileCount} file{fileCount === 1 ? "" : "s"}...
              </h3>
              <p className="text-body-md text-white/70">
                Detecting BPM, key, and genre for each track.
              </p>
              <div className="h-2 w-full max-w-md overflow-hidden rounded-full bg-white/20">
                <div className="h-full w-1/3 animate-indeterminate rounded-full bg-secondary-container" />
              </div>
            </div>
          )}

          {phase === "auth-required" && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-white/20 bg-white/10 p-12 text-center backdrop-blur-md">
              <span className="material-symbols-outlined text-[36px] text-secondary-container">
                lock
              </span>
              <h3 className="text-headline-sm text-white">
                Sign in to process {fileCount} file{fileCount === 1 ? "" : "s"}
              </h3>
              <p className="text-body-md text-white/70">
                Creating a free account takes a few seconds and unlocks 25 tracks
                a month, no credit card required.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => navigate("/auth")}
                  className="rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
                >
                  Sign in / Sign up
                </button>
                <button
                  onClick={reset}
                  className="text-body-sm font-semibold text-white/70 underline hover:text-white"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {phase === "error" && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-red-400/30 bg-red-500/10 p-12 text-center backdrop-blur-md">
              <span className="material-symbols-outlined text-[36px] text-red-300">error</span>
              <h3 className="text-headline-sm text-white">
                {errorMessage ? "Monthly limit reached" : "Processing failed"}
              </h3>
              <p className="text-body-md text-white/70">
                {errorMessage ??
                  "The backend didn't respond. Check that it's awake and try again."}
              </p>
              <div className="flex items-center gap-3">
                {errorMessage && (
                  <button
                    onClick={() => navigate("/#pricing")}
                    className="rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
                  >
                    Upgrade to Pro
                  </button>
                )}
                <button
                  onClick={reset}
                  className={
                    errorMessage
                      ? "text-body-sm font-semibold text-white/70 underline hover:text-white"
                      : "rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
                  }
                >
                  Try again
                </button>
              </div>
            </div>
          )}

          {phase === "done" && (
            <div className="w-full overflow-hidden rounded border border-white/20 bg-white/10 backdrop-blur-md">
              <div className="grid grid-cols-12 items-center bg-white/5 px-6 py-2 font-mono text-meta-badge uppercase tracking-wider text-white/70">
                <div className="col-span-1 text-center">#</div>
                <div className="col-span-3">Track Title &amp; Artist</div>
                <div className="col-span-1 text-center">BPM</div>
                <div className="col-span-2 text-center">Key</div>
                <div className="col-span-1 text-center">Energy</div>
                <div className="col-span-2 hidden lg:block">Genre Tag</div>
                <div className="col-span-3 text-right lg:col-span-2">Status</div>
              </div>

              {results.map((track, i) => (
                <div
                  key={track.name + i}
                  draggable
                  onDragStart={() => handleRowDragStart(i)}
                  onDragOver={(e) => handleRowDragOver(e, i)}
                  onDragEnd={handleRowDragEnd}
                  className={`grid grid-cols-12 items-center border-t border-white/10 px-6 py-4 transition-colors hover:bg-white/5 ${
                    draggingIndex === i ? "opacity-40" : ""
                  }`}
                >
                  <div className="col-span-1 flex items-center justify-center gap-1 text-center font-mono text-meta-numeric text-white/60">
                    <span className="material-symbols-outlined cursor-grab text-[16px] text-white/40">
                      drag_indicator
                    </span>
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div className="col-span-3 flex min-w-0 flex-col pr-2">
                    <span className="truncate text-body-md font-bold text-white">
                      {track.name}
                    </span>
                    {track.originalFilename && (
                      <span className="truncate text-body-sm text-white/50">
                        was: {track.originalFilename}
                      </span>
                    )}
                  </div>
                  <div className="col-span-1 text-center font-mono text-meta-numeric font-bold text-secondary-container">
                    {track.bpm !== null ? Math.round(track.bpm) : "—"}
                  </div>
                  <div className="col-span-2 text-center">
                    {track.key ? (
                      <span className="rounded bg-white/10 px-2 py-px font-mono text-meta-numeric text-white">
                        {track.key}
                      </span>
                    ) : (
                      <span className="font-mono text-meta-numeric text-white/50">—</span>
                    )}
                  </div>
                  <div className="col-span-1 text-center font-mono text-meta-numeric font-bold text-secondary-container">
                    {track.energy !== null ? track.energy : "—"}
                  </div>
                  <div className="col-span-2 hidden items-center lg:flex">
                    {track.genre && (
                      <span className="rounded-full bg-white/15 px-2 py-px text-body-sm text-white">
                        {track.genre}
                      </span>
                    )}
                  </div>
                  <div className="col-span-3 text-right lg:col-span-2">
                    <span
                      className={`inline-flex items-center gap-1 font-mono text-meta-badge font-bold uppercase ${
                        track.failed ? "text-red-300" : "text-secondary-container"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          track.failed ? "bg-red-300" : "bg-secondary-container"
                        }`}
                      />
                      {track.failed ? "Error" : "Done"}
                    </span>
                  </div>
                </div>
              ))}

              <div className="flex flex-col items-center justify-between gap-4 border-t border-white/10 bg-white/5 p-6 sm:flex-row">
                <div className="flex items-center gap-4 font-mono text-meta-numeric text-white/70">
                  <span className="flex items-center gap-1 text-white">
                    <span className="material-symbols-outlined text-[18px] text-secondary-container">
                      verified
                    </span>
                    {results.length} track{results.length === 1 ? "" : "s"} processed
                  </span>
                  <button
                    onClick={reset}
                    className="text-body-sm font-semibold text-white/70 underline hover:text-white"
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
