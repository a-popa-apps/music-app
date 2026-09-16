import { LegalPage } from "./LegalPage"

export function CookiePolicyPage() {
  return (
    <LegalPage
      title="Cookie Policy"
      path="/cookie-policy"
      sections={[
        {
          heading: "1. What Are Cookies",
          body: "Cookies (and similar technologies like local storage) are small pieces of data a website stores in your browser, typically to remember who you are between visits.",
        },
        {
          heading: "2. Cookies We Use",
          body: "Strictly necessary: local storage set by Firebase Authentication to keep you signed in between visits — always on, since the app can't function without it. We don't use any analytics, advertising, or ad-tracking cookies, and we don't sell or share data with ad networks.",
        },
        {
          heading: "3. Third-Party Cookies",
          body: "We don't use any third-party cookies. Genre lookups against Spotify and Discogs happen server-side and never set cookies on your device.",
        },
        {
          heading: "4. Managing Cookies",
          body: "Disabling the strictly-necessary sign-in storage will simply sign you out and require you to log in again. You can clear all cookies for this site at any time through your browser's settings.",
        },
        {
          heading: "5. Changes to This Policy",
          body: "If we start using additional cookies beyond what's listed here, we'll update this page and, where required, ask for your consent first.",
        },
        {
          heading: "6. Contact",
          body: "Questions about this policy? Reach us through the \"Contact Support\" option available from the \"?\" button on any page.",
        },
      ]}
    />
  )
}
