import { useEffect, useRef, useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { AccountMenu } from "./AccountMenu"
import { useAuth } from "../hooks/useAuth"
import { useProfile } from "../hooks/useProfile"
import { createCheckoutSession } from "../services/api"
import { trackEvent } from "../utils/analytics"

const NAV_LINKS = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Features", href: "/#features" },
  { label: "Pricing", href: "/#pricing" },
  { label: "FAQ", href: "/#faq" },
]

// `dark` forces the same translucent-over-dark treatment normally reserved
// for sitting on top of the hero image, for pages with a solid black
// background of their own (e.g. the restyled Profile page).
export function Header({ dark = false }: { dark?: boolean }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const { user, isVerified, logOut, loading } = useAuth()
  const { profile } = useProfile()
  const isAdmin = profile?.is_admin ?? false
  const loggedIn = user && isVerified
  const isPro = Boolean(loggedIn && profile?.plan === "pro")
  // Nothing to upgrade to once you're already Pro -- and the landing page's
  // Pricing section itself is hidden for Pro users (see Pricing.tsx), so
  // the anchor link would just scroll to a spot that no longer exists.
  const navLinks = isPro ? NAV_LINKS.filter((link) => link.label !== "Pricing") : NAV_LINKS
  const location = useLocation()
  const navigate = useNavigate()
  const overHero = dark || (location.pathname === "/" && !scrolled)
  const headerRef = useRef<HTMLElement>(null)
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const [goProLoading, setGoProLoading] = useState(false)

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > window.innerHeight - 64)
    }
    handleScroll()
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // Highlights the nav link for whichever section currently sits just below
  // the fixed header, so the nav reflects where you actually are on the
  // page instead of staying static the whole scroll.
  useEffect(() => {
    if (location.pathname !== "/") {
      setActiveSection(null)
      return
    }

    const sectionIds = ["how-it-works", "features", "pricing", "faq"]
    const elements = sectionIds
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null)
    if (elements.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting)
        if (visible.length === 0) return
        const topMost = visible.reduce((a, b) =>
          a.boundingClientRect.top < b.boundingClientRect.top ? a : b
        )
        setActiveSection(topMost.target.id)
      },
      { rootMargin: "-80px 0px -70% 0px", threshold: 0 }
    )
    elements.forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [location.pathname])

  async function handleGoPro() {
    if (!user || !isVerified) {
      navigate("/auth")
      return
    }
    setGoProLoading(true)
    try {
      const token = await user.getIdToken()
      trackEvent("begin_checkout", { billing_cycle: "annual", source: "header" })
      const url = await createCheckoutSession(token, "annual")
      window.location.href = url
    } catch {
      setGoProLoading(false)
    }
  }

  // Close the mobile menu on an outside tap/click or on scroll, matching
  // the usual dropdown-menu convention (nothing else on this page does
  // this yet, so it's scoped to just this menu's own open state).
  useEffect(() => {
    if (!menuOpen) return

    function handlePointerDown(e: PointerEvent) {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    function handleScrollClose() {
      setMenuOpen(false)
    }

    document.addEventListener("pointerdown", handlePointerDown)
    window.addEventListener("scroll", handleScrollClose, { passive: true })
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown)
      window.removeEventListener("scroll", handleScrollClose)
    }
  }, [menuOpen])

  return (
    <header
      ref={headerRef}
      className={`fixed top-0 z-50 w-full border-b transition-colors duration-300 ${
        overHero
          ? "border-white/10 bg-black/20 backdrop-blur-md"
          : "border-transparent bg-surface/90 shadow-[0_1px_8px_rgba(0,0,0,0.03)] backdrop-blur-xl"
      }`}
    >
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 lg:px-12">
        <Link
          to="/"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="flex items-center gap-2"
        >
          <span
            className={`font-mono text-headline-sm font-bold tracking-tight ${
              overHero ? "text-white" : "text-on-surface"
            }`}
          >
            crateprep.
          </span>
          <span className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-secondary-container">
            Pro
          </span>
        </Link>
        <nav className="hidden items-center gap-2 md:flex">
          {navLinks.map((link) => {
            const isActive = activeSection !== null && link.href === `/#${activeSection}`
            return (
              <a
                key={link.href}
                href={link.href}
                className={`rounded-full px-4 py-2 text-body-md transition-colors ${
                  isActive
                    ? overHero
                      ? "bg-white/10 text-white"
                      : "bg-surface-container-low text-on-surface"
                    : overHero
                      ? "text-white/80 hover:text-white"
                      : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {link.label}
              </a>
            )
          })}
        </nav>
        <div className="flex items-center gap-3">
          {loading ? (
            <div
              className={`h-9 w-20 animate-pulse rounded-full ${
                overHero ? "bg-white/15" : "bg-surface-container-low"
              }`}
            />
          ) : (
            <>
              {!loggedIn && (
                <Link
                  to="/auth"
                  className={`text-body-sm font-semibold transition-colors ${
                    overHero
                      ? "text-white/80 hover:text-white"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  Sign In
                </Link>
              )}
              {loggedIn && (
                <div className="hidden md:block">
                  <AccountMenu profile={profile} />
                </div>
              )}
              {!isPro && (
                <button
                  onClick={handleGoPro}
                  disabled={goProLoading}
                  className="hidden items-center justify-center rounded-full bg-secondary-container px-6 py-2 text-body-sm font-semibold text-white shadow-[0_4px_16px_rgba(255,107,53,0.4)] transition-transform hover:scale-[1.03] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 md:inline-flex"
                >
                  {goProLoading ? "Loading..." : "Go Pro"}
                </button>
              )}
            </>
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
          {navLinks.map((link) => (
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
              {profile?.plan === "free" && (
                <a
                  href="/#pricing"
                  onClick={() => setMenuOpen(false)}
                  className="mt-2 inline-flex w-fit items-center gap-1 rounded-full bg-gradient-to-r from-secondary-container to-[#ff3d78] px-3 py-1.5 text-body-sm font-semibold text-on-primary shadow-[0_4px_16px_rgba(255,61,120,0.4)] transition-transform hover:scale-[1.03] active:scale-95"
                >
                  <span className="material-symbols-outlined text-[16px]">bolt</span>
                  Upgrade
                </a>
              )}
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
              <Link
                to="/history"
                onClick={() => setMenuOpen(false)}
                className={`py-1 text-body-md font-semibold ${overHero ? "text-white" : "text-on-surface"}`}
              >
                History
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
