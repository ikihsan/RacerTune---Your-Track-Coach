'use client'

import { useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'

export function FinalCTA() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (email) {
      // Handle form submission
      setSubmitted(true)
    }
  }

  return (
    <section id="early-access" ref={sectionRef} className="relative py-32 lg:py-48">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-carbon-900 via-carbon-950 to-carbon-950" />

      {/* Subtle grid */}
      <div className="absolute inset-0 grid-overlay opacity-20" />

      {/* Accent lines */}
      <div className="absolute top-0 left-1/4 w-px h-32 bg-gradient-to-b from-racing-orange/40 to-transparent" />
      <div className="absolute top-0 right-1/4 w-px h-32 bg-gradient-to-b from-racing-orange/40 to-transparent" />

      <div className="relative max-w-3xl mx-auto px-6 lg:px-8 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 mb-8 px-4 py-2 rounded-full border border-racing-orange/30 bg-racing-orange/5"
        >
          <span className="w-2 h-2 rounded-full bg-racing-orange animate-pulse" />
          <span className="text-xs font-mono text-racing-orange tracking-wider uppercase">
            Early Access
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold text-white mb-6"
        >
          Join the Early Grid
        </motion.h2>

        {/* Subline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-steel-400 text-lg mb-12 max-w-xl mx-auto"
        >
          Be part of the first drivers coached by RacerTune.
          <br />
          <span className="text-steel-500">Limited spots available.</span>
        </motion.p>

        {/* Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          {!submitted ? (
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                className="flex-1 px-5 py-4 rounded-lg bg-carbon-800 border border-subtle text-white placeholder:text-steel-600 focus:outline-none focus:border-racing-orange/50 transition-colors"
              />
              <button
                type="submit"
                className="px-8 py-4 rounded-lg bg-racing-orange text-white font-medium hover:bg-racing-red transition-colors duration-300 whitespace-nowrap"
              >
                Join Early Access
              </button>
            </form>
          ) : (
            <div className="flex flex-col items-center gap-4 p-8 rounded-lg border border-racing-orange/30 bg-racing-orange/5">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="w-12 h-12 text-racing-orange"
              >
                <path d="M20 6L9 17l-5-5" />
              </svg>
              <p className="text-white font-medium">You're on the grid.</p>
              <p className="text-steel-400 text-sm">We'll be in touch when RacerTune is ready.</p>
            </div>
          )}
        </motion.div>

        {/* Secondary CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-8"
        >
          <a
            href="#"
            className="inline-flex items-center gap-2 text-steel-400 hover:text-white transition-colors text-sm"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            Follow Development
          </a>
        </motion.div>

        {/* Trust indicators */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-16 pt-16 border-t border-subtle"
        >
          <div className="flex flex-wrap items-center justify-center gap-8 text-steel-600 text-xs font-mono">
            <span>Privacy-first</span>
            <span className="w-1 h-1 rounded-full bg-steel-700" />
            <span>No spam</span>
            <span className="w-1 h-1 rounded-full bg-steel-700" />
            <span>Unsubscribe anytime</span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
