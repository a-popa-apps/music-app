export function FinalCta() {
  return (
    <section className="w-full bg-black px-4 py-16 lg:px-12">
      <div className="relative mx-auto max-w-7xl overflow-hidden rounded-2xl bg-gradient-to-r from-[#1e1033] via-[#0d0d14] to-[#2e1408] px-6 py-16 text-center">
        <h2 className="mb-4 text-headline-xl tracking-tight text-white">
          Ready to prep this weekend's gig?
        </h2>
        <p className="mx-auto mb-8 max-w-xl text-body-lg text-white/70">
          Drag in your unorganized promo folder now. Free forever for up to 10
          tracks every month.
        </p>
        <a
          href="/#demo"
          className="inline-flex items-center gap-2 rounded-full bg-secondary-container px-8 py-4 text-headline-sm font-semibold text-white shadow-[0_8px_30px_rgba(255,107,53,0.45)] transition-transform hover:scale-[1.02] active:scale-95"
        >
          Open CratePrep
          <span className="material-symbols-outlined text-[20px]">
            arrow_forward
          </span>
        </a>
      </div>
    </section>
  )
}
