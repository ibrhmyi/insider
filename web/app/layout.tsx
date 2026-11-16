import type {Metadata, Viewport} from 'next';
import {SodiumPortalProvider} from '@/lib/sodium/portal';
import './globals.css';

export const metadata: Metadata = {
  title: {default: 'Insider signal', template: '%s | Insider signal'},
  description: 'Who insiders are, where they trade and how they behave on prediction markets, and a model that scores Polymarket wallets on six signs. Unusual activity for review, not proof of insider trading.',
};
export const viewport: Viewport = {themeColor: '#141412', colorScheme: 'dark'};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en" data-theme="dark">
    <body className="sodium min-h-dvh bg-page text-text-1">
      <SodiumPortalProvider>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:start-2 focus:top-2 focus:z-(--z-overlay) focus:bg-panel focus:px-3 focus:py-2 focus-ring type-label">Skip to content</a>
        <main id="main" tabIndex={-1}>{children}</main>
      </SodiumPortalProvider>
    </body>
  </html>;
}
