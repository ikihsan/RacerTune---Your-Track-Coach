'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'

export function Navigation() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navItems = [
    { label: 'How It Works', href: '#how-it-works' },
    { label: 'Safety', href: '#safety' },
    { label: 'Technology', href: '#tech' },
  ]

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
      className={clsx(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-500',
        scrolled ? 'bg-glass border-b border-subtle' : 'bg-transparent'
      )}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2 group">
            <div className="w-8 h-8 relative">
              <svg viewBox="0 0 32 32" fill="none" className="w-full h-full">
                <path
                  d="M16 4L28 10V22L16 28L4 22V10L16 4Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className="text-steel-400 group-hover:text-racing-orange transition-colors duration-300"
                />
                <path
                  d="M16 8L24 12V20L16 24L8 20V12L16 8Z"
                  fill="currentColor"
                  className="text-racing-orange"
                />
              </svg>
            </div>
            <span className="font-display font-semibold text-lg tracking-tight">
              RacerTune
            </span>
          </a>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                className="text-sm text-steel-400 hover:text-white transition-colors duration-300"
              >
                {item.label}
              </a>
            ))}
          </div>

          {/* CTA */}
          <div className="hidden md:flex items-center gap-4">
            <a
              href="#early-access"
              className="text-sm px-5 py-2.5 rounded bg-racing-orange/10 text-racing-orange border border-racing-orange/20 hover:bg-racing-orange hover:text-white hover:border-racing-orange transition-all duration-300"
            >
              Early Access
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-steel-400 hover:text-white"
            aria-label="Toggle menu"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {mobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden bg-carbon-900 border-b border-subtle"
          >
            <div className="px-6 py-6 space-y-4">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block text-steel-400 hover:text-white transition-colors py-2"
                >
                  {item.label}
                </a>
              ))}
              <a
                href="#early-access"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-center mt-4 px-5 py-3 rounded bg-racing-orange text-white font-medium"
              >
                Early Access
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  )
}
