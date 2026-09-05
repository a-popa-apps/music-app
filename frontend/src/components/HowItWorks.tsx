const STEPS = [
  {
    number: "01",
    icon: "folder_zip",
    title: "Drop",
    description:
      "Drag any raw folder of MP3, WAV, AIFF, or FLAC files straight into your web browser. No software installation needed.",
    footnote: "Uncompressed 24-bit audio safe",
  },
  {
    number: "02",
    icon: "tune",
    title: "Sort",
    description:
      "Fast transient engine computes exact BPM, detects Camelot & OpenKey harmony, strips promo URLs, and tags subgenres.",
    footnote: "Camelot 1A–12B Harmonic System",
  },
  {
    number: "03",
    icon: "download_done",
    title: "Export",
    description:
      "Receive a pristine structured ZIP folder alongside playlists engineered to drop immediately into Rekordbox.",
    footnote: "Zero CDJ USB re-analysis latency",
  },
]

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="w-full bg-tertiary-container px-4 py-16 lg:px-12"
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-12">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <span className="font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
              Workflow Architecture
            </span>
            <h2 className="mt-1 text-headline-xl tracking-tight text-white">
              Three deliberate steps. Zero manual curation.
            </h2>
          </div>
          <p className="max-w-md text-body-md text-white/70">
            Architected for touring DJs who download 80 promo tracks two
            hours before call time.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {STEPS.map((step) => (
            <div
              key={step.number}
              className="flex flex-col rounded border border-white/10 bg-white/10 p-8 backdrop-blur-md transition-all hover:bg-white/15"
            >
              <div className="mb-8 flex items-center justify-between">
                <span className="font-mono text-headline-lg font-bold text-secondary-container">
                  {step.number}
                </span>
                <span className="material-symbols-outlined text-[28px] text-white/60">
                  {step.icon}
                </span>
              </div>
              <h3 className="mb-2 text-headline-sm text-white">
                {step.title}
              </h3>
              <p className="mb-6 text-body-md text-white/70">
                {step.description}
              </p>
              <div className="mt-auto flex items-center gap-1 pt-4 font-mono text-meta-badge text-white/70">
                <span className="material-symbols-outlined text-[16px] text-secondary-container">
                  check_circle
                </span>
                <span>{step.footnote}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
