'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const techSpecs = [
  { label: 'Deterministic physics', detail: 'Predictable, repeatable calculations' },
  { label: 'Sensor fusion', detail: 'GPS + IMU integration' },
  { label: 'On-device processing', detail: 'No latency, full privacy' },
  { label: 'No cloud dependency', detail: 'Works offline, anywhere' },
]

export function Tech() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })

  return (
    <section id="tech" ref={sectionRef} className="relative py-32 lg:py-40">
      {/* Background */}
      <div className="absolute inset-0 bg-carbon-950" />
      <div className="absolute inset-0 grid-overlay opacity-10" />

      <div className="relative max-w-4xl mx-auto px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 text-xs font-mono tracking-wider uppercase text-steel-400 border border-subtle rounded-full mb-6">
            Technology
          </span>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-white mb-4">
            Built With
          </h2>
        </motion.div>

        {/* Tech Specs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-carbon-900/50 border border-subtle rounded-lg overflow-hidden"
        >
          {techSpecs.map((spec, index) => (
            <motion.div
              key={spec.label}
              initial={{ opacity: 0, x: -20 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
              className={`flex items-center justify-between p-6 ${
                index !== techSpecs.length - 1 ? 'border-b border-subtle' : ''
              }`}
            >
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 rounded-full bg-racing-orange" />
                <span className="font-mono text-white">{spec.label}</span>
              </div>
              <span className="text-steel-500 text-sm hidden sm:block">{spec.detail}</span>
            </motion.div>
          ))}
        </motion.div>

        {/* Architecture Diagram */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-16"
        >
          <div className="bg-carbon-900/30 border border-subtle rounded-lg p-8">
            <div className="flex flex-col md:flex-row items-center justify-center gap-8">
              {/* Input */}
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-3 rounded-lg border border-steel-600 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-8 h-8 text-steel-400">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
                  </svg>
                </div>
                <p className="font-mono text-xs text-steel-400">SENSORS</p>
                <p className="text-xs text-steel-600">GPS + IMU</p>
              </div>

              {/* Arrow */}
              <svg viewBox="0 0 40 24" className="w-10 h-6 text-steel-600 hidden md:block">
                <path d="M0 12h35M30 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="1.5" />
              </svg>
              <svg viewBox="0 0 24 40" className="w-6 h-10 text-steel-600 md:hidden">
                <path d="M12 0v35M6 30l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="1.5" />
              </svg>

              {/* Process */}
              <div className="text-center">
                <div className="w-20 h-20 mx-auto mb-3 rounded-lg border border-racing-orange/40 bg-racing-orange/10 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-10 h-10 text-racing-orange">
                    <rect x="4" y="4" width="16" height="16" rx="2" />
                    <path d="M9 9h6M9 12h6M9 15h4" />
                  </svg>
                </div>
                <p className="font-mono text-xs text-racing-orange">PHYSICS ENGINE</p>
                <p className="text-xs text-steel-600">On-device</p>
              </div>

              {/* Arrow */}
              <svg viewBox="0 0 40 24" className="w-10 h-6 text-steel-600 hidden md:block">
                <path d="M0 12h35M30 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="1.5" />
              </svg>
              <svg viewBox="0 0 24 40" className="w-6 h-10 text-steel-600 md:hidden">
                <path d="M12 0v35M6 30l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="1.5" />
              </svg>

              {/* Output */}
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-3 rounded-lg border border-steel-600 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-8 h-8 text-steel-400">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
                  </svg>
                </div>
                <p className="font-mono text-xs text-steel-400">VOICE OUTPUT</p>
                <p className="text-xs text-steel-600">Real-time</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* No Buzzwords Note */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="text-center text-steel-600 text-sm mt-8"
        >
          No buzzwords. No hype. Just engineering.
        </motion.p>
      </div>
    </section>
  )
}
