const PRODUCT_LINKS = [
  { label: "Key & BPM Analysis", href: "#features" },
  { label: "Genre Sorting", href: "#features" },
  { label: "Pricing", href: "#pricing" },
]

const RESOURCE_LINKS = [
  { label: "FAQ", href: "#faq" },
  { label: "How it works", href: "#how-it-works" },
]

export function Footer() {
  return (
    <footer className="w-full bg-tertiary-container text-inverse-on-surface">
      <div className="mx-auto w-full max-w-7xl px-4 pb-12 pt-16 lg:px-12">
        <div className="grid grid-cols-1 gap-8 pb-12 md:grid-cols-4">
          <div className="flex flex-col gap-2 md:col-span-2">
            <span className="text-headline-sm font-bold tracking-tight text-inverse-on-surface">
              crateprep.
            </span>
            <p className="max-w-md text-body-md text-on-tertiary-container">
              Surgical track organization for precision DJs, selector crates,
              and live performance harmony.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <span className="font-mono text-meta-badge font-semibold uppercase tracking-wider text-on-tertiary-container">
              Product
            </span>
            {PRODUCT_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-body-sm text-inverse-on-surface transition-colors hover:text-secondary-container"
              >
                {link.label}
              </a>
            ))}
          </div>
          <div className="flex flex-col gap-2">
            <span className="font-mono text-meta-badge font-semibold uppercase tracking-wider text-on-tertiary-container">
              Resources
            </span>
            {RESOURCE_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-body-sm text-inverse-on-surface transition-colors hover:text-secondary-container"
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-center justify-between gap-4 pt-6 md:flex-row">
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 animate-pulse rounded-full bg-secondary-container" />
            <span className="font-mono text-meta-numeric text-on-tertiary-container">
              Built for zero friction
            </span>
          </div>
          <div className="text-body-sm text-on-tertiary-container">
            &copy; 2026 CratePrep. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  )
}
