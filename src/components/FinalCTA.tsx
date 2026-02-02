'use client'

import { useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'

const DEFAULT_MESSAGE = `Hi RacerTune Team,

I'd like to request early access to RacerTune.

GitHub Username: [YOUR_GITHUB_USERNAME]

I'm interested because:
- [Your racing background / experience]
- [What you hope to achieve with RacerTune]

Track/Circuit I usually drive at:
- [Your local track]

Looking forward to being part of the early grid!

Best regards`

export function FinalCTA() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' })
  const [githubUsername, setGithubUsername] = useState('')
  const [message, setMessage] = useState(DEFAULT_MESSAGE)
  const [step, setStep] = useState<'form' | 'compose'>('form')

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
          className="max-w-2xl mx-auto"
        >
          {step === 'form' ? (
            <div className="space-y-6">
              {/* GitHub Username Input */}
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1 relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-steel-500">
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    value={githubUsername}
                    onChange={(e) => setGithubUsername(e.target.value)}
                    placeholder="Your GitHub username"
                    required
                    className="w-full pl-12 pr-5 py-4 rounded-lg bg-carbon-800 border border-subtle text-white placeholder:text-steel-600 focus:outline-none focus:border-racing-orange/50 transition-colors"
                  />
                </div>
                <button
                  onClick={() => {
                    if (githubUsername) {
                      setMessage(message.replace('[YOUR_GITHUB_USERNAME]', githubUsername))
                      setStep('compose')
                    }
                  }}
                  disabled={!githubUsername}
                  className="px-8 py-4 rounded-lg bg-racing-orange text-white font-medium hover:bg-racing-red transition-colors duration-300 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Continue
                </button>
              </div>
              <p className="text-steel-600 text-sm text-center">
                We use your GitHub to verify your developer/racing background
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Email Composer */}
              <div className="bg-carbon-900 border border-subtle rounded-lg overflow-hidden">
                {/* Email Header */}
                <div className="px-4 py-3 border-b border-subtle bg-carbon-800/50">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-steel-500">To:</span>
                    <span className="text-white">hello@racertune.com</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm mt-1">
                    <span className="text-steel-500">Subject:</span>
                    <span className="text-white">GitHub Early Access Request — @{githubUsername}</span>
                  </div>
                </div>
                {/* Email Body */}
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={12}
                  className="w-full px-4 py-4 bg-transparent text-white placeholder:text-steel-600 focus:outline-none resize-none font-mono text-sm leading-relaxed"
                />
              </div>
              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={() => setStep('form')}
                  className="px-6 py-3 rounded-lg border border-steel-600 text-steel-400 hover:text-white hover:border-steel-500 transition-colors"
                >
                  ← Back
                </button>
                <a
                  href={`mailto:hello@racertune.com?subject=${encodeURIComponent(`GitHub Early Access Request — @${githubUsername}`)}&body=${encodeURIComponent(message)}`}
                  className="flex-1 px-8 py-3 rounded-lg bg-racing-orange text-white font-medium hover:bg-racing-red transition-colors duration-300 text-center flex items-center justify-center gap-2"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                  </svg>
                  Send Request
                </a>
              </div>
              <p className="text-steel-600 text-xs text-center">
                Clicking "Send Request" will open your default email client
              </p>
            </div>
          )}
        </motion.div>

        {/* Secondary CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-8 flex items-center justify-center gap-6"
        >
          <a
            href="https://github.com/ikihsan"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-steel-400 hover:text-white transition-colors text-sm"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            Follow on GitHub
          </a>
          <a
            href="https://linkedin.com/in/ikihsan"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-steel-400 hover:text-white transition-colors text-sm"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            Connect on LinkedIn
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
