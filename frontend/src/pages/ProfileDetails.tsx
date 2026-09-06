import { useEffect, useState } from "react"
import { Navigate, useNavigate, useSearchParams } from "react-router-dom"
import { Header } from "../components/Header"
import { ProfileFieldsForm, Section } from "../components/ProfileFieldsForm"
import { useAuth } from "../hooks/useAuth"
import {
  createBillingPortalSession,
  createCheckoutSession,
  deleteAccount,
  getProfile,
  saveProfile,
  type ProfileSettings,
} from "../services/api"

const SUBSCRIPTION_WARNINGS: Record<string, string> = {
  past_due: "Your last payment failed. Update your payment method to keep Pro.",
  unpaid: "Your subscription is unpaid. Update your payment method to keep Pro.",
  incomplete: "Your subscription setup is incomplete.",
}

// The monthly quota always rolls over at the start of the next calendar
// month (UTC), regardless of settings.usage_period_start -- matches
// check_and_reserve_usage's rollover logic in profile_store.py.
function quotaResetLabel(): string {
  const now = new Date()
  const resetDate = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1))
  return resetDate.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

export function ProfileDetails() {
  const { user, isVerified, loading: authLoading, logOut } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [settings, setSettings] = useState<ProfileSettings | null>(null)
  const [savedSettings, setSavedSettings] = useState<ProfileSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [dangerZoneOpen, setDangerZoneOpen] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState("")
  const [billingLoading, setBillingLoading] = useState(false)
  const checkoutResult = searchParams.get("checkout")

  useEffect(() => {
    if (!user) return

    let cancelled = false
    async function load() {
      try {
        const token = await user!.getIdToken()
        const profile = await getProfile(token)
        if (!cancelled) {
          setSettings(profile)
          setSavedSettings(profile)
        }
      } catch {
        if (!cancelled) setError("Couldn't load your profile. Try refreshing.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()

    return () => {
      cancelled = true
    }
  }, [user])

  const isDirty = JSON.stringify(settings) !== JSON.stringify(savedSettings)

  useEffect(() => {
    if (!isDirty) return
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault()
    }
    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [isDirty])

  if (!authLoading && (!user || !isVerified)) {
    return <Navigate to="/auth" replace />
  }

  if (loading) {
    return (
      <>
        <Header dark />
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-black pt-16">
          <span className="material-symbols-outlined animate-spin text-[40px] text-secondary-container">
            progress_activity
          </span>
          <p className="text-headline-sm text-white">Loading your profile...</p>
        </div>
      </>
    )
  }

  if (!settings) {
    return (
      <>
        <Header dark />
        <div className="flex min-h-screen items-center justify-center bg-black pt-16">
          <p className="text-body-md text-red-400">
            {error ?? "Couldn't load your profile."}
          </p>
        </div>
      </>
    )
  }

  function update<K extends keyof ProfileSettings>(key: K, value: ProfileSettings[K]) {
    setSettings((s) => (s ? { ...s, [key]: value } : s))
  }

  async function handleSave() {
    if (!user || !settings) return
    setSaving(true)
    setError(null)
    try {
      const token = await user.getIdToken()
      const updated = await saveProfile(token, {
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
      setError("Couldn't save your profile. Try again.")
    } finally {
      setSaving(false)
    }
  }

  async function handleUpgrade() {
    if (!user) return
    setBillingLoading(true)
    setError(null)
    try {
      const token = await user.getIdToken()
      const url = await createCheckoutSession(token, "monthly")
      window.location.href = url
    } catch {
      setError("Couldn't start checkout. Try again.")
      setBillingLoading(false)
    }
  }

  async function handleManageBilling() {
    if (!user) return
    setBillingLoading(true)
    setError(null)
    try {
      const token = await user.getIdToken()
      const url = await createBillingPortalSession(token)
      window.location.href = url
    } catch {
      setError("Couldn't open billing portal. Try again.")
      setBillingLoading(false)
    }
  }

  async function handleDeleteAccount() {
    if (!user) return
    setDeleting(true)
    setError(null)
    try {
      const token = await user.getIdToken()
      await deleteAccount(token)
      await logOut()
      navigate("/")
    } catch {
      setError("Couldn't delete your account. Try again.")
      setDeleting(false)
    }
  }

  return (
    <>
      <Header dark />
      <div className="min-h-screen w-full bg-black px-4 py-12 pb-28 pt-32">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-headline-lg text-white">Profile Details</h1>

        <div className="flex flex-col gap-6">
          {checkoutResult === "success" && (
            <div className="rounded border border-green-400/30 bg-green-500/10 px-4 py-3 text-body-sm text-green-300">
              Welcome to Pro! Your subscription is now active.
              <button
                onClick={() => setSearchParams({}, { replace: true })}
                className="ml-2 underline"
              >
                Dismiss
              </button>
            </div>
          )}
          {checkoutResult === "cancelled" && (
            <div className="rounded border border-white/10 bg-white/5 px-4 py-3 text-body-sm text-white/70">
              Checkout was cancelled — no changes were made.
              <button
                onClick={() => setSearchParams({}, { replace: true })}
                className="ml-2 underline"
              >
                Dismiss
              </button>
            </div>
          )}

          {settings.plan === "free" && (
            <div className="flex flex-col items-start gap-4 rounded-2xl bg-gradient-to-r from-secondary-container to-[#ff3d78] p-6 text-on-primary shadow-[0_8px_30px_rgba(255,61,120,0.35)] sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-[32px]">bolt</span>
                <div className="flex flex-col">
                  <span className="text-headline-sm font-bold">
                    Go Pro for more tracks &amp; priority detection
                  </span>
                  <span className="text-body-sm text-on-primary/80">
                    {settings.tracks_processed_this_period} / 25 tracks used this month
                    (resets {quotaResetLabel()}) — unlock 50/batch, custom filename
                    templates &amp; more.
                  </span>
                </div>
              </div>
              <button
                onClick={handleUpgrade}
                disabled={billingLoading}
                className="whitespace-nowrap rounded-full bg-white px-5 py-2 text-body-sm font-semibold text-[#ff3d78] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {billingLoading ? "Loading..." : "Upgrade to Pro"}
              </button>
            </div>
          )}

          <ProfileFieldsForm settings={settings} onChange={update} email={user?.email ?? ""} />

          <Section title="Billing">
            <div className="flex items-center justify-between gap-4">
              <div className="flex flex-col gap-1">
                <span className="flex items-center gap-1 text-body-md text-white">
                  Current plan:{" "}
                  <strong className="inline-flex items-center gap-1">
                    {settings.plan === "pro" ? "Pro" : "Free"}
                    {settings.plan === "pro" && (
                      <span className="material-symbols-outlined text-[15px] text-blue-500">
                        verified
                      </span>
                    )}
                  </strong>
                </span>
                {settings.plan === "pro" ? (
                  settings.subscription_status && SUBSCRIPTION_WARNINGS[settings.subscription_status] ? (
                    <span className="text-body-sm text-red-400">
                      {SUBSCRIPTION_WARNINGS[settings.subscription_status]}
                    </span>
                  ) : (
                    <span className="text-body-sm text-white/60">
                      Manage your payment method, invoices, or cancel anytime.
                    </span>
                  )
                ) : (
                  <>
                    <span className="text-body-sm text-white/60">
                      {settings.tracks_processed_this_period} / 25 tracks used this month
                      (resets {quotaResetLabel()})
                    </span>
                    <span className="text-body-sm text-white/60">
                      Upgrade for more tracks and priority detection.
                    </span>
                  </>
                )}
              </div>
              <button
                onClick={settings.plan === "pro" ? handleManageBilling : handleUpgrade}
                disabled={billingLoading}
                className="whitespace-nowrap rounded-full bg-secondary-container px-4 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {billingLoading
                  ? "Loading..."
                  : settings.plan === "pro"
                    ? "Manage billing"
                    : "Upgrade to Pro"}
              </button>
            </div>
          </Section>

          {error && <p className="text-body-sm text-red-400">{error}</p>}

          <div className="rounded border border-white/10 p-3">
            <button
              onClick={() => setDangerZoneOpen((o) => !o)}
              aria-expanded={dangerZoneOpen}
              className="flex w-full items-center justify-between text-left"
            >
              <span className="text-body-sm font-semibold text-white/70">
                Danger Zone
              </span>
              <span
                className={`material-symbols-outlined text-[18px] text-white/70 transition-transform ${
                  dangerZoneOpen ? "rotate-180" : ""
                }`}
              >
                expand_more
              </span>
            </button>
            {dangerZoneOpen && (
              <div className="mt-3 flex flex-col gap-3">
                <p className="text-body-sm text-white/60">
                  Permanently delete your account and all saved settings. This cannot be
                  undone.
                </p>
                {!confirmingDelete ? (
                  <button
                    onClick={() => setConfirmingDelete(true)}
                    className="self-start rounded-full border border-red-400 px-6 py-2 text-body-sm font-semibold text-red-300 transition-colors hover:bg-red-500/10"
                  >
                    Delete Account
                  </button>
                ) : (
                  <div className="flex flex-col gap-2 rounded border border-red-400/30 bg-red-500/10 p-4">
                    <label className="flex flex-col gap-1">
                      <span className="text-body-sm text-red-300">
                        Type <strong>Delete</strong> to confirm.
                      </span>
                      <input
                        type="text"
                        value={deleteConfirmText}
                        onChange={(e) => setDeleteConfirmText(e.target.value)}
                        autoFocus
                        className="rounded border border-red-400/40 bg-black/40 px-3 py-2 text-body-md text-white outline-none focus:border-red-400"
                      />
                    </label>
                    <div className="flex gap-2">
                      <button
                        onClick={handleDeleteAccount}
                        disabled={deleting || deleteConfirmText.trim().toLowerCase() !== "delete"}
                        className="rounded-full bg-red-600 px-6 py-2 text-body-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {deleting ? "Deleting..." : "Confirm Delete"}
                      </button>
                      <button
                        onClick={() => {
                          setConfirmingDelete(false)
                          setDeleteConfirmText("")
                        }}
                        disabled={deleting}
                        className="rounded-full border border-white/20 px-6 py-2 text-body-sm font-semibold text-white/70 hover:bg-white/10"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      </div>
      {(isDirty || saved) && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-black/95 px-4 py-3 backdrop-blur-md">
          <div className="mx-auto flex max-w-2xl items-center justify-between gap-4">
            <span className="text-body-sm text-white/70">
              {saved ? "Your changes have been saved." : "You have unsaved changes."}
            </span>
            <div className="flex items-center gap-2">
              {isDirty && !saved && (
                <button
                  onClick={() => setSettings(savedSettings)}
                  disabled={saving}
                  className="whitespace-nowrap rounded-full border border-white/20 px-6 py-2 text-body-sm font-semibold text-white/70 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Discard
                </button>
              )}
              <button
                onClick={handleSave}
                disabled={saving || !isDirty}
                className="whitespace-nowrap rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {saving ? "Saving..." : saved ? "Saved!" : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
