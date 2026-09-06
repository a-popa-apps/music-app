import { useEffect, useMemo, useState } from "react"
import { Navigate } from "react-router-dom"
import { Header } from "../components/Header"
import { useAuth } from "../hooks/useAuth"
import { clearHistory, getHistory, type HistoryEntry } from "../services/api"

type SortKey = "processed_at" | "bpm" | "camelot" | "genre"
type StatusFilter = "all" | "success" | "failed"

const SORT_LABELS: { key: SortKey; label: string }[] = [
  { key: "processed_at", label: "Date" },
  { key: "bpm", label: "BPM" },
  { key: "camelot", label: "Key" },
  { key: "genre", label: "Genre" },
]

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-4 rounded border border-white/10 bg-white/10 p-6 backdrop-blur-md">
      {children}
    </div>
  )
}

export function HistoryPage() {
  const { user, isVerified, loading: authLoading } = useAuth()
  const [token, setToken] = useState<string | null>(null)
  const [history, setHistory] = useState<HistoryEntry[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [clearing, setClearing] = useState(false)

  const [search, setSearch] = useState("")
  const [genreFilter, setGenreFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [sortKey, setSortKey] = useState<SortKey>("processed_at")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")

  useEffect(() => {
    if (user) user.getIdToken().then(setToken)
  }, [user])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    getHistory(token)
      .then((h) => {
        if (!cancelled) setHistory(h)
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load your history. Try refreshing.")
      })
    return () => {
      cancelled = true
    }
  }, [token])

  const genres = useMemo(() => {
    const set = new Set((history ?? []).map((e) => e.genre).filter((g): g is string => Boolean(g)))
    return Array.from(set).sort()
  }, [history])

  const visible = useMemo(() => {
    let rows = history ?? []

    if (search.trim()) {
      const q = search.trim().toLowerCase()
      rows = rows.filter(
        (e) =>
          e.filename.toLowerCase().includes(q) || e.original_filename.toLowerCase().includes(q)
      )
    }
    if (genreFilter !== "all") {
      rows = rows.filter((e) => e.genre === genreFilter)
    }
    if (statusFilter !== "all") {
      rows = rows.filter((e) => (statusFilter === "failed" ? e.failed : !e.failed))
    }

    const sorted = [...rows].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av === null || av === undefined) return 1
      if (bv === null || bv === undefined) return -1
      if (av < bv) return sortDir === "asc" ? -1 : 1
      if (av > bv) return sortDir === "asc" ? 1 : -1
      return 0
    })
    return sorted
  }, [history, search, genreFilter, statusFilter, sortKey, sortDir])

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir(key === "processed_at" ? "desc" : "asc")
    }
  }

  async function handleClear() {
    if (!token) return
    const confirmed = window.confirm(
      "Clear your entire processing history? This can't be undone."
    )
    if (!confirmed) return
    setClearing(true)
    try {
      await clearHistory(token)
      setHistory([])
    } catch {
      setError("Couldn't clear your history. Try again.")
    } finally {
      setClearing(false)
    }
  }

  if (!authLoading && (!user || !isVerified)) {
    return <Navigate to="/auth" replace />
  }

  return (
    <>
      <Header dark />
      <div className="min-h-screen w-full bg-black px-4 py-12 pt-32">
        <div className="mx-auto max-w-5xl">
          <div className="mb-6 flex items-center justify-between gap-4">
            <h1 className="text-headline-lg text-white">History</h1>
            {history && history.length > 0 && (
              <button
                onClick={handleClear}
                disabled={clearing}
                className="whitespace-nowrap rounded-full border border-red-400 px-4 py-2 text-body-sm font-semibold text-red-300 transition-colors hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {clearing ? "Clearing..." : "Clear History"}
              </button>
            )}
          </div>

          {error && <p className="mb-4 text-body-sm text-red-400">{error}</p>}

          {!history ? (
            <p className="text-body-md text-white/60">Loading...</p>
          ) : history.length === 0 ? (
            <Card>
              <p className="text-body-md text-white/60">
                You haven't processed any tracks yet. Drop some files on the home page to get
                started.
              </p>
            </Card>
          ) : (
            <Card>
              <div className="flex flex-wrap items-center gap-3">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by filename..."
                  className="flex-1 rounded border border-white/20 bg-white/5 px-4 py-2 text-body-md text-white outline-none placeholder:text-white/40 focus:border-secondary-container"
                />
                <select
                  value={genreFilter}
                  onChange={(e) => setGenreFilter(e.target.value)}
                  className="rounded border border-white/20 bg-white/5 px-3 py-2 text-body-sm text-white"
                >
                  <option value="all">All genres</option>
                  {genres.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                  className="rounded border border-white/20 bg-white/5 px-3 py-2 text-body-sm text-white"
                >
                  <option value="all">All statuses</option>
                  <option value="success">Successful</option>
                  <option value="failed">Failed</option>
                </select>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-body-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-white/60">
                      <th className="py-2 pr-4">Filename</th>
                      {SORT_LABELS.map(({ key, label }) => (
                        <th key={key} className="py-2 pr-4">
                          <button
                            onClick={() => toggleSort(key)}
                            className="flex items-center gap-1 font-semibold hover:text-white"
                          >
                            {label}
                            {sortKey === key && (
                              <span className="material-symbols-outlined text-[16px]">
                                {sortDir === "asc" ? "arrow_upward" : "arrow_downward"}
                              </span>
                            )}
                          </button>
                        </th>
                      ))}
                      <th className="py-2 pr-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((e) => (
                      <tr key={e.history_id} className="border-b border-white/10">
                        <td className="py-2 pr-4">
                          <div className="flex flex-col">
                            <span className="font-semibold text-white">{e.filename}</span>
                            {e.original_filename !== e.filename && (
                              <span className="text-body-sm text-white/60">
                                was: {e.original_filename}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2 pr-4 text-white/60">
                          {new Date(e.processed_at).toLocaleString()}
                        </td>
                        <td className="py-2 pr-4 text-white/60">
                          {e.bpm !== null ? Math.round(e.bpm) : "—"}
                        </td>
                        <td className="py-2 pr-4 text-white/60">
                          {e.camelot ?? "—"}
                        </td>
                        <td className="py-2 pr-4 text-white/60">{e.genre ?? "—"}</td>
                        <td className="py-2 pr-4">
                          <span
                            className={`font-mono text-meta-badge font-bold uppercase ${
                              e.failed ? "text-red-400" : "text-secondary-container"
                            }`}
                          >
                            {e.failed ? "Error" : "Done"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {visible.length === 0 && (
                  <p className="py-6 text-center text-body-md text-white/60">
                    No tracks match your filters.
                  </p>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  )
}
