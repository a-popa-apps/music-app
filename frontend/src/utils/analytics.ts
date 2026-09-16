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

export function getStoredConsent(): Consent | null {
  try {
    const value = window.localStorage.getItem(CONSENT_STORAGE_KEY)
    return value === "granted" || value === "denied" ? value : null
  } catch {
    return null
  }
}

// Runs as soon as this module is first imported, rather than from a React
// effect -- module evaluation always happens before any component mounts,
// so this can't race a sibling component's own mount effect. window.gtag
// itself used to be assigned from a React effect and that alone caused a
// real bug (see below); a second, subtler version of the same race
// survived even after that fix: the granted/denied consent re-apply used to
// run from CookieConsentBanner's mount effect via initAnalytics(), and
// App.tsx renders <PageViewTracker /> before <CookieConsentBanner /> --
// React fires sibling effects in mount order, so trackPageView()'s very
// first call was *always* processed by gtag.js while consent was still the
// default "denied", before CookieConsentBanner's effect ever got a chance
// to re-apply a stored "granted" choice. Since send_page_view: false makes
// that initial call the only page_view a single-page visit ever sends, it
// was silently dropped by Google's consent gating on every single load,
// for every returning visitor, regardless of their actual stored consent.
// Re-applying stored consent here, before any component mounts, removes
// the dependency on mount order entirely.
//
// (The window.gtag assignment itself moved here for the same reason: a
// component whose effect happened to fire first could previously call
// trackPageView()/trackEvent() before window.gtag existed. React 19
// StrictMode's dev-only double-invoke of effects masked this in
// development -- the second pass usually won the race -- but it reproduced
// every time in a production build, where effects run only once.)
if (GA_MEASUREMENT_ID) {
  window.gtag = gtag
  gtag("consent", "default", { analytics_storage: "denied" })
  if (getStoredConsent() === "granted") {
    gtag("consent", "update", { analytics_storage: "granted" })
  }
  gtag("js", new Date())
  gtag("config", GA_MEASUREMENT_ID, { send_page_view: false })

  const script = document.createElement("script")
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`
  document.head.appendChild(script)
}

// A first-time visitor's very first trackPageView() call (see below) fires
// the instant the app mounts, well before they've had a chance to click
// the consent banner -- so at that moment getStoredConsent() is still null
// (undecided), not yet "granted" or "denied". Sending it anyway would have
// gtag.js process it under the "denied" default and silently drop it, and
// Consent Mode never retroactively resends a dropped hit once consent is
// later granted -- there is no natural second page_view to fall back on
// for a single-page visit, since config() above passes send_page_view:
// false specifically to avoid double-counting route changes. So instead of
// sending immediately, an undecided page view is held here and flushed the
// moment the visitor actually answers the banner.
let pendingPageViewPath: string | null = null

function sendPageView(path: string) {
  window.gtag?.("event", "page_view", {
    page_path: path,
    page_location: window.location.href,
    page_title: document.title,
  })
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
  if (consent === "granted" && pendingPageViewPath) {
    sendPageView(pendingPageViewPath)
  }
  pendingPageViewPath = null
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
  const consent = getStoredConsent()
  if (consent === null) {
    pendingPageViewPath = path
    return
  }
  if (consent === "denied") return
  sendPageView(path)
}
