import { useEffect, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import { AccountMenu } from "./AccountMenu"
import { useAuth } from "../hooks/useAuth"
import { useProfile } from "../hooks/useProfile"

const NAV_LINKS = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Features", href: "/#features" },
  { label: "Pricing", href: "/#pricing" },
  { label: "FAQ", href: "/#faq" },
]

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const { user, isVerified, logOut, loading } = useAuth()
  const { profile } = useProfile()
  const isAdmin = profile?.is_admin ?? false
  const loggedIn = user && isVerified
  const location = useLocation()
  const overHero = location.pathname === "/" && !scrolled

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > window.innerHeight - 64)
    }
    handleScroll()
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <header
      className={`fixed top-0 z-50 w-full border-b transition-colors duration-300 ${
        overHero
          ? "border-white/10 bg-black/20 backdrop-blur-md"
          : "border-transparent bg-surface/90 shadow-[0_1px_8px_rgba(0,0,0,0.03)] backdrop-blur-xl"
      }`}
    >
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 lg:px-12">
        <Link to="/" className="flex items-center gap-2">
          <span
            className={`font-mono text-headline-sm font-bold tracking-tight ${
              overHero ? "text-white" : "text-on-surface"
            }`}
          >
            crateprep.
          </span>
        </Link>
        <nav className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className={`text-body-md transition-colors ${
                overHero
                  ? "text-white/80 hover:text-white"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              {link.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {loading ? (
            <div
              className={`h-9 w-20 animate-pulse rounded-full ${
                overHero ? "bg-white/15" : "bg-surface-container-low"
              }`}
            />
          ) : loggedIn ? (
            <div className="hidden md:block">
              <AccountMenu profile={profile} />
            </div>
          ) : (
            <Link
              to="/auth"
              className={`inline-flex items-center justify-center rounded-full px-6 py-2 text-body-sm font-semibold transition-all ${
                overHero
                  ? "border border-white/30 bg-white/15 text-white backdrop-blur-sm hover:bg-white/25"
                  : "bg-primary text-on-primary hover:bg-inverse-surface"
              }`}
            >
              Sign In
            </Link>
          )}
          <button
            onClick={() => setMenuOpen((open) => !open)}
            aria-label="Toggle menu"
            className={`flex h-9 w-9 items-center justify-center rounded-full md:hidden ${
              overHero ? "text-white" : "text-on-surface"
            }`}
          >
            <span className="material-symbols-outlined">
              {menuOpen ? "close" : "menu"}
            </span>
          </button>
        </div>
      </div>
      {menuOpen && (
        <nav
          className={`flex flex-col gap-1 border-t px-4 py-4 md:hidden ${
            overHero
              ? "border-white/20 bg-black/50 backdrop-blur-xl"
              : "border-outline-variant bg-surface"
          }`}
        >
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className={`rounded px-2 py-3 text-body-md ${
                overHero
                  ? "text-white/80 hover:bg-white/10 hover:text-white"
                  : "text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
              }`}
            >
              {link.label}
            </a>
          ))}
          {loading ? null : loggedIn ? (
            <div className="flex flex-col gap-1 px-2 py-3">
              {profile?.name?.trim() && (
                <span
                  className={`flex items-center gap-1 text-body-md font-semibold ${
                    overHero ? "text-white" : "text-on-surface"
                  }`}
                >
                  {profile.name}
                  {profile.plan === "pro" && (
                    <span className="material-symbols-outlined text-[15px] text-blue-500">
                      verified
                    </span>
                  )}
                </span>
              )}
              <span className={`text-body-sm ${overHero ? "text-white/70" : "text-on-surface-variant"}`}>
                {user.email}
              </span>
              {isAdmin && (
                <Link
                  to="/admin"
                  onClick={() => setMenuOpen(false)}
                  className={`py-1 text-body-md font-semibold ${overHero ? "text-white" : "text-on-surface"}`}
                >
                  Admin
                </Link>
              )}
              <Link
                to="/profile"
                onClick={() => setMenuOpen(false)}
                className={`py-1 text-body-md font-semibold ${overHero ? "text-white" : "text-on-surface"}`}
              >
                Profile Details
              </Link>
              <button
                onClick={() => logOut()}
                className={`py-1 text-left text-body-sm font-semibold underline ${
                  overHero ? "text-white" : "text-on-surface"
                }`}
              >
                Log out
              </button>
            </div>
          ) : (
            <Link
              to="/auth"
              onClick={() => setMenuOpen(false)}
              className={`rounded px-2 py-3 text-body-md font-semibold ${
                overHero
                  ? "text-white hover:bg-white/10"
                  : "text-on-surface hover:bg-surface-container-low"
              }`}
            >
              Sign In
            </Link>
          )}
        </nav>
      )}
    </header>
  )
}
