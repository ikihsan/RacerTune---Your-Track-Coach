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
    { label: 'How It Works', href: '#how-it-works', title: 'Learn how RacerTune AI race engineer works' },
    { label: 'Safety', href: '#safety', title: 'Our safety-first approach to race engineering' },
    { label: 'Technology', href: '#tech', title: 'The technology behind RacerTune AI' },
  ]

  return (
    <header role="banner">
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        className={clsx(
          'fixed top-0 left-0 right-0 z-50 transition-all duration-500',
          scrolled ? 'bg-glass border-b border-subtle' : 'bg-transparent'
        )}
        aria-label="Main navigation"
        itemScope
        itemType="https://schema.org/SiteNavigationElement"
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-20">
            {/* Logo */}
            <a 
              href="/" 
              className="flex items-center gap-2 group"
              title="RacerTune - AI Race Engineer Home"
              aria-label="RacerTune Home"
              itemProp="url"
            >
              <div className="w-10 h-10 relative" aria-hidden="true">
                <svg viewBox="0 0 100 100" fill="none" className="w-full h-full" role="img" aria-label="RacerTune Logo">
                  <defs>
                    <linearGradient id="navOrangeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#FF6B35"/>
                      <stop offset="100%" stopColor="#EA580C"/>
                    </linearGradient>
                    <linearGradient id="navRedGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#DC2626"/>
                      <stop offset="100%" stopColor="#FF6B35"/>
                    </linearGradient>
                  </defs>
                  {/* R Letter */}
                  <path 
                    d="M25 20 L25 80 L35 80 L35 55 L50 55 L65 80 L78 80 L60 52 C72 48 78 38 78 28 C78 18 68 20 50 20 L25 20 Z M35 28 L48 28 C60 28 68 32 68 40 C68 48 62 52 50 52 L35 52 L35 28 Z" 
                    fill="url(#navRedGradient)"
                    className="group-hover:opacity-90 transition-opacity duration-300"
                  />
                  {/* Heartbeat/Racing Line */}
                  <path 
                    d="M10 60 L22 60 L28 45 L38 75 L48 55 L55 60 L90 60" 
                    stroke="url(#navOrangeGradient)" 
                    strokeWidth="4" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                    fill="none"
                    className="group-hover:opacity-100 opacity-90 transition-opacity duration-300"
                  />
                </svg>
              </div>
              <span className="font-display font-bold text-lg tracking-tight" itemProp="name">
                <span className="text-white">RACER</span>
                <span className="text-racing-orange">TUNE</span>
              </span>
            </a>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8" role="menubar">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  title={item.title}
                  className="text-sm text-steel-400 hover:text-white transition-colors duration-300"
                  role="menuitem"
                  itemProp="url"
                >
                  <span itemProp="name">{item.label}</span>
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
  </header>
  )
}
