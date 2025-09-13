import type { Metadata } from 'next'
import PWAInit from '@/components/PWAInit'
import { DM_Mono, Geist } from 'next/font/google'
import { NuqsAdapter } from 'nuqs/adapters/next/app'
import { Toaster } from '@/components/ui/sonner'
import SophiaContextChat from '@/components/SophiaContextChat'
import './globals.css'
const geistSans = Geist({
  variable: '--font-geist-sans',
  weight: '400',
  subsets: ['latin']
})

const dmMono = DM_Mono({
  subsets: ['latin'],
  variable: '--font-dm-mono',
  weight: '400'
})

export const metadata: Metadata = {
  title: 'Sophia Intel App',
  description:
    'Unified Business Intelligence Platform for PayReady - Integrating Salesforce, Slack, HubSpot, Gong with AI-powered insights'
}

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#0ea5e9" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </head>
      <body className={`${geistSans.variable} ${dmMono.variable} antialiased`}>
        <PWAInit />
        <NuqsAdapter>{children}</NuqsAdapter>
        <SophiaContextChat />
        <Toaster />
      </body>
    </html>
  )
}
