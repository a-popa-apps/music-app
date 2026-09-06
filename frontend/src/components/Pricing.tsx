import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import { useProfile } from "../hooks/useProfile"
import { createBillingPortalSession, createCheckoutSession } from "../services/api"

const FREE_INCLUDED = [
  "25 tracks per month",
  "Standard BPM & key detection",
  "FLAC, AIFF & WAV 24-bit precision",
  "Rekordbox-ready .m3u8 playlist export",
]

const FREE_EXCLUDED = ["Custom filename syntax templating", "Priority processing"]

const PRO_CHECKLIST = [
  "Everything in Free, plus:",
  "Unlimited tracks per month",
  "Rekordbox, Serato & Traktor XML export",
  "Custom filename syntax templating",
  "Priority harmonic key analyzer",
]

export function Pricing() {
  const { user, isVerified } = useAuth()
  const { profile } = useProfile()
  const isPro = Boolean(user && isVerified && profile?.plan === "pro")
  const navigate = useNavigate()
  const [billing, setBilling] = useState<"monthly" | "annual">("annual")
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const price = billing === "annual" ? 5 : 8
  const cadence =
    billing === "annual" ? "/ month (billed annually)" : "/ month"

  async function handleGetPro() {
    if (!user || !isVerified) {
      navigate("/auth")
      return
    }
    setCheckoutLoading(true)
    try {
      const token = await user.getIdToken()
      const url = isPro
        ? await createBillingPortalSession(token)
        : await createCheckoutSession(token, billing)
      window.location.href = url
    } catch {
      setCheckoutLoading(false)
    }
  }

  return (
    <section id="pricing" className="relative w-full overflow-hidden bg-black px-4 py-16 lg:px-12">
      <div className="relative z-10 mx-auto flex max-w-5xl flex-col items-center text-center">
        <span className="mb-1 font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
          Fair Selector Pricing
        </span>
        <h2 className="mb-4 text-headline-xl tracking-tight text-white">
          Free for one-off gigs. Pro for the grind.
        </h2>
        <p className="mb-12 max-w-xl text-body-lg text-white/70">
          Start free to prep this weekend's gig, upgrade when your download
          folders get wild.
        </p>

        <div className="grid w-full grid-cols-1 items-stretch gap-6 text-left md:grid-cols-2">
          {/* Free plan */}
          <div className="flex h-full flex-col rounded-2xl border border-white/10 bg-white/5 p-10 backdrop-blur-md">
            <h3 className="text-headline-lg font-bold text-white">Free</h3>
            <span className="text-body-sm text-white/70">
              Perfect for one-off gig prep
            </span>

            <div className="flex items-baseline gap-1 py-6">
              <span className="text-display-hero tracking-tight text-white">$0</span>
              <span className="text-body-md text-white/70">/ forever</span>
            </div>

            <div className="flex flex-col gap-2">
              {FREE_INCLUDED.map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-secondary-container">
                    check_circle
                  </span>
                  <span className="text-body-md text-white">{item}</span>
                </div>
              ))}
              {FREE_EXCLUDED.map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-white/30">
                    cancel
                  </span>
                  <span className="text-body-md text-white/40 line-through">{item}</span>
                </div>
              ))}
            </div>

            {!isPro && (
              <>
                {user && isVerified ? (
                  <div className="mt-auto w-full rounded-full border border-white/10 bg-white/5 px-6 py-4 text-center text-headline-sm font-semibold text-white/50">
                    Your Current Plan
                  </div>
                ) : (
                  <button
                    onClick={() => navigate("/auth")}
                    className="mt-auto w-full rounded-full border border-white/20 bg-white/10 px-6 py-4 text-center text-headline-sm font-semibold text-white transition-colors hover:bg-white/15"
                  >
                    Get Started Free
                  </button>
                )}
                <span className="mt-2 text-center font-mono text-meta-numeric text-white/60">
                  {user && isVerified ? "You're all set" : "No credit card required"}
                </span>
              </>
            )}
          </div>

          {/* Pro plan */}
          <div className="h-full rounded-[calc(1rem+4px)] bg-gradient-to-r from-secondary-container to-[#ff3d78] p-[2px] shadow-[0_0_70px_rgba(255,107,53,0.3)]">
            <div className="flex h-full w-full flex-col rounded-2xl bg-[#12122a]/90 p-10 backdrop-blur-md">
              <div>
                <h3 className="text-headline-lg font-bold text-white">CratePrep Pro</h3>
                <span className="text-body-sm text-white/70">
                  Complete autonomy for working selectors
                </span>
              </div>

              <div className="flex items-baseline gap-1 pt-6">
                <span className="text-display-hero tracking-tight text-white">
                  ${price}
                </span>
                <span className="text-body-md text-white/70">{cadence}</span>
              </div>

              <div className="my-6 flex items-center gap-2 self-start rounded-full border border-white/10 bg-white/10 p-1">
                <button
                  onClick={() => setBilling("monthly")}
                  className={`rounded-full px-6 py-1 text-body-sm font-semibold transition-all ${
                    billing === "monthly" ? "bg-white/20 text-white" : "text-white/60"
                  }`}
                >
                  Monthly
                </button>
                <button
                  onClick={() => setBilling("annual")}
                  className={`flex items-center gap-1 rounded-full px-6 py-1 text-body-sm font-semibold transition-all ${
                    billing === "annual" ? "bg-white/20 text-white" : "text-white/60"
                  }`}
                >
                  Annual
                  <span className="rounded-full bg-secondary-container px-1 py-px text-[10px] font-bold uppercase text-on-primary">
                    Save 38%
                  </span>
                </button>
              </div>

              <div className="flex flex-col gap-2">
                {PRO_CHECKLIST.map((item, i) =>
                  i === 0 ? (
                    <span key={item} className="text-body-sm font-semibold text-white/70">
                      {item}
                    </span>
                  ) : (
                    <div key={item} className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-[20px] text-secondary-container">
                        check_circle
                      </span>
                      <span className="text-body-md text-white">{item}</span>
                    </div>
                  )
                )}
              </div>

              <div className="mt-auto pt-8">
                <button
                  onClick={handleGetPro}
                  disabled={checkoutLoading}
                  className="w-full rounded-full bg-gradient-to-r from-secondary-container to-[#ff3d78] px-6 py-4 text-center text-headline-sm font-semibold text-on-primary shadow-[0_8px_30px_rgba(255,107,53,0.45)] transition-transform hover:scale-[1.02] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {checkoutLoading ? "Loading..." : isPro ? "Manage Billing" : "Get CratePrep Pro"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
