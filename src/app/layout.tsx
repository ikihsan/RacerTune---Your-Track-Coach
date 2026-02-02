import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'RacerTune — Your AI Race Engineer',
  description: 'Trust over performance. Always. Voice-only, physics-first AI race engineering built for the track.',
  keywords: ['AI race engineer', 'racing', 'motorsport', 'track day', 'telemetry', 'driver coaching'],
  authors: [{ name: 'RacerTune' }],
  openGraph: {
    title: 'RacerTune — Your AI Race Engineer',
    description: 'Trust over performance. Always. Voice-only, physics-first AI race engineering built for the track.',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'RacerTune — Your AI Race Engineer',
    description: 'Trust over performance. Always.',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
