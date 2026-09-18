import { motion, useScroll, useSpring } from "motion/react"

/** Thin brand-gradient bar pinned under the fixed header, tracking how far
 * down the page the visitor has scrolled. Springs the raw scroll fraction
 * so it reads as fluid rather than stepping frame-to-frame. */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 300,
    damping: 40,
    mass: 0.2,
  })

  return (
    <motion.div
      aria-hidden
      className="fixed left-0 top-16 z-40 h-[2px] w-full origin-left bg-gradient-to-r from-secondary-container to-[#ff3d78]"
      style={{ scaleX }}
    />
  )
}
