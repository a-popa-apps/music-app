import { motion, useMotionValue, useSpring, useTransform } from "motion/react"
import type { MouseEvent, ReactNode } from "react"
import { useFinePointer } from "../hooks/useFinePointer"
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion"

interface TiltCardProps {
  children: ReactNode
  className?: string
  /** Max rotation in degrees at the card's edge. Keep this small --
   * pricing cards holding real copy get illegible past ~6-8deg. */
  maxTilt?: number
}

/** A light CSS-3D tilt that follows the cursor across the card's surface,
 * for the couple of cards on the page substantial enough to earn it
 * (the pricing cards). Pairs naturally with a specular highlight the
 * caller can layer on top using the same mouse position if it wants one.
 * Flat (no tilt) on touch devices and under reduced-motion. */
export function TiltCard({ children, className, maxTilt = 6 }: TiltCardProps) {
  const isFine = useFinePointer()
  const reducedMotion = usePrefersReducedMotion()
  const active = isFine && !reducedMotion

  const px = useMotionValue(0.5)
  const py = useMotionValue(0.5)
  const springConfig = { stiffness: 150, damping: 20, mass: 0.5 }
  const springX = useSpring(px, springConfig)
  const springY = useSpring(py, springConfig)

  const rotateX = useTransform(springY, [0, 1], [maxTilt, -maxTilt])
  const rotateY = useTransform(springX, [0, 1], [-maxTilt, maxTilt])

  if (!active) {
    return <div className={className}>{children}</div>
  }

  function handleMove(e: MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    px.set((e.clientX - rect.left) / rect.width)
    py.set((e.clientY - rect.top) / rect.height)
  }

  function handleLeave() {
    px.set(0.5)
    py.set(0.5)
  }

  return (
    <motion.div
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      style={{ rotateX, rotateY, transformPerspective: 1000 }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
