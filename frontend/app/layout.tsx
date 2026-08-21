import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Geist, Cinzel } from 'next/font/google'

import TargetCursor from '@/components/ui/target-cursor'

import './globals.css'

const geistSans = Geist({
  subsets: ['latin'],
  variable: '--font-geist-sans',
})

const cinzel = Cinzel({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '900'],
  variable: '--font-cinzel',
})

export const metadata: Metadata = {
  title:
    'KATANA — Kernel Anomaly Tracking, Analysis & Neural Assistant',

  description:
    'An AI-powered Linux security system for kernel-level behavioral anomaly detection, threat analysis, explainability, and human-controlled investigation.',
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#050506',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      className={`dark ${geistSans.variable} ${cinzel.variable}`}
    >
      <body className="bg-background text-foreground antialiased">
        {/* Global custom targeting cursor */}
        <TargetCursor />

        {/* Application */}
        {children}

        {/* Analytics */}
        {process.env.NODE_ENV === 'production' && (
          <Analytics />
        )}
      </body>
    </html>
  )
}