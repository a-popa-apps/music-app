import { unzipSync, zipSync, type Unzipped } from "fflate"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useDropzone, type FileRejection } from "react-dropzone"
import { useNavigate } from "react-router-dom"
import heroBg from "../assets/hero-bg.webp"
import { useAuth } from "../hooks/useAuth"
import { useProfile } from "../hooks/useProfile"
import {
  ApiError,
  createCheckoutSession,
  retagFiles,
  uploadAndProcess,
  type TrackCorrection,
} from "../services/api"
import { trackEvent } from "../utils/analytics"
import { buildPlaylist } from "../utils/buildPlaylist"
import { suggestSetOrder } from "../utils/suggestSetOrder"
import { TrackWaveform } from "./TrackWaveform"
import { UpgradeModal } from "./UpgradeModal"
import { Waveform } from "./Waveform"

interface ManifestEntry {
  bpm?: number | null
  camelot?: string | null
  genre?: string | null
  energy?: number | null
  duration_seconds?: number | null
  original_filename?: string
  artist?: string | null
  title?: string | null
  tonality?: string | null
  name_source?: string | null
  error?: string
  preview_filename?: string
}

interface ProcessedTrack {
  name: string
  originalFilename?: string
  // Set only for formats Chrome/Firefox can't decode natively (AIFF) --
  // a browser-playable WAV transcode of the same audio, zipped alongside
  // the real file. Playback/waveform use this when present; download
  // still exports the original, untouched file.
  previewFilename?: string
  bpm: number | null
  key: string | null
  genre: string | null
  energy: number | null
  duration: number | null
  artist: string | null
  title: string | null
  tonality: string | null
  nameSource: string | null
  failed: boolean
  // Stable identity based on upload position -- unlike `name`, this never
  // changes even when a correction renames the file (a new artist/title
  // composes a new filename), so playback/editing state keyed on this
  // survives both a drag-reorder and a save.
  originalIndex: number
}

// How confidently a track's artist/title (and everything built on it) was
// identified -- mirrors backend/app/process_audio.py's _resolve_artist_
// title_genre resolution order. "guess" also covers the rare case where
// nothing resolved at all (no name_source and no error).
type Quality = "verified" | "guess" | "failed"
const VERIFIED_SOURCES = new Set(["embedded_tags", "local_dash_split", "catalog_match"])

function trackQuality(track: ProcessedTrack): Quality {
  if (track.failed) return "failed"
  if (track.nameSource && VERIFIED_SOURCES.has(track.nameSource)) return "verified"
  return "guess"
}

function buildQualitySummary(tracks: ProcessedTrack[]): string | null {
  if (tracks.length === 0) return null
  let verified = 0
  let guess = 0
  let failed = 0
  for (const track of tracks) {
    const quality = trackQuality(track)
    if (quality === "verified") verified++
    else if (quality === "guess") guess++
    else failed++
  }

  const parts: string[] = []
  if (verified) parts.push(`${verified} catalog-verified`)
  if (guess) parts.push(`${guess} best-effort guess${guess === 1 ? "" : "es"}`)
  if (failed) parts.push(`${failed} couldn't be processed`)

  const needsReview = guess > 0 || failed > 0
  return `${parts.join(", ")}${needsReview ? " — worth a quick check before you gig." : "."}`
}

type Phase = "idle" | "auth-required" | "processing" | "done" | "error"

// No-signup trial: up to this many tracks can be processed anonymously,
// once, ever -- matches backend/app/anon_trial_store.py's ANON_TRIAL_LIMIT.
const ANON_TRIAL_LIMIT = 5

// Rotates during the "processing" phase so the wait shows what's actually
// happening under the hood (real pipeline steps, in roughly the order
// _analyze_and_tag runs them) instead of one static line.
const PROCESSING_STATUSES = [
  "Stripping junk from filenames…",
  "Reading the beat grid for BPM…",
  "Detecting musical key…",
  "Matching against Spotify & Discogs for genre…",
  "Scoring loudness for the Energy rating…",
  "Tagging files for your DJ software…",
]
const PROCESSING_STATUS_INTERVAL_MS = 2000

function parseBatchSummary(files: Unzipped): string | null {
  const bytes = files["crateprep-summary.json"]
  if (!bytes) return null
  try {
    const parsed = JSON.parse(new TextDecoder().decode(bytes))
    return typeof parsed.summary === "string" ? parsed.summary : null
  } catch {
    return null
  }
}

function sortByEnergy<T extends { energy: number | null }>(
  tracks: T[],
  direction: "asc" | "desc"
): T[] {
  return [...tracks].sort((a, b) => {
    if (a.energy === null && b.energy === null) return 0
    if (a.energy === null) return 1 // failed/unscored tracks always sort last
    if (b.energy === null) return -1
    return direction === "asc" ? a.energy - b.energy : b.energy - a.energy
  })
}

