// Same gradient-border + glow treatment as the Pro plan card in Pricing.tsx,
// as a "this is what Pro feels like" preview on cards that live on the free
// part of the page -- but only on hover, faded in with opacity rather than
// toggling the gradient itself. A CSS background-image (what a gradient is)
// can't be smoothly transitioned -- toggling it directly via hover: pops in
// and out instantly no matter what transition classes surround it, which is
// exactly what read as "flashing." The gradient here is always rendered on
// its own layer behind the content and only ever fades via opacity, which
// *does* transition smoothly; the content card on top keeps its own colors
// transitioning normally since solid colors interpolate fine.
function FeatureCard({
  className = "",
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div className={`group relative rounded-[calc(1rem+4px)] ${className}`}>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -inset-[2px] rounded-[calc(1rem+4px)] bg-gradient-to-r from-secondary-container to-[#ff3d78] opacity-0 shadow-[0_0_70px_rgba(255,107,53,0.3)] transition-opacity duration-500 ease-out group-hover:opacity-100"
      />
      <div className="relative flex h-full flex-col rounded-2xl border border-white/10 bg-white/10 p-8 backdrop-blur-md transition-colors duration-500 ease-out group-hover:border-transparent group-hover:bg-[#12122a]/95">
        {children}
      </div>
    </div>
  )
}

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
    icon: "sell",
    title: "Verified Genre & Energy Tags",
    description:
      "Cross-references Spotify and Discogs to tag every track's real genre, then rates its energy 1-10 from loudness -- no more guessing by ear.",
    footnote: "Spotify + Discogs Verified",
  },
  {
    icon: "auto_awesome",
    title: "AI-Assisted Filename Cleanup",
    description:
      "When a filename has no separator and no catalog match -- the cases regex and Spotify/Discogs can't crack -- an AI model steps in to split artist and title correctly instead of a coin-flip word-count guess.",
    footnote: "Pro Feature",
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
      "One click orders your whole batch by Camelot-wheel compatibility and BPM -- starting straight from the messy files you dropped, no separate step to first build an organized library like other set-building tools require.",
    footnote: "Pro Feature",
  },
]

export function Features() {
  return (
    <section id="features" className="relative w-full overflow-hidden bg-black px-4 py-16 lg:px-12">
      <div className="relative z-10 mx-auto flex max-w-7xl flex-col gap-12">
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
            <FeatureCard key={feature.title}>
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
            </FeatureCard>
          ))}

          <FeatureCard className="lg:col-span-2">
            <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
              <span className="material-symbols-outlined text-[22px] text-secondary-container">
                devices
              </span>
            </div>
            <h3 className="mb-2 text-headline-sm text-white">
              Ready For Any DJ Software
            </h3>
            <p className="mb-4 text-body-md text-white/70">
              Every track is tagged with the correct BPM, key, and genre
              before you download, so it shows up right the moment you drag
              it into your library — no manual fixes, no re-tagging.
            </p>
            <div className="mt-auto flex flex-wrap gap-1">
              {[
                "Standard BPM & Key Tags",
                "Works With Any DJ Software",
                "No Manual Re-Tagging",
              ].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-white/10 px-4 py-1 font-mono text-meta-badge text-white"
                >
                  {tag}
                </span>
              ))}
            </div>
          </FeatureCard>

          <FeatureCard>
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
          </FeatureCard>
        </div>
      </div>
    </section>
  )
}
