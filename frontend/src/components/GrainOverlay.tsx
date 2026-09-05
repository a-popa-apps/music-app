const NOISE_BG =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")"

/** Subtle photographic grain matching the hero image's own texture, for
 * sections using a flat/gradient color instead of the actual photo. */
export function GrainOverlay() {
  return (
    <div
      className="pointer-events-none absolute inset-0 opacity-[0.15] mix-blend-screen"
      style={{ backgroundImage: NOISE_BG }}
    />
  )
}
