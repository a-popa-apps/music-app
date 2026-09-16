import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { getStoredConsent, setAnalyticsConsent } from "../utils/analytics"

const GA_ENABLED = Boolean(import.meta.env.VITE_GA_MEASUREMENT_ID)

export function CookieConsentBanner() {
  const [visible, setVisible] = useState(false)

  // Stored consent is already re-applied to gtag at analytics.ts's module
  // load, before this (or any other) component even mounts -- this effect
  // only needs to decide whether the banner itself should show.
  useEffect(() => {
    if (!GA_ENABLED) return
    setVisible(getStoredConsent() === null)
  }, [])

  if (!visible) return null

  function respond(consent: "granted" | "denied") {
    setAnalyticsConsent(consent)
    setVisible(false)
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-3 border-t border-outline-variant bg-inverse-surface px-4 py-4 text-inverse-on-surface sm:flex-row sm:justify-between sm:gap-6 sm:px-8">
      <p className="text-body-sm">
        We use Google Analytics to understand how CratePrep is used. No ad tracking, no
        selling data. See our{" "}
        <Link to="/cookie-policy" className="underline hover:opacity-80">
          Cookie Policy
        </Link>
        .
      </p>
      <div className="flex shrink-0 gap-2">
        <button
          onClick={() => respond("denied")}
          className="rounded-full border border-inverse-on-surface/40 px-4 py-2 text-body-sm font-semibold hover:bg-white/10"
        >
          Decline
        </button>
        <button
          onClick={() => respond("granted")}
          className="rounded-full bg-secondary-container px-4 py-2 text-body-sm font-semibold text-on-primary hover:opacity-90"
        >
          Accept
        </button>
      </div>
    </div>
  )
}
