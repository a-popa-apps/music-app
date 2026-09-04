import { useState } from "react"

const NAV_LINKS = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
]

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="fixed top-0 z-50 w-full bg-surface/90 shadow-[0_1px_8px_rgba(0,0,0,0.03)] backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 lg:px-12">
        <div className="flex items-center gap-2">
          <span className="font-mono text-headline-sm font-bold tracking-tight text-on-surface">
            quickie.
          </span>
        </div>
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
          <a
            href="#pricing"
            className="inline-flex items-center justify-center rounded-full bg-primary px-6 py-2 text-body-sm font-semibold text-on-primary transition-all hover:bg-inverse-surface"
          >
            Go Pro
          </a>
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
        </nav>
      )}
    </header>
  )
}
