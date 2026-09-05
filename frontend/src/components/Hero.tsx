import { Waveform } from "./Waveform"

export function Hero() {
  return (
    <section className="w-full bg-surface-container-lowest px-4 pb-16 pt-12 lg:px-12">
      <div className="mx-auto flex max-w-7xl flex-col items-center text-center">
        <div className="mb-6 inline-flex items-center gap-1 rounded-full bg-surface-container-low px-4 py-1 shadow-sm">
          <span className="h-2 w-2 animate-ping rounded-full bg-secondary-container" />
          <span className="font-mono text-meta-badge uppercase tracking-wider text-on-surface-variant">
            DJ Utility 1.0 &middot; Rekordbox Ready
          </span>
        </div>

        <h1 className="mb-4 max-w-4xl text-display-hero-mobile tracking-tighter text-on-surface lg:text-display-hero">
          Let's do it quick.
        </h1>

        <p className="mb-8 max-w-2xl text-body-lg text-on-surface-variant">
          Drop your messy download folder. Get back clean filenames, verified
          BPM and Camelot keys, genre playlists, and ready-to-gig Rekordbox
          exports in seconds.
        </p>

        <div className="mb-16 flex flex-col items-center">
          <a
            href="#demo"
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-secondary-container px-8 py-4 text-headline-sm font-semibold text-on-primary shadow-md transition-all hover:opacity-90 active:scale-95 sm:w-auto"
          >
            Drop Folder to Clean
            <span className="material-symbols-outlined text-[20px]">
              arrow_forward
            </span>
          </a>
        </div>

        <div className="flex w-full max-w-4xl flex-col gap-4 rounded bg-surface-container-low p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 text-left">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-secondary-container" />
              <span className="font-mono text-meta-numeric font-semibold text-on-surface">
                INPUT: ~/Downloads/Bandcamp_Packs_2024
              </span>
            </div>
            <div className="flex items-center gap-1">
              <span className="rounded-full bg-surface-container-lowest px-2 py-1 font-mono text-meta-badge font-bold text-secondary-container">
                128.00 BPM
              </span>
              <span className="rounded-full bg-surface-container-lowest px-2 py-1 font-mono text-meta-badge font-bold text-secondary-container">
                8A / A MINOR
              </span>
              <span className="rounded-full bg-surface-container-lowest px-2 py-1 font-mono text-meta-badge text-on-surface">
                TECH HOUSE
              </span>
            </div>
          </div>

          <div className="relative h-24 w-full overflow-hidden rounded bg-surface-container-highest px-4">
            <Waveform progress={0.5} />
            <div className="pointer-events-none absolute inset-y-0 left-1/2 w-0.5 bg-primary" />
            <div className="absolute left-1/2 top-2 -translate-x-1/2 rounded bg-primary px-1 py-px font-mono text-meta-badge text-on-primary">
              TRANSIENT LOCK
            </div>
          </div>

          <div className="flex items-center justify-between font-mono text-meta-numeric text-on-surface-variant">
            <span>00:00.000</span>
            <span className="font-semibold text-secondary-container">
              NEURAL GRID LOCK: 99.8% PRECISION
            </span>
            <span>06:42.120</span>
          </div>
        </div>
      </div>
    </section>
  )
}
