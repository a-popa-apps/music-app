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
        <Header />
        <div className="flex min-h-screen items-center justify-center bg-surface pt-16">
          <p className="text-body-md text-on-surface-variant">Loading...</p>
        </div>
      </>
    )
  }

  if (!settings) {
    return (
      <>
        <Header />
        <div className="flex min-h-screen items-center justify-center bg-surface pt-16">
          <p className="text-body-md text-red-600">
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
      <Header />
      <div className="min-h-screen w-full bg-surface px-4 py-12 pb-28 pt-32">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-headline-lg text-on-surface">Profile Details</h1>

        <div className="flex flex-col gap-6">
          {checkoutResult === "success" && (
            <div className="rounded border border-green-200 bg-green-50 px-4 py-3 text-body-sm text-green-800">
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
            <div className="rounded border border-outline-variant bg-surface-container-low px-4 py-3 text-body-sm text-on-surface-variant">
              Checkout was cancelled — no changes were made.
              <button
                onClick={() => setSearchParams({}, { replace: true })}
                className="ml-2 underline"
              >
                Dismiss
              </button>
            </div>
          )}

          <ProfileFieldsForm settings={settings} onChange={update} email={user?.email ?? ""} />

          <Section title="Billing">
            <div className="flex items-center justify-between gap-4">
              <div className="flex flex-col gap-1">
                <span className="flex items-center gap-1 text-body-md text-on-surface">
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
                    <span className="text-body-sm text-red-600">
                      {SUBSCRIPTION_WARNINGS[settings.subscription_status]}
                    </span>
                  ) : (
                    <span className="text-body-sm text-on-surface-variant">
                      Manage your payment method, invoices, or cancel anytime.
                    </span>
                  )
                ) : (
                  <span className="text-body-sm text-on-surface-variant">
                    Upgrade for unlimited processing and priority detection.
                  </span>
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

          {error && <p className="text-body-sm text-red-600">{error}</p>}

          <div className="rounded border border-outline-variant p-3">
            <button
              onClick={() => setDangerZoneOpen((o) => !o)}
              aria-expanded={dangerZoneOpen}
              className="flex w-full items-center justify-between text-left"
            >
              <span className="text-body-sm font-semibold text-on-surface-variant">
                Danger Zone
              </span>
              <span
                className={`material-symbols-outlined text-[18px] text-on-surface-variant transition-transform ${
                  dangerZoneOpen ? "rotate-180" : ""
                }`}
              >
                expand_more
              </span>
            </button>
            {dangerZoneOpen && (
              <div className="mt-3 flex flex-col gap-3">
                <p className="text-body-sm text-on-surface-variant">
                  Permanently delete your account and all saved settings. This cannot be
                  undone.
                </p>
                {!confirmingDelete ? (
                  <button
                    onClick={() => setConfirmingDelete(true)}
                    className="self-start rounded-full border border-red-600 px-6 py-2 text-body-sm font-semibold text-red-700 transition-colors hover:bg-red-100"
                  >
                    Delete Account
                  </button>
                ) : (
                  <div className="flex flex-col gap-2 rounded border border-red-200 bg-red-50 p-4">
                    <label className="flex flex-col gap-1">
                      <span className="text-body-sm text-red-700">
                        Type <strong>Delete</strong> to confirm.
                      </span>
                      <input
                        type="text"
                        value={deleteConfirmText}
                        onChange={(e) => setDeleteConfirmText(e.target.value)}
                        autoFocus
                        className="rounded border border-red-300 bg-surface-container-lowest px-3 py-2 text-body-md text-on-surface outline-none focus:border-red-600"
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
                        className="rounded-full border border-outline-variant px-6 py-2 text-body-sm font-semibold text-on-surface-variant hover:bg-surface-container-low"
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
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-outline-variant bg-surface/95 px-4 py-3 backdrop-blur-md">
          <div className="mx-auto flex max-w-2xl items-center justify-between gap-4">
            <span className="text-body-sm text-on-surface-variant">
              {saved ? "Your changes have been saved." : "You have unsaved changes."}
            </span>
            <button
              onClick={handleSave}
              disabled={saving || !isDirty}
              className="whitespace-nowrap rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {saving ? "Saving..." : saved ? "Saved!" : "Save"}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
