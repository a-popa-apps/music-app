import { motion, useMotionValue, useSpring } from "motion/react"
import { useEffect, useState } from "react"
import { useFinePointer } from "../hooks/useFinePointer"
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion"

// Any element the cursor should "notice" -- grows the ring and hides the
// dot, signaling "this is clickable" without relying on the browser's own
// pointer cursor (which is hidden while this is active).
const INTERACTIVE_SELECTOR = "a, button, input, textarea, select, [role='button'], [data-cursor-hover]"

/** A small dot-and-ring cursor replacement, desktop-with-a-mouse only.
 * Sits fixed at the viewport level (mounted once in App) rather than per
 * section, since the ring needs to survive scrolling between sections and
 * track the real OS cursor position continuously. */
export function CustomCursor() {
  const isFine = useFinePointer()
  const reducedMotion = usePrefersReducedMotion()
  const [hovering, setHovering] = useState(false)
  const [visible, setVisible] = useState(false)

  const x = useMotionValue(-100)
  const y = useMotionValue(-100)
  // A touch of spring lag on the ring only -- the dot tracks the real
  // pointer exactly (0 lag reads as "broken" otherwise), the ring trailing
  // slightly behind is what actually reads as deliberate rather than janky.
  const ringX = useSpring(x, { stiffness: 500, damping: 40, mass: 0.5 })
  const ringY = useSpring(y, { stiffness: 500, damping: 40, mass: 0.5 })

  const active = isFine && !reducedMotion

  useEffect(() => {
    if (!active) return

    function handleMove(e: PointerEvent) {
      x.set(e.clientX)
      y.set(e.clientY)
      if (!visible) setVisible(true)
      const target = e.target as Element | null
      setHovering(Boolean(target?.closest(INTERACTIVE_SELECTOR)))
    }
    function handleLeave() {
      setVisible(false)
    }

    window.addEventListener("pointermove", handleMove)
    document.documentElement.addEventListener("pointerleave", handleLeave)
    document.body.classList.add("custom-cursor-active")
    return () => {
      window.removeEventListener("pointermove", handleMove)
      document.documentElement.removeEventListener("pointerleave", handleLeave)
      document.body.classList.remove("custom-cursor-active")
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active])

  if (!active) return null

  return (
    <>
      <motion.div
        aria-hidden
        className="pointer-events-none fixed left-0 top-0 z-[9999] h-2 w-2 rounded-full bg-secondary-container mix-blend-difference"
        style={{ x, y, translateX: "-50%", translateY: "-50%" }}
        animate={{ opacity: visible ? 1 : 0, scale: hovering ? 0 : 1 }}
        transition={{ duration: 0.15 }}
      />
      <motion.div
        aria-hidden
        className="pointer-events-none fixed left-0 top-0 z-[9999] rounded-full border border-white mix-blend-difference"
        style={{ x: ringX, y: ringY, translateX: "-50%", translateY: "-50%" }}
        animate={{
          opacity: visible ? 1 : 0,
          width: hovering ? 56 : 32,
          height: hovering ? 56 : 32,
        }}
        transition={{ duration: 0.25, ease: "easeOut" }}
      />
    </>
  )
}
