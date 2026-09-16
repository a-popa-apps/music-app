// Google Analytics 4, gated on VITE_GA_MEASUREMENT_ID -- no-op if unset,
// same pattern as every other optional integration in this app.
//
// Deliberately NOT using Google's Consent Mode v2 pattern (gtag.js loaded
// immediately with analytics_storage defaulted to "denied", flipped to
// "granted" on accept): a previous implementation followed that pattern
// exactly, including fixing two real consent-vs-mount-order races, and
// verified via direct dataLayer inspection that the commands were queued
// in the correct order -- and GA4 still never received a single hit, on
// any device, with no way to confirm whether gtag.js's own internal
// consent-gating was ever actually the thing at fault. Rather than trust
// that black box again, consent is now enforced entirely on this side:
// gtag.js is never loaded and nothing is ever pushed to a dataLayer until
// the visitor has explicitly granted consent. No consent, no script, no
// network request -- there's no internal "denied" state for a hit to get
// silently dropped from in the first place.

const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID as string | undefined

const CONSENT_STORAGE_KEY = "crateprep-analytics-consent"

type Consent = "granted" | "denied"

declare global {
  interface Window {
    dataLayer?: unknown[]
    gtag?: (...args: unknown[]) => void
  }
}

let initialized = false

function gtag(...args: unknown[]) {
  window.dataLayer = window.dataLayer || []
  window.dataLayer.push(args)
}

function initGtag() {
  if (initialized || !GA_MEASUREMENT_ID) return
  initialized = true

  window.gtag = gtag
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

// Runs at module load, before any component mounts: a returning visitor
// who already granted consent gets GA initialized immediately, so their
// page view isn't lost waiting for a banner interaction that already
// happened on a previous visit.
if (getStoredConsent() === "granted") {
  initGtag()
}

export function setAnalyticsConsent(consent: Consent) {
  if (!GA_MEASUREMENT_ID) return
  try {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, consent)
  } catch {
    // private-browsing / storage disabled -- consent still applies for this
    // page load via initGtag() below, just won't persist.
  }
  if (consent !== "granted") return

  // A first-time visitor's PageViewTracker effect (see App.tsx) already
  // ran once for the current route before they had a chance to accept the
  // banner, and trackPageView() below no-ops until `initialized` is true --
  // so that initial view never got sent. Send it now, immediately after
  // initializing, rather than waiting for a route change that might never
  // come during this visit.
  initGtag()
  trackPageView(window.location.pathname)
}

export function trackEvent(name: string, params?: Record<string, unknown>) {
  if (!initialized) return
  window.gtag?.("event", name, params)
}

/** Sent manually on the initial load (once consent is granted) and every
 * client-side route change -- config() above passes send_page_view: false
 * so this is the only source of page_view events, avoiding a double-count
 * on first load. No-ops entirely until consent has been granted. */
export function trackPageView(path: string) {
  if (!initialized) return
  window.gtag?.("event", "page_view", {
    page_path: path,
    page_location: window.location.href,
    page_title: document.title,
  })
}
