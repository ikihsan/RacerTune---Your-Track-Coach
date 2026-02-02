'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const pillars = [
  {
    id: 'sensor-fusion',
    title: 'Sensor Fusion',
    subtitle: 'GPS + IMU automatically build the track.',
    icon: (
      <svg viewBox="0 0 64 64" className="w-full h-full" fill="none" stroke="currentColor" strokeWidth="1.5">
        {/* GPS satellite */}
        <circle cx="32" cy="12" r="4" />
        <path d="M28 16L20 32M36 16L44 32" strokeDasharray="2 2" />
        {/* IMU sensor */}
        <rect x="22" y="36" width="20" height="16" rx="2" />
        <circle cx="32" cy="44" r="4" />
        {/* Connection lines */}
        <path d="M32 20V36" className="text-racing-orange" />
        <circle cx="32" cy="28" r="2" className="text-racing-orange" fill="currentColor" />
      </svg>
    ),
    diagram: (
      <div className="relative h-32 w-full">
        {/* GPS Wave */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 200 80" preserveAspectRatio="none">
          <path
            d="M0 40 Q 50 10, 100 40 T 200 40"
            fill="none"
            stroke="#06B6D4"
            strokeWidth="1"
            className="opacity-60"
          />
          <path
            d="M0 50 Q 50 20, 100 50 T 200 50"
            fill="none"
            stroke="#EA580C"
            strokeWidth="1"
            className="opacity-60"
          />
        </svg>
        {/* Data points */}
        <div className="absolute inset-0 flex items-center justify-around">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-telemetry-cyan"
              style={{ opacity: 0.4 + i * 0.15 }}
            />
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 'physics-envelopes',
    title: 'Physics Envelopes',
    subtitle: 'Never exceeds controllable limits.',
    icon: (
      <svg viewBox="0 0 64 64" className="w-full h-full" fill="none" stroke="currentColor" strokeWidth="1.5">
        {/* Friction circle */}
        <circle cx="32" cy="32" r="20" strokeDasharray="4 2" />
        <circle cx="32" cy="32" r="14" className="text-racing-orange" />
        {/* Force vectors */}
        <path d="M32 32L32 18" strokeWidth="2" />
        <path d="M32 32L44 26" strokeWidth="2" className="text-racing-orange" />
        <polygon points="32,15 29,21 35,21" fill="currentColor" />
        <polygon points="46,24 40,26 42,32" fill="currentColor" className="text-racing-orange" />
      </svg>
    ),
    diagram: (
      <div className="relative h-32 w-full flex items-center justify-center">
        {/* Friction Circle Visualization */}
        <div className="relative w-28 h-28">
          <svg viewBox="0 0 100 100" className="w-full h-full">
            {/* Outer limit */}
            <circle cx="50" cy="50" r="45" fill="none" stroke="#4B5563" strokeWidth="1" />
            {/* Safe zone */}
            <circle cx="50" cy="50" r="35" fill="none" stroke="#EA580C" strokeWidth="1.5" strokeDasharray="4 2" />
            {/* Current force vector */}
            <line x1="50" y1="50" x2="65" y2="35" stroke="#06B6D4" strokeWidth="2" />
            <circle cx="65" cy="35" r="3" fill="#06B6D4" />
            {/* Axes */}
            <line x1="50" y1="10" x2="50" y2="90" stroke="#25292E" strokeWidth="0.5" />
            <line x1="10" y1="50" x2="90" y2="50" stroke="#25292E" strokeWidth="0.5" />
          </svg>
          <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-xs font-mono text-steel-500">
            G-Force
          </span>
        </div>
      </div>
    ),
  },
  {
    id: 'adaptive-learning',
    title: 'Adaptive Learning',
    subtitle: 'Improves accuracy with clean laps.',
    icon: (
      <svg viewBox="0 0 64 64" className="w-full h-full" fill="none" stroke="currentColor" strokeWidth="1.5">
        {/* Brain/learning symbol */}
        <path d="M20 40C16 36 16 28 20 24C24 20 32 20 32 24" />
        <path d="M44 40C48 36 48 28 44 24C40 20 32 20 32 24" />
        <path d="M32 24V44" strokeDasharray="2 2" />
        {/* Progress nodes */}
        <circle cx="32" cy="28" r="3" className="text-steel-500" />
        <circle cx="32" cy="36" r="3" className="text-racing-orange" />
        <circle cx="32" cy="44" r="3" fill="currentColor" className="text-racing-orange" />
      </svg>
    ),
    diagram: (
      <div className="relative h-32 w-full">
        {/* Learning progression bars */}
        <div className="flex items-end justify-center gap-3 h-full pb-6">
          {[40, 55, 65, 75, 88, 95].map((height, i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <div
                className="w-6 rounded-t transition-all duration-500"
                style={{
                  height: `${height}%`,
                  background: i < 4 ? '#4B5563' : i === 4 ? '#EA580C' : '#DC2626',
                  opacity: 0.6 + i * 0.07,
                }}
              />
              <span className="text-[10px] font-mono text-steel-600">L{i + 1}</span>
            </div>
          ))}
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-steel-700" />
      </div>
    ),
  },
]

export function HowItWorks() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })

  return (
    <section id="how-it-works" ref={sectionRef} className="relative py-32 lg:py-40">
      {/* Background */}
      <div className="absolute inset-0 bg-carbon-950" />
      <div className="absolute inset-0 grid-overlay opacity-20" />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 text-xs font-mono tracking-wider uppercase text-steel-400 border border-subtle rounded-full mb-6">
            How It Works
          </span>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold text-white mb-4">
            Engineered, Not Guessed
          </h2>
          <p className="text-steel-400 text-lg max-w-2xl mx-auto">
            Three core systems work together to provide accurate, physics-based guidance.
          </p>
        </motion.div>

        {/* Pillars Grid */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {pillars.map((pillar, index) => (
            <motion.div
              key={pillar.id}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.2 + index * 0.15 }}
              className="group"
            >
              <div className="h-full bg-carbon-900 border border-subtle rounded-lg p-8 hover:border-racing-orange/30 transition-colors duration-500">
                {/* Icon */}
                <div className="w-16 h-16 mb-6 text-steel-400 group-hover:text-racing-orange transition-colors duration-500">
                  {pillar.icon}
                </div>

                {/* Title */}
                <h3 className="font-display text-xl font-semibold text-white mb-2">
                  {pillar.title}
                </h3>

                {/* Subtitle */}
                <p className="text-steel-400 text-sm mb-8">
                  {pillar.subtitle}
                </p>

                {/* Diagram */}
                <div className="border-t border-subtle pt-6">
                  {pillar.diagram}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Connection Line */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={isInView ? { scaleX: 1 } : {}}
          transition={{ duration: 1.2, delay: 0.8 }}
          className="hidden md:block h-px bg-gradient-to-r from-transparent via-racing-orange/40 to-transparent mt-12"
        />
      </div>
    </section>
  )
}
