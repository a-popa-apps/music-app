import { LegalPage } from "./LegalPage"

export function CookiePolicyPage() {
  return (
    <LegalPage
      title="Cookie Policy"
      sections={[
        {
          heading: "1. What Are Cookies",
          body: "Cookies (and similar technologies like local storage) are small pieces of data a website stores in your browser, typically to remember who you are between visits.",
        },
        {
          heading: "2. Cookies We Use",
          body: "CratePrep uses only strictly necessary cookies and local storage, set by Firebase Authentication, to keep you signed in between visits. We don't use any advertising, analytics, or tracking cookies, and we don't sell or share data with ad networks.",
        },
        {
          heading: "3. Third-Party Cookies",
          body: "We don't embed any third-party trackers, ads, or analytics scripts that set cookies in your browser. Genre lookups against Spotify and Discogs happen server-side and never set cookies on your device.",
        },
        {
          heading: "4. Managing Cookies",
          body: "Because we only use the cookies required to keep you signed in, disabling them in your browser will simply sign you out and require you to log in again — there's nothing optional to turn off. You can still clear cookies for this site at any time through your browser's settings.",
        },
        {
          heading: "5. Changes to This Policy",
          body: "If we ever start using additional cookies (for example, if we add analytics in the future), we'll update this page and, where required, ask for your consent first.",
        },
        {
          heading: "6. Contact",
          body: "Questions about this policy? Reach us through the \"Contact Support\" option available from the \"?\" button on any page.",
        },
      ]}
    />
  )
}