function parseManifest(files: Unzipped): ProcessedTrack[] {
  const manifestBytes = files["crateprep-manifest.json"]
  if (!manifestBytes) return []

  const manifest: Record<string, ManifestEntry> = JSON.parse(
    new TextDecoder().decode(manifestBytes)
  )

  return Object.entries(manifest).map(([name, entry], originalIndex) => ({
    name,
    originalFilename: entry.original_filename,
    previewFilename: entry.preview_filename,
    bpm: entry.bpm ?? null,
    key: entry.camelot ?? null,
    genre: entry.genre ?? null,
    energy: entry.energy ?? null,
    duration: entry.duration_seconds ?? null,
    artist: entry.artist ?? null,
    title: entry.title ?? null,
    tonality: entry.tonality ?? null,
    nameSource: entry.name_source ?? null,
    failed: Boolean(entry.error),
    originalIndex,
  }))
}

export function Hero() {
  const { user, isVerified } = useAuth()
  const { profile } = useProfile()
  const isPro = Boolean(user && isVerified && profile?.plan === "pro")
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>("idle")
  const [fileCount, setFileCount] = useState(0)
  const [results, setResults] = useState<ProcessedTrack[]>([])
  // Snapshot of the order right after processing -- "default state" to
  // revert to if a free user previews a reorder (drag or Suggest Set Order)
  // and dismisses the upgrade prompt without upgrading.
  const [originalResults, setOriginalResults] = useState<ProcessedTrack[]>([])
  const [zipFiles, setZipFiles] = useState<Unzipped | null>(null)
  const [aiSummary, setAiSummary] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  // Only a 402 (quota exhausted) gets the "upgrade" treatment (headline +
  // CTA button) -- a 400 (bad file, unsupported format, batch too large)
  // still shows its own specific backend message, just without implying
  // upgrading would fix it.
  const [isQuotaError, setIsQuotaError] = useState(false)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [billingLoading, setBillingLoading] = useState(false)
  const [statusIndex, setStatusIndex] = useState(0)
  // Separate from `phase === "processing"` -- a large batch of lossless
  // files can take far longer to *upload* than the server takes to
  // analyze it, and without this the UI showed "Processing..." (with the
  // analysis-step messages below) for the entire upload too, which read as
  // stuck/misleading rather than just slow.
  const [isUploading, setIsUploading] = useState(false)
  const [uploadFraction, setUploadFraction] = useState(0)
  // Files react-dropzone silently excluded from the drop (wrong
  // extension/type) -- shown so a batch quietly coming up short of what
  // was actually dropped has a visible explanation instead of none.
  const [skippedFiles, setSkippedFiles] = useState<string[]>([])

  useEffect(() => {
    // Gated on !isUploading too -- these are the analysis pipeline's own
    // steps, so cycling through them while the upload itself is still in
    // flight would claim work hasn't even started yet.
    if (phase !== "processing" || isUploading) return
    setStatusIndex(0)
    const id = setInterval(() => {
      setStatusIndex((i) => (i + 1) % PROCESSING_STATUSES.length)
    }, PROCESSING_STATUS_INTERVAL_MS)
    return () => clearInterval(id)
  }, [phase, isUploading])
  const dragIndex = useRef<number | null>(null)
  const [draggingIndex, setDraggingIndex] = useState<number | null>(null)
  const [energySort, setEnergySort] = useState<"asc" | "desc" | null>(null)
  const qualitySummary = useMemo(() => buildQualitySummary(results), [results])

  // Playback and editing are keyed by originalIndex, not name -- name
  // changes when a correction renames the file (new artist/title compose
  // a new filename), so either survives a reorder *and* a save without
  // silently pointing at the wrong track.
  const [playingTrack, setPlayingTrack] = useState<number | null>(null)
  // Whether audioRef is actively playing playingTrack right now -- kept
  // separate so pausing doesn't lose which track is loaded (needed for
  // the waveform's scrub-while-paused case and for resuming in place
  // instead of restarting from 0).
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackProgress, setPlaybackProgress] = useState(0)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioUrlRef = useRef<string | null>(null)

  // The raw uploads, kept around (not just the processed zip) so a
  // correction can be re-sent through /process/retag without asking the
  // user to re-drop their files.
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [editingTrack, setEditingTrack] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState({ artist: "", title: "", genre: "", bpm: "" })
  const [retagging, setRetagging] = useState(false)
  const [retagError, setRetagError] = useState<string | null>(null)

  function revokeAudioUrl() {
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current)
      audioUrlRef.current = null
    }
  }

  useEffect(() => revokeAudioUrl, [])

  function togglePlay(track: ProcessedTrack) {
    const audio = audioRef.current
    // Prefer the browser-playable preview transcode when one was generated
    // (formats like AIFF that Chrome/Firefox can't decode natively) -- the
    // real file (used for download) stays untouched either way.
    const bytes = zipFiles?.[track.previewFilename ?? track.name]
    if (!audio || !bytes) return

    if (playingTrack === track.originalIndex) {
      // Same track already loaded -- toggle play/pause in place rather
      // than reloading, so pausing and resuming keeps its position.
      if (isPlaying) {
        audio.pause()
        setIsPlaying(false)
      } else {
        setIsPlaying(true)
        void audio.play()
      }
      return
    }

    revokeAudioUrl()
    const url = URL.createObjectURL(new Blob([bytes]))
    audioUrlRef.current = url
    audio.src = url
    setPlaybackProgress(0)
    setPlayingTrack(track.originalIndex)
    setIsPlaying(true)
    void audio.play()
  }

  // Scrubbing the waveform: seeks within the already-loaded track in
  // place, or loads-and-seeks a track that isn't the active one yet, so
  // dragging a row that was never played still jumps straight to that point.
  function handleSeek(track: ProcessedTrack, fraction: number) {
    const audio = audioRef.current
    const bytes = zipFiles?.[track.previewFilename ?? track.name]
    if (!audio || !bytes) return

    if (playingTrack !== track.originalIndex) {
      revokeAudioUrl()
      const url = URL.createObjectURL(new Blob([bytes]))
      audioUrlRef.current = url
      audio.src = url
      setPlayingTrack(track.originalIndex)
      setIsPlaying(true)
      const seekOnceReady = () => {
        audio.currentTime = fraction * (audio.duration || 0)
        setPlaybackProgress(fraction)
        audio.removeEventListener("loadedmetadata", seekOnceReady)
      }
      audio.addEventListener("loadedmetadata", seekOnceReady)
      void audio.play()
      return
    }

    if (!audio.duration) return
    audio.currentTime = fraction * audio.duration
    setPlaybackProgress(fraction)
  }

  function handleAudioTimeUpdate() {
    const audio = audioRef.current
    if (!audio || !audio.duration) return
    setPlaybackProgress(audio.currentTime / audio.duration)
  }

  function handleAudioEnded() {
    setPlayingTrack(null)
    setIsPlaying(false)
    setPlaybackProgress(0)
  }

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      // react-dropzone would otherwise silently exclude non-matching files
      // from acceptedFiles with zero indication why -- some browsers report
      // no MIME type at all for less common extensions (.aif in
      // particular), so a batch coming up short of what was actually
      // dropped needs a visible explanation instead of none.
      setSkippedFiles(fileRejections.map((r) => r.file.name))

      if (acceptedFiles.length === 0) return
      const loggedIn = user && isVerified
      if (!loggedIn && acceptedFiles.length > ANON_TRIAL_LIMIT) {
        setFileCount(acceptedFiles.length)
        setPhase("auth-required")
        return
      }
      // Anonymous drops within the trial limit go straight to processing --
      // no signup wall for the free trial itself, only for exceeding it.
      void processFiles(acceptedFiles)
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [user, isVerified]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: phase === "processing",
    accept: {
      "audio/*": [".mp3", ".wav", ".flac", ".aiff", ".aif", ".ogg", ".aac"],
    },
  })

  async function processFiles(files: File[]) {
    setFileCount(files.length)
    setPhase("processing")
    setIsUploading(true)
    setUploadFraction(0)

    // The one event every other funnel report (activation, free->Pro
    // conversion, drop-off) actually depends on -- without this, GA has no
    // visibility into the app's core action at all, only auth/billing.
    const eventParams = {
      track_count: files.length,
      plan: profile?.plan ?? "free",
      enhanced_detection: Boolean(isPro && profile?.enhanced_detection),
      anonymous: !user,
    }
    trackEvent("process_started", eventParams)

    try {
      const idToken = user ? await user.getIdToken() : undefined
      const blob = await uploadAndProcess(files, idToken, (fraction) => {
        setUploadFraction(fraction)
        if (fraction >= 1) {
          // A short delay, not an immediate flip -- otherwise this and the
          // uploadFraction update above land in the same render and the
          // bar swaps to the "Processing" screen before ever actually
          // being seen at 100%, which read as it resetting partway rather
          // than completing.
          setTimeout(() => setIsUploading(false), 400)
        }
      })
      const bytes = new Uint8Array(await blob.arrayBuffer())
      const unzipped = unzipSync(bytes)
      let parsed = parseManifest(unzipped)
      if (isPro && profile?.auto_sort_by_energy) {
        parsed = sortByEnergy(parsed, "asc")
        setEnergySort("asc")
      }
      setUploadedFiles(files)
      setZipFiles(unzipped)
      setResults(parsed)
      setOriginalResults(parsed)
      setAiSummary(parseBatchSummary(unzipped))
      setPhase("done")
      trackEvent("process_completed", eventParams)
    } catch (err) {
      let quotaError = false
      if (err instanceof ApiError) {
        setErrorMessage(err.message)
        quotaError = err.status === 402
        setIsQuotaError(quotaError)
      } else {
        // Not an ApiError at all -- a real network failure (timeout,
        // connection refused), not a response the backend actually sent.
        // That's the one case "didn't respond" is an accurate message.
        setErrorMessage(null)
        setIsQuotaError(false)
      }
      setIsUploading(false)
      setPhase("error")
      trackEvent("process_failed", { ...eventParams, quota_error: quotaError })
    }
  }

  // Only true once the batch's order actually differs from right after
  // processing -- a drag that ends up back where it started, or a Suggest
  // Set Order click on a batch too small to reorder, doesn't count.
  function isReordered(current: ProcessedTrack[]): boolean {
    return current.some((track, i) => track.name !== originalResults[i]?.name)
  }

  function handleDownload() {
    if (!zipFiles) return
    const reordered = isReordered(results)
    // The actual "got real value" moment -- process_completed only means the
    // server finished, not that the user ever took their files.
    trackEvent("download_export", {
      track_count: results.length,
      reordered,
      plan: profile?.plan ?? "free",
      anonymous: !user,
    })
    const width = String(results.length).length
    const exportTracks = results.map((track, i) => ({
      ...track,
      exportName: reordered ? `${String(i + 1).padStart(width, "0")} - ${track.name}` : track.name,
    }))

    // crateprep-manifest.json / crateprep-summary.json are internal-only --
    // the app already read everything it needs from them (results table,
    // AI summary, reorder state) right after processing. They were never
    // meant to land in the DJ's actual crate folder alongside the tracks.
    const rebuilt: Unzipped = {}
    for (const track of exportTracks) {
      const bytes = zipFiles[track.name]
      if (bytes) rebuilt[track.exportName] = bytes
    }

    const playlist = buildPlaylist(
      exportTracks.map((t) => ({ name: t.exportName, duration: t.duration }))
    )
    rebuilt["crateprep-playlist.m3u8"] = new TextEncoder().encode(playlist)

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
    audioRef.current?.pause()
    revokeAudioUrl()
    setPlayingTrack(null)
    setIsPlaying(false)
    setPlaybackProgress(0)
    setPhase("idle")
    setFileCount(0)
    setIsUploading(false)
    setUploadFraction(0)
    setResults([])
    setOriginalResults([])
    setZipFiles(null)
    setUploadedFiles([])
    setAiSummary(null)
    setErrorMessage(null)
    setIsQuotaError(false)
    setShowUpgradeModal(false)
    setEditingTrack(null)
    setRetagError(null)
    setSkippedFiles([])
  }

  function startEdit(track: ProcessedTrack) {
    setEditingTrack(track.originalIndex)
    setRetagError(null)
    setEditDraft({
      artist: track.artist ?? "",
      title: track.title ?? "",
      genre: track.genre ?? "",
      bpm: track.bpm !== null ? String(track.bpm) : "",
    })
  }

  function cancelEdit() {
    setEditingTrack(null)
    setRetagError(null)
  }

  async function saveEdit(track: ProcessedTrack) {
    const bpm = editDraft.bpm.trim() === "" ? null : Number(editDraft.bpm)
    if (bpm !== null && !Number.isFinite(bpm)) {
      setRetagError("BPM must be a number.")
      return
    }

    const updates = {
      artist: editDraft.artist.trim() || null,
      title: editDraft.title.trim() || null,
      genre: editDraft.genre.trim() || null,
      bpm,
    }
    const values = { ...track, ...updates }
    const correction: TrackCorrection = {
      artist: values.artist,
      title: values.title,
      genre: values.genre,
      bpm: values.bpm,
      camelot: values.key,
      tonality: values.tonality,
      energy: values.energy,
      duration_seconds: values.duration,
    }

    setRetagging(true)
    setRetagError(null)
    try {
      // Only the corrected file needs to go back to the backend -- every
      // other track's already-tagged bytes are still sitting in zipFiles
      // from the original /process response, so there's no reason to
      // re-upload and re-tag the whole batch for a single typo fix.
      const file = uploadedFiles[track.originalIndex]
      const idToken = user ? await user.getIdToken() : undefined
      const blob = await retagFiles([file], [correction], idToken)
      const bytes = new Uint8Array(await blob.arrayBuffer())
      const unzipped = unzipSync(bytes)
      const [fresh] = parseManifest(unzipped)
      if (!fresh) throw new Error("Empty retag response")
      // parseManifest assigns originalIndex from position within this
      // (single-entry) response -- always 0, so it has to be overridden
      // with the real, stable index rather than trusted as-is.
      const updated: ProcessedTrack = { ...fresh, originalIndex: track.originalIndex }
      const newBytes = unzipped[updated.name]

      setZipFiles((prev) => {
        if (!prev) return prev
        const next = { ...prev }
        if (track.name !== updated.name) delete next[track.name]
        if (newBytes) next[updated.name] = newBytes
        return next
      })
      setResults((prev) => prev.map((t) => (t.originalIndex === track.originalIndex ? updated : t)))
      setOriginalResults((prev) => prev.map((t) => (t.originalIndex === track.originalIndex ? updated : t)))
      setEditingTrack(null)
    } catch {
      setRetagError("Couldn't save that correction. Try again.")
    } finally {
      setRetagging(false)
    }
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
    if (!isPro && isReordered(results)) setShowUpgradeModal(true)
  }

  const canSuggestSetOrder =
    results.filter((t) => t.bpm !== null || t.key !== null).length >= 3

  function handleSuggestSetOrder() {
    const suggested = suggestSetOrder(results)
    setResults(suggested)
    if (!isPro && isReordered(suggested)) setShowUpgradeModal(true)
  }

  function closeUpgradeModalWithoutUpgrading() {
    setShowUpgradeModal(false)
    setResults(originalResults)
    setEnergySort(null)
  }

  async function handleUpgrade() {
    if (!user) {
      navigate("/auth")
      return
    }
    setBillingLoading(true)
    try {
      const token = await user.getIdToken()
      const url = await createCheckoutSession(token, "monthly")
      window.location.href = url
    } catch {
      setBillingLoading(false)
    }
  }

  // Any reordering is a Pro feature -- same preview-then-revert gate as
  // drag and Suggest Set Order, since this reorders the same `results`
  // array they all share.
  function toggleEnergySort() {
    const next = energySort === "asc" ? "desc" : "asc"
    const sorted = sortByEnergy(results, next)
    setEnergySort(next)
    setResults(sorted)
    if (!isPro && isReordered(sorted)) setShowUpgradeModal(true)
  }

  return (
    <section
      id="demo"
      className="relative -mt-16 flex min-h-screen w-full flex-col items-center justify-center overflow-hidden bg-cover bg-center px-4 py-12 lg:px-12"
      style={{ backgroundImage: `url(${heroBg})` }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/40 to-black" />

      <audio
        ref={audioRef}
        onTimeUpdate={handleAudioTimeUpdate}
        onEnded={handleAudioEnded}
        className="hidden"
      />

      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col items-center text-center">
        <div className="mb-6 inline-flex items-center gap-1 rounded-full bg-white/10 px-4 py-1 backdrop-blur-sm">
          <span className="h-2 w-2 animate-ping rounded-full bg-secondary-container" />
          <span className="font-mono text-meta-badge uppercase tracking-wider text-white/90">
            DJ Utility 1.0 &middot; Rekordbox Ready
          </span>
        </div>

        <h1 className="mb-4 text-display-hero-mobile tracking-tighter text-white lg:whitespace-nowrap lg:text-display-hero">
          Your crate. <span className="text-secondary-container">Ready in seconds.</span>
        </h1>

        <p className="mb-10 max-w-2xl text-body-lg text-white/80">
          Drop your messy downloads. Get back clean filenames and tracks
          tagged with verified BPM and keys, ready to drop straight into
          your playlists.
        </p>

        <div className="w-full text-left">
          {skippedFiles.length > 0 && (
            <div className="mb-4 flex items-start gap-2 rounded border border-yellow-400/30 bg-yellow-400/10 p-4 text-body-sm text-white/80">
              <span className="material-symbols-outlined text-[18px] text-yellow-300" aria-hidden="true">warning</span>
              <span>
                Skipped {skippedFiles.length} file{skippedFiles.length === 1 ? "" : "s"} your browser
                didn't recognize as audio: {skippedFiles.join(", ")}
              </span>
            </div>
          )}
          {phase === "idle" && (
            <div
              {...getRootProps()}
              className={`flex w-full cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-white/30 bg-white/10 p-12 text-center backdrop-blur-md transition-all hover:bg-white/15 ${
                isDragActive ? "border-secondary-container bg-white/20 ring-2 ring-secondary-container" : ""
              }`}
            >
              <input {...getInputProps()} />
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-secondary-container">
                <span className="material-symbols-outlined text-[36px] text-on-secondary" aria-hidden="true">
                  graphic_eq
                </span>
              </div>
              <h3 className="mb-1 text-headline-sm text-white">
                Drag your track folder here
              </h3>
              <p className="mb-4 text-body-md text-white/70">
                Drop .WAV, .MP3, .AIFF, or .FLAC directly from Finder or Explorer
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2">
                <span className="rounded-full bg-secondary-container px-4 py-1 font-mono text-meta-badge uppercase tracking-wider text-on-secondary">
                  Lossless Supported
                </span>
                <span className="rounded-full bg-white/10 px-4 py-1 font-mono text-meta-badge uppercase tracking-wider text-white/70">
                  Try {ANON_TRIAL_LIMIT} Tracks Free, No Signup
                </span>
              </div>
            </div>
          )}

          {phase === "processing" && isUploading && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-white/20 bg-white/10 p-12 text-center backdrop-blur-md">
              <Waveform className="h-9" />
              <h3 className="text-headline-sm text-white">
                Uploading {fileCount} file{fileCount === 1 ? "" : "s"}…{" "}
                {Math.round(uploadFraction * 100)}%
              </h3>
              <p className="text-body-md text-white/70">
                Larger lossless batches can take a while to send before analysis even starts.
              </p>
              <div className="h-2 w-full max-w-md overflow-hidden rounded-full bg-white/20">
                <div
                  className="h-full rounded-full bg-secondary-container transition-[width] duration-300"
                  style={{ width: `${Math.max(uploadFraction * 100, 3)}%` }}
                />
              </div>
            </div>
          )}

          {phase === "processing" && !isUploading && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-white/20 bg-white/10 p-12 text-center backdrop-blur-md">
              <Waveform className="h-9" />
              <h3 className="text-headline-sm text-white">
                Processing {fileCount} file{fileCount === 1 ? "" : "s"}…
              </h3>
              <p className="text-body-md text-white/70">
                {PROCESSING_STATUSES[statusIndex]}
              </p>
              <div className="h-2 w-full max-w-md overflow-hidden rounded-full bg-white/20">
                <div className="h-full w-1/3 animate-indeterminate rounded-full bg-secondary-container" />
              </div>
            </div>
          )}

          {phase === "auth-required" && (
            <div className="flex w-full flex-col items-center gap-4 rounded border-2 border-white/20 bg-white/10 p-12 text-center backdrop-blur-md">
              <span className="material-symbols-outlined text-[36px] text-secondary-container" aria-hidden="true">
                lock
              </span>
              <h3 className="text-headline-sm text-white">
                That's {fileCount} files — more than the {ANON_TRIAL_LIMIT}-track free trial
              </h3>
              <p className="text-body-md text-white/70">
                Drop {ANON_TRIAL_LIMIT} or fewer to try it with no account, or sign up free
                for 10 tracks a month, no credit card required.
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
            <div
              role="alert"
              aria-live="polite"
              className="flex w-full flex-col items-center gap-4 rounded border-2 border-red-400/30 bg-red-500/10 p-12 text-center backdrop-blur-md"
            >
              <span className="material-symbols-outlined text-[36px] text-red-300" aria-hidden="true">error</span>
              <h3 className="text-headline-sm text-white">
                {isQuotaError
                  ? user
                    ? "Monthly limit reached"
                    : "Free trial used up"
                  : errorMessage
                    ? "Couldn't process those files"
                    : "Processing failed"}
              </h3>
              <p className="text-body-md text-white/70">
                {errorMessage ??
                  "The backend didn't respond. Check that it's awake and try again."}
              </p>
              <div className="flex items-center gap-3">
                {isQuotaError && (
                  <button
                    onClick={() => navigate(user ? "/#pricing" : "/auth")}
                    className="rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
                  >
                    {user ? "Upgrade to Pro" : "Sign up free"}
                  </button>
                )}
                <button
                  onClick={reset}
                  className={
                    isQuotaError
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
              {!user && (
                <div className="flex flex-col items-center justify-between gap-3 border-b border-white/10 bg-secondary-container/15 px-6 py-4 text-center sm:flex-row sm:text-left">
                  <div className="flex flex-col">
                    <span className="text-body-md font-semibold text-white">
                      Like what you see? That was your free trial.
                    </span>
                    <span className="text-body-sm text-white/70">
                      Sign up free for 10 tracks a month, saved history, and drag-to-reorder.
                    </span>
                  </div>
                  <button
                    onClick={() => navigate("/auth")}
                    className="whitespace-nowrap rounded-full bg-secondary-container px-5 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
                  >
                    Sign up free
                  </button>
                </div>
              )}
              {aiSummary && (
                <div className="flex items-center gap-2 border-b border-white/10 px-6 py-3 text-body-sm text-white/70">
                  <span className="material-symbols-outlined text-[18px] text-secondary-container" aria-hidden="true">
                    auto_awesome
                  </span>
                  {aiSummary}
                </div>
              )}
              {qualitySummary && (
                <div className="flex items-center gap-2 border-b border-white/10 px-6 py-3 text-body-sm text-white/70">
                  <span className="material-symbols-outlined text-[18px] text-secondary-container" aria-hidden="true">
                    fact_check
                  </span>
                  {qualitySummary}
                </div>
              )}
              <div className="grid grid-cols-12 items-center bg-white/5 px-6 py-2 font-mono text-meta-badge uppercase tracking-wider text-white/70">
                <div className="col-span-1 text-center">#</div>
                <div className="col-span-5 lg:col-span-6">Track Title &amp; Artist</div>
                <div className="col-span-1 text-center">BPM</div>
                <div className="col-span-1 text-center">Key</div>
                <div className="col-span-1 text-center">
                  <button
                    onClick={toggleEnergySort}
                    aria-label={
                      !isPro
                        ? "Energy (Pro feature)"
                        : energySort
                          ? `Energy, sorted ${energySort === "asc" ? "ascending" : "descending"}`
                          : "Energy"
                    }
                    className="flex w-full items-center justify-center gap-0.5 hover:text-white"
                  >
                    Energy
                    {!isPro && (
                      <span className="material-symbols-outlined text-[13px] text-secondary-container" aria-hidden="true">
                        lock
                      </span>
                    )}
                    {energySort && (
                      <span className="material-symbols-outlined text-[14px]" aria-hidden="true">
                        {energySort === "asc" ? "arrow_upward" : "arrow_downward"}
                      </span>
                    )}
                  </button>
                </div>
                <div className="col-span-1 hidden text-center lg:block">Genre Tag</div>
                <div className="col-span-3 text-center lg:col-span-1">Status</div>
              </div>

              {results.map((track, i) => (
                <div key={track.originalIndex}>
                <div
                  draggable
                  onDragStart={() => handleRowDragStart(i)}
                  onDragOver={(e) => handleRowDragOver(e, i)}
                  onDragEnd={handleRowDragEnd}
                  className={`grid grid-cols-12 items-center border-t border-white/10 px-6 py-2.5 transition-colors hover:bg-white/5 ${
                    draggingIndex === i ? "opacity-40" : ""
                  }`}
                >
                  <div className="col-span-1 flex items-center justify-center gap-1 text-center font-mono text-meta-numeric text-white/60">
                    <span className="material-symbols-outlined cursor-grab text-[16px] text-white/40" aria-hidden="true">
                      drag_indicator
                    </span>
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div className="col-span-5 flex min-w-0 items-center gap-2 pr-2 lg:col-span-6">
                    {!track.failed && zipFiles?.[track.name] && (
                      <button
                        onClick={() => togglePlay(track)}
                        aria-label={playingTrack === track.originalIndex && isPlaying ? "Pause" : "Play"}
                        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/10 text-white transition-colors hover:bg-white/20"
                      >
                        <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
                          {playingTrack === track.originalIndex && isPlaying ? "pause" : "play_arrow"}
                        </span>
                      </button>
                    )}
                    <div className="flex min-w-0 flex-1 flex-col gap-1">
                      <span className="break-words text-body-md font-bold text-white">
                        {track.name}
                      </span>
                      {track.originalFilename && (
                        <span className="break-words text-body-sm text-white/50">
                          was: {track.originalFilename}
                        </span>
                      )}
                      {!track.failed && zipFiles?.[track.name] && (
                        <TrackWaveform
                          bytes={zipFiles[track.previewFilename ?? track.name]}
                          progress={playingTrack === track.originalIndex ? playbackProgress : 0}
                          onSeek={(fraction) => handleSeek(track, fraction)}
                          className="h-4"
                        />
                      )}
                    </div>
                  </div>
                  <div className="col-span-1 text-center font-mono text-meta-numeric font-bold text-secondary-container">
                    {track.bpm !== null ? Math.round(track.bpm) : "—"}
                  </div>
                  <div className="col-span-1 text-center">
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
                  <div className="col-span-1 hidden min-w-0 items-center justify-center lg:flex">
                    {track.genre && (
                      <span
                        title={track.genre}
                        className="max-w-full truncate rounded-full bg-white/15 px-2 py-px text-body-sm text-white"
                      >
                        {track.genre}
                      </span>
                    )}
                  </div>
                  <div className="col-span-3 flex items-center justify-center gap-2 lg:col-span-1">
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
                    {!track.failed && (
                      <button
                        onClick={() =>
                          editingTrack === track.originalIndex ? cancelEdit() : startEdit(track)
                        }
                        aria-label="Correct this track's tags"
                        className="flex h-6 w-6 items-center justify-center rounded-full text-white/50 transition-colors hover:bg-white/10 hover:text-white"
                      >
                        <span className="material-symbols-outlined text-[15px]" aria-hidden="true">edit</span>
                      </button>
                    )}
                  </div>
                </div>

                {editingTrack === track.originalIndex && (
                  <div className="border-t border-white/10 bg-white/5 px-6 py-4">
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      <label className="flex flex-col gap-1">
                        <span className="text-body-sm text-white/60">Artist</span>
                        <input
                          name="edit-artist"
                          autoComplete="off"
                          value={editDraft.artist}
                          onChange={(e) => setEditDraft((d) => ({ ...d, artist: e.target.value }))}
                          className="rounded border border-white/20 bg-black/30 px-3 py-1.5 text-body-sm text-white outline-none focus-visible:border-secondary-container"
                        />
                      </label>
                      <label className="flex flex-col gap-1">
                        <span className="text-body-sm text-white/60">Title</span>
                        <input
                          name="edit-title"
                          autoComplete="off"
                          value={editDraft.title}
                          onChange={(e) => setEditDraft((d) => ({ ...d, title: e.target.value }))}
                          className="rounded border border-white/20 bg-black/30 px-3 py-1.5 text-body-sm text-white outline-none focus-visible:border-secondary-container"
                        />
                      </label>
                      <label className="flex flex-col gap-1">
                        <span className="text-body-sm text-white/60">Genre</span>
                        <input
                          name="edit-genre"
                          autoComplete="off"
                          value={editDraft.genre}
                          onChange={(e) => setEditDraft((d) => ({ ...d, genre: e.target.value }))}
                          className="rounded border border-white/20 bg-black/30 px-3 py-1.5 text-body-sm text-white outline-none focus-visible:border-secondary-container"
                        />
                      </label>
                      <label className="flex flex-col gap-1">
                        <span className="text-body-sm text-white/60">BPM</span>
                        <input
                          type="number"
                          name="edit-bpm"
                          autoComplete="off"
                          inputMode="decimal"
                          value={editDraft.bpm}
                          onChange={(e) => setEditDraft((d) => ({ ...d, bpm: e.target.value }))}
                          className="rounded border border-white/20 bg-black/30 px-3 py-1.5 text-body-sm text-white outline-none focus-visible:border-secondary-container"
                        />
                      </label>
                    </div>
                    <div aria-live="polite">
                      {retagError && <p className="mt-2 text-body-sm text-red-400">{retagError}</p>}
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <button
                        onClick={() => saveEdit(track)}
                        disabled={retagging}
                        className="rounded-full bg-secondary-container px-4 py-1.5 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {retagging ? "Saving…" : "Save"}
                      </button>
                      <button
                        onClick={cancelEdit}
                        disabled={retagging}
                        className="text-body-sm font-semibold text-white/70 underline hover:text-white disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
                </div>
              ))}

              <div className="flex flex-col items-center justify-between gap-4 border-t border-white/10 bg-white/5 p-6 sm:flex-row">
                <div className="flex items-center gap-4 font-mono text-meta-numeric text-white/70">
                  <span className="flex items-center gap-1 text-white">
                    <span className="material-symbols-outlined text-[18px] text-secondary-container" aria-hidden="true">
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
                <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
                  <button
                    onClick={handleSuggestSetOrder}
                    disabled={!canSuggestSetOrder}
                    className="inline-flex items-center justify-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-5 py-2 text-body-sm font-semibold text-white transition-colors hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <span className="material-symbols-outlined text-[18px] text-secondary-container" aria-hidden="true">
                      shuffle
                    </span>
                    Suggest Set Order
                    {!isPro && (
                      <span className="rounded-full bg-secondary-container/20 px-2 py-px font-mono text-[10px] font-bold uppercase tracking-wider text-secondary-container">
                        Pro
                      </span>
                    )}
                  </button>
                  <button
                    onClick={handleDownload}
                    className="inline-flex w-full items-center justify-center gap-1 rounded-full bg-secondary-container px-6 py-2 text-headline-sm font-semibold text-on-primary transition-all hover:opacity-90 sm:w-auto"
                  >
                    <span className="material-symbols-outlined text-[18px]" aria-hidden="true">folder_zip</span>
                    Download processed files
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {showUpgradeModal && (
          <UpgradeModal
            title="Custom Track Ordering is a Pro feature"
            description="Upgrade to Pro to reorder your tracks -- drag to rearrange, sort by energy, or auto-order by harmonic key and BPM compatibility -- and keep it when you export."
            loading={billingLoading}
            onUpgrade={handleUpgrade}
            onClose={closeUpgradeModalWithoutUpgrading}
          />
        )}
      </div>
    </section>
  )
}
