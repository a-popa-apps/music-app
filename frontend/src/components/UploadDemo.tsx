import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { useAuth } from "../hooks/useAuth"
import { uploadAndProcess } from "../services/api"

const SAMPLE_TRACKS = [
  {
    title: "Glue (Original Mix)",
    artist: "Bicep · Ninja Tune",
    bpm: "130.00",
    key: "11B",
    genre: "Deep House",
  },
  {
    title: "Liverpool Street In The Rain",
    artist: "Mall Grab · Steel City Dance Discs",
    bpm: "126.00",
    key: "4A",
    genre: "Lo-Fi House",
  },
  {
    title: "So U Kno",
    artist: "Overmono · Poly Kicks",
    bpm: "134.00",
    key: "8A",
    genre: "UK Bass",
  },
]

type DownloadState = "idle" | "processing" | "done" | "error"

export function UploadDemo() {
  const { user, isVerified } = useAuth()
  const [droppedFiles, setDroppedFiles] = useState<File[]>([])
  const [downloadState, setDownloadState] = useState<DownloadState>("idle")

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setDroppedFiles(acceptedFiles)
    setDownloadState("idle")
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "audio/*": [".mp3", ".wav", ".aiff", ".flac"],
    },
  })

  async function handleDownload() {
    if (droppedFiles.length === 0) return
    setDownloadState("processing")
    try {
      const idToken = user && isVerified ? await user.getIdToken() : undefined
      const blob = await uploadAndProcess(droppedFiles, idToken)
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = "quickie-export.zip"
      link.click()
      URL.revokeObjectURL(url)
      setDownloadState("done")
    } catch {
      setDownloadState("error")
    }
  }

  const hasRealFiles = droppedFiles.length > 0

  return (
    <section
      id="demo"
      className="w-full bg-primary-container px-4 py-16 text-on-primary lg:px-12"
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="mb-1 flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-secondary-container" />
              <span className="font-mono text-meta-badge uppercase tracking-widest text-secondary-container">
                Standalone Deck View
              </span>
            </div>
            <h2 className="text-headline-xl tracking-tight text-on-primary">
              Interactive Clean Engine
            </h2>
          </div>
          <div className="font-mono text-meta-numeric text-on-primary-container">
            PARSER ENGINE: ACTIVE
          </div>
        </div>

        <div
          {...getRootProps()}
          className={`flex w-full cursor-pointer flex-col items-center justify-center rounded bg-tertiary-container p-12 text-center shadow-md transition-all hover:bg-inverse-surface/40 ${
            isDragActive ? "ring-2 ring-secondary-container" : ""
          }`}
        >
          <input {...getInputProps()} />
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-container">
            <span className="material-symbols-outlined text-[36px] text-secondary-container">
              graphic_eq
            </span>
          </div>
          <h3 className="mb-1 text-headline-sm text-on-primary">
            {hasRealFiles
              ? `${droppedFiles.length} file${droppedFiles.length > 1 ? "s" : ""} ready`
              : "Drag your track folder here"}
          </h3>
          <p className="mb-4 text-body-md text-on-tertiary-container">
            Drop .WAV, .MP3, .AIFF, or .FLAC directly from Finder or Explorer
          </p>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-primary-container px-4 py-1 font-mono text-meta-badge uppercase tracking-wider text-on-primary-container">
              Lossless Supported
            </span>
          </div>
        </div>

        <div className="w-full overflow-hidden rounded bg-tertiary-container shadow-lg">
          <div className="grid grid-cols-12 items-center bg-primary-container px-6 py-2 font-mono text-meta-badge uppercase tracking-wider text-on-primary-container">
            <div className="col-span-1 text-center">#</div>
            <div className="col-span-4">Track Title &amp; Artist</div>
            <div className="col-span-2 text-center">BPM</div>
            <div className="col-span-2 text-center">Key</div>
            <div className="col-span-2 hidden lg:block">Genre Tag</div>
            <div className="col-span-3 text-right lg:col-span-1">Status</div>
          </div>

          {hasRealFiles
            ? droppedFiles.map((file, i) => (
                <div
                  key={file.name + i}
                  className="grid grid-cols-12 items-center px-6 py-4 transition-colors hover:bg-inverse-surface/30"
                >
                  <div className="col-span-1 text-center font-mono text-meta-numeric text-on-tertiary-container">
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div className="col-span-4 flex min-w-0 flex-col pr-2">
                    <span className="truncate text-body-md font-bold text-on-primary">
                      {file.name}
                    </span>
                    <span className="truncate text-body-sm text-on-tertiary-container">
                      {(file.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </div>
                  <div className="col-span-2 text-center font-mono text-meta-numeric text-on-surface-variant">
                    —
                  </div>
                  <div className="col-span-2 text-center font-mono text-meta-numeric text-on-surface-variant">
                    —
                  </div>
                  <div className="col-span-2 hidden lg:flex" />
                  <div className="col-span-3 text-right lg:col-span-1">
                    <span className="inline-flex items-center gap-1 font-mono text-meta-badge font-bold uppercase text-on-surface-variant">
                      Queued
                    </span>
                  </div>
                </div>
              ))
            : SAMPLE_TRACKS.map((track, i) => (
                <div
                  key={track.title}
                  className="grid grid-cols-12 items-center px-6 py-4 transition-colors hover:bg-inverse-surface/30"
                >
                  <div className="col-span-1 text-center font-mono text-meta-numeric text-on-tertiary-container">
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div className="col-span-4 flex min-w-0 flex-col pr-2">
                    <span className="truncate text-body-md font-bold text-on-primary">
                      {track.title}
                    </span>
                    <span className="truncate text-body-sm text-on-tertiary-container">
                      {track.artist}
                    </span>
                  </div>
                  <div className="col-span-2 text-center font-mono text-meta-numeric font-bold text-secondary-container">
                    {track.bpm}
                  </div>
                  <div className="col-span-2 text-center">
                    <span className="rounded bg-primary-container px-2 py-px font-mono text-meta-numeric text-on-primary">
                      {track.key}
                    </span>
                  </div>
                  <div className="col-span-2 hidden items-center lg:flex">
                    <span className="rounded-full bg-inverse-surface px-2 py-px text-body-sm text-inverse-on-surface">
                      {track.genre}
                    </span>
                  </div>
                  <div className="col-span-3 text-right lg:col-span-1">
                    <span className="inline-flex items-center gap-1 font-mono text-meta-badge font-bold uppercase text-secondary-container">
                      <span className="h-1.5 w-1.5 rounded-full bg-secondary-container" />
                      Ready
                    </span>
                  </div>
                </div>
              ))}

          <div className="flex flex-col items-center justify-between gap-4 bg-primary-container p-6 sm:flex-row">
            <div className="flex items-center gap-4 font-mono text-meta-numeric text-on-tertiary-container">
              <span className="flex items-center gap-1 text-on-primary">
                <span className="material-symbols-outlined text-[18px] text-secondary-container">
                  verified
                </span>
                {hasRealFiles
                  ? `${droppedFiles.length} tracks queued`
                  : "3 sample tracks"}
              </span>
            </div>
            <button
              onClick={handleDownload}
              disabled={!hasRealFiles || downloadState === "processing"}
              className="inline-flex w-full items-center justify-center gap-1 rounded-full bg-secondary-container px-6 py-2 text-headline-sm font-semibold text-on-primary transition-all hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            >
              <span className="material-symbols-outlined text-[18px]">
                {downloadState === "processing"
                  ? "progress_activity"
                  : "folder_zip"}
              </span>
              {downloadState === "processing"
                ? "Processing..."
                : downloadState === "error"
                  ? "Backend not ready — retry"
                  : hasRealFiles
                    ? "Process & Download ZIP"
                    : "Drop files to process"}
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
