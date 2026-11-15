'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';

const LINKS = [
  {href: '/', label: 'Investigation'},
  {href: '/cases', label: 'Cases'},
  {href: '/method', label: 'Method'},
  {href: '/live', label: 'Live'},
  {href: '/story', label: 'Story'},
];

export function SiteNav() {
  const path = usePathname();
  if (path.startsWith('/story')) return null;
  return <header className="sticky top-0 z-(--z-raised) border-b border-line bg-page">
    <div className="mx-auto flex h-(--head) max-w-7xl items-center gap-6 px-4 sm:px-6">
      <Link href="/" className="hidden shrink-0 type-label-lg text-text-1 focus-visible:focus-ring sm:inline">Insider signal</Link>
      <nav aria-label="Main" className="flex min-w-0 items-center gap-4 overflow-x-auto sm:ms-auto sm:gap-6">
        {LINKS.map(l => {
          const on = l.href === '/' ? path === '/' : path.startsWith(l.href);
          return <Link key={l.href} href={l.href} aria-current={on ? 'page' : undefined}
            className="shrink-0 type-label text-text-3 hover:text-text-1 aria-[current=page]:text-text-1 focus-visible:focus-ring">{l.label}</Link>;
        })}
      </nav>
    </div>
  </header>;
}
