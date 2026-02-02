'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const audiences = [
  {
    id: 'track-day',
    title: 'Track Day Drivers',
    description: 'Weekend enthusiasts looking to improve safely.',
    icon: (
      <svg viewBox="0 0 80 80" className="w-full h-full" fill="none" stroke="currentColor" strokeWidth="1">
        {/* Helmet silhouette */}
        <ellipse cx="40" cy="45" rx="25" ry="22" className="text-steel-500" />
        <path d="M20 42 C20 28, 60 28, 60 42" className="text-steel-400" />
        <rect x="22" y="38" width="36" height="8" rx="4" className="text-racing-orange" fill="currentColor" opacity="0.3" />
      </svg>
    ),
  },
  {
    id: 'amateur-racers',
    title: 'Amateur Racers',
    description: 'Competitors who need reliable, consistent coaching.',
    icon: (
      <svg viewBox="0 0 80 80" className="w-full h-full" fill="none" stroke="currentColor" strokeWidth="1">
        {/* Racing flag pattern */}
        <rect x="20" y="20" width="40" height="40" className="text-steel-500" />
        <rect x="20" y="20" width="10" height="10" fill="currentColor" className="text-steel-500" />
        <rect x="40" y="20" width="10" height="10" fill="currentColor" className="text-steel-500" />
        <rect x="30" y="30" width="10" height="10" fill="currentColor" className="text-steel-500" />
        <rect x="50" y="30" width="10" height="10" fill="currentColor" className="text-steel-500" />
        <rect x="20" y="40" width="10" height="10" fill="currentColor" className="text-steel-500" />
        <rect x="40" y="40" width="10" height="10" fill="currentColor" className="text-steel-500" />
        <rect x="30" y="50" width="10" height="10" fill="currentColor" className="text-steel-500" />
        <rect x="50" y="50" width="10" height="10" fill="currentColor" className="text-steel-500" />
      </svg>
    ),
  },
  {
    id: 'karting',
    title: 'Karting Enthusiasts',
    description: 'Precision matters most when margins are smallest.',
    icon: (
      <svg viewBox="0 0 80 80" className="w-full h-full" fill="none" stroke="currentColor" strokeWidth="1">
        {/* Kart silhouette */}
        <ellipse cx="25" cy="55" rx="8" ry="8" className="text-steel-500" />
        <ellipse cx="55" cy="55" rx="8" ry="8" className="text-steel-500" />
        <path d="M20 48 L60 48 L55 40 L25 40 Z" className="text-steel-400" />
        <rect x="35" y="35" width="10" height="8" rx="2" className="text-racing-orange" />
      </svg>
    ),
  },
  {
    id: 'instructors',
    title: 'Driving Instructors',
    description: 'Supplement your coaching with objective data.',
    icon: (
      <svg viewBox="0 0 80 80" className="w-full h-full" fill="none" stroke="currentColor" strokeWidth="1">
        {/* Instructor with clipboard */}
        <circle cx="40" cy="28" r="10" className="text-steel-500" />
        <path d="M25 70 L25 48 C25 42, 55 42, 55 48 L55 70" className="text-steel-400" />
        <rect x="32" y="50" width="16" height="20" rx="2" className="text-racing-orange" fill="currentColor" opacity="0.3" />
        <line x1="35" y1="56" x2="45" y2="56" className="text-racing-orange" />
        <line x1="35" y1="60" x2="45" y2="60" className="text-racing-orange" />
        <line x1="35" y1="64" x2="42" y2="64" className="text-racing-orange" />
      </svg>
    ),
  },
]

export function Audience() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })

  return (
    <section ref={sectionRef} className="relative py-32 lg:py-40">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-carbon-950 via-carbon-900 to-carbon-950" />

      <div className="relative max-w-6xl mx-auto px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 text-xs font-mono tracking-wider uppercase text-steel-400 border border-subtle rounded-full mb-6">
            Who It's For
          </span>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold text-white mb-4">
            For Drivers Who Want to Improve
          </h2>
          <p className="text-steel-400 text-lg">
            Without guessing. Without distraction.
          </p>
        </motion.div>

        {/* Audience Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {audiences.map((audience, index) => (
            <motion.div
              key={audience.id}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.1 + index * 0.1 }}
              className="group"
            >
              <div className="h-full flex flex-col items-center text-center p-8 rounded-lg border border-subtle bg-carbon-900/30 hover:border-racing-orange/30 hover:bg-carbon-900/60 transition-all duration-500">
                {/* Icon */}
                <div className="w-20 h-20 mb-6 text-steel-400 group-hover:text-steel-300 transition-colors duration-300">
                  {audience.icon}
                </div>

                {/* Title */}
                <h3 className="font-display text-lg font-medium text-white mb-2">
                  {audience.title}
                </h3>

                {/* Description */}
                <p className="text-steel-500 text-sm">
                  {audience.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Unified Message */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="text-center text-steel-400 mt-16 max-w-2xl mx-auto"
        >
          Whether you're finding your first racing line or refining your technique,
          RacerTune adapts to <span className="text-white">your</span> level.
        </motion.p>
      </div>
    </section>
  )
}
