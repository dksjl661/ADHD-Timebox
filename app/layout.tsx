import type { Metadata } from 'next'
import React from 'react'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'TIME BOX - ADHD Timebox Agent',
  description: 'A timeboxing app for ADHD users',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}): React.JSX.Element {
  return (
    <html lang="zh" className={inter.variable}>
      <body className={inter.className}>{children}</body>
    </html>
  )
}
