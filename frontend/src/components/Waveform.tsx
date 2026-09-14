// A small looping audio-equalizer icon: bars bounce independently (varied
// duration/delay per bar) rather than in lockstep, so it reads as organic
// motion instead of a mechanical pulse.
const BAR_DURATIONS = [0.9, 1.15, 0.8, 1.3, 0.85, 1.2, 0.95]
const BAR_DELAYS = [0, 0.15, 0.3, 0.05, 0.25, 0.1, 0.35]

interface WaveformProps {
  className?: string
}

export function Waveform({ className = "" }: WaveformProps) {
  return (
    <div className={`flex items-center justify-center gap-1 ${className}`} aria-hidden="true">
      {BAR_DURATIONS.map((duration, i) => (
        <span
          key={i}
          className="h-full w-1.5 rounded-full bg-secondary-container animate-waveform-bar"
          style={{
            animationDuration: `${duration}s`,
            animationDelay: `${BAR_DELAYS[i]}s`,
          }}
        />
      ))}
    </div>
  )
}
