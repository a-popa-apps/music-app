const BAR_HEIGHTS = [
  20, 35, 15, 50, 65, 40, 80, 55, 30, 70, 90, 60, 45, 75, 35, 55, 85, 50, 25,
  60, 95, 70, 40, 65, 30, 50, 80, 45, 60, 20, 55, 75, 35, 65, 90, 50, 30, 70,
  45, 60,
]

interface WaveformProps {
  progress?: number
  className?: string
}

export function Waveform({ progress = 0.5, className = "" }: WaveformProps) {
  return (
    <div className={`flex h-full w-full items-center gap-[1px] ${className}`}>
      {BAR_HEIGHTS.map((height, i) => (
        <div
          key={i}
          className="w-[2px] flex-1 rounded-full"
          style={{
            height: `${height}%`,
            backgroundColor:
              i / BAR_HEIGHTS.length < progress
                ? "var(--color-secondary-container)"
                : "var(--color-surface-container-highest)",
          }}
        />
      ))}
    </div>
  )
}
