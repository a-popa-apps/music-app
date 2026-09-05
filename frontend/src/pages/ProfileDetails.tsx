import { useEffect, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Header } from "../components/Header"
import { ProfileFieldsForm, Section } from "../components/ProfileFieldsForm"
import { useAuth } from "../hooks/useAuth"
import { deleteAccount, getProfile, saveProfile, type ProfileSettings } from "../services/api"

export function ProfileDetails() {
  const { user, isVerified, loading: authLoading, logOut } = useAuth()
  const navigate = useNavigate()

  const [settings, setSettings] = useState<ProfileSettings | null>(null)
  const [savedSettings, setSavedSettings] = useState<ProfileSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [deleting, setDeleting] = useState(false)

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

  const isDirty = JSON.stringify(settings) !== JSON.stringify(savedSettings)

  async function handleDeleteAccount() {
    if (!user) return
    const confirmed = window.confirm(
      "Delete your account? This permanently removes your profile and saved settings, and cannot be undone."
    )
    if (!confirmed) return

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
      <div className="min-h-screen w-full bg-surface px-4 py-12 pt-32">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-headline-lg text-on-surface">Profile Details</h1>

        <div className="flex flex-col gap-6">
          <ProfileFieldsForm settings={settings} onChange={update} email={user?.email ?? ""} />

          <Section title="Billing">
            <div className="flex items-center justify-between gap-4">
              <div className="flex flex-col gap-1">
                <span className="text-body-md text-on-surface">
                  Current plan: <strong>{settings.plan === "pro" ? "Pro" : "Free"}</strong>
                </span>
                <span className="text-body-sm text-on-surface-variant">
                  No payment method on file. Billing isn't live yet — check back soon.
                </span>
              </div>
              <button
                disabled
                title="Coming soon"
                className="whitespace-nowrap rounded-full bg-outline-variant px-4 py-2 text-body-sm font-semibold text-on-surface-variant cursor-not-allowed"
              >
                Manage billing
              </button>
            </div>
          </Section>

          {error && <p className="text-body-sm text-red-600">{error}</p>}

          <button
            onClick={handleSave}
            disabled={saving || !isDirty}
            className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {saving ? "Saving..." : saved ? "Saved!" : "Save"}
          </button>

          <div className="flex flex-col gap-3 rounded border border-red-200 bg-red-50 p-6">
            <h2 className="text-headline-sm text-red-700">Danger Zone</h2>
            <p className="text-body-sm text-red-700/80">
              Permanently delete your account and all saved settings. This cannot be
              undone.
            </p>
            <button
              onClick={handleDeleteAccount}
              disabled={deleting}
              className="self-start rounded-full border border-red-600 px-6 py-2 text-body-sm font-semibold text-red-700 transition-colors hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {deleting ? "Deleting..." : "Delete Account"}
            </button>
          </div>
        </div>
      </div>
      </div>
    </>
  )
}
