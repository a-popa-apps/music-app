import { motion } from "motion/react"
import type { ReactNode } from "react"
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion"

interface RevealProps {
  children: ReactNode
  className?: string
  /** Stagger delay in seconds -- pass index * 0.08 or so across a grid of
   * siblings so they cascade in rather than all popping at once. */
  delay?: number
  /** Slide-up distance in px before the fade completes. */
  distance?: number
}

/** Fades + slides an element up as it enters the viewport, once, then
 * leaves it alone (no re-triggering on scroll back up -- that reads as
 * flickery on a marketing page you're meant to read top to bottom once).
 * Reduces to a plain opacity fade under prefers-reduced-motion. */
export function Reveal({ children, className, delay = 0, distance = 24 }: RevealProps) {
  const reducedMotion = usePrefersReducedMotion()

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: reducedMotion ? 0 : distance }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: reducedMotion ? 0.2 : 0.6, delay, ease: [0.21, 0.47, 0.32, 0.98] }}
    >
      {children}
    </motion.div>
  )
}
