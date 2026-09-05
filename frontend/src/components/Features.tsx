const FEATURES = [
  {
    icon: "spellcheck",
    title: "Zero Junk Filenames",
    description:
      "Surgically strips '[FREE DOWNLOAD]', 'BUY_ON_BEATPORT', Telegram watermarks, and rip garbage automatically before export.",
    footnote: 'Cleaned: "Artist - Title.wav"',
  },
  {
    icon: "speed",
    title: "Rock-Solid BPM & Key",
    description:
      "High-precision transient detection and Camelot harmonic wheel matching. Handles polyrhythms without drifting off grid.",
    footnote: "99.8% Beat-Grid Transient Lock",
  },
  {
    icon: "auto_awesome_motion",
    title: "Genre-Sorted Playlists",
    description:
      "Acoustic fingerprinting organizes your chaos into logical energy brackets and subgenres: Warmup, Peak-Time, Closing.",
    footnote: "Automated Subfolder Taxonomy",
  },
]

export function Features() {
  return (
    <section
      id="features"
      className="w-full bg-[#15122e] px-4 py-16 lg:px-12"
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-12">
        <div className="flex max-w-2xl flex-col gap-1">
          <span className="font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
            System Capabilities
          </span>
          <h2 className="text-headline-xl tracking-tight text-white">
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

          <div className="flex flex-col rounded border border-white/10 bg-white/10 p-8 backdrop-blur-md transition-colors hover:bg-white/15 lg:col-span-2">
            <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
              <span className="material-symbols-outlined text-[22px] text-secondary-container">
                devices
              </span>
            </div>
            <h3 className="mb-2 text-headline-sm text-white">
              Rekordbox, Serato & Traktor Native
            </h3>
            <p className="mb-4 text-body-md text-white/70">
              Exports playlist files ready to drag directly into your current
              library without recalculating waveforms or corrupting cues.
            </p>
            <div className="mt-auto flex flex-wrap gap-1">
              {[
                "Rekordbox 6 & 7 XML",
                "Serato DJ Pro .crate",
                "Traktor Pro 3/4 NML",
                "Standard CDJ FAT32",
              ].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-white/10 px-4 py-1 font-mono text-meta-badge text-white"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-col rounded border border-white/10 bg-white/10 p-8 backdrop-blur-md transition-colors hover:bg-white/15">
            <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
              <span className="material-symbols-outlined text-[22px] text-secondary-container">
                security
              </span>
            </div>
            <h3 className="mb-2 text-headline-sm text-white">
              No Files Retained
            </h3>
            <p className="mb-4 text-body-md text-white/70">
              Your tracks are processed for a single request and streamed
              back — nothing is stored on our servers afterward.
            </p>
            <div className="mt-auto font-mono text-meta-numeric font-semibold text-secondary-container">
              &bull; Zero Retention Policy
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
