import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Search Platform - Sistema Híbrido de Búsqueda',
  description: 'Plataforma inteligente de búsqueda en documentos con tecnología híbrida avanzada',
  keywords: ['AI', 'búsqueda', 'documentos', 'inteligencia artificial', 'híbrido', 'análisis'],
  authors: [{ name: 'AI Search Team' }],
  robots: 'index,follow',
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="theme-color" content="#1f2937" />
      </head>
      <body className={`${inter.className} antialiased`}>
        <div className="min-h-screen bg-white">
          {children}
        </div>
        <Toaster />
      </body>
    </html>
  )
}