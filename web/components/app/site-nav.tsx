'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {Button} from '@/components/quartz/ui/button';

const LINKS = [
  {href: '/', label: 'Overview'},
  {href: '/markets/maduro', label: 'Markets', match: '/markets'},
  {href: '/live', label: 'Live scan'},
  {href: '/method', label: 'Method'},
  {href: '/story', label: 'Story'},
];

export function SiteNav() {
  const path = usePathname();
  return <nav aria-label="Main" className="flex min-w-0 items-center gap-1 overflow-x-auto">
    {LINKS.map(l => {
      const current = l.href === '/' ? path === '/' : path.startsWith(l.match ?? l.href);
      return <Button key={l.href} variant="ghost" size="sm" nativeButton={false}
        render={<Link href={l.href} aria-current={current ? 'page' : undefined}/>}
        className={current ? 'bg-selected' : 'text-text-2'}>{l.label}</Button>;
    })}
  </nav>;
}
