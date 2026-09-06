import { useRef, useState } from "react"
import { useAuth } from "../hooks/useAuth"
import { useClickOutside } from "../hooks/useClickOutside"
import { Modal } from "./Modal"
import { submitFeedback } from "../services/api"

type ActiveModal = "support" | "feedback" | null

function FeedbackForm({
  category,
  onClose,
}: {
  category: "support" | "feedback"
  onClose: () => void
}) {
  const { user } = useAuth()
  const [subject, setSubject] = useState("")
  const [message, setMessage] = useState("")
  const [email, setEmail] = useState(user?.email ?? "")
  const [website, setWebsite] = useState("") // honeypot -- real users never see this field
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formRenderedAt] = useState(() => Date.now())

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const idToken = user ? await user.getIdToken() : undefined
      await submitFeedback(category, message, {
        email: email || undefined,
        subject: category === "support" ? subject || undefined : undefined,
        idToken,
        website: website || undefined,
        formRenderedAt,
      })
      setDone(true)
      setTimeout(onClose, 2000)
    } catch {
      setError("Couldn't submit. Please try again.")
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <div className="flex flex-col items-center gap-2 py-4 text-center">
        <span className="material-symbols-outlined text-[40px] text-green-600">check_circle</span>
        <p className="text-body-md text-on-surface">Thanks! We'll be in touch.</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {/* Honeypot -- hidden from real users (off-screen, unreachable by tab,
          skipped by screen readers), but a bot filling every input blindly
          will fill this too. Any non-empty value here silently discards the
          submission server-side without erroring, so a bot never learns why. */}
      <div className="absolute -left-[9999px]" aria-hidden="true">
        <label>
          Website
          <input
            type="text"
            name="website"
            tabIndex={-1}
            autoComplete="off"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
          />
        </label>
      </div>
      {category === "support" && (
        <label className="flex flex-col gap-1">
          <span className="text-body-sm font-semibold text-on-surface">Subject</span>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-3 text-body-md text-on-surface outline-none focus:border-secondary-container"
          />
        </label>
      )}
      <label className="flex flex-col gap-1">
        <span className="text-body-sm font-semibold text-on-surface">
          {category === "support" ? "How can we help?" : "Your feedback"}
        </span>
        <textarea
          required
          rows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-3 text-body-md text-on-surface outline-none focus:border-secondary-container"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-body-sm font-semibold text-on-surface">
          Email {category === "feedback" && "(optional)"}
        </span>
        <input
          type="email"
          required={category === "support"}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-3 text-body-md text-on-surface outline-none focus:border-secondary-container"
        />
      </label>
      {error && <p className="text-body-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {submitting ? "Sending..." : "Send"}
      </button>
    </form>
  )
}

export function FeedbackWidget() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeModal, setActiveModal] = useState<ActiveModal>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  useClickOutside(containerRef, () => setMenuOpen(false), menuOpen)

  return (
    <>
      <div className="fixed bottom-6 right-6 z-50" ref={containerRef}>
        {menuOpen && (
          <div className="absolute bottom-14 right-0 w-56 rounded bg-inverse-surface p-2 shadow-md">
            <button
              onClick={() => {
                setActiveModal("support")
                setMenuOpen(false)
              }}
              className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-body-md text-inverse-on-surface hover:bg-white/10"
            >
              <span className="material-symbols-outlined text-[18px]">support_agent</span>
              Contact Support
            </button>
            <button
              onClick={() => {
                setActiveModal("feedback")
                setMenuOpen(false)
              }}
              className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-body-md text-inverse-on-surface hover:bg-white/10"
            >
              <span className="material-symbols-outlined text-[18px]">chat_bubble</span>
              Give Feedback
            </button>
          </div>
        )}
        <button
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Help and feedback"
          className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary-container text-on-primary shadow-[0_4px_16px_rgba(0,0,0,0.3)] transition-transform hover:scale-105"
        >
          <span className="material-symbols-outlined text-[24px]">
            {menuOpen ? "close" : "help"}
          </span>
        </button>
      </div>

      {activeModal === "support" && (
        <Modal title="Contact Support" onClose={() => setActiveModal(null)}>
          <FeedbackForm category="support" onClose={() => setActiveModal(null)} />
        </Modal>
      )}
      {activeModal === "feedback" && (
        <Modal title="Give Feedback" onClose={() => setActiveModal(null)}>
          <FeedbackForm category="feedback" onClose={() => setActiveModal(null)} />
        </Modal>
      )}
    </>
  )
}
