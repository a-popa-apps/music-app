import { useState } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import { useIsAdmin } from "../hooks/useIsAdmin"

export function AccountMenu() {
  const { user, logOut, resetPassword } = useAuth()
  const { isAdmin } = useIsAdmin()
  const [open, setOpen] = useState(false)
  const [resetSent, setResetSent] = useState(false)

  if (!user) return null

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
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Account menu"
        className="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container text-on-surface transition-colors hover:bg-surface-container-high"
      >
        <span className="material-symbols-outlined text-[20px]">person</span>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-50 mt-2 w-64 rounded bg-inverse-surface p-2 shadow-md">
            <div className="border-b border-outline px-3 py-2 text-body-sm text-inverse-on-surface/70">
              {user.email}
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
        </>
      )}
    </div>
  )
}
