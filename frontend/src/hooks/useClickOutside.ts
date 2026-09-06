import { useEffect } from "react"

/** Calls onOutside when a mousedown/touchstart lands outside the ref'd
 * element, while enabled. Only listens while enabled so closed
 * dropdowns/tooltips don't pay for a global listener. */
export function useClickOutside(
  ref: React.RefObject<HTMLElement | null>,
  onOutside: () => void,
  enabled: boolean
) {
  useEffect(() => {
    if (!enabled) return

    function handlePointerDown(event: MouseEvent | TouchEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        onOutside()
      }
    }

    document.addEventListener("mousedown", handlePointerDown)
    document.addEventListener("touchstart", handlePointerDown)
    return () => {
      document.removeEventListener("mousedown", handlePointerDown)
      document.removeEventListener("touchstart", handlePointerDown)
    }
  }, [enabled, onOutside, ref])
}
