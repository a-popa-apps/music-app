import { useRef, useState } from "react"
import { COUNTRIES } from "../data/countries"
import { useClickOutside } from "../hooks/useClickOutside"
import type { ProfileSettings } from "../services/api"
import { KNOWN_PLACEHOLDERS, previewFilename, unknownPlaceholders } from "../utils/filenameTemplate"

export const ROLES: { value: string; label: string }[] = [
  { value: "dj", label: "DJ" },
  { value: "producer", label: "Music Producer" },
  { value: "dj_producer", label: "DJ / Producer" },
  { value: "enthusiast", label: "Music Enthusiast" },
]

export const GENRES = [
  "Electronic music",
  "Hip-Hop / R&B",
  "Urban",
  "Latin",
  "Open Format / Multi-genre",
  "Other",
]

export const MAX_GENRES = 3

export function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-6 rounded border border-white/10 bg-white/10 p-8 backdrop-blur-md">
      <h2 className="text-headline-sm text-white">{title}</h2>
      {children}
    </div>
  )
}

export function ProfileFieldsForm({
  settings,
  onChange,
  email,
}: {
  settings: ProfileSettings
  onChange: <K extends keyof ProfileSettings>(key: K, value: ProfileSettings[K]) => void
  email?: string
}) {
  const isPro = settings.plan === "pro"
  const [showDiscogsHelp, setShowDiscogsHelp] = useState(false)
  const discogsHelpRef = useRef<HTMLButtonElement>(null)
  useClickOutside(discogsHelpRef, () => setShowDiscogsHelp(false), showDiscogsHelp)
  const templateInputRef = useRef<HTMLInputElement>(null)

  const [countryOpen, setCountryOpen] = useState(false)
  const [countrySearch, setCountrySearch] = useState("")
  const countryContainerRef = useRef<HTMLDivElement>(null)
  useClickOutside(countryContainerRef, () => setCountryOpen(false), countryOpen)
  const filteredCountries = COUNTRIES.filter((c) =>
    c.toLowerCase().includes(countrySearch.toLowerCase())
  )

  function insertPlaceholder(tag: string) {
    const current = settings.filename_template ?? ""
    const input = templateInputRef.current
    const insertion = `{${tag}}`

    if (!input) {
      onChange("filename_template", current + insertion)
      return
    }

    const start = input.selectionStart ?? current.length
    const end = input.selectionEnd ?? current.length
    const next = current.slice(0, start) + insertion + current.slice(end)
    onChange("filename_template", next)

    requestAnimationFrame(() => {
      const cursor = start + insertion.length
      input.focus()
      input.setSelectionRange(cursor, cursor)
    })
  }

  function toggleGenre(genre: string) {
    const current = settings.primary_genres
    if (current.includes(genre)) {
      onChange("primary_genres", current.filter((g) => g !== genre))
    } else if (current.length < MAX_GENRES) {
      onChange("primary_genres", [...current, genre])
    }
  }

  return (
    <>
      <Section title="Personal Details">
        <label className="flex flex-col gap-1">
          <span className="text-body-sm font-semibold text-white">Name</span>
          <input
            type="text"
            value={settings.name}
            onChange={(e) => onChange("name", e.target.value)}
            className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none focus:border-secondary-container"
          />
        </label>

        {email !== undefined && (
          <label className="flex flex-col gap-1">
            <span className="text-body-sm font-semibold text-white">Email</span>
            <input
              type="text"
              value={email}
              disabled
              className="rounded border border-white/10 bg-white/5 px-4 py-3 text-body-md text-white/50"
            />
          </label>
        )}

        <label className="flex flex-col gap-1">
          <span className="text-body-sm font-semibold text-white">Country</span>
          <div className="relative" ref={countryContainerRef}>
            <input
              type="text"
              value={countryOpen ? countrySearch : settings.country}
              onChange={(e) => setCountrySearch(e.target.value)}
              onFocus={() => {
                setCountrySearch("")
                setCountryOpen(true)
              }}
              placeholder="Select country..."
              className="w-full rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none placeholder:text-white/40 focus:border-secondary-container"
            />
            {countryOpen && (
              <div className="absolute z-10 mt-1 max-h-56 w-full overflow-y-auto rounded border border-white/20 bg-[#111] shadow-md">
                {filteredCountries.length === 0 ? (
                  <div className="px-4 py-2 text-body-sm text-white/60">
                    No matches
                  </div>
                ) : (
                  filteredCountries.map((c) => (
                    <button
                      type="button"
                      key={c}
                      onClick={() => {
                        onChange("country", c)
                        setCountryOpen(false)
                        setCountrySearch("")
                      }}
                      className={`block w-full px-4 py-2 text-left text-body-md text-white hover:bg-white/10 ${
                        c === settings.country ? "bg-white/10 font-semibold" : ""
                      }`}
                    >
                      {c}
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </label>
      </Section>

      <Section title="Artist Details">
        <label className="flex flex-col gap-1">
          <span className="text-body-sm font-semibold text-white">Artist name</span>
          <input
            type="text"
            placeholder="How you're credited on your releases"
            value={settings.artist_name}
            onChange={(e) => onChange("artist_name", e.target.value)}
            className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none placeholder:text-white/40 focus:border-secondary-container"
          />
        </label>

        <div className="flex flex-col gap-2">
          <span className="text-body-sm font-semibold text-white">Role</span>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {ROLES.map((role) => (
              <label
                key={role.value}
                className={`flex cursor-pointer items-center gap-2 rounded border px-4 py-3 text-body-md text-white ${
                  settings.role === role.value
                    ? "border-secondary-container bg-white/10"
                    : "border-white/20"
                }`}
              >
                <input
                  type="radio"
                  name="role"
                  checked={settings.role === role.value}
                  onChange={() => onChange("role", role.value)}
                />
                {role.label}
              </label>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-body-sm font-semibold text-white">Primary genres</span>
            <span className="text-body-sm text-white/60">
              {settings.primary_genres.length} / {MAX_GENRES} max
            </span>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:flex sm:flex-wrap">
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
                      : "border-white/20 text-white hover:bg-white/10"
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
          <span className="flex items-center gap-1.5 text-body-sm font-semibold text-white">
            Filename template
            {!isPro && (
              <span className="rounded-full bg-secondary-container/15 px-2 py-px font-mono text-[10px] font-bold uppercase tracking-wider text-secondary-container">
                Pro
              </span>
            )}
          </span>
          <input
            ref={templateInputRef}
            type="text"
            placeholder="{artist} - {title} [{bpm} - {key}]"
            value={settings.filename_template ?? ""}
            onChange={(e) => onChange("filename_template", e.target.value)}
            disabled={!isPro}
            className="rounded border border-white/20 bg-white/5 px-4 py-3 font-mono text-body-md text-white outline-none placeholder:text-white/40 focus:border-secondary-container disabled:cursor-not-allowed disabled:opacity-50"
          />
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="text-body-sm text-white/60">Click to insert:</span>
            {KNOWN_PLACEHOLDERS.map((tag) => (
              <button
                type="button"
                key={tag}
                onClick={() => insertPlaceholder(tag)}
                disabled={!isPro}
                className="rounded-full border border-white/20 px-2.5 py-0.5 font-mono text-body-sm text-white transition-colors hover:border-secondary-container hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-white/20 disabled:hover:bg-transparent"
              >
                {`{${tag}}`}
              </button>
            ))}
          </div>
          {!isPro && (
            <span className="text-body-sm text-secondary-container">
              Custom filename templates are a CratePrep Pro feature.{" "}
              <a href="/#pricing" className="underline">
                Upgrade to unlock
              </a>
              .
            </span>
          )}
          <span className="text-body-sm text-white/60">
            Leave blank for the default "Artist - Title (Remix)" format.
          </span>
          <span className="font-mono text-body-sm text-white/60">
            Preview: {previewFilename(settings.filename_template ?? "")}
          </span>
          {(() => {
            const unknown = settings.filename_template
              ? unknownPlaceholders(settings.filename_template)
              : []
            if (unknown.length === 0) return null
            const plural = unknown.length > 1
            return (
              <span className="text-body-sm text-red-400">
                Unrecognized placeholder{plural ? "s" : ""}:{" "}
                {unknown.map((p) => `{${p}}`).join(", ")}. {plural ? "They" : "It"} will be
                left as-is in the output.
              </span>
            )
          })()}
        </label>

        <div className="flex items-center justify-between rounded border border-white/10 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-body-md text-white">Deep catalog search</span>
            <button
              ref={discogsHelpRef}
              type="button"
              onClick={() => setShowDiscogsHelp((v) => !v)}
              aria-label="What is deep catalog search?"
              aria-expanded={showDiscogsHelp}
              className="relative flex h-5 w-5 items-center justify-center rounded-full bg-white/10 text-white/70"
            >
              ?
              {showDiscogsHelp && (
                <span className="absolute bottom-full left-1/2 mb-2 w-64 -translate-x-1/2 rounded border border-white/15 bg-[#111] p-3 text-left text-body-sm normal-case text-white shadow-md">
                  Searches an artist's full release catalog to find genre and track matches
                  that a basic search misses. More accurate, but slower per track.
                </span>
              )}
            </button>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={settings.discogs_deep_search}
            onClick={() => onChange("discogs_deep_search", !settings.discogs_deep_search)}
            className={`h-6 w-11 rounded-full transition-colors ${
              settings.discogs_deep_search ? "bg-secondary-container" : "bg-white/20"
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
    </>
  )
}
