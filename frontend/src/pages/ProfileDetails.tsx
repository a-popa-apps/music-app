import { useEffect, useState } from "react"
import { Navigate } from "react-router-dom"
import { COUNTRIES } from "../data/countries"
import { useAuth } from "../hooks/useAuth"
import { getProfile, saveProfile, type ProfileSettings } from "../services/api"

const ROLES: { value: string; label: string }[] = [
  { value: "dj", label: "DJ" },
  { value: "producer", label: "Music Producer" },
  { value: "dj_producer", label: "DJ / Producer" },
  { value: "enthusiast", label: "Music Enthusiast" },
]

const GENRES = [
  "Electronic music",
  "Hip-Hop / R&B",
  "Urban",
  "Latin",
  "Open Format / Multi-genre",
  "Other",
]

const MAX_GENRES = 2

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-6 rounded bg-surface-container-lowest p-8 shadow-sm">
      <h2 className="text-headline-sm text-on-surface">{title}</h2>
      {children}
    </div>
  )
}

export function ProfileDetails() {
  const { user, isVerified, loading: authLoading } = useAuth()

  const [settings, setSettings] = useState<ProfileSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [showDiscogsHelp, setShowDiscogsHelp] = useState(false)

  useEffect(() => {
    if (!user) return

    let cancelled = false
    async function load() {
      try {
        const token = await user!.getIdToken()
        const profile = await getProfile(token)
        if (!cancelled) setSettings(profile)
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
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <p className="text-body-md text-on-surface-variant">Loading...</p>
      </div>
    )
  }

  if (!settings) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <p className="text-body-md text-red-600">
          {error ?? "Couldn't load your profile."}
        </p>
      </div>
    )
  }

  function update<K extends keyof ProfileSettings>(key: K, value: ProfileSettings[K]) {
    setSettings((s) => (s ? { ...s, [key]: value } : s))
  }

  function toggleGenre(genre: string) {
    if (!settings) return
    const current = settings.primary_genres
    if (current.includes(genre)) {
      update("primary_genres", current.filter((g) => g !== genre))
    } else if (current.length < MAX_GENRES) {
      update("primary_genres", [...current, genre])
    }
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
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      setError("Couldn't save your profile. Try again.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-surface px-4 py-12">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-headline-lg text-on-surface">Profile Details</h1>

        {settings.plan === "free" && (
          <div className="mb-6 flex items-center justify-between gap-4 rounded bg-gradient-to-r from-secondary-container to-secondary px-6 py-4 text-on-primary">
            <span className="text-body-md font-semibold">
              You're on the free plan. Upgrade for full access.
            </span>
            <button className="whitespace-nowrap rounded-full bg-on-primary px-4 py-2 text-body-sm font-semibold text-secondary">
              Upgrade
            </button>
          </div>
        )}

        <div className="flex flex-col gap-6">
          <Section title="Personal Details">
            <label className="flex flex-col gap-1">
              <span className="text-body-sm font-semibold text-on-surface">Name</span>
              <input
                type="text"
                value={settings.name}
                onChange={(e) => update("name", e.target.value)}
                className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-3 text-body-md text-on-surface outline-none focus:border-secondary-container"
              />
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-body-sm font-semibold text-on-surface">Email</span>
              <input
                type="text"
                value={user?.email ?? ""}
                disabled
                className="rounded border border-outline-variant bg-surface-container px-4 py-3 text-body-md text-on-surface-variant"
              />
            </label>

            <label className="flex flex-col gap-1">
              <span className="text-body-sm font-semibold text-on-surface">Country</span>
              <select
                value={settings.country}
                onChange={(e) => update("country", e.target.value)}
                className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-3 text-body-md text-on-surface outline-none focus:border-secondary-container"
              >
                <option value="">Select country...</option>
                {COUNTRIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
          </Section>

          <Section title="Artist Details">
            <label className="flex flex-col gap-1">
              <span className="text-body-sm font-semibold text-on-surface">
                Artist name
              </span>
              <input
                type="text"
                placeholder="How you're credited on your releases"
                value={settings.artist_name}
                onChange={(e) => update("artist_name", e.target.value)}
                className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-3 text-body-md text-on-surface outline-none focus:border-secondary-container"
              />
            </label>

            <div className="flex flex-col gap-2">
              <span className="text-body-sm font-semibold text-on-surface">Role</span>
              <div className="grid grid-cols-2 gap-3">
                {ROLES.map((role) => (
                  <label
                    key={role.value}
                    className={`flex cursor-pointer items-center gap-2 rounded border px-4 py-3 text-body-md ${
                      settings.role === role.value
                        ? "border-secondary-container bg-surface-container-low"
                        : "border-outline-variant"
                    }`}
                  >
                    <input
                      type="radio"
                      name="role"
                      checked={settings.role === role.value}
                      onChange={() => update("role", role.value)}
                    />
                    {role.label}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-body-sm font-semibold text-on-surface">
                  Primary genres
                </span>
                <span className="text-body-sm text-on-surface-variant">
                  {settings.primary_genres.length} / {MAX_GENRES} max
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {GENRES.map((genre) => {
                  const selected = settings.primary_genres.includes(genre)
                  return (
                    <button
                      type="button"
                      key={genre}
                      onClick={() => toggleGenre(genre)}
                      className={`rounded-full border px-4 py-2 text-body-sm transition-colors ${
                        selected
                          ? "border-secondary-container bg-secondary-container text-on-primary"
                          : "border-outline-variant text-on-surface hover:bg-surface-container-low"
                      }`}
                    >
                      {genre}
                    </button>
                  )
                })}
              </div>
            </div>
          </Section>

          <Section title="Output Settings">
            <label className="flex flex-col gap-1">
              <span className="text-body-sm font-semibold text-on-surface">
                Filename template
              </span>
              <input
                type="text"
                placeholder="{artist} - {title} [{bpm} - {key}]"
                value={settings.filename_template ?? ""}
                onChange={(e) => update("filename_template", e.target.value)}
                className="rounded border border-outline-variant bg-surface-container-lowest px-4 py-3 font-mono text-body-md text-on-surface outline-none focus:border-secondary-container"
              />
              <span className="text-body-sm text-on-surface-variant">
                Placeholders: {"{artist} {title} {bpm} {key} {genre}"}. Leave blank for
                the default "Artist - Title (Remix)" format.
              </span>
            </label>

            <div className="flex items-center justify-between rounded border border-outline-variant px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-body-md text-on-surface">Deep catalog search</span>
                <button
                  type="button"
                  onClick={() => setShowDiscogsHelp((v) => !v)}
                  aria-label="What is deep catalog search?"
                  className="relative flex h-5 w-5 items-center justify-center rounded-full bg-surface-container text-on-surface-variant"
                >
                  ?
                  {showDiscogsHelp && (
                    <span className="absolute bottom-full left-1/2 mb-2 w-64 -translate-x-1/2 rounded bg-inverse-surface p-3 text-left text-body-sm normal-case text-inverse-on-surface shadow-md">
                      Searches an artist's full release catalog to find genre and track
                      matches that a basic search misses. More accurate, but slower per
                      track.
                    </span>
                  )}
                </button>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.discogs_deep_search}
                onClick={() =>
                  update("discogs_deep_search", !settings.discogs_deep_search)
                }
                className={`h-6 w-11 rounded-full transition-colors ${
                  settings.discogs_deep_search
                    ? "bg-secondary-container"
                    : "bg-outline-variant"
                }`}
              >
                <span
                  className={`block h-5 w-5 rounded-full bg-white transition-transform ${
                    settings.discogs_deep_search ? "translate-x-5" : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
          </Section>

          {error && <p className="text-body-sm text-red-600">{error}</p>}

          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {saving ? "Saving..." : saved ? "Saved!" : "Save"}
          </button>
        </div>
      </div>
    </div>
  )
}
