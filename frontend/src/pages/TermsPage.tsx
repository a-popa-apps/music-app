import { LegalPage } from "./LegalPage"

export function TermsPage() {
  return (
    <LegalPage
      title="Terms and Conditions"
      sections={[
        {
          heading: "1. Acceptance of Terms",
          body: "By creating an account or using CratePrep, you agree to these Terms and our Privacy Policy. If you don't agree to them, please don't use the service.",
        },
        {
          heading: "2. Description of Service",
          body: "CratePrep processes audio files you upload to detect BPM, musical key, and genre, cleans up filenames, embeds the detected metadata as tags, and returns a ZIP archive for download.",
        },
        {
          heading: "3. Accounts",
          body: "Creating an account requires a valid email address and password, or signing in with Google. You're responsible for keeping your account credentials secure. You can permanently delete your account and all associated data at any time from Profile Details.",
        },
        {
          heading: "4. Acceptable Use",
          body: "You agree not to: upload audio you don't have the rights to use or process; attempt to disrupt, overload, or gain unauthorized access to the service or its infrastructure; use the service to violate any applicable law; or resell or redistribute access to the service without our permission. We may suspend or terminate accounts that violate this policy.",
        },
        {
          heading: "5. Your Content",
          body: "You retain all rights to audio files you upload. Files are processed for the duration of a single request and are not stored on our servers afterward.",
        },
        {
          heading: "6. Disclaimers and Limitation of Liability",
          body: "CratePrep is provided \"as is\" and \"as available,\" without warranties of any kind, express or implied, including as to the accuracy of detected BPM, key, genre, or energy metadata. To the fullest extent permitted by law, CratePrep and its operators are not liable for any indirect, incidental, or consequential damages arising from your use of the service, including loss of data or files. Our total liability for any claim relating to the service is limited to the amount you paid us in the 12 months before the claim arose.",
        },
        {
          heading: "7. Changes to These Terms",
          body: "We may update these Terms from time to time. If we make material changes, we'll post a notice in the app before they take effect. Continuing to use the service after changes take effect means you accept the updated Terms.",
        },
        {
          heading: "8. Contact",
          body: "Questions about these Terms? Reach us through the \"Contact Support\" option available from the \"?\" button on any page.",
        },
      ]}
    />
  )
}
