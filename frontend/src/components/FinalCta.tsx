export function FinalCta() {
  return (
    <section className="w-full bg-black px-4 py-16 lg:px-12">
      <div className="relative mx-auto max-w-7xl rounded-[calc(1rem+4px)] bg-gradient-to-r from-secondary-container to-[#ff3d78] p-[2px] shadow-[0_0_70px_rgba(255,107,53,0.3)]">
        <div className="overflow-hidden rounded-2xl bg-[#12122a]/90 px-6 py-16 text-center backdrop-blur-md">
          <h2 className="mb-4 text-headline-xl tracking-tight text-white">
            Ready to prep this weekend's gig?
          </h2>
          <p className="mx-auto mb-8 max-w-xl text-body-lg text-white/70">
            Drag in your unorganized promo folder now. Free forever for up to
            10 tracks every month.
          </p>
          <a
            href="/#demo"
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-secondary-container to-[#ff3d78] px-8 py-4 text-headline-sm font-semibold text-on-primary shadow-[0_8px_30px_rgba(255,107,53,0.45)] transition-transform hover:scale-[1.02] active:scale-95"
          >
            Open CratePrep
            <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
              arrow_forward
            </span>
          </a>
        </div>
      </div>
    </section>
  )
}
