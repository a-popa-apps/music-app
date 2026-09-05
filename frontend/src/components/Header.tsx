import { useState } from "react"
import { Link } from "react-router-dom"
import { AccountMenu } from "./AccountMenu"
import { useAuth } from "../hooks/useAuth"
import { useIsAdmin } from "../hooks/useIsAdmin"

const NAV_LINKS = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Features", href: "/#features" },
  { label: "Pricing", href: "/#pricing" },
  { label: "FAQ", href: "/#faq" },
]

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { user, isVerified, logOut, loading } = useAuth()
  const { isAdmin } = useIsAdmin()
  const loggedIn = user && isVerified

  return (
    <header className="fixed top-0 z-50 w-full bg-surface/90 shadow-[0_1px_8px_rgba(0,0,0,0.03)] backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 lg:px-12">
        <Link to="/" className="flex items-center gap-2">
          <span className="font-mono text-headline-sm font-bold tracking-tight text-on-surface">
            crateprep.
          </span>
        </Link>
        <nav className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-body-md text-on-surface-variant transition-colors hover:text-on-surface"
            >
              {link.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {loading ? (
            <div className="h-9 w-20 animate-pulse rounded-full bg-surface-container-low" />
          ) : loggedIn ? (
            <div className="hidden md:block">
              <AccountMenu />
            </div>
          ) : (
            <Link
              to="/auth"
              className="inline-flex items-center justify-center rounded-full bg-primary px-6 py-2 text-body-sm font-semibold text-on-primary transition-all hover:bg-inverse-surface"
            >
              Sign In
            </Link>
          )}
          <button
            onClick={() => setMenuOpen((open) => !open)}
            aria-label="Toggle menu"
            className="flex h-9 w-9 items-center justify-center rounded-full text-on-surface md:hidden"
          >
            <span className="material-symbols-outlined">
              {menuOpen ? "close" : "menu"}
            </span>
          </button>
        </div>
      </div>
      {menuOpen && (
        <nav className="flex flex-col gap-1 border-t border-outline-variant bg-surface px-4 py-4 md:hidden">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="rounded px-2 py-3 text-body-md text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
            >
              {link.label}
            </a>
          ))}
          {loading ? null : loggedIn ? (
            <div className="flex flex-col gap-1 px-2 py-3">
              <span className="text-body-sm text-on-surface-variant">
                {user.email}
              </span>
              {isAdmin && (
                <Link
                  to="/admin"
                  onClick={() => setMenuOpen(false)}
                  className="py-1 text-body-md font-semibold text-on-surface"
                >
                  Admin
                </Link>
              )}
              <Link
                to="/profile"
                onClick={() => setMenuOpen(false)}
                className="py-1 text-body-md font-semibold text-on-surface"
              >
                Profile Details
              </Link>
              <button
                onClick={() => logOut()}
                className="py-1 text-left text-body-sm font-semibold text-on-surface underline"
              >
                Log out
              </button>
            </div>
          ) : (
            <Link
              to="/auth"
              onClick={() => setMenuOpen(false)}
              className="rounded px-2 py-3 text-body-md font-semibold text-on-surface hover:bg-surface-container-low"
            >
              Sign In
            </Link>
          )}
        </nav>
      )}
    </header>
  )
}
