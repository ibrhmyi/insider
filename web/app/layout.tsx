import type {Metadata} from 'next';
import Link from 'next/link';
import {QuartzPortalProvider} from '@/lib/quartz/portal';
import './globals.css';

export const metadata: Metadata = {
  title: {default: 'Insider Signal', template: '%s | Insider Signal'},
  description: 'A frozen wallet screen for unusual pre-news trading on Polymarket. Unusual activity for review, not proof of insider trading.',
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en">
    <body className="quartz">
      <QuartzPortalProvider>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:start-2 focus:top-2 focus:z-(--z-overlay) focus:bg-page focus:px-3 focus:py-2 focus-ring type-label">Skip to content</a>
        <header className="sticky top-0 z-(--z-raised) flex h-(--topbar) shrink-0 items-center gap-2 bg-page sm:gap-4 px-2 rule-row sm:px-(--gutter)">
          <Link href="/" className="shrink-0 type-label rounded-inner focus-visible:focus-ring">Insider Signal</Link>
          <nav aria-label="Sections" className="ms-auto hidden gap-4 type-label text-text-2 sm:flex">
            <a href="#explore" className="hover:text-text-1 rounded-inner focus-visible:focus-ring">Wallets</a>
            <a href="#line" className="hover:text-text-1 rounded-inner focus-visible:focus-ring">Threshold</a>
            <a href="#luck" className="hover:text-text-1 rounded-inner focus-visible:focus-ring">Luck check</a>
            <a href="#live" className="hover:text-text-1 rounded-inner focus-visible:focus-ring">Live scan</a>
          </nav>
        </header>
        <main id="main" tabIndex={-1} data-control>{children}</main>
      </QuartzPortalProvider>
    </body>
  </html>;
}
