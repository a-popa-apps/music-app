import { useRef, useState } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import { useClickOutside } from "../hooks/useClickOutside"
import type { ProfileSettings } from "../services/api"

export function AccountMenu({ profile }: { profile: ProfileSettings | null }) {
  const { user, logOut, resetPassword } = useAuth()
  const [open, setOpen] = useState(false)
  const [resetSent, setResetSent] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  useClickOutside(containerRef, () => setOpen(false), open)

  if (!user) return null

  const isAdmin = profile?.is_admin ?? false
  const displayName = profile?.name?.trim()

  async function handleChangePassword() {
    if (!user!.email) return
    await resetPassword(user!.email)
    setResetSent(true)
    setTimeout(() => {
      setResetSent(false)
      setOpen(false)
    }, 2000)
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Account menu"
        className="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container text-on-surface transition-colors hover:bg-surface-container-high"
      >
        <span className="material-symbols-outlined text-[20px]">person</span>
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-64 rounded bg-inverse-surface p-2 shadow-md">
          <div className="flex flex-col gap-1.5 border-b border-outline px-3 py-2">
            {displayName && (
              <div className="flex items-center gap-1 text-body-md font-semibold text-inverse-on-surface">
                <span>{displayName}</span>
                {profile?.plan === "pro" && (
                  <span className="material-symbols-outlined text-[15px] text-blue-500">
                    verified
                  </span>
                )}
              </div>
            )}
            <div className="text-body-sm text-inverse-on-surface/70">{user.email}</div>
          </div>
          {isAdmin && (
            <Link
              to="/admin"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 rounded px-3 py-2 text-body-md text-inverse-on-surface hover:bg-white/10"
            >
              <span className="material-symbols-outlined text-[18px]">
                shield_person
              </span>
              Admin
            </Link>
          )}
          <Link
            to="/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded px-3 py-2 text-body-md text-inverse-on-surface hover:bg-white/10"
          >
            <span className="material-symbols-outlined text-[18px]">
              manage_accounts
            </span>
            Profile Details
          </Link>
          <Link
            to="/history"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded px-3 py-2 text-body-md text-inverse-on-surface hover:bg-white/10"
          >
            <span className="material-symbols-outlined text-[18px]">history</span>
            History
          </Link>
          <button
            onClick={handleChangePassword}
            className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-body-md text-inverse-on-surface hover:bg-white/10"
          >
            <span className="material-symbols-outlined text-[18px]">key</span>
            {resetSent ? "Email sent!" : "Change password"}
          </button>
          <button
            onClick={() => logOut()}
            className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-body-md text-inverse-on-surface hover:bg-white/10"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
            Log out
          </button>
        </div>
      )}
    </div>
  )
}
