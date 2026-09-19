import { useEffect } from "react"

/** Calls onEscape when the Escape key is pressed, while enabled. Only
 * listens while enabled so closed modals/menus don't pay for a global
 * listener. */
export function useEscapeKey(onEscape: () => void, enabled: boolean) {
  useEffect(() => {
    if (!enabled) return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onEscape()
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [enabled, onEscape])
}
