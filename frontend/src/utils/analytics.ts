// Google Analytics 4. The gtag.js snippet itself is loaded statically in
// index.html's <head> (not from here) -- see the comment there for why:
// a dynamically-created <script> tag, injected only after this bundle
// mounted and consent resolved, reproducibly never delivered a single hit
// in production, while an identical static snippet always did. This
// module only manages consent state and sends events through the
// already-globally-defined window.gtag.

const CONSENT_STORAGE_KEY = "crateprep-analytics-consent"

const GA_ENABLED = Boolean(import.meta.env.VITE_GA_MEASUREMENT_ID)

type Consent = "granted" | "denied"

declare global {
  interface Window {
    dataLayer?: unknown[]
    gtag?: (...args: unknown[]) => void
  }
}

export function getStoredConsent(): Consent | null {
  try {
    const value = window.localStorage.getItem(CONSENT_STORAGE_KEY)
    return value === "granted" || value === "denied" ? value : null
  } catch {
    return null
  }
}

// index.html's inline script already re-applies a previously granted
// consent before any component mounts, so a returning visitor's page view
// (below) sends normally. A first-time visitor's initial trackPageView()
// call fires before they've had any chance to click the consent banner,
// though, so consent is still "denied" at that moment and gtag.js drops
// the hit -- and since config() disables the automatic page_view, there's
// no natural second one to fall back on for a single-page visit. Held
// here and flushed the instant they actually grant consent.
let pendingPageViewPath: string | null = null

function sendPageView(path: string) {
  window.gtag?.("event", "page_view", {
    page_path: path,
    page_location: window.location.href,
    page_title: document.title,
  })
}

export function setAnalyticsConsent(consent: Consent) {
  if (!GA_ENABLED) return
  try {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, consent)
  } catch {
    // private-browsing / storage disabled -- consent still applies for this
    // page load via the gtag call below, just won't persist.
  }
  window.gtag?.("consent", "update", {
    analytics_storage: consent === "granted" ? "granted" : "denied",
  })
  if (consent === "granted" && pendingPageViewPath) {
    sendPageView(pendingPageViewPath)
  }
  pendingPageViewPath = null
}

export function trackEvent(name: string, params?: Record<string, unknown>) {
  if (!GA_ENABLED) return
  window.gtag?.("event", name, params)
}

/** Sent manually on the initial load and every client-side route change --
 * index.html's config() call passes send_page_view: false so this is the
 * only source of page_view events, avoiding a double-count on first load. */
export function trackPageView(path: string) {
  if (!GA_ENABLED) return
  const consent = getStoredConsent()
  if (consent === null) {
    pendingPageViewPath = path
    return
  }
  if (consent === "denied") return
  sendPageView(path)
}
