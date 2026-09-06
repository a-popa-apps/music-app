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
          body: "TODO: document any cookies/local storage used (e.g. Firebase Auth's session persistence) once finalized.",
        },
        {
          heading: "7. Children's Privacy",
          body: "TODO: standard children's-privacy language, reviewed by a lawyer before launch.",
        },
        {
          heading: "8. Changes to This Policy",
          body: "TODO: how and when this policy may be updated, and how users are notified.",
        },
        {
          heading: "9. Contact",
          body: "TODO: a real contact email or address.",
        },
      ]}
    />
  )
}
