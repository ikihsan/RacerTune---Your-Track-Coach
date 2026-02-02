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
    <main className="relative">
      <Navigation />
      <Hero />
      <Problem />
      <HowItWorks />
      <Voice />
      <Safety />
      <Audience />
      <Tech />
      <FinalCTA />
      <Footer />
    </main>
  )
}
