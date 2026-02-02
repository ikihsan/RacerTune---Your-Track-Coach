'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

export function Problem() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })

  const bullets = [
    'No screens in corners',
    'No generic advice',
    'No pressure to push',
  ]

  return (
    <section 
      ref={sectionRef} 
      className="relative py-32 lg:py-40 overflow-hidden"
      id="problem"
      aria-labelledby="problem-heading"
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-carbon-950 via-carbon-900 to-carbon-950" />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section Label */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 text-xs font-mono tracking-wider uppercase text-steel-400 border border-subtle rounded-full">
            The Problem
          </span>
          <h2 id="problem-heading" className="sr-only">Why Traditional Racing Apps Fail - The Problem with Screen-Based Coaching</h2>
        </motion.div>

        {/* Split Visual Comparison */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-16 mb-20">
          {/* Left - Chaos */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="aspect-[4/3] rounded-lg bg-carbon-800 border border-subtle overflow-hidden relative">
              {/* Chaotic Dashboard Visualization */}
              <div className="absolute inset-0 p-6 flex flex-col justify-center">
                {/* Simulated cluttered dashboard */}
                <div className="grid grid-cols-4 gap-2 mb-4">
                  {[...Array(16)].map((_, i) => (
                    <div
                      key={i}
                      className="aspect-square rounded bg-carbon-700 border border-steel-600/30"
                      style={{
                        opacity: 0.4 + Math.random() * 0.6,
                      }}
                    />
                  ))}
                </div>
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="h-3 rounded bg-carbon-700"
                      style={{ width: `${40 + Math.random() * 60}%` }}
                    />
                  ))}
                </div>
                {/* Overlay showing chaos */}
                <div className="absolute inset-0 bg-gradient-to-t from-carbon-800/90 to-transparent flex items-end p-6">
                  <div className="flex items-center gap-3 text-racing-red">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="font-mono text-sm">Cognitive Overload</span>
                  </div>
                </div>
              </div>
            </div>
            <p className="mt-4 text-steel-400 text-center">
              Screens everywhere. Data overload.
            </p>
          </motion.div>

          {/* Right - Clarity */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="relative"
          >
            <div className="aspect-[4/3] rounded-lg bg-carbon-800 border border-racing-orange/20 overflow-hidden relative">
              {/* Clean Cockpit Visualization */}
              <div className="absolute inset-0 flex items-center justify-center">
                {/* Minimalist steering wheel silhouette */}
                <svg
                  viewBox="0 0 200 200"
                  className="w-40 h-40 text-steel-600"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1"
                >
                  <circle cx="100" cy="100" r="70" />
                  <circle cx="100" cy="100" r="60" strokeDasharray="4 4" />
                  <line x1="30" y1="100" x2="70" y2="100" />
                  <line x1="130" y1="100" x2="170" y2="100" />
                  <line x1="100" y1="30" x2="100" y2="50" />
                </svg>
                {/* Focus indicator */}
                <div className="absolute inset-0 bg-gradient-to-t from-carbon-800/90 to-transparent flex items-end p-6">
                  <div className="flex items-center gap-3 text-racing-orange">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="font-mono text-sm">Full Focus</span>
                  </div>
                </div>
              </div>
            </div>
            <p className="mt-4 text-steel-400 text-center">
              Eyes on track. Voice guidance only.
            </p>
          </motion.div>
        </div>

        {/* Main Copy */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold text-white mb-6">
            Most racing apps overwhelm you with data.
            <br />
            <span className="text-racing-orange">RacerTune removes it.</span>
          </h2>
        </motion.div>

        {/* Bullet Points */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-12">
          {bullets.map((bullet, index) => (
            <motion.div
              key={bullet}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.7 + index * 0.15 }}
              className="flex items-center gap-3"
            >
              <div className="w-2 h-2 rounded-full bg-racing-orange" />
              <span className="text-steel-400 font-mono text-sm">{bullet}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
