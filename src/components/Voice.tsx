'use client'

import { useRef, useState, useEffect } from 'react'
import { motion, useInView, AnimatePresence } from 'framer-motion'

const voiceCommands = [
  { text: 'Brake earlier next lap.', type: 'instruction' },
  { text: 'Smooth steering.', type: 'reminder' },
  { text: 'Good exit.', type: 'confirmation' },
  { text: 'Trail brake into apex.', type: 'instruction' },
  { text: 'Hold this line.', type: 'confirmation' },
]

export function Voice() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (!isInView) return
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % voiceCommands.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [isInView])

  return (
    <section ref={sectionRef} className="relative py-32 lg:py-48 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-carbon-950 via-carbon-900 to-carbon-950" />

      {/* Subtle waveform background */}
      <div className="absolute inset-0 flex items-center justify-center opacity-10">
        <svg
          viewBox="0 0 800 200"
          className="w-full max-w-5xl"
          preserveAspectRatio="none"
        >
          {[...Array(40)].map((_, i) => (
            <line
              key={i}
              x1={i * 20 + 10}
              y1={100 - Math.sin(i * 0.5) * 40 - Math.random() * 20}
              x2={i * 20 + 10}
              y2={100 + Math.sin(i * 0.5) * 40 + Math.random() * 20}
              stroke="#EA580C"
              strokeWidth="2"
              opacity={0.3 + Math.random() * 0.5}
            />
          ))}
        </svg>
      </div>

      <div className="relative max-w-5xl mx-auto px-6 lg:px-8">
        {/* Section Label */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 text-xs font-mono tracking-wider uppercase text-steel-400 border border-subtle rounded-full">
            Your Engineer
          </span>
        </motion.div>

        {/* Voice Command Display */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={isInView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative text-center mb-16"
        >
          {/* Quote marks */}
          <div className="absolute -top-8 left-1/2 -translate-x-1/2 text-6xl text-racing-orange/20 font-serif">
            "
          </div>

          {/* Animated voice command */}
          <div className="h-24 sm:h-32 flex items-center justify-center">
            <AnimatePresence mode="wait">
              <motion.h2
                key={currentIndex}
                initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                exit={{ opacity: 0, y: -20, filter: 'blur(10px)' }}
                transition={{ duration: 0.5 }}
                className="font-display text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-semibold text-white"
              >
                {voiceCommands[currentIndex].text}
              </motion.h2>
            </AnimatePresence>
          </div>

          {/* Progress indicators */}
          <div className="flex items-center justify-center gap-2 mt-8">
            {voiceCommands.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  index === currentIndex
                    ? 'bg-racing-orange w-8'
                    : 'bg-steel-600 hover:bg-steel-500'
                }`}
                aria-label={`Show command ${index + 1}`}
              />
            ))}
          </div>
        </motion.div>

        {/* Supporting Copy */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center"
        >
          <div className="max-w-md mx-auto space-y-4">
            <p className="text-steel-400 text-lg">
              No chatter.
            </p>
            <p className="text-steel-400 text-lg">
              No motivation talk.
            </p>
            <p className="text-white text-lg font-medium">
              Just facts.
            </p>
          </div>
        </motion.div>

        {/* Voice waveform indicator */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="flex items-center justify-center gap-1 mt-16"
        >
          <div className="flex items-end justify-center gap-0.5 h-8">
            {[...Array(5)].map((_, i) => (
              <motion.div
                key={i}
                animate={{
                  height: [8, 20 + i * 2, 8],
                }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: 'easeInOut',
                }}
                className="w-1 bg-racing-orange/60 rounded-full"
                style={{ height: 8 }}
              />
            ))}
          </div>
          <span className="ml-3 text-xs font-mono text-steel-500 uppercase tracking-wider">
            Voice Active
          </span>
        </motion.div>
      </div>
    </section>
  )
}
