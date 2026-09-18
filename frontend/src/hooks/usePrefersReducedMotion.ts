import { useEffect, useState } from "react"

/** Live-updating read of the user's OS-level reduced-motion preference --
 * every micro-interaction hook below checks this before doing anything
 * beyond a plain opacity fade. */
export function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches
  )

  useEffect(() => {
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)")
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
    mql.addEventListener("change", handler)
    return () => mql.removeEventListener("change", handler)
  }, [])

  return reduced
}
