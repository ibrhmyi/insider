'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';

const LINKS = [
  {href: '/', label: 'Overview'},
  {href: '/markets/maduro', label: 'Markets', match: '/markets'},
  {href: '/live', label: 'Live scan'},
  {href: '/method', label: 'Method'},
  {href: '/story', label: 'Story'},
];

export function SiteNav() {
  const path = usePathname();
  return <nav aria-label="Main" className="flex min-w-0 items-center gap-0.5 overflow-x-auto sm:gap-1">
    {LINKS.map(l => {
      const current = l.href === '/' ? path === '/' : path.startsWith(l.match ?? l.href);
      return <Link key={l.href} href={l.href} aria-current={current ? 'page' : undefined}
        className="inline-flex h-(--control-sm) shrink-0 items-center rounded-soft px-2 type-label sm:px-3 text-text-2 hover:bg-hover hover:text-text-1 focus-visible:focus-ring aria-[current=page]:bg-selected aria-[current=page]:text-text-1">{l.label}</Link>;
    })}
  </nav>;
}
