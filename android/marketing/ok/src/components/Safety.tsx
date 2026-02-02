'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const safetyPoints = [
  {
    title: 'Physics is the ceiling',
    description: 'Advice never exceeds calculated grip limits.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
  },
  {
    title: 'AI never decides safety',
    description: 'The driver always maintains full control.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    title: 'Silence over bad advice',
    description: 'When uncertain, RacerTune stays quiet.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6">
        <path d="M5.586 15.414a2 2 0 001.414.586h3l4 4v-4h2a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v7a2 2 0 00.586 1.414z" />
        <line x1="9" y1="10" x2="15" y2="10" strokeDasharray="2 2" />
      </svg>
    ),
  },
  {
    title: 'Offline, on-device',
    description: 'No cloud dependency. Works anywhere.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6">
        <rect x="5" y="2" width="14" height="20" rx="2" />
        <line x1="12" y1="18" x2="12" y2="18.01" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: 'Closed-track only',
    description: 'Designed exclusively for controlled environments.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
      </svg>
    ),
  },
]

export function Safety() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })

  return (
    <section id="safety" ref={sectionRef} className="relative py-32 lg:py-40">
      {/* Background */}
      <div className="absolute inset-0 bg-carbon-950" />

      {/* Subtle border accent */}
      <div className="absolute left-0 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-racing-orange/30 to-transparent" />

      <div className="relative max-w-6xl mx-auto px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="mb-20"
        >
          <span className="inline-block px-4 py-1.5 text-xs font-mono tracking-wider uppercase text-steel-400 border border-subtle rounded-full mb-6">
            Safety First
          </span>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold text-white mb-4">
            Trust Built on Discipline
          </h2>
          <p className="text-steel-400 text-lg max-w-xl">
            Every decision follows a strict hierarchy: safety, then accuracy, then helpfulness.
          </p>
        </motion.div>

        {/* Safety Checklist */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {safetyPoints.map((point, index) => (
            <motion.div
              key={point.title}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.1 + index * 0.1 }}
              className="group"
            >
              <div className="h-full p-6 rounded-lg border border-subtle bg-carbon-900/50 hover:border-steel-600 transition-colors duration-300">
                {/* Check Icon + Title Row */}
                <div className="flex items-start gap-4 mb-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-carbon-800 border border-subtle flex items-center justify-center text-steel-400 group-hover:text-racing-orange group-hover:border-racing-orange/30 transition-colors duration-300">
                    {point.icon}
                  </div>
                  <div>
                    <h3 className="font-display text-lg font-medium text-white mb-1">
                      {point.title}
                    </h3>
                    <p className="text-steel-500 text-sm">
                      {point.description}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Trust Statement */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-16 pt-16 border-t border-subtle"
        >
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full border-2 border-racing-orange/40 flex items-center justify-center">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="w-6 h-6 text-racing-orange"
                >
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M9 12l2 2 4-4" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">Safety-First Architecture</p>
                <p className="text-steel-500 text-sm">Every line of code prioritizes driver safety.</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-steel-400 text-sm font-mono">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Deterministic • Predictable • Reliable
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
