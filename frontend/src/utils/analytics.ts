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

// Runs as soon as this module is first imported, rather than from a React
// effect -- module evaluation always happens before any component mounts,
// so this can't race a sibling component's own mount effect for who sets
// window.gtag first. It used to run from CookieConsentBanner's effect via
// initAnalytics(), which meant trackPageView()/trackEvent() calls from a
// component whose effect happened to fire first (order isn't guaranteed
// between siblings) silently no-opped on window.gtag being undefined yet.
// React 19 StrictMode's dev-only double-invoke of effects masked this in
// development (the second pass usually won the race) but it reproduced
// every time in a production build, where effects run only once.
if (GA_MEASUREMENT_ID) {
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

/** Call once on app startup to re-apply a previously stored consent choice,
 * if any (gtag.js itself is already loaded by the time this runs -- see
 * above). */
export function initAnalytics() {
  if (!GA_MEASUREMENT_ID) return
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
  window.gtag?.("consent", "update", {
    analytics_storage: consent === "granted" ? "granted" : "denied",
  })
}

export function trackEvent(name: string, params?: Record<string, unknown>) {
  if (!GA_MEASUREMENT_ID) return
  window.gtag?.("event", name, params)
}

/** Sent manually on the initial load and every client-side route change --
 * config() above passes send_page_view: false so this is the only source of
 * page_view events, avoiding a double-count on first load. */
export function trackPageView(path: string) {
  if (!GA_MEASUREMENT_ID) return
  window.gtag?.("event", "page_view", {
    page_path: path,
    page_location: window.location.href,
    page_title: document.title,
  })
}
