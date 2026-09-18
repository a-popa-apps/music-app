import { useEffect, useState } from "react"

/** True only for devices with an actual mouse/trackpad -- touch devices
 * report "coarse" here, so magnetic buttons, the custom cursor, and 3D
 * tilt all skip themselves rather than doing something meaningless (or
 * actively annoying, in the cursor's case) on a phone or tablet. */
export function useFinePointer() {
  const [fine, setFine] = useState(
    () => window.matchMedia("(pointer: fine)").matches
  )

  useEffect(() => {
    const mql = window.matchMedia("(pointer: fine)")
    const handler = (e: MediaQueryListEvent) => setFine(e.matches)
    mql.addEventListener("change", handler)
    return () => mql.removeEventListener("change", handler)
  }, [])

  return fine
}
