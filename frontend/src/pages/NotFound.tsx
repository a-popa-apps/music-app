import { Link } from "react-router-dom"
import { Header } from "../components/Header"

export function NotFound() {
  return (
    <>
      <Header />
      <div className="flex min-h-screen w-full flex-col items-center justify-center gap-4 bg-surface px-4 pt-16 text-center">
        <span className="font-mono text-display-hero-mobile tracking-tighter text-on-surface">
          404
        </span>
        <p className="text-body-lg text-on-surface-variant">
          This page doesn't exist.
        </p>
        <Link
          to="/"
          className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
        >
          Back to home
        </Link>
      </div>
    </>
  )
}
