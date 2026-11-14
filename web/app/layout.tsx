import type {Metadata} from 'next';
import Link from 'next/link';
import {QuartzPortalProvider} from '@/lib/quartz/portal';
import {SiteNav} from '@/components/app/site-nav';
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
        <header className="sticky top-0 z-(--z-raised) flex h-(--topbar) shrink-0 items-center gap-4 bg-page px-(--gutter-sm) rule-row sm:px-(--gutter)">
          <Link href="/" className="shrink-0 type-label rounded-sm focus-visible:focus-ring">Insider Signal</Link>
          <SiteNav/>
        </header>
        <main id="main" tabIndex={-1} className="outline-none">{children}</main>
      </QuartzPortalProvider>
    </body>
  </html>;
}
