import { createPortal } from "react-dom"
import { AuthForm } from "./AuthForm"

// A modal alternative to the /auth route -- opened from the landing page's
// Header (Sign In / Go Pro) so signing in doesn't feel like leaving the
// page you were on. Dismisses on a backdrop click or the close button,
// same interaction pattern as Modal.tsx/UpgradeModal.tsx.
//
// Rendered via a portal into document.body: Header has backdrop-blur-*
// (backdrop-filter), which creates a new containing block for
// position:fixed descendants, so a plain nested `fixed inset-0` here would
// size itself against the header bar instead of the viewport.
export function AuthModal({
  onClose,
  initialMode,
}: {
  onClose: () => void
  initialMode?: "login" | "signup"
}) {
  return createPortal(
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-md rounded border border-white/10 bg-[#12122a]/95 p-8 shadow-[0_20px_60px_rgba(0,0,0,0.5)] backdrop-blur-md"
      >
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-white/60 transition-colors hover:bg-white/10 hover:text-white"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>

        <div className="mb-6 text-center">
          <span className="font-mono text-headline-sm font-bold tracking-tight text-white">
            crateprep.
          </span>
        </div>

        <AuthForm onSuccess={onClose} initialMode={initialMode} />
      </div>
    </div>,
    document.body
  )
}
