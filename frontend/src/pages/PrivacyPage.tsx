import { LegalPage } from "./LegalPage"

export function PrivacyPage() {
  return (
    <LegalPage
      title="Privacy Policy"
      sections={[
        {
          heading: "1. Information We Collect",
          body: "Your email address (for account creation), and any profile details you choose to provide (name, artist name, country, role, genre preferences, filename template). Audio files you upload are processed in memory for the duration of a single request and are not retained afterward. If you're signed in, we also keep a history of the tracks you've processed — filename, detected BPM/key/genre, and duration — so you can review it later; this history never includes the audio itself.",
        },
        {
          heading: "2. How We Use Your Information",
          body: "To provide and personalize the service — for example, applying your saved filename template and preferences when processing your uploads.",
        },
        {
          heading: "3. Third-Party Services",
          body: "We use Firebase (Google) for account authentication and to store your profile settings. To help detect a track's genre, we send the cleaned artist/title text (never the audio file itself) to Spotify's and Discogs' public APIs.",
        },
        {
          heading: "4. Data Retention",
          body: "Uploaded audio is never retained. Account and profile data is kept until you delete your account, which you can do at any time from Profile Details. Processing history (metadata only, never audio) is kept until you clear it from the History page or delete your account.",
        },
        {
          heading: "5. Your Rights",
          body: "You can view and edit your stored profile data at any time from Profile Details, and permanently delete your account and all associated data from the same page.",
        },
        {
          heading: "6. Cookies and Local Storage",
          body: "We use only strictly necessary cookies and local storage required to keep you signed in, via Firebase Authentication — no advertising, analytics, or tracking cookies. See our Cookie Policy for details.",
        },
        {
          heading: "7. Children's Privacy",
          body: "CratePrep is not directed at children under 16, and we do not knowingly collect personal information from anyone under 16. If you believe a child has provided us with personal information, contact us and we'll delete it.",
        },
        {
          heading: "8. Changes to This Policy",
          body: "We may update this Privacy Policy from time to time. If we make material changes, we'll post a notice in the app before they take effect.",
        },
        {
          heading: "9. Contact",
          body: "Questions about this policy? Reach us through the \"Contact Support\" option available from the \"?\" button on any page.",
        },
      ]}
    />
  )
}
