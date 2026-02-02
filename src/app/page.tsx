'use client'

import { Hero } from '@/components/Hero'
import { Problem } from '@/components/Problem'
import { HowItWorks } from '@/components/HowItWorks'
import { Voice } from '@/components/Voice'
import { Safety } from '@/components/Safety'
import { Audience } from '@/components/Audience'
import { Tech } from '@/components/Tech'
import { FinalCTA } from '@/components/FinalCTA'
import { Navigation } from '@/components/Navigation'
import { Footer } from '@/components/Footer'

export default function Home() {
  return (
    <>
      {/* Skip to main content link for accessibility */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-racing-orange focus:text-white focus:rounded"
      >
        Skip to main content
      </a>
      
      <Navigation />
      
      <main id="main-content" className="relative" role="main" aria-label="RacerTune AI Race Engineer - Main Content">
        {/* Hero Section */}
        <Hero />
        
        {/* Problem Section - Why traditional coaching fails */}
        <Problem />
        
        {/* How It Works - The RacerTune difference */}
        <article itemScope itemType="https://schema.org/HowTo">
          <HowItWorks />
        </article>
        
        {/* Voice-First Experience */}
        <Voice />
        
        {/* Safety Philosophy */}
        <Safety />
        
        {/* Target Audience */}
        <Audience />
        
        {/* Technology Stack */}
        <Tech />
        
        {/* Final Call-to-Action */}
        <FinalCTA />
      </main>
      
      <Footer />
    </>
  )
}
