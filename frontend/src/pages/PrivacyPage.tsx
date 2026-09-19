import { LegalPage } from "./LegalPage"

export function PrivacyPage() {
  return (
    <LegalPage
      title="Privacy Policy"
      path="/privacy"
      lastUpdated="2026-09-17"
      sections={[
        {
          heading: "1. Information We Collect",
          body: "Your email address (for account creation), and any profile details you choose to provide (name, artist name, country, role, genre preferences, filename template). Audio files you upload are processed in memory for the duration of a single request and are not retained afterward. If you're signed in, we also keep a history of the tracks you've processed — filename, detected BPM/key/genre, and duration — so you can review it later; this history never includes the audio itself. If you use the free trial without an account, we store a one-way hash of your IP address (not the address itself) only to enforce the trial's track limit. If you submit feedback or a support request, we keep the category, message, and email address you provide. If another CratePrep user invites you, we store the email address (and name, if given) they provided in order to send the invitation.",
        },
        {
          heading: "2. How We Use Your Information",
          body: "To provide and personalize the service — for example, applying your saved filename template and preferences when processing your uploads — and to respond to feedback or support requests you send us.",
        },
        {
          heading: "3. Third-Party Services",
          body: "We use Firebase (Google) for account authentication and to store your profile settings. To help detect a track's genre, we send the cleaned artist/title text (never the audio file itself) to several public music catalogs and databases — Spotify, Discogs, iTunes, Deezer, MusicBrainz, TheAudioDB, and Last.fm — trying each in turn until one returns a usable result. If you opt in via our cookie consent banner, we use Google Analytics to understand overall usage (pages visited, features used, and product actions like processing a batch or upgrading) — it doesn't run unless you accept, and never sees your audio files or filenames. If you enable AI-assisted features (filename cleanup, batch summaries, feedback triage), the relevant text is sent to Google's Gemini API to generate that feature's output. Stripe processes payments for Pro subscriptions and never sees your audio files. We use Resend to deliver transactional emails (verification, password reset, receipts, and similar account notices) and Sentry to capture error reports if something breaks, which can include technical request details but never your audio files.",
        },
        {
          heading: "4. Data Retention",
          body: "Uploaded audio is never retained. Account and profile data is kept until you delete your account, which you can do at any time from Profile Details. Processing history (metadata only, never audio) is kept until you clear it from the History page or delete your account. Feedback submissions and invite records are kept for as long as needed to respond to them or track whether an invite was used, and are removed on request.",
        },
        {
          heading: "5. Your Rights",
          body: "You can view and edit your stored profile data at any time from Profile Details, and permanently delete your account and all associated data from the same page. You can also ask us to access, correct, or delete other data we hold about you (such as a feedback submission) by contacting us as described below.",
        },
        {
          heading: "6. Cookies and Local Storage",
          body: "We use strictly necessary cookies and local storage to keep you signed in, via Firebase Authentication. If you accept our cookie consent banner, we also use Google Analytics cookies to understand overall usage — this is entirely optional and off by default until you accept. We don't use any advertising or ad-tracking cookies, and we don't sell or share data with ad networks. See our Cookie Policy for details.",
        },
        {
          heading: "7. Children's Privacy",
          body: "CratePrep is not directed at children under 16, and we do not knowingly collect personal information from anyone under 16. If you believe a child has provided us with personal information, contact us and we'll delete it.",
        },
        {
          heading: "8. Changes to This Policy",
          body: "We may update this Privacy Policy from time to time. If we make material changes, we'll post a notice in the app before they take effect and update the date at the top of this page.",
        },
        {
          heading: "9. Contact",
          body: "Questions about this policy? Reach us through the “Contact Support” option available from the “?” button on any page.",
        },
      ]}
    />
  )
}
