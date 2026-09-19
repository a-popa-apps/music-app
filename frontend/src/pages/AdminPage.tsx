import { useCallback, useEffect, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Header } from "../components/Header"
import { useAuth } from "../hooks/useAuth"
import { useIsAdmin } from "../hooks/useIsAdmin"
import {
  createAdminInvite,
  createDiscountCode,
  deleteFeedback,
  deleteFeedbackBatch,
  deleteUserAsAdmin,
  getAdminInvites,
  getAdminStats,
  getAdminUsers,
  getBillingStats,
  getDiscountCodes,
  getFeedback,
  revokeInvite,
  setDiscountCodeActive,
  setFeedbackRead,
  setUserAdmin,
  setUserPlan,
  summarizeFeedback,
  type AdminStats,
  type AdminUser,
  type BillingStats,
  type DiscountCode,
  type FeedbackSubmission,
  type Invite,
} from "../services/api"

const TABS = ["Stats", "Users", "Discounts", "Billing", "Feedback", "Invites"] as const
type Tab = (typeof TABS)[number]

const PERCENT_OPTIONS = [25, 50, 75, 100]

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-4 rounded border border-white/10 bg-white/10 p-6 backdrop-blur-md">
      {children}
    </div>
  )
}

function UsersTab({
  token,
  currentUid,
  users,
  error,
  onReload,
}: {
  token: string
  currentUid: string
  users: AdminUser[] | null
  error: string | null
  onReload: () => void
}) {
  const navigate = useNavigate()
  const [busyUid, setBusyUid] = useState<string | null>(null)
  const [search, setSearch] = useState("")

  async function handlePlanChange(uid: string, plan: "free" | "pro") {
    setBusyUid(uid)
    try {
      await setUserPlan(token, uid, plan)
      onReload()
    } catch {
      // surfaced via the shared `error` prop on next reload
    } finally {
      setBusyUid(null)
    }
  }

  async function handleAdminToggle(uid: string, isAdmin: boolean) {
    if (uid === currentUid && !isAdmin) {
      const confirmed = window.confirm(
        "This removes your own admin access. You'll lose access to this page. Continue?"
      )
      if (!confirmed) return
    }
    setBusyUid(uid)
    try {
      await setUserAdmin(token, uid, isAdmin)
      onReload()
    } finally {
      setBusyUid(null)
    }
  }

  async function handleDelete(user: AdminUser) {
    const confirmed = window.confirm(
      `Delete ${user.email ?? user.uid}? This permanently removes their account and cannot be undone.`
    )
    if (!confirmed) return
    setBusyUid(user.uid)
    try {
      await deleteUserAsAdmin(token, user.uid)
      onReload()
    } finally {
      setBusyUid(null)
    }
  }

  if (error) return <p role="alert" className="text-body-sm text-red-400">{error}</p>
  if (!users) return <p className="text-body-md text-white/60">Loading…</p>

  const query = search.trim().toLowerCase()
  const visible = query
    ? users.filter((u) =>
        [u.name, u.artist_name, u.email].some((f) => f?.toLowerCase().includes(query))
      )
    : users

  return (
    <Card>
      <input
        type="text"
        name="user-search"
        autoComplete="off"
        aria-label="Search users by name or email"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by name or email…"
        className="rounded border border-white/20 bg-white/5 px-4 py-2 text-body-md text-white outline-none placeholder:text-white/40 focus-visible:border-secondary-container"
      />
      <div className="overflow-x-auto">
        <table className="w-full text-left text-body-sm">
          <thead>
            <tr className="border-b border-white/10 text-white/60">
              <th className="py-2 pr-4">Name</th>
              <th className="py-2 pr-4">Email</th>
              <th className="py-2 pr-4">Plan</th>
              <th className="py-2 pr-4">Admin</th>
              <th className="py-2 pr-4"></th>
            </tr>
          </thead>
          <tbody>
            {visible.map((u) => (
              <tr
                key={u.uid}
                onClick={() => navigate(`/admin/users/${u.uid}`)}
                className="cursor-pointer border-b border-white/10 hover:bg-white/5"
              >
                <td className="py-2 pr-4 text-white">{u.name || u.artist_name || "—"}</td>
                <td className="py-2 pr-4 text-white/60">{u.email}</td>
                <td className="py-2 pr-4" onClick={(e) => e.stopPropagation()}>
                  <select
                    aria-label={`Plan for ${u.email ?? u.uid}`}
                    value={u.plan}
                    disabled={busyUid === u.uid}
                    onChange={(e) => handlePlanChange(u.uid, e.target.value as "free" | "pro")}
                    className="rounded border border-white/20 bg-white/5 px-2 py-1 text-body-sm text-white"
                  >
                    <option value="free">Free</option>
                    <option value="pro">Pro</option>
                  </select>
                </td>
                <td className="py-2 pr-4" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={u.is_admin}
                    aria-label={`Admin access for ${u.email ?? u.uid}`}
                    disabled={busyUid === u.uid}
                    onClick={() => handleAdminToggle(u.uid, !u.is_admin)}
                    className={`h-6 w-11 rounded-full transition-colors ${
                      u.is_admin ? "bg-secondary-container" : "bg-white/20"
                    }`}
                  >
                    <span
                      className={`block h-5 w-5 rounded-full bg-white transition-transform ${
                        u.is_admin ? "translate-x-5" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </td>
                <td className="py-2 pr-4" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleDelete(u)}
                    disabled={busyUid === u.uid}
                    className="rounded-full border border-red-400 px-3 py-1 text-body-sm font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {visible.length === 0 && (
          <p className="py-6 text-center text-body-md text-white/60">
            No users match your search.
          </p>
        )}
      </div>
    </Card>
  )
}

function AiUsageCard({ callsToday, dailyLimit }: { callsToday: number; dailyLimit: number }) {
  const ratio = dailyLimit > 0 ? callsToday / dailyLimit : 0
  const exhausted = ratio >= 1
  const nearLimit = !exhausted && ratio >= 0.8

  const barColor = exhausted ? "bg-red-500" : nearLimit ? "bg-amber-400" : "bg-secondary-container"
  const textColor = exhausted ? "text-red-400" : nearLimit ? "text-amber-400" : "text-white"

  return (
    <Card>
      <div className="flex items-center justify-between">
        <h3 className="text-headline-sm text-white">AI Calls Today</h3>
        <span className={`text-body-sm font-semibold ${textColor}`}>
          {exhausted ? "Budget exhausted" : nearLimit ? "Approaching limit" : "Healthy"}
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-headline-lg ${textColor}`}>{callsToday}</span>
        <span className="text-body-sm text-white/60">/ {dailyLimit} today</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full ${barColor}`}
          style={{ width: `${Math.min(ratio, 1) * 100}%` }}
        />
      </div>
      {(exhausted || nearLimit) && (
        <p className="text-body-sm text-white/60">
          Filename cleanup, batch summaries, and feedback triage share this cap.
          {exhausted
            ? " They're sitting out for the rest of the day; an alert email has been sent."
            : " Getting close to today's cap."}
        </p>
      )}
    </Card>
  )
}

function StatsTab({ stats, error }: { stats: AdminStats | null; error: string | null }) {
  if (error) return <p role="alert" className="text-body-sm text-red-400">{error}</p>
  if (!stats) return <p className="text-body-md text-white/60">Loading…</p>

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <span className="text-body-sm text-white/60">Total users</span>
          <span className="text-headline-lg text-white">{stats.total_users}</span>
        </Card>
        <Card>
          <span className="text-body-sm text-white/60">Free</span>
          <span className="text-headline-lg text-white">{stats.by_plan.free ?? 0}</span>
        </Card>
        <Card>
          <span className="text-body-sm text-white/60">Pro</span>
          <span className="text-headline-lg text-white">{stats.by_plan.pro ?? 0}</span>
        </Card>
        <Card>
          <span className="text-body-sm text-white/60">Admins</span>
          <span className="text-headline-lg text-white">{stats.admin_count}</span>
        </Card>
      </div>

      <AiUsageCard callsToday={stats.ai_calls_today} dailyLimit={stats.ai_daily_limit} />

      <Card>
        <h3 className="text-headline-sm text-white">Recent Signups</h3>
        <ul className="flex flex-col gap-2">
          {stats.recent_signups.map((u) => (
            <li key={u.uid} className="flex justify-between text-body-sm text-white/60">
              <span>{u.email}</span>
              <span>{new Date(u.created_at).toLocaleDateString()}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}

function DiscountCodesTab({
  token,
  codes,
  error,
  onReload,
}: {
  token: string
  codes: DiscountCode[] | null
  error: string | null
  onReload: () => void
}) {
  const [percentOff, setPercentOff] = useState(25)
  const [maxUses, setMaxUses] = useState(1)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  async function handleCreate() {
    setCreating(true)
    setCreateError(null)
    try {
      await createDiscountCode(token, percentOff, maxUses)
      onReload()
    } catch {
      setCreateError("Couldn't create discount code.")
    } finally {
      setCreating(false)
    }
  }

  async function handleToggleActive(code: DiscountCode) {
    try {
      await setDiscountCodeActive(token, code.code, !code.active)
      onReload()
    } catch {
      setCreateError("Couldn't update discount code.")
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <h3 className="text-headline-sm text-white">Generate a Code</h3>
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-white">% off</span>
            <select
              value={percentOff}
              onChange={(e) => setPercentOff(Number(e.target.value))}
              className="rounded border border-white/20 bg-white/5 px-3 py-2 text-body-md text-white"
            >
              {PERCENT_OPTIONS.map((p) => (
                <option key={p} value={p}>
                  {p}%
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-white">Max uses</span>
            <input
              type="number"
              min={1}
              value={maxUses}
              onChange={(e) => setMaxUses(Math.max(1, Number(e.target.value)))}
              className="w-24 rounded border border-white/20 bg-white/5 px-3 py-2 text-body-md text-white"
            />
          </label>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="rounded-full bg-secondary-container px-6 py-2 text-body-md font-semibold text-on-primary disabled:opacity-50"
          >
            {creating ? "Creating…" : "Generate code"}
          </button>
        </div>
        <div aria-live="polite">
          {(createError || error) && (
            <p className="text-body-sm text-red-400">{createError ?? error}</p>
          )}
        </div>
      </Card>

      <Card>
        <h3 className="text-headline-sm text-white">Existing Codes</h3>
        {!codes ? (
          <p className="text-body-md text-white/60">Loading…</p>
        ) : codes.length === 0 ? (
          <p className="text-body-md text-white/60">No discount codes yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-body-sm">
              <thead>
                <tr className="border-b border-white/10 text-white/60">
                  <th className="py-2 pr-4">Code</th>
                  <th className="py-2 pr-4">% off</th>
                  <th className="py-2 pr-4">Uses</th>
                  <th className="py-2 pr-4">Active</th>
                </tr>
              </thead>
              <tbody>
                {codes.map((c) => (
                  <tr key={c.code} className="border-b border-white/10">
                    <td className="py-2 pr-4 font-mono text-white">{c.code}</td>
                    <td className="py-2 pr-4 text-white/60">{c.percent_off}%</td>
                    <td className="py-2 pr-4 text-white/60">
                      {c.used_count} / {c.max_uses}
                    </td>
                    <td className="py-2 pr-4">
                      <button
                        type="button"
                        role="switch"
                        aria-checked={c.active}
                        aria-label={`Active status for code ${c.code}`}
                        onClick={() => handleToggleActive(c)}
                        className={`h-6 w-11 rounded-full transition-colors ${
                          c.active ? "bg-secondary-container" : "bg-white/20"
                        }`}
                      >
                        <span
                          className={`block h-5 w-5 rounded-full bg-white transition-transform ${
                            c.active ? "translate-x-5" : "translate-x-0.5"
                          }`}
                        />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

const INVITE_STATUS_STYLES: Record<Invite["status"], string> = {
  pending: "bg-blue-500/20 text-blue-300",
  accepted: "bg-green-500/20 text-green-300",
  revoked: "bg-white/10 text-white/50",
  expired: "bg-white/10 text-white/50",
  existing_user: "bg-yellow-500/20 text-yellow-300",
}

const INVITE_STATUS_LABELS: Record<Invite["status"], string> = {
  pending: "Pending",
  accepted: "Accepted",
  revoked: "Revoked",
  expired: "Expired",
  existing_user: "Already a member",
}

function InviteStatusBadge({ status }: { status: Invite["status"] }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-body-sm font-semibold ${INVITE_STATUS_STYLES[status]}`}>
      {INVITE_STATUS_LABELS[status]}
    </span>
  )
}

function InvitesTab({
  token,
  invites,
  error,
  onReload,
}: {
  token: string
  invites: Invite[] | null
  error: string | null
  onReload: () => void
}) {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [adminNote, setAdminNote] = useState("")
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)

  async function handleSend() {
    if (!email.trim()) return
    setSending(true)
    setSendError(null)
    try {
      await createAdminInvite(token, email.trim(), name.trim() || undefined, adminNote.trim() || undefined)
      setName("")
      setEmail("")
      setAdminNote("")
      onReload()
    } catch {
      setSendError("Couldn't send invite.")
    } finally {
      setSending(false)
    }
  }

  async function handleRevoke(invite: Invite) {
    try {
      await revokeInvite(token, invite.invite_id)
      onReload()
    } catch {
      setSendError("Couldn't revoke invite.")
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <h3 className="text-headline-sm text-white">Send an Invite</h3>
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-white">Name (optional)</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Sam"
              className="w-48 rounded border border-white/20 bg-white/5 px-3 py-2 text-body-md text-white placeholder:text-white/30"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-white">Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="sam@example.com"
              className="w-64 rounded border border-white/20 bg-white/5 px-3 py-2 text-body-md text-white placeholder:text-white/30"
            />
          </label>
          <button
            onClick={handleSend}
            disabled={sending || !email.trim()}
            className="rounded-full bg-secondary-container px-6 py-2 text-body-md font-semibold text-on-primary disabled:opacity-50"
          >
            {sending ? "Sending…" : "Send invite"}
          </button>
        </div>
        <label className="flex flex-col gap-1">
          <span className="text-body-sm font-semibold text-white">Personal note (optional)</span>
          <textarea
            value={adminNote}
            onChange={(e) => setAdminNote(e.target.value)}
            placeholder="Included as a quoted line in the invite email"
            rows={2}
            className="w-full rounded border border-white/20 bg-white/5 px-3 py-2 text-body-md text-white placeholder:text-white/30"
          />
        </label>
        <div aria-live="polite">
          {sendError && <p className="text-body-sm text-red-400">{sendError}</p>}
        </div>
      </Card>

      <Card>
        <h3 className="text-headline-sm text-white">All Invites</h3>
        {error && !invites ? (
          <p className="text-body-md text-red-400">
            {error}{" "}
            <button onClick={onReload} className="underline hover:text-red-300">
              Retry
            </button>
          </p>
        ) : !invites ? (
          <p className="text-body-md text-white/60">Loading…</p>
        ) : invites.length === 0 ? (
          <p className="text-body-md text-white/60">No invites sent yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-body-sm">
              <thead>
                <tr className="border-b border-white/10 text-white/60">
                  <th className="py-2 pr-4">Recipient</th>
                  <th className="py-2 pr-4">Source</th>
                  <th className="py-2 pr-4">Sent by</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Sent</th>
                  <th className="py-2 pr-4"></th>
                </tr>
              </thead>
              <tbody>
                {invites.map((invite) => (
                  <tr key={invite.invite_id} className="border-b border-white/10">
                    <td className="py-2 pr-4 text-white">
                      {invite.name ? `${invite.name} ` : ""}
                      <span className="text-white/60">{invite.email}</span>
                    </td>
                    <td className="py-2 pr-4">
                      <span
                        className={`rounded-full px-2.5 py-1 text-body-sm font-semibold ${
                          invite.source === "admin" ? "bg-secondary-container/20 text-secondary-container" : "bg-white/10 text-white/70"
                        }`}
                      >
                        {invite.source === "admin" ? "Admin" : "Referral"}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-white/60">{invite.invited_by_email}</td>
                    <td className="py-2 pr-4">
                      <InviteStatusBadge status={invite.status} />
                    </td>
                    <td className="py-2 pr-4 text-white/60">
                      {new Date(invite.sent_at).toLocaleDateString()}
                    </td>
                    <td className="py-2 pr-4">
                      {invite.status === "pending" && (
                        <button
                          onClick={() => handleRevoke(invite)}
                          className="text-body-sm font-semibold text-red-400 hover:text-red-300"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD",
})

function formatCents(cents: number): string {
  return CURRENCY_FORMATTER.format(cents / 100)
}

function BillingTab({
  stats,
  billing,
  codes,
  error,
}: {
  stats: AdminStats | null
  billing: BillingStats | null
  codes: DiscountCode[] | null
  error: string | null
}) {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <span className="text-body-sm text-white/60">MRR</span>
          <span className="text-headline-lg text-white">
            {billing ? formatCents(billing.mrr_cents) : "—"}
          </span>
        </Card>
        <Card>
          <span className="text-body-sm text-white/60">Active subscribers</span>
          <span className="text-headline-lg text-white">
            {billing?.active_subscribers ?? "—"}
          </span>
        </Card>
        <Card>
          <span className="text-body-sm text-white/60">Trialing</span>
          <span className="text-headline-lg text-white">
            {billing?.trialing_subscribers ?? "—"}
          </span>
        </Card>
        <Card>
          <span className="text-body-sm text-white/60">Canceled (30d)</span>
          <span className="text-headline-lg text-white">
            {billing?.canceled_last_30_days ?? "—"}
          </span>
        </Card>
      </div>

      <Card>
        <span className="text-body-sm text-white/60">
          Revenue collected, last 30 days
        </span>
        <span className="text-headline-lg text-white">
          {billing ? formatCents(billing.revenue_last_30_days_cents) : "—"}
        </span>
      </Card>

      {error && <p className="text-body-sm text-red-400">{error}</p>}

      {stats && (
        <Card>
          <h3 className="text-headline-sm text-white">Signups by Plan</h3>
          <div className="flex gap-6 text-body-md text-white">
            <span>Free: {stats.by_plan.free ?? 0}</span>
            <span>Pro: {stats.by_plan.pro ?? 0}</span>
          </div>
        </Card>
      )}

      <Card>
        <h3 className="text-headline-sm text-white">Discount Code Usage</h3>
        {!codes ? (
          <p className="text-body-md text-white/60">Loading…</p>
        ) : codes.length === 0 ? (
          <p className="text-body-md text-white/60">No discount codes yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-body-sm">
              <thead>
                <tr className="border-b border-white/10 text-white/60">
                  <th className="py-2 pr-4">Code</th>
                  <th className="py-2 pr-4">% off</th>
                  <th className="py-2 pr-4">Used</th>
                  <th className="py-2 pr-4">Active</th>
                </tr>
              </thead>
              <tbody>
                {codes.map((c) => (
                  <tr key={c.code} className="border-b border-white/10">
                    <td className="py-2 pr-4 font-mono text-white">{c.code}</td>
                    <td className="py-2 pr-4 text-white/60">{c.percent_off}%</td>
                    <td className="py-2 pr-4 text-white/60">
                      {c.used_count} / {c.max_uses}
                    </td>
                    <td className="py-2 pr-4 text-white/60">
                      {c.active ? "Yes" : "No"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

function FeedbackTab({
  token,
  feedback,
  error,
  onReload,
}: {
  token: string
  feedback: FeedbackSubmission[] | null
  error: string | null
  onReload: () => void
}) {
  const [busyId, setBusyId] = useState<string | null>(null)
  // undefined = never requested, null = requested but nothing came back
  // (e.g. AI not configured), string = an actual summary.
  const [aiSummary, setAiSummary] = useState<string | null | undefined>(undefined)
  const [summarizing, setSummarizing] = useState(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  async function handleToggleRead(f: FeedbackSubmission) {
    setBusyId(f.feedback_id)
    try {
      await setFeedbackRead(token, f.feedback_id, !f.read)
      onReload()
    } finally {
      setBusyId(null)
    }
  }

  async function handleSummarize() {
    setSummarizing(true)
    setSummaryError(null)
    try {
      const { summary } = await summarizeFeedback(token)
      setAiSummary(summary)
    } catch {
      setSummaryError("Couldn't generate a summary.")
    } finally {
      setSummarizing(false)
    }
  }

  function toggleSelected(feedbackId: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(feedbackId)) next.delete(feedbackId)
      else next.add(feedbackId)
      return next
    })
  }

  function toggleSelectAll() {
    if (!feedback) return
    setSelected((prev) => (prev.size === feedback.length ? new Set() : new Set(feedback.map((f) => f.feedback_id))))
  }

  async function handleDelete(f: FeedbackSubmission) {
    const confirmed = window.confirm("Delete this submission? This cannot be undone.")
    if (!confirmed) return
    setDeleteError(null)
    setBusyId(f.feedback_id)
    try {
      await deleteFeedback(token, f.feedback_id)
      setSelected((prev) => {
        const next = new Set(prev)
        next.delete(f.feedback_id)
        return next
      })
      onReload()
    } catch {
      setDeleteError("Couldn't delete that submission.")
    } finally {
      setBusyId(null)
    }
  }

  async function handleBulkDelete() {
    const count = selected.size
    const confirmed = window.confirm(
      `Delete ${count} submission${count === 1 ? "" : "s"}? This cannot be undone.`
    )
    if (!confirmed) return
    setDeleteError(null)
    setBulkDeleting(true)
    try {
      await deleteFeedbackBatch(token, [...selected])
      setSelected(new Set())
      onReload()
    } catch {
      setDeleteError("Couldn't delete the selected submissions.")
    } finally {
      setBulkDeleting(false)
    }
  }

  if (error) return <p role="alert" className="text-body-sm text-red-400">{error}</p>
  if (!feedback) return <p className="text-body-md text-white/60">Loading…</p>

  const unreadCount = feedback.filter((f) => !f.read).length
  const allSelected = feedback.length > 0 && selected.size === feedback.length

  return (
    <div className="flex flex-col gap-4">
      {unreadCount > 0 && (
        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2 text-body-sm text-white/70">
              <span className="material-symbols-outlined text-[18px] text-secondary-container" aria-hidden="true">
                auto_awesome
              </span>
              {aiSummary === undefined && (
                <span>
                  {unreadCount} unread submission{unreadCount === 1 ? "" : "s"} — summarize with AI
                  to triage quickly.
                </span>
              )}
              {aiSummary === null && (
                <span>No summary available right now (AI may not be configured).</span>
              )}
              {aiSummary && <span className="text-white">{aiSummary}</span>}
            </div>
            <button
              type="button"
              onClick={handleSummarize}
              disabled={summarizing}
              className="whitespace-nowrap rounded-full border border-white/20 bg-white/10 px-4 py-2 text-body-sm font-semibold text-white transition-colors hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {summarizing ? "Summarizing…" : aiSummary ? "Re-summarize" : "Summarize unread"}
            </button>
          </div>
          <div aria-live="polite">
            {summaryError && <p className="mt-2 text-body-sm text-red-400">{summaryError}</p>}
          </div>
        </Card>
      )}

      <div aria-live="polite">
        {deleteError && <p className="text-body-sm text-red-400">{deleteError}</p>}
      </div>

      {selected.size > 0 && (
        <div className="flex items-center justify-between rounded border border-red-400/40 bg-red-500/10 px-4 py-3">
          <span className="text-body-sm text-white/80">
            {selected.size} selected
          </span>
          <button
            type="button"
            onClick={handleBulkDelete}
            disabled={bulkDeleting}
            className="rounded-full border border-red-400 px-4 py-1.5 text-body-sm font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
          >
            {bulkDeleting ? "Deleting…" : `Delete selected (${selected.size})`}
          </button>
        </div>
      )}

      <Card>
      {feedback.length === 0 ? (
        <p className="text-body-md text-white/60">No submissions yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-body-sm">
            <thead>
              <tr className="border-b border-white/10 text-white/60">
                <th className="py-2 pr-4">
                  <input
                    type="checkbox"
                    aria-label="Select all"
                    checked={allSelected}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 rounded border-white/30 bg-transparent accent-secondary-container"
                  />
                </th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Subject / Message</th>
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Read</th>
                <th className="py-2 pr-4"></th>
              </tr>
            </thead>
            <tbody>
              {feedback.map((f) => (
                <tr
                  key={f.feedback_id}
                  className={`border-b border-white/10 ${f.read ? "" : "bg-secondary-container/10"}`}
                >
                  <td className="py-2 pr-4">
                    <input
                      type="checkbox"
                      aria-label={`Select submission from ${f.email || "anonymous"}`}
                      checked={selected.has(f.feedback_id)}
                      onChange={() => toggleSelected(f.feedback_id)}
                      className="h-4 w-4 rounded border-white/30 bg-transparent accent-secondary-container"
                    />
                  </td>
                  <td className="py-2 pr-4 text-white/60">
                    {f.category === "support" ? "Support" : "Feedback"}
                  </td>
                  <td className="py-2 pr-4 text-white">
                    {f.subject && <div className="font-semibold">{f.subject}</div>}
                    <div className="max-w-md truncate text-white/60">{f.message}</div>
                  </td>
                  <td className="py-2 pr-4 text-white/60">{f.email || "—"}</td>
                  <td className="py-2 pr-4 text-white/60">
                    {new Date(f.submitted_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 pr-4">
                    <button
                      type="button"
                      role="switch"
                      aria-checked={f.read}
                      aria-label={`Read status for feedback from ${f.email || "anonymous"}`}
                      disabled={busyId === f.feedback_id}
                      onClick={() => handleToggleRead(f)}
                      className={`h-6 w-11 rounded-full transition-colors ${
                        f.read ? "bg-secondary-container" : "bg-white/20"
                      }`}
                    >
                      <span
                        className={`block h-5 w-5 rounded-full bg-white transition-transform ${
                          f.read ? "translate-x-5" : "translate-x-0.5"
                        }`}
                      />
                    </button>
                  </td>
                  <td className="py-2 pr-4">
                    <button
                      type="button"
                      onClick={() => handleDelete(f)}
                      disabled={busyId === f.feedback_id}
                      className="rounded-full border border-red-400 px-3 py-1 text-body-sm font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      </Card>
    </div>
  )
}

export function AdminPage() {
  const { user, isVerified, loading: authLoading } = useAuth()
  const { isAdmin, loading: adminLoading } = useIsAdmin()
  const [tab, setTab] = useState<Tab>("Stats")
  const [token, setToken] = useState<string | null>(null)

  // Fetched once per admin session and shared across tabs instead of each
  // tab re-fetching on every switch -- list_discount_codes() makes one live
  // Stripe API call per code, and list_users()/getAdminStats() does one
  // Firestore read per registered user, so repeat fetches for unchanged
  // data were pure waste.
  const [users, setUsers] = useState<AdminUser[] | null>(null)
  const [usersError, setUsersError] = useState<string | null>(null)
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [statsError, setStatsError] = useState<string | null>(null)
  const [billing, setBilling] = useState<BillingStats | null>(null)
  const [billingError, setBillingError] = useState<string | null>(null)
  const [codes, setCodes] = useState<DiscountCode[] | null>(null)
  const [codesError, setCodesError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<FeedbackSubmission[] | null>(null)
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [invites, setInvites] = useState<Invite[] | null>(null)
  const [invitesError, setInvitesError] = useState<string | null>(null)

  const reloadUsers = useCallback(async () => {
    if (!token) return
    try {
      setUsers(await getAdminUsers(token))
      setUsersError(null)
    } catch {
      setUsersError("Couldn't load users.")
    }
  }, [token])

  const reloadStats = useCallback(async () => {
    if (!token) return
    try {
      setStats(await getAdminStats(token))
      setStatsError(null)
    } catch {
      setStatsError("Couldn't load stats.")
    }
  }, [token])

  const reloadBilling = useCallback(async () => {
    if (!token) return
    try {
      setBilling(await getBillingStats(token))
      setBillingError(null)
    } catch {
      setBillingError("Couldn't load billing stats. Is Stripe configured?")
    }
  }, [token])

  const reloadCodes = useCallback(async () => {
    if (!token) return
    try {
      setCodes(await getDiscountCodes(token))
      setCodesError(null)
    } catch {
      setCodesError("Couldn't load discount codes.")
    }
  }, [token])

  const reloadFeedback = useCallback(async () => {
    if (!token) return
    try {
      setFeedback(await getFeedback(token))
      setFeedbackError(null)
    } catch {
      setFeedbackError("Couldn't load feedback.")
    }
  }, [token])

  const reloadInvites = useCallback(async () => {
    if (!token) return
    try {
      setInvites(await getAdminInvites(token))
      setInvitesError(null)
    } catch {
      setInvitesError("Couldn't load invites.")
    }
  }, [token])

  useEffect(() => {
    if (user) user.getIdToken().then(setToken)
  }, [user])

  useEffect(() => {
    if (!token) return
    reloadUsers()
    reloadStats()
    reloadBilling()
    reloadCodes()
    reloadFeedback()
    reloadInvites()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const unreadFeedbackCount = feedback?.filter((f) => !f.read).length ?? 0

  if (!authLoading && (!user || !isVerified)) {
    return <Navigate to="/auth" replace />
  }

  if (authLoading || adminLoading || !token) {
    return (
      <>
        <Header dark />
        <div className="flex min-h-screen items-center justify-center bg-black pt-16">
          <p className="text-body-md text-white/60">Loading…</p>
        </div>
      </>
    )
  }

  if (!isAdmin) {
    return (
      <>
        <Header dark />
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-black px-4 pt-16 text-center">
          <p className="text-headline-sm text-white">Not authorized</p>
          <p className="text-body-md text-white/60">
            You don't have access to the admin area.
          </p>
        </div>
      </>
    )
  }

  return (
    <>
      <Header dark />
      <div className="min-h-screen w-full bg-black py-12 pt-32">
        <div className="mx-auto w-full max-w-7xl px-4 lg:px-12">
          <h1 className="mb-6 text-headline-lg text-white">Admin</h1>

          <div className="mb-6 flex gap-2 border-b border-white/10">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`relative px-4 py-2 text-body-md font-semibold ${
                  tab === t
                    ? "border-b-2 border-secondary-container text-white"
                    : "text-white/60"
                }`}
              >
                {t}
                {t === "Feedback" && unreadFeedbackCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 font-mono text-[11px] font-bold text-white">
                    {unreadFeedbackCount > 99 ? "99+" : unreadFeedbackCount}
                  </span>
                )}
              </button>
            ))}
          </div>

          {tab === "Stats" && <StatsTab stats={stats} error={statsError} />}
          {tab === "Users" && (
            <UsersTab
              token={token}
              currentUid={user!.uid}
              users={users}
              error={usersError}
              onReload={reloadUsers}
            />
          )}
          {tab === "Discounts" && (
            <DiscountCodesTab token={token} codes={codes} error={codesError} onReload={reloadCodes} />
          )}
          {tab === "Billing" && (
            <BillingTab stats={stats} billing={billing} codes={codes} error={billingError} />
          )}
          {tab === "Feedback" && (
            <FeedbackTab
              token={token}
              feedback={feedback}
              error={feedbackError}
              onReload={reloadFeedback}
            />
          )}
          {tab === "Invites" && (
            <InvitesTab token={token} invites={invites} error={invitesError} onReload={reloadInvites} />
          )}
        </div>
      </div>
    </>
  )
}
