import type { Metadata, Viewport } from 'next'
import { Analytics } from '@vercel/analytics/next'
import { TopNav } from '@/components/layout/top-nav'
import './globals.css'

export const metadata: Metadata = {
  title: 'METRA — R-76 Evaluation Engine',
  description:
    'Configuration-driven OIML R 76 legal metrology type evaluation platform for non-automatic weighing instruments (NAWI).',
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#0b0d0c',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased" style={{ minHeight: '100vh', background: 'var(--black)' }}>
        <TopNav />
        <div className="main-wrapper">
          {children}
        </div>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
