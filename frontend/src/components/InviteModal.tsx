import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { useAuth } from "../hooks/useAuth"
import { ApiError, getMyInvites, sendInvite, type Invite } from "../services/api"
import { trackEvent } from "../utils/analytics"
import { useEscapeKey } from "../hooks/useEscapeKey"

// Deliberately collapses "existing_user" into the same "Sent" label as
// "pending" -- the whole point of that status server-side is to avoid
// emailing someone who already has an account, but showing the sender a
// visibly different status for it would turn "invite a friend" into a way
// to check whether an arbitrary email is already registered, one probe at
// a time. Only the admin table (not user-facing) needs the real distinction.
const STATUS_LABELS: Record<Invite["status"], string> = {
  pending: "Sent",
  existing_user: "Sent",
  accepted: "Joined!",
  revoked: "Revoked",
  expired: "Expired",
}

// Same shell as AuthModal.tsx -- dark, translucent, backdrop-blurred, and
// rendered via a portal for the same reason AuthModal is: AccountMenu (this
// modal's only caller) lives inside Header, which has its own
// backdrop-blur-* and so establishes a containing block for `fixed`
// descendants -- a plain nested `fixed inset-0` here would size itself
// against the header bar instead of the viewport, not cover the screen.
export function InviteModal({ onClose }: { onClose: () => void }) {
  const { user } = useAuth()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [justSent, setJustSent] = useState(false)
  const [invites, setInvites] = useState<Invite[] | null>(null)

  useEscapeKey(onClose, true)

  async function loadInvites() {
    if (!user) return
    try {
      const token = await user.getIdToken()
      setInvites(await getMyInvites(token))
    } catch {
      // Best-effort -- sending an invite still works even if this list fails to load.
    }
  }

  useEffect(() => {
    loadInvites()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleSend() {
    if (!user || !email.trim()) return
    setSending(true)
    setError(null)
    setJustSent(false)
    try {
      const token = await user.getIdToken()
      await sendInvite(token, email.trim(), name.trim() || undefined)
      setName("")
      setEmail("")
      setJustSent(true)
      trackEvent("invite_sent")
      loadInvites()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't send invite. Try again.")
    } finally {
      setSending(false)
    }
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-md rounded border border-white/10 bg-[#12122a]/95 p-8 shadow-[0_20px_60px_rgba(0,0,0,0.5)] backdrop-blur-md"
      >
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-white/60 transition-colors hover:bg-white/10 hover:text-white"
        >
          <span className="material-symbols-outlined text-[20px]" aria-hidden="true">close</span>
        </button>

        <h2 className="mb-2 text-headline-sm font-bold text-white">Invite a friend</h2>
        <p className="mb-6 text-body-sm text-white/70">
          Know a DJ who'd like CratePrep? Send them an invite -- they'll get
          the same free trial as anyone else who signs up.
        </p>

        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-white">Name (optional)</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Their name"
              className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none placeholder:text-white/30 focus-visible:border-secondary-container"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-white">Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="friend@example.com"
              className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none placeholder:text-white/30 focus-visible:border-secondary-container"
            />
          </label>
          {error && <p className="text-body-sm text-red-400">{error}</p>}
          {justSent && !error && <p className="text-body-sm text-green-400">Invite sent!</p>}
          <button
            onClick={handleSend}
            disabled={sending || !email.trim()}
            className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {sending ? "Sending…" : "Send invite"}
          </button>
        </div>

        {invites && invites.length > 0 && (
          <div className="mt-6 border-t border-white/10 pt-4">
            <h3 className="mb-2 text-body-sm font-semibold text-white">Invites you've sent</h3>
            <div className="flex max-h-40 flex-col gap-2 overflow-y-auto">
              {invites.map((invite) => (
                <div key={invite.invite_id} className="flex items-center justify-between text-body-sm">
                  <span className="truncate text-white/70">{invite.name || invite.email}</span>
                  <span className="shrink-0 pl-2 text-white/50">{STATUS_LABELS[invite.status]}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}
