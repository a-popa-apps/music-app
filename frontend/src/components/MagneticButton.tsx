import { motion, useMotionValue, useSpring } from "motion/react"
import type { MouseEvent, ReactNode } from "react"
import { useFinePointer } from "../hooks/useFinePointer"
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion"

interface MagneticButtonProps {
  children: ReactNode
  className?: string
  /** How far the button is willing to drift toward the cursor, in px. */
  strength?: number
  onClick?: () => void
  disabled?: boolean
  type?: "button" | "submit"
  /** Renders an <a> instead of a <button> -- for CTAs that are really
   * anchor-scroll or navigation links, not form actions. */
  href?: string
}

/** Wraps a CTA so it pulls slightly toward the cursor while hovered, then
 * springs back on leave -- a subtle "this wants to be clicked" cue for the
 * handful of buttons on the page that most need the extra weight (primary
 * conversion actions only; wrapping every button would just read as
 * twitchy). No-ops on touch devices and under reduced-motion, rendering a
 * plain element so it never blocks a tap or an assistive click. */
export function MagneticButton({
  children,
  className,
  strength = 18,
  onClick,
  disabled,
  type = "button",
  href,
}: MagneticButtonProps) {
  const isFine = useFinePointer()
  const reducedMotion = usePrefersReducedMotion()
  const active = isFine && !reducedMotion

  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const springX = useSpring(x, { stiffness: 200, damping: 15, mass: 0.4 })
  const springY = useSpring(y, { stiffness: 200, damping: 15, mass: 0.4 })

  if (!active) {
    if (href) {
      return (
        <a href={href} onClick={onClick} className={className}>
          {children}
        </a>
      )
    }
    return (
      <button type={type} onClick={onClick} disabled={disabled} className={className}>
        {children}
      </button>
    )
  }

  function handleMove(e: MouseEvent<HTMLElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    const relX = e.clientX - (rect.left + rect.width / 2)
    const relY = e.clientY - (rect.top + rect.height / 2)
    x.set((relX / (rect.width / 2)) * strength)
    y.set((relY / (rect.height / 2)) * strength)
  }

  function handleLeave() {
    x.set(0)
    y.set(0)
  }

  if (href) {
    return (
      <motion.a
        href={href}
        onClick={onClick}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
        style={{ x: springX, y: springY }}
        className={className}
      >
        {children}
      </motion.a>
    )
  }

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      style={{ x: springX, y: springY }}
      className={className}
    >
      {children}
    </motion.button>
  )
}
