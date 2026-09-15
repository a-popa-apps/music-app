import { useEffect, useRef, useState, type PointerEvent } from "react"

const BAR_COUNT = 60

// One AudioContext shared across every row -- browsers cap how many can
// exist at once, and decodeAudioData doesn't need a dedicated context per
// call.
let sharedAudioContext: AudioContext | null = null
function getAudioContext(): AudioContext {
  if (!sharedAudioContext) sharedAudioContext = new AudioContext()
  return sharedAudioContext
}

function extractPeaks(buffer: AudioBuffer, bars: number): number[] {
  const channel = buffer.getChannelData(0)
  const samplesPerBar = Math.max(1, Math.floor(channel.length / bars))
  const peaks: number[] = []
  for (let i = 0; i < bars; i++) {
    const start = i * samplesPerBar
    const end = Math.min(start + samplesPerBar, channel.length)
    let max = 0
    for (let j = start; j < end; j++) {
      const abs = Math.abs(channel[j])
      if (abs > max) max = abs
    }
    peaks.push(max)
  }
  // Normalize so the loudest bar in this track always reaches full height
  // -- a quiet ambient track's waveform should still be readable, not a
  // flat line dwarfed by an implicit "loud track" scale.
  const loudest = Math.max(...peaks, 0.0001)
  return peaks.map((p) => p / loudest)
}

interface TrackWaveformProps {
  bytes: Uint8Array | null
  progress: number // 0-1, how far through playback
  onSeek?: (fraction: number) => void // 0-1, called while clicking/dragging the bars
  className?: string
}

// Renders a static bar-style waveform (decoded lazily the first time this
// row scrolls into view, then cached) with bars up to `progress` styled as
// "played". Playback control lives in the parent -- this component only
// draws, and reports back where a click/drag landed via `onSeek`.
export function TrackWaveform({ bytes, progress, onSeek, className = "" }: TrackWaveformProps) {
  const [peaks, setPeaks] = useState<number[] | null>(null)
  const [inView, setInView] = useState(false)
  const [seeking, setSeeking] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)

  function fractionFromPointer(e: PointerEvent<HTMLDivElement>): number {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect || rect.width === 0) return 0
    return Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
  }

  function handlePointerDown(e: PointerEvent<HTMLDivElement>) {
    if (!onSeek) return
    e.currentTarget.setPointerCapture(e.pointerId)
    setSeeking(true)
    onSeek(fractionFromPointer(e))
  }

  function handlePointerMove(e: PointerEvent<HTMLDivElement>) {
    if (!seeking || !onSeek) return
    onSeek(fractionFromPointer(e))
  }

  function stopSeeking() {
    setSeeking(false)
  }

  useEffect(() => {
    const el = containerRef.current
    if (!el || inView) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) setInView(true)
      },
      { rootMargin: "200px" }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [inView])

  useEffect(() => {
    if (!inView || !bytes || peaks) return
    let cancelled = false
    // decodeAudioData detaches/consumes the buffer it's given -- copy the
    // bytes first so the underlying zip data (still needed for download)
    // is untouched.
    const copy = bytes.slice().buffer
    getAudioContext()
      .decodeAudioData(copy)
      .then((decoded) => {
        if (!cancelled) setPeaks(extractPeaks(decoded, BAR_COUNT))
      })
      .catch(() => {
        if (!cancelled) setPeaks(new Array(BAR_COUNT).fill(0.15))
      })
    return () => {
      cancelled = true
    }
  }, [inView, bytes, peaks])

  const playedBars = peaks ? Math.round(progress * peaks.length) : 0

  return (
    <div
      ref={containerRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={stopSeeking}
      onPointerLeave={stopSeeking}
      className={`flex touch-none items-end gap-px ${onSeek ? "cursor-pointer" : ""} ${className}`}
    >
      {(peaks ?? new Array(BAR_COUNT).fill(0.2)).map((height, i) => (
        <span
          key={i}
          className={`min-w-[1px] flex-1 rounded-full transition-colors ${
            peaks && i < playedBars ? "bg-secondary-container" : "bg-white/25"
          } ${peaks ? "" : "animate-pulse"}`}
          style={{ height: `${Math.max(8, height * 100)}%` }}
        />
      ))}
    </div>
  )
}
