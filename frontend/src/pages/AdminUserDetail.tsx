import { useEffect, useState } from "react"
import { Link, Navigate, useParams } from "react-router-dom"
import { Header } from "../components/Header"
import { ProfileFieldsForm } from "../components/ProfileFieldsForm"
import { useAuth } from "../hooks/useAuth"
import { useIsAdmin } from "../hooks/useIsAdmin"
import {
  getAdminUsers,
  getUserHistoryAsAdmin,
  getUserProfileAsAdmin,
  resetUserUsage,
  saveUserProfileAsAdmin,
  type HistoryEntry,
  type ProfileSettings,
} from "../services/api"

export function AdminUserDetail() {
  const { uid } = useParams<{ uid: string }>()
  const { user, isVerified, loading: authLoading } = useAuth()
  const { isAdmin, loading: adminLoading } = useIsAdmin()

  const [token, setToken] = useState<string | null>(null)
  const [email, setEmail] = useState<string>("")
  const [settings, setSettings] = useState<ProfileSettings | null>(null)
  const [savedSettings, setSavedSettings] = useState<ProfileSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resettingUsage, setResettingUsage] = useState(false)
  const [usageResetDone, setUsageResetDone] = useState(false)
  const [history, setHistory] = useState<HistoryEntry[] | null>(null)

  useEffect(() => {
    if (user) user.getIdToken().then(setToken)
  }, [user])

  useEffect(() => {
    if (!token || !uid) return

    let cancelled = false
    async function load() {
      try {
        const [profile, users, userHistory] = await Promise.all([
          getUserProfileAsAdmin(token!, uid!),
          getAdminUsers(token!),
          getUserHistoryAsAdmin(token!, uid!).catch(() => []),
        ])
        if (cancelled) return
        setSettings(profile)
        setSavedSettings(profile)
        setEmail(users.find((u) => u.uid === uid)?.email ?? "")
        setHistory(userHistory)
      } catch {
        if (!cancelled) setError("Couldn't load this user's profile.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()

    return () => {
      cancelled = true
    }
  }, [token, uid])

  if (!authLoading && (!user || !isVerified)) {
    return <Navigate to="/auth" replace />
  }

  if (authLoading || adminLoading) {
    return (
      <>
        <Header dark />
        <div className="flex min-h-screen items-center justify-center bg-black pt-16">
          <p className="text-body-md text-white/60">Loading...</p>
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
        </div>
      </>
    )
  }

  function update<K extends keyof ProfileSettings>(key: K, value: ProfileSettings[K]) {
    setSettings((s) => (s ? { ...s, [key]: value } : s))
  }

  async function handleSave() {
    if (!token || !uid || !settings) return
    setSaving(true)
    setError(null)
    try {
      const updated = await saveUserProfileAsAdmin(token, uid, {
        name: settings.name,
        country: settings.country,
        artist_name: settings.artist_name,
        role: settings.role,
        primary_genres: settings.primary_genres,
        filename_template: settings.filename_template,
        discogs_deep_search: settings.discogs_deep_search,
      })
      setSettings(updated)
      setSavedSettings(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      setError("Couldn't save this user's profile.")
    } finally {
      setSaving(false)
    }
  }

  async function handleResetUsage() {
    if (!token || !uid) return
    setResettingUsage(true)
    setError(null)
    try {
      const updated = await resetUserUsage(token, uid)
      setSettings(updated)
      setSavedSettings(updated)
      setUsageResetDone(true)
      setTimeout(() => setUsageResetDone(false), 2000)
    } catch {
      setError("Couldn't reset this user's usage.")
    } finally {
      setResettingUsage(false)
    }
  }

  const isDirty = JSON.stringify(settings) !== JSON.stringify(savedSettings)

  return (
    <>
      <Header dark />
      <div className="min-h-screen w-full bg-black px-4 py-12 pt-32">
        <div className="mx-auto max-w-2xl">
          <Link
            to="/admin"
            className="mb-4 inline-block text-body-sm font-semibold text-white/60 hover:text-white"
          >
            &larr; Back to Admin
          </Link>
          <h1 className="mb-6 text-headline-lg text-white">Edit User</h1>

          {loading || !settings ? (
            <p className="text-body-md text-white/60">
              {error ?? "Loading..."}
            </p>
          ) : (
            <div className="flex flex-col gap-6">
              {settings.plan === "free" && (
                <div className="flex items-center justify-between gap-4 rounded border border-white/10 bg-white/10 p-6 backdrop-blur-md">
                  <div className="flex flex-col gap-1">
                    <h2 className="text-headline-sm text-white">Monthly usage</h2>
                    <span className="text-body-sm text-white/60">
                      {settings.tracks_processed_this_period} / 25 tracks used
                      {settings.usage_period_start ? ` (${settings.usage_period_start})` : ""}
                    </span>
                  </div>
                  <button
                    onClick={handleResetUsage}
                    disabled={resettingUsage || settings.tracks_processed_this_period === 0}
                    className="whitespace-nowrap rounded-full border border-white/20 px-4 py-2 text-body-sm font-semibold text-white transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {resettingUsage ? "Resetting..." : usageResetDone ? "Reset!" : "Reset usage"}
                  </button>
                </div>
              )}

              <div className="rounded border border-white/10 bg-white/10 p-6 backdrop-blur-md">
                <h2 className="mb-3 text-headline-sm text-white">Processing history</h2>
                {!history ? (
                  <p className="text-body-sm text-white/60">Loading...</p>
                ) : history.length === 0 ? (
                  <p className="text-body-sm text-white/60">
                    Hasn't processed any tracks yet.
                  </p>
                ) : (
                  <div className="flex flex-col gap-2">
                    <span className="text-body-sm text-white/60">
                      {history.length} track{history.length === 1 ? "" : "s"} processed --
                      showing the 10 most recent
                    </span>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-body-sm">
                        <thead>
                          <tr className="border-b border-white/10 text-white/60">
                            <th className="py-1 pr-4">Filename</th>
                            <th className="py-1 pr-4">Date</th>
                            <th className="py-1 pr-4">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {history.slice(0, 10).map((h) => (
                            <tr key={h.history_id} className="border-b border-white/10">
                              <td className="py-1 pr-4 text-white">{h.filename}</td>
                              <td className="py-1 pr-4 text-white/60">
                                {new Date(h.processed_at).toLocaleDateString()}
                              </td>
                              <td
                                className={`py-1 pr-4 font-mono text-meta-badge font-bold uppercase ${
                                  h.failed ? "text-red-400" : "text-secondary-container"
                                }`}
                              >
                                {h.failed ? "Error" : "Done"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              <ProfileFieldsForm settings={settings} onChange={update} email={email} />

              {error && <p className="text-body-sm text-red-400">{error}</p>}

              <button
                onClick={handleSave}
                disabled={saving || !isDirty}
                className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {saving ? "Saving..." : saved ? "Saved!" : "Save"}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
