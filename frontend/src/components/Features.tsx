const FEATURES = [
  {
    icon: "spellcheck",
    title: "Zero Junk Filenames",
    description:
      "Surgically strips '[FREE DOWNLOAD]', 'BUY_ON_BEATPORT', Telegram watermarks, and rip garbage automatically before export. When a filename has no separator and no catalog match, an AI model steps in to split artist and title correctly instead of a coin-flip guess.",
    footnote: "AI Split: Pro Feature",
  },
  {
    icon: "speed",
    title: "Rock-Solid BPM, Key & Genre",
    description:
      "High-precision transient detection and Camelot harmonic wheel matching handle polyrhythms without drifting off grid. Every track's real genre is cross-referenced against Spotify, Discogs, and more, then rated for energy 1-10 from loudness -- no more guessing by ear.",
    footnote: "Verified Across 5+ Catalogs",
  },
  {
    icon: "insights",
    title: "AI Batch Insights",
    description:
      "The moment your batch finishes, get a plain-English read on its genre mix, BPM range, and energy arc -- plus a heads-up on anything that stands out from the rest -- so you know what you're working with before you even open your DJ software.",
    footnote: "Included On Every Plan",
  },
  {
    icon: "shuffle",
    title: "AI Harmonic Set Ordering",
    description:
      "One click orders your whole batch by Camelot-wheel compatibility and BPM -- starting straight from the messy files you just downloaded. Other set-building tools, including ones built specifically for this, need an already-organized library to import first; CratePrep skips that step entirely.",
    footnote: "Pro Feature",
  },
  {
    icon: "devices",
    title: "Ready For Any DJ Software",
    description:
      "Every track is tagged with the correct BPM, key, and genre before you download, so it shows up right the moment you drag it into your library -- no manual fixes, no re-tagging.",
    footnote: "Rekordbox, Serato & Traktor Verified",
  },
  {
    icon: "security",
    title: "No Files Retained",
    description:
      "Your tracks are processed for a single request and streamed back -- nothing is stored on our servers afterward.",
    footnote: "Zero Retention Policy",
  },
]

export function Features() {
  return (
    <section id="features" className="relative w-full overflow-hidden bg-black px-4 py-16 lg:px-12">
      <div className="relative z-10 mx-auto flex max-w-7xl flex-col gap-12">
        <div className="flex flex-col gap-1">
          <span className="font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
            System Capabilities
          </span>
          <h2 className="text-headline-xl tracking-tight text-white lg:whitespace-nowrap">
            Built strictly for selectors with high standards.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="flex flex-col rounded border border-white/10 bg-white/10 p-8 backdrop-blur-md transition-colors hover:bg-white/15"
            >
              <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
                <span className="material-symbols-outlined text-[22px] text-secondary-container">
                  {feature.icon}
                </span>
              </div>
              <h3 className="mb-2 text-headline-sm text-white">
                {feature.title}
              </h3>
              <p className="mb-4 text-body-md text-white/70">
                {feature.description}
              </p>
              <div className="mt-auto font-mono text-meta-numeric font-semibold text-secondary-container">
                &bull; {feature.footnote}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
