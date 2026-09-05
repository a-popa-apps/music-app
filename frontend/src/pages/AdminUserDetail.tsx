import { useEffect, useState } from "react"
import { Link, Navigate, useParams } from "react-router-dom"
import { Header } from "../components/Header"
import { ProfileFieldsForm } from "../components/ProfileFieldsForm"
import { useAuth } from "../hooks/useAuth"
import { useIsAdmin } from "../hooks/useIsAdmin"
import {
  getAdminUsers,
  getUserProfileAsAdmin,
  saveUserProfileAsAdmin,
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

  useEffect(() => {
    if (user) user.getIdToken().then(setToken)
  }, [user])

  useEffect(() => {
    if (!token || !uid) return

    let cancelled = false
    async function load() {
      try {
        const [profile, users] = await Promise.all([
          getUserProfileAsAdmin(token!, uid!),
          getAdminUsers(token!),
        ])
        if (cancelled) return
        setSettings(profile)
        setSavedSettings(profile)
        setEmail(users.find((u) => u.uid === uid)?.email ?? "")
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

  const isDirty = JSON.stringify(settings) !== JSON.stringify(savedSettings)

  return (
    <>
      <Header />
      <div className="min-h-screen w-full bg-surface px-4 py-12 pt-32">
        <div className="mx-auto max-w-2xl">
          <Link
            to="/admin"
            className="mb-4 inline-block text-body-sm font-semibold text-on-surface-variant hover:text-on-surface"
          >
            &larr; Back to Admin
          </Link>
          <h1 className="mb-6 text-headline-lg text-on-surface">Edit User</h1>

          {loading || !settings ? (
            <p className="text-body-md text-on-surface-variant">
              {error ?? "Loading..."}
            </p>
          ) : (
            <div className="flex flex-col gap-6">
              <ProfileFieldsForm settings={settings} onChange={update} email={email} />

              {error && <p className="text-body-sm text-red-600">{error}</p>}

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
