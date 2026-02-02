'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { RacingLineCanvas } from './three/RacingLineCanvas'

export function Hero() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  })

  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const y = useTransform(scrollYProgress, [0, 0.5], [0, 100])

  return (
    <section
      ref={containerRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
    >
      {/* Background Grid */}
      <div className="absolute inset-0 grid-overlay opacity-40" />

      {/* 3D Racing Line Background */}
      <div className="absolute inset-0">
        <RacingLineCanvas />
      </div>

      {/* Gradient Overlays */}
      <div className="absolute inset-0 bg-gradient-to-b from-carbon-950 via-transparent to-carbon-950" />
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-carbon-950 to-transparent" />

      {/* Content */}
      <motion.div
        style={{ opacity, y }}
        className="relative z-10 max-w-5xl mx-auto px-6 text-center"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="inline-flex items-center gap-2 mb-8 px-4 py-2 rounded-full border border-subtle bg-carbon-900/50"
        >
          <span className="w-2 h-2 rounded-full bg-racing-orange animate-pulse" />
          <span className="text-xs font-mono text-steel-400 tracking-wider uppercase">
            Early Development
          </span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
          className="font-display text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight mb-6"
        >
          <span className="text-white">Racer</span>
          <span className="text-gradient-orange">Tune</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="font-display text-2xl sm:text-3xl lg:text-4xl text-white/90 mb-4"
        >
          Your AI Race Engineer.
        </motion.p>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="text-xl sm:text-2xl text-racing-orange font-medium mb-6"
        >
          Trust over performance. Always.
        </motion.p>

        {/* Supporting Line */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="text-steel-400 text-lg max-w-xl mx-auto mb-12"
        >
          Voice-only. Physics-first. Built for the track.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="#how-it-works"
            className="group px-8 py-4 rounded bg-white text-carbon-950 font-medium text-base hover:bg-steel-400 transition-colors duration-300 flex items-center gap-3"
          >
            See How It Works
            <svg
              className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </a>
          <a
            href="#early-access"
            className="px-8 py-4 rounded border border-steel-600 text-steel-400 font-medium text-base hover:border-racing-orange hover:text-racing-orange transition-colors duration-300"
          >
            Join the Early Grid
          </a>
        </motion.div>


      </motion.div>
    </section>
  )
}
