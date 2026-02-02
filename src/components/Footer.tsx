'use client'

import { motion } from 'framer-motion'

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer 
      className="relative py-16 border-t border-subtle"
      role="contentinfo"
      itemScope
      itemType="https://schema.org/WPFooter"
    >
      <div className="absolute inset-0 bg-carbon-950" />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3" itemScope itemType="https://schema.org/Organization">
            <div className="w-8 h-8" aria-hidden="true">
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
            <span className="font-display font-semibold text-white" itemProp="name">RacerTune</span>
            <meta itemProp="url" content="https://racertune.com" />
          </div>

          {/* Links */}
          <nav className="flex items-center gap-8 text-sm" aria-label="Footer navigation">
            <a href="/privacy" className="text-steel-500 hover:text-white transition-colors" title="RacerTune Privacy Policy">
              Privacy
            </a>
            <a href="/terms" className="text-steel-500 hover:text-white transition-colors" title="RacerTune Terms of Service">
              Terms
            </a>
            <a href="mailto:support@racertune.com" className="text-steel-500 hover:text-white transition-colors" title="Contact RacerTune Support">
              Contact
            </a>
          </nav>

          {/* Social */}
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/ikihsan"
              target="_blank"
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-lg border border-subtle flex items-center justify-center text-steel-500 hover:text-white hover:border-steel-500 transition-colors"
              aria-label="GitHub"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            </a>
            <a
              href="https://linkedin.com/in/ikihsan"
              target="_blank"
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-lg border border-subtle flex items-center justify-center text-steel-500 hover:text-white hover:border-steel-500 transition-colors"
              aria-label="LinkedIn"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
              </svg>
            </a>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-subtle flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-steel-600 text-sm">
            © {currentYear} <span itemProp="copyrightHolder">RacerTune</span>. All rights reserved.
          </p>
          <p className="text-steel-700 text-xs font-mono">
            <strong>Designed for closed-track use only.</strong> AI race engineer for track day enthusiasts.
          </p>
        </div>
        
        {/* Hidden SEO content */}
        <div className="sr-only">
          <p>RacerTune is the world's first AI race engineer app, providing real-time voice coaching for track days and motorsport events. Our physics-based telemetry analysis helps drivers improve lap times safely.</p>
          <address>
            Contact us at <a href="mailto:support@racertune.com">support@racertune.com</a>
          </address>
        </div>
      </div>
    </footer>
  )
}
