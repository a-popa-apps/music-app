import { useState } from "react"
import { GrainOverlay } from "./GrainOverlay"

const CHECKLIST = [
  "Unlimited track batch processing",
  "FLAC, AIFF & WAV 24-bit precision",
  "Rekordbox, Serato & Traktor XML export",
  "Custom filename syntax templating",
  "Priority harmonic key analyzer",
]

export function Pricing() {
  const [billing, setBilling] = useState<"monthly" | "annual">("annual")
  const price = billing === "annual" ? 5 : 8
  const cadence =
    billing === "annual" ? "/ month (billed annually)" : "/ month"

  return (
    <section
      id="pricing"
      className="relative w-full overflow-hidden bg-gradient-to-br from-[#141a44] to-[#07081a] px-4 py-16 lg:px-12"
    >
      <GrainOverlay />
      <div className="relative z-10 mx-auto flex max-w-4xl flex-col items-center text-center">
        <span className="mb-1 font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
          Fair Selector Pricing
        </span>
        <h2 className="mb-4 text-headline-xl tracking-tight text-white">
          One plan. Infinite track crates.
        </h2>
        <p className="mb-8 max-w-xl text-body-lg text-white/70">
          No complicated tiers. Start free to prep this weekend's gig,
          upgrade when your download folders get wild.
        </p>

        <div className="mb-12 flex items-center gap-2 rounded-full border border-white/10 bg-white/10 p-1 backdrop-blur-md">
          <button
            onClick={() => setBilling("monthly")}
            className={`rounded-full px-6 py-1 text-body-sm font-semibold transition-all ${
              billing === "monthly"
                ? "bg-white/20 text-white"
                : "text-white/60"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBilling("annual")}
            className={`flex items-center gap-1 rounded-full px-6 py-1 text-body-sm font-semibold transition-all ${
              billing === "annual"
                ? "bg-white/20 text-white"
                : "text-white/60"
            }`}
          >
            Annual
            <span className="rounded-full bg-secondary-container px-1 py-px text-[10px] font-bold uppercase text-on-primary">
              Save 38%
            </span>
          </button>
        </div>

        <div className="w-full max-w-lg rounded-[calc(1rem+4px)] bg-gradient-to-r from-secondary-container to-[#ff3d78] p-[2px] shadow-[0_0_70px_rgba(255,107,53,0.3)]">
          <div className="flex w-full flex-col rounded-2xl bg-[#12122a]/90 p-12 text-left backdrop-blur-md">
            <div className="flex items-center justify-between gap-4 pb-4">
              <div>
                <h3 className="text-headline-lg font-bold text-white">
                  Pro DJ Plan
                </h3>
                <span className="text-body-sm text-white/70">
                  Complete autonomy for working selectors
                </span>
              </div>
              {billing === "annual" && (
                <span className="whitespace-nowrap rounded-full border border-secondary-container/40 bg-secondary-container/10 px-3 py-1 font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
                  Best Value &mdash; Save 38%
                </span>
              )}
            </div>

            <div className="flex items-baseline gap-1 py-6">
              <span className="text-display-hero tracking-tight text-white">
                ${price}
              </span>
              <span className="text-body-md text-white/70">
                {cadence}
              </span>
            </div>

            <div className="mb-8 flex flex-col gap-2 py-4">
              {CHECKLIST.map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-secondary-container">
                    check_circle
                  </span>
                  <span className="text-body-md text-white">{item}</span>
                </div>
              ))}
            </div>

            <button className="w-full rounded-full bg-gradient-to-r from-secondary-container to-[#ff3d78] px-6 py-4 text-center text-headline-sm font-semibold text-on-primary shadow-[0_8px_30px_rgba(255,107,53,0.45)] transition-transform hover:scale-[1.02] active:scale-95">
              Get Started Free (First 50 Tracks On Us)
            </button>
            <span className="mt-2 text-center font-mono text-meta-numeric text-white/60">
              No credit card required &bull; Instant activation
            </span>
          </div>
        </div>
      </div>
    </section>
  )
}
