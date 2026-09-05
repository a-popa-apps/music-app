import { LegalPage } from "./LegalPage"

export function TermsPage() {
  return (
    <LegalPage
      title="Terms and Conditions"
      sections={[
        {
          heading: "1. Acceptance of Terms",
          body: "TODO: standard acceptance-of-terms language, reviewed by a lawyer before launch.",
        },
        {
          heading: "2. Description of Service",
          body: "Quickie processes audio files you upload to detect BPM, musical key, and genre, cleans up filenames, embeds the detected metadata as tags, and returns a ZIP archive for download.",
        },
        {
          heading: "3. Accounts",
          body: "Creating an account requires a valid email address and password, or signing in with Google. You're responsible for keeping your account credentials secure. You can permanently delete your account and all associated data at any time from Profile Details.",
        },
        {
          heading: "4. Acceptable Use",
          body: "TODO: define prohibited uses (e.g. uploading content you don't have rights to, abuse of the service, etc.).",
        },
        {
          heading: "5. Your Content",
          body: "You retain all rights to audio files you upload. Files are processed for the duration of a single request and are not stored on our servers afterward.",
        },
        {
          heading: "6. Disclaimers and Limitation of Liability",
          body: "TODO: standard disclaimer/liability limitation language, reviewed by a lawyer before launch.",
        },
        {
          heading: "7. Changes to These Terms",
          body: "TODO: how and when these terms may be updated, and how users are notified.",
        },
        {
          heading: "8. Contact",
          body: "TODO: a real contact email or address.",
        },
      ]}
    />
  )
}
