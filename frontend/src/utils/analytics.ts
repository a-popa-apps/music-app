// Google Analytics 4, gated on VITE_GA_MEASUREMENT_ID -- no-op if unset,
// same pattern as every other optional integration in this app. GA is only
// wired in behind the Cookie Consent banner (see CookieConsentBanner.tsx):
// the gtag.js snippet loads immediately with analytics_storage defaulted to
// "denied" (Google Consent Mode v2), and only flips to "granted" once the
// visitor accepts, so no analytics cookie is set without consent.

const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID as string | undefined

const CONSENT_STORAGE_KEY = "crateprep-analytics-consent"

type Consent = "granted" | "denied"

declare global {
  interface Window {
    dataLayer?: unknown[]
    gtag?: (...args: unknown[]) => void
  }
}

function gtag(...args: unknown[]) {
  window.dataLayer = window.dataLayer || []
  window.dataLayer.push(args)
}

let scriptLoaded = false

function loadScript() {
  if (!GA_MEASUREMENT_ID || scriptLoaded) return
  scriptLoaded = true

  window.gtag = gtag
  gtag("consent", "default", { analytics_storage: "denied" })
  gtag("js", new Date())
  gtag("config", GA_MEASUREMENT_ID, { send_page_view: false })

  const script = document.createElement("script")
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`
  document.head.appendChild(script)
}

export function getStoredConsent(): Consent | null {
  try {
    const value = window.localStorage.getItem(CONSENT_STORAGE_KEY)
    return value === "granted" || value === "denied" ? value : null
  } catch {
    return null
  }
}

/** Call once on app startup. Loads gtag.js (consent still defaulted to
 * denied) and re-applies a previously stored consent choice, if any. */
export function initAnalytics() {
  if (!GA_MEASUREMENT_ID) return
  loadScript()
  if (getStoredConsent() === "granted") {
    window.gtag?.("consent", "update", { analytics_storage: "granted" })
  }
}

export function setAnalyticsConsent(consent: Consent) {
  if (!GA_MEASUREMENT_ID) return
  try {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, consent)
  } catch {
    // private-browsing / storage disabled -- consent still applies for this
    // page load via the in-memory gtag call below, just won't persist.
  }
  loadScript()
  window.gtag?.("consent", "update", {
    analytics_storage: consent === "granted" ? "granted" : "denied",
  })
}

export function trackEvent(name: string, params?: Record<string, unknown>) {
  if (!GA_MEASUREMENT_ID) return
  window.gtag?.("event", name, params)
}
