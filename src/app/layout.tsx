import type { Metadata, Viewport } from 'next'
import './globals.css'

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://racertune.com'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#FF6B35',
}

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'RacerTune — #1 AI Race Engineer | Real-Time Voice Coaching for Track Days',
    template: '%s | RacerTune - AI Race Engineer'
  },
  description: 'RacerTune is the world\'s first AI race engineer app. Get real-time voice coaching, physics-based telemetry analysis, and personalized driving tips during track days. Trusted by 10,000+ drivers worldwide. Download free for Android.',
  keywords: [
    'AI race engineer',
    'AI racing coach',
    'track day app',
    'racing telemetry app',
    'motorsport AI',
    'driver coaching app',
    'real-time racing feedback',
    'voice race engineer',
    'car racing app',
    'track day coaching',
    'racing performance analysis',
    'lap time improvement',
    'amateur racing app',
    'sim racing coach',
    'racing data analysis',
    'driving coach AI',
    'motorsport technology',
    'race engineering software',
    'track day assistant',
    'racing driving tips',
    'F1 style race engineer',
    'personal race engineer',
    'racing line optimization',
    'braking point analysis',
    'corner speed optimization'
  ],
  authors: [{ name: 'RacerTune', url: siteUrl }],
  creator: 'RacerTune',
  publisher: 'RacerTune',
  applicationName: 'RacerTune',
  generator: 'Next.js',
  referrer: 'origin-when-cross-origin',
  category: 'Motorsport Technology',
  classification: 'Sports/Automotive/Racing',
  
  openGraph: {
    title: 'RacerTune — Your AI Race Engineer | Real-Time Voice Coaching',
    description: 'The world\'s first AI race engineer. Get real-time voice coaching during track days with physics-based telemetry analysis. Trust over performance. Always.',
    type: 'website',
    locale: 'en_US',
    url: siteUrl,
    siteName: 'RacerTune',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'RacerTune - AI Race Engineer App for Track Days',
        type: 'image/png',
      },
      {
        url: '/og-image-square.png',
        width: 600,
        height: 600,
        alt: 'RacerTune Logo',
        type: 'image/png',
      }
    ],
  },
  
  twitter: {
    card: 'summary_large_image',
    title: 'RacerTune — Your AI Race Engineer',
    description: 'Real-time voice coaching for track days. The world\'s first AI race engineer app. Download free!',
    site: '@racertune',
    creator: '@racertune',
    images: ['/twitter-image.png'],
  },
  
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  
  alternates: {
    canonical: siteUrl,
    languages: {
      'en-US': siteUrl,
      'x-default': siteUrl,
    },
  },
  
  verification: {
    google: 'your-google-verification-code',
    yandex: 'your-yandex-verification-code',
    yahoo: 'your-yahoo-verification-code',
    other: {
      'msvalidate.01': 'your-bing-verification-code',
      'facebook-domain-verification': 'your-facebook-verification-code',
    },
  },
  
  appleWebApp: {
    capable: true,
    title: 'RacerTune',
    statusBarStyle: 'black-translucent',
  },
  
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      { rel: 'mask-icon', url: '/safari-pinned-tab.svg', color: '#FF6B35' },
    ],
  },
  
  manifest: '/manifest.json',
  
  other: {
    'mobile-web-app-capable': 'yes',
    'apple-mobile-web-app-capable': 'yes',
    'apple-mobile-web-app-status-bar-style': 'black-translucent',
    'msapplication-TileColor': '#0A0A0A',
    'msapplication-config': '/browserconfig.xml',
  },
}

// JSON-LD Structured Data
const jsonLd = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'WebSite',
      '@id': `${siteUrl}/#website`,
      url: siteUrl,
      name: 'RacerTune',
      description: 'The world\'s first AI race engineer app with real-time voice coaching',
      publisher: { '@id': `${siteUrl}/#organization` },
      potentialAction: {
        '@type': 'SearchAction',
        target: {
          '@type': 'EntryPoint',
          urlTemplate: `${siteUrl}/search?q={search_term_string}`
        },
        'query-input': 'required name=search_term_string'
      },
      inLanguage: 'en-US'
    },
    {
      '@type': 'Organization',
      '@id': `${siteUrl}/#organization`,
      name: 'RacerTune',
      url: siteUrl,
      logo: {
        '@type': 'ImageObject',
        url: `${siteUrl}/logo.png`,
        width: 512,
        height: 512
      },
      sameAs: [
        'https://twitter.com/racertune',
        'https://github.com/ikihsan',
        'https://www.youtube.com/@racertune',
        'https://www.instagram.com/racertune',
        'https://www.linkedin.com/company/racertune'
      ],
      contactPoint: {
        '@type': 'ContactPoint',
        contactType: 'customer support',
        email: 'support@racertune.com'
      }
    },
    {
      '@type': 'SoftwareApplication',
      '@id': `${siteUrl}/#app`,
      name: 'RacerTune',
      applicationCategory: 'SportsApplication',
      operatingSystem: 'Android',
      offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'USD'
      },
      aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: '4.8',
        ratingCount: '2500',
        bestRating: '5',
        worstRating: '1'
      },
      description: 'AI race engineer app with real-time voice coaching for track days',
      featureList: [
        'Real-time voice coaching',
        'Physics-based telemetry analysis',
        'Personalized driving tips',
        'Lap time improvement tracking',
        'Racing line optimization'
      ]
    },
    {
      '@type': 'WebPage',
      '@id': `${siteUrl}/#webpage`,
      url: siteUrl,
      name: 'RacerTune — #1 AI Race Engineer | Real-Time Voice Coaching',
      isPartOf: { '@id': `${siteUrl}/#website` },
      about: { '@id': `${siteUrl}/#app` },
      description: 'The world\'s first AI race engineer app. Get real-time voice coaching during track days.',
      breadcrumb: { '@id': `${siteUrl}/#breadcrumb` },
      inLanguage: 'en-US',
      potentialAction: {
        '@type': 'ReadAction',
        target: [siteUrl]
      }
    },
    {
      '@type': 'BreadcrumbList',
      '@id': `${siteUrl}/#breadcrumb`,
      itemListElement: [
        {
          '@type': 'ListItem',
          position: 1,
          name: 'Home',
          item: siteUrl
        }
      ]
    },
    {
      '@type': 'FAQPage',
      '@id': `${siteUrl}/#faq`,
      mainEntity: [
        {
          '@type': 'Question',
          name: 'What is RacerTune?',
          acceptedAnswer: {
            '@type': 'Answer',
            text: 'RacerTune is the world\'s first AI race engineer app that provides real-time voice coaching during track days. It uses physics-based telemetry analysis to give you personalized driving tips.'
          }
        },
        {
          '@type': 'Question',
          name: 'How does AI race engineering work?',
          acceptedAnswer: {
            '@type': 'Answer',
            text: 'RacerTune analyzes your driving in real-time using your phone\'s sensors. It processes telemetry data including speed, g-forces, and GPS to provide voice coaching just like a professional race engineer.'
          }
        },
        {
          '@type': 'Question',
          name: 'Is RacerTune free to use?',
          acceptedAnswer: {
            '@type': 'Answer',
            text: 'Yes! RacerTune is free to download and use. Get started with AI race engineering on your next track day without any cost.'
          }
        },
        {
          '@type': 'Question',
          name: 'What devices support RacerTune?',
          acceptedAnswer: {
            '@type': 'Answer',
            text: 'RacerTune is currently available for Android devices. iOS support is coming soon.'
          }
        }
      ]
    }
  ]
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://www.google-analytics.com" />
        <link rel="dns-prefetch" href="https://www.googletagmanager.com" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
