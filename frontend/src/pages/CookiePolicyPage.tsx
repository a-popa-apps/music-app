import { LegalPage } from "./LegalPage"

export function CookiePolicyPage() {
  return (
    <LegalPage
      title="Cookie Policy"
      path="/cookie-policy"
      lastUpdated="September 17, 2026"
      sections={[
        {
          heading: "1. What Are Cookies",
          body: "Cookies (and similar technologies like local storage) are small pieces of data a website stores in your browser, typically to remember who you are between visits.",
        },
        {
          heading: "2. Cookies We Use",
          body: "Strictly necessary: local storage set by Firebase Authentication to keep you signed in between visits, and fraud-prevention cookies set by Stripe while you're on its checkout or billing-portal pages during an upgrade or billing-management flow — always on, since the app (and taking payment) can't function without them. Optional analytics: if you accept our cookie consent banner, Google Analytics sets cookies to help us understand overall usage (pages visited, features used). It's off by default and only activates if you click \"Accept\" — declining or ignoring the banner keeps it off. We don't use any advertising or ad-tracking cookies, and we don't sell or share data with ad networks.",
        },
        {
          heading: "3. Third-Party Cookies",
          body: "Stripe sets its own cookies while you're on its checkout or billing-portal pages, to prevent fraud and keep that session secure — these are Stripe's, not ours, and only apply during an actual checkout/billing session, never elsewhere on the site. Google Analytics sets cookies only after you accept the consent banner. Genre lookups against Spotify, Discogs, and the other catalogs we use happen server-side and never set cookies on your device.",
        },
        {
          heading: "4. Managing Cookies",
          body: "You can withdraw analytics consent at any time by clearing your browser's local storage for this site, which brings the consent banner back on your next visit. Disabling the strictly-necessary sign-in storage will simply sign you out and require you to log in again. You can also clear all cookies for this site at any time through your browser's settings.",
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
