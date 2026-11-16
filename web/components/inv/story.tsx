'use client';

import {useCallback, useEffect, useRef, useState, type ReactNode} from 'react';
import Link from 'next/link';
import {Button} from '@/components/sodium/ui/button';
import {Kbd} from '@/components/sodium/ui/kbd';

/** Full-screen recording mode: arrow keys, PageUp/PageDown, Home/End; ?slide=N opens a slide. */
export function Story({slides}: {slides: {title: string; body: ReactNode}[]}) {
  const [i, setI] = useState(0);
  const region = useRef<HTMLDivElement>(null);
  const n = slides.length;
  const go = useCallback((d: number) => setI(x => Math.max(0, Math.min(n - 1, x + d))), [n]);

  useEffect(() => {
    const s = Number(new URLSearchParams(window.location.search).get('slide'));
    if (s >= 1 && s <= n) setI(s - 1);
  }, [n]);
  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('slide', String(i + 1));
    window.history.replaceState(null, '', url);
  }, [i]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); go(1); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); go(-1); }
      else if (e.key === 'Home') { e.preventDefault(); setI(0); }
      else if (e.key === 'End') { e.preventDefault(); setI(n - 1); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [go, n]);

  return <div className="fixed inset-0 z-(--z-overlay) flex flex-col bg-page">
    <div className="flex h-(--head) shrink-0 items-center gap-4 border-b border-line px-6">
      <span className="type-label text-text-2">Insider signal</span>
      <div role="progressbar" aria-label="Slide" aria-valuemin={1} aria-valuemax={n} aria-valuenow={i + 1} aria-valuetext={`Slide ${i + 1} of ${n}: ${slides[i].title}`}
        className="flex flex-1 gap-1">
        {slides.map((s, k) => <span key={s.title} className={`h-1 flex-1 ${k <= i ? 'bg-text-1' : 'bg-line'}`}/>)}
      </div>
      <span className="type-code-sm text-text-3">{i + 1}/{n}</span>
      <Link href="/" className="type-label text-text-2 hover:text-text-1 focus-visible:focus-ring">Exit</Link>
    </div>
    <div ref={region} aria-live="polite" aria-label={`${slides[i].title}, slide ${i + 1} of ${n}`}
      className="flex min-h-0 flex-1 flex-col overflow-y-auto px-6 py-10 sm:px-12 lg:px-20">
      <div key={i} className="my-auto flex w-full flex-col gap-8 self-center">{slides[i].body}</div>
    </div>
    <div className="flex shrink-0 items-center justify-between gap-4 border-t border-line px-6 py-3">
      <Button variant="secondary" size="sm" onClick={() => go(-1)} disabled={i === 0}>Previous slide</Button>
      <span className="hidden items-center gap-2 type-label-sm text-text-3 sm:flex"><Kbd>←</Kbd><Kbd>→</Kbd>to move</span>
      <Button size="sm" onClick={() => go(1)} disabled={i === n - 1}>Next slide</Button>
    </div>
  </div>;
}
