import { useCallback, useEffect, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Header } from "../components/Header"
import { useAuth } from "../hooks/useAuth"
import { useIsAdmin } from "../hooks/useIsAdmin"
import {
  createDiscountCode,
  deleteUserAsAdmin,
  getAdminStats,
  getAdminUsers,
  getBillingStats,
  getDiscountCodes,
  getFeedback,
  setDiscountCodeActive,
  setFeedbackRead,
  setUserAdmin,
  setUserPlan,
  type AdminStats,
  type AdminUser,
  type BillingStats,
  type DiscountCode,
  type FeedbackSubmission,
} from "../services/api"

const TABS = ["Stats", "Users", "Discounts", "Billing", "Feedback"] as const
type Tab = (typeof TABS)[number]

const PERCENT_OPTIONS = [25, 50, 75, 100]

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-4 rounded bg-surface-container-lowest p-6 shadow-sm">
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

  if (error) return <p className="text-body-sm text-red-600">{error}</p>
  if (!users) return <p className="text-body-md text-on-surface-variant">Loading...</p>

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
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by name or email..."
        className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-2 text-body-md text-on-surface outline-none focus:border-secondary-container"
      />
      <div className="overflow-x-auto">
        <table className="w-full text-left text-body-sm">
          <thead>
            <tr className="border-b border-outline-variant text-on-surface-variant">
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
                className="cursor-pointer border-b border-outline-variant/50 hover:bg-surface-container-low"
              >
                <td className="py-2 pr-4 text-on-surface">{u.name || u.artist_name || "—"}</td>
                <td className="py-2 pr-4 text-on-surface-variant">{u.email}</td>
                <td className="py-2 pr-4" onClick={(e) => e.stopPropagation()}>
                  <select
                    value={u.plan}
                    disabled={busyUid === u.uid}
                    onChange={(e) => handlePlanChange(u.uid, e.target.value as "free" | "pro")}
                    className="rounded border border-outline-variant bg-surface-container-lowest px-2 py-1 text-body-sm text-on-surface"
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
                    disabled={busyUid === u.uid}
                    onClick={() => handleAdminToggle(u.uid, !u.is_admin)}
                    className={`h-6 w-11 rounded-full transition-colors ${
                      u.is_admin ? "bg-secondary-container" : "bg-outline-variant"
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
                    className="rounded-full border border-red-600 px-3 py-1 text-body-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {visible.length === 0 && (
          <p className="py-6 text-center text-body-md text-on-surface-variant">
            No users match your search.
          </p>
        )}
      </div>
    </Card>
  )
}

function StatsTab({ stats, error }: { stats: AdminStats | null; error: string | null }) {
  if (error) return <p className="text-body-sm text-red-600">{error}</p>
  if (!stats) return <p className="text-body-md text-on-surface-variant">Loading...</p>

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <span className="text-body-sm text-on-surface-variant">Total users</span>
          <span className="text-headline-lg text-on-surface">{stats.total_users}</span>
        </Card>
        <Card>
          <span className="text-body-sm text-on-surface-variant">Free</span>
          <span className="text-headline-lg text-on-surface">{stats.by_plan.free ?? 0}</span>
        </Card>
        <Card>
          <span className="text-body-sm text-on-surface-variant">Pro</span>
          <span className="text-headline-lg text-on-surface">{stats.by_plan.pro ?? 0}</span>
        </Card>
        <Card>
          <span className="text-body-sm text-on-surface-variant">Admins</span>
          <span className="text-headline-lg text-on-surface">{stats.admin_count}</span>
        </Card>
      </div>

      <Card>
        <h3 className="text-headline-sm text-on-surface">Recent signups</h3>
        <ul className="flex flex-col gap-2">
          {stats.recent_signups.map((u) => (
            <li key={u.uid} className="flex justify-between text-body-sm text-on-surface-variant">
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
        <h3 className="text-headline-sm text-on-surface">Generate a code</h3>
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-on-surface">% off</span>
            <select
              value={percentOff}
              onChange={(e) => setPercentOff(Number(e.target.value))}
              className="rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md text-on-surface"
            >
              {PERCENT_OPTIONS.map((p) => (
                <option key={p} value={p}>
                  {p}%
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-on-surface">Max uses</span>
            <input
              type="number"
              min={1}
              value={maxUses}
              onChange={(e) => setMaxUses(Math.max(1, Number(e.target.value)))}
              className="w-24 rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md text-on-surface"
            />
          </label>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="rounded-full bg-secondary-container px-6 py-2 text-body-md font-semibold text-on-primary disabled:opacity-50"
          >
            {creating ? "Creating..." : "Generate code"}
          </button>
        </div>
        {(createError || error) && (
          <p className="text-body-sm text-red-600">{createError ?? error}</p>
        )}
      </Card>

      <Card>
        <h3 className="text-headline-sm text-on-surface">Existing codes</h3>
        {!codes ? (
          <p className="text-body-md text-on-surface-variant">Loading...</p>
        ) : codes.length === 0 ? (
          <p className="text-body-md text-on-surface-variant">No discount codes yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-body-sm">
              <thead>
                <tr className="border-b border-outline-variant text-on-surface-variant">
                  <th className="py-2 pr-4">Code</th>
                  <th className="py-2 pr-4">% off</th>
                  <th className="py-2 pr-4">Uses</th>
                  <th className="py-2 pr-4">Active</th>
                </tr>
              </thead>
              <tbody>
                {codes.map((c) => (
                  <tr key={c.code} className="border-b border-outline-variant/50">
                    <td className="py-2 pr-4 font-mono text-on-surface">{c.code}</td>
                    <td className="py-2 pr-4 text-on-surface-variant">{c.percent_off}%</td>
                    <td className="py-2 pr-4 text-on-surface-variant">
                      {c.used_count} / {c.max_uses}
                    </td>
                    <td className="py-2 pr-4">
                      <button
                        type="button"
                        role="switch"
                        aria-checked={c.active}
                        onClick={() => handleToggleActive(c)}
                        className={`h-6 w-11 rounded-full transition-colors ${
                          c.active ? "bg-secondary-container" : "bg-outline-variant"
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

function formatCents(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
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
          <span className="text-body-sm text-on-surface-variant">MRR</span>
          <span className="text-headline-lg text-on-surface">
            {billing ? formatCents(billing.mrr_cents) : "—"}
          </span>
        </Card>
        <Card>
          <span className="text-body-sm text-on-surface-variant">Active subscribers</span>
          <span className="text-headline-lg text-on-surface">
            {billing?.active_subscribers ?? "—"}
          </span>
        </Card>
        <Card>
          <span className="text-body-sm text-on-surface-variant">Trialing</span>
          <span className="text-headline-lg text-on-surface">
            {billing?.trialing_subscribers ?? "—"}
          </span>
        </Card>
        <Card>
          <span className="text-body-sm text-on-surface-variant">Canceled (30d)</span>
          <span className="text-headline-lg text-on-surface">
            {billing?.canceled_last_30_days ?? "—"}
          </span>
        </Card>
      </div>

      <Card>
        <span className="text-body-sm text-on-surface-variant">
          Revenue collected, last 30 days
        </span>
        <span className="text-headline-lg text-on-surface">
          {billing ? formatCents(billing.revenue_last_30_days_cents) : "—"}
        </span>
      </Card>

      {error && <p className="text-body-sm text-red-600">{error}</p>}

      {stats && (
        <Card>
          <h3 className="text-headline-sm text-on-surface">Signups by plan</h3>
          <div className="flex gap-6 text-body-md text-on-surface">
            <span>Free: {stats.by_plan.free ?? 0}</span>
            <span>Pro: {stats.by_plan.pro ?? 0}</span>
          </div>
        </Card>
      )}

      <Card>
        <h3 className="text-headline-sm text-on-surface">Discount code usage</h3>
        {!codes ? (
          <p className="text-body-md text-on-surface-variant">Loading...</p>
        ) : codes.length === 0 ? (
          <p className="text-body-md text-on-surface-variant">No discount codes yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-body-sm">
              <thead>
                <tr className="border-b border-outline-variant text-on-surface-variant">
                  <th className="py-2 pr-4">Code</th>
                  <th className="py-2 pr-4">% off</th>
                  <th className="py-2 pr-4">Used</th>
                  <th className="py-2 pr-4">Active</th>
                </tr>
              </thead>
              <tbody>
                {codes.map((c) => (
                  <tr key={c.code} className="border-b border-outline-variant/50">
                    <td className="py-2 pr-4 font-mono text-on-surface">{c.code}</td>
                    <td className="py-2 pr-4 text-on-surface-variant">{c.percent_off}%</td>
                    <td className="py-2 pr-4 text-on-surface-variant">
                      {c.used_count} / {c.max_uses}
                    </td>
                    <td className="py-2 pr-4 text-on-surface-variant">
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

  async function handleToggleRead(f: FeedbackSubmission) {
    setBusyId(f.feedback_id)
    try {
      await setFeedbackRead(token, f.feedback_id, !f.read)
      onReload()
    } finally {
      setBusyId(null)
    }
  }

  if (error) return <p className="text-body-sm text-red-600">{error}</p>
  if (!feedback) return <p className="text-body-md text-on-surface-variant">Loading...</p>

  return (
    <Card>
      {feedback.length === 0 ? (
        <p className="text-body-md text-on-surface-variant">No submissions yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-body-sm">
            <thead>
              <tr className="border-b border-outline-variant text-on-surface-variant">
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Subject / Message</th>
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Read</th>
              </tr>
            </thead>
            <tbody>
              {feedback.map((f) => (
                <tr
                  key={f.feedback_id}
                  className={`border-b border-outline-variant/50 ${f.read ? "" : "bg-secondary-container/5"}`}
                >
                  <td className="py-2 pr-4 text-on-surface-variant">
                    {f.category === "support" ? "Support" : "Feedback"}
                  </td>
                  <td className="py-2 pr-4 text-on-surface">
                    {f.subject && <div className="font-semibold">{f.subject}</div>}
                    <div className="max-w-md truncate text-on-surface-variant">{f.message}</div>
                  </td>
                  <td className="py-2 pr-4 text-on-surface-variant">{f.email || "—"}</td>
                  <td className="py-2 pr-4 text-on-surface-variant">
                    {new Date(f.submitted_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 pr-4">
                    <button
                      type="button"
                      role="switch"
                      aria-checked={f.read}
                      disabled={busyId === f.feedback_id}
                      onClick={() => handleToggleRead(f)}
                      className={`h-6 w-11 rounded-full transition-colors ${
                        f.read ? "bg-secondary-container" : "bg-outline-variant"
                      }`}
                    >
                      <span
                        className={`block h-5 w-5 rounded-full bg-white transition-transform ${
                          f.read ? "translate-x-5" : "translate-x-0.5"
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const unreadFeedbackCount = feedback?.filter((f) => !f.read).length ?? 0

  if (!authLoading && (!user || !isVerified)) {
    return <Navigate to="/auth" replace />
  }

  if (authLoading || adminLoading || !token) {
    return (
      <>
        <Header />
        <div className="flex min-h-screen items-center justify-center bg-surface pt-16">
          <p className="text-body-md text-on-surface-variant">Loading...</p>
        </div>
      </>
    )
  }

  if (!isAdmin) {
    return (
      <>
        <Header />
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-surface px-4 pt-16 text-center">
          <p className="text-headline-sm text-on-surface">Not authorized</p>
          <p className="text-body-md text-on-surface-variant">
            You don't have access to the admin area.
          </p>
        </div>
      </>
    )
  }

  return (
    <>
      <Header />
      <div className="min-h-screen w-full bg-surface px-4 py-12 pt-32">
        <div className="mx-auto max-w-4xl">
          <h1 className="mb-6 text-headline-lg text-on-surface">Admin</h1>

          <div className="mb-6 flex gap-2 border-b border-outline-variant">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`relative px-4 py-2 text-body-md font-semibold ${
                  tab === t
                    ? "border-b-2 border-secondary-container text-on-surface"
                    : "text-on-surface-variant"
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
        </div>
      </div>
    </>
  )
}
