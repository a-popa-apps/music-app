import { useEffect, useState } from "react"
import { useAuth } from "../hooks/useAuth"
import { ApiError, getMyInvites, sendInvite, type Invite } from "../services/api"
import { Modal } from "./Modal"

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

export function InviteModal({ onClose }: { onClose: () => void }) {
  const { user } = useAuth()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [justSent, setJustSent] = useState(false)
  const [invites, setInvites] = useState<Invite[] | null>(null)

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
      loadInvites()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't send invite. Try again.")
    } finally {
      setSending(false)
    }
  }

  return (
    <Modal title="Invite a friend" onClose={onClose}>
      <p className="mb-4 text-body-sm text-on-surface-variant">
        Know a DJ who'd like CratePrep? Send them an invite -- they'll get the
        same free trial as anyone else who signs up.
      </p>
      <div className="flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-body-sm font-semibold text-on-surface">Name (optional)</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Their name"
            className="rounded border border-outline-variant bg-surface px-3 py-2 text-body-md text-on-surface"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-body-sm font-semibold text-on-surface">Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="friend@example.com"
            className="rounded border border-outline-variant bg-surface px-3 py-2 text-body-md text-on-surface"
          />
        </label>
        {error && <p className="text-body-sm text-red-600">{error}</p>}
        {justSent && !error && <p className="text-body-sm text-green-700">Invite sent!</p>}
        <button
          onClick={handleSend}
          disabled={sending || !email.trim()}
          className="mt-1 rounded-full bg-secondary-container px-6 py-2 text-body-md font-semibold text-on-primary disabled:opacity-50"
        >
          {sending ? "Sending..." : "Send invite"}
        </button>
      </div>

      {invites && invites.length > 0 && (
        <div className="mt-6 border-t border-outline-variant pt-4">
          <h3 className="mb-2 text-body-sm font-semibold text-on-surface">Invites you've sent</h3>
          <div className="flex max-h-40 flex-col gap-2 overflow-y-auto">
            {invites.map((invite) => (
              <div key={invite.invite_id} className="flex items-center justify-between text-body-sm">
                <span className="truncate text-on-surface-variant">{invite.name || invite.email}</span>
                <span className="shrink-0 pl-2 text-on-surface-variant/70">
                  {STATUS_LABELS[invite.status]}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Modal>
  )
}
