// Visually mirrors the "Go Pro for more tracks & priority detection"
// gradient banner already on ProfileDetails.tsx, just as a centered
// overlay instead of an inline banner -- used when a free-plan user tries
// to flip a Pro-only toggle.
export function UpgradeModal({
  title,
  description,
  loading,
  onUpgrade,
  onClose,
}: {
  title: string
  description: string
  loading?: boolean
  onUpgrade: () => void
  onClose: () => void
}) {
  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-gradient-to-r from-secondary-container to-[#ff3d78] p-6 text-on-primary shadow-[0_8px_30px_rgba(255,61,120,0.45)]"
      >
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-[32px]">bolt</span>
          <div className="flex flex-1 flex-col gap-1">
            <span className="text-headline-sm font-bold">{title}</span>
            <span className="text-body-sm text-on-primary/80">{description}</span>
          </div>
        </div>
        <div className="mt-5 flex items-center justify-end gap-4">
          <button
            onClick={onClose}
            className="text-body-sm font-semibold text-on-primary/80 underline hover:text-on-primary"
          >
            Maybe later
          </button>
          <button
            onClick={onUpgrade}
            disabled={loading}
            className="whitespace-nowrap rounded-full bg-white px-5 py-2 text-body-sm font-semibold text-[#ff3d78] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Loading..." : "Upgrade to Pro"}
          </button>
        </div>
      </div>
    </div>
  )
}
