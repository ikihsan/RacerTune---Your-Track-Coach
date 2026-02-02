'use client'

import { motion } from 'framer-motion'

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="relative py-16 border-t border-subtle">
      <div className="absolute inset-0 bg-carbon-950" />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8">
              <svg viewBox="0 0 32 32" fill="none" className="w-full h-full">
                <path
                  d="M16 4L28 10V22L16 28L4 22V10L16 4Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className="text-steel-600"
                />
                <path
                  d="M16 8L24 12V20L16 24L8 20V12L16 8Z"
                  fill="currentColor"
                  className="text-racing-orange"
                />
              </svg>
            </div>
            <span className="font-display font-semibold text-white">RacerTune</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8 text-sm">
            <a href="#" className="text-steel-500 hover:text-white transition-colors">
              Privacy
            </a>
            <a href="#" className="text-steel-500 hover:text-white transition-colors">
              Terms
            </a>
            <a href="#" className="text-steel-500 hover:text-white transition-colors">
              Contact
            </a>
          </div>

          {/* Social */}
          <div className="flex items-center gap-4">
            <a
              href="#"
              className="w-10 h-10 rounded-lg border border-subtle flex items-center justify-center text-steel-500 hover:text-white hover:border-steel-500 transition-colors"
              aria-label="GitHub"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            </a>
            <a
              href="#"
              className="w-10 h-10 rounded-lg border border-subtle flex items-center justify-center text-steel-500 hover:text-white hover:border-steel-500 transition-colors"
              aria-label="Twitter"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-subtle flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-steel-600 text-sm">
            © {currentYear} RacerTune. All rights reserved.
          </p>
          <p className="text-steel-700 text-xs font-mono">
            Designed for closed-track use only.
          </p>
        </div>
      </div>
    </footer>
  )
}
