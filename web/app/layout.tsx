import type {Metadata, Viewport} from 'next';
import {SodiumPortalProvider} from '@/lib/sodium/portal';
import {Swirl} from '@/components/product/swirl';
import './globals.css';

export const metadata: Metadata = {
  title: {default: 'Insider signal', template: '%s | Insider signal'},
  description: 'Who insiders are, where they trade and how they behave on prediction markets, and a model that scores Polymarket wallets on six signs. Unusual activity for review, not proof of insider trading.',
};
export const viewport: Viewport = {themeColor: '#141412', colorScheme: 'dark'};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en" data-theme="dark">
    <head>
      <link rel="preconnect" href="https://fonts.googleapis.com"/>
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin=""/>
      {/* eslint-disable-next-line @next/next/no-page-custom-font */}
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;1,400&display=swap"/>
    </head>
    <body className="sodium min-h-dvh bg-page text-text-1">
      <SodiumPortalProvider>
        <Swirl/>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:start-2 focus:top-2 focus:z-(--z-overlay) focus:bg-panel focus:px-3 focus:py-2 focus-ring type-label">Skip to content</a>
        <main id="main" tabIndex={-1}>{children}</main>
      </SodiumPortalProvider>
    </body>
  </html>;
}
