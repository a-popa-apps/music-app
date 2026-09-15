import { useEffect, useRef, useState } from "react"

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
  className?: string
}

// Renders a static bar-style waveform (decoded lazily the first time this
// row scrolls into view, then cached) with bars up to `progress` styled as
// "played". Playback control lives in the parent -- this component only
// draws.
export function TrackWaveform({ bytes, progress, className = "" }: TrackWaveformProps) {
  const [peaks, setPeaks] = useState<number[] | null>(null)
  const [inView, setInView] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)

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
    <div ref={containerRef} className={`flex items-end gap-px ${className}`}>
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
