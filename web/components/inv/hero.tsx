'use client';

import {useEffect, useState} from 'react';
import {StatusStrip, StatusStripCell, StatusStripLabel, StatusStripUnit, StatusStripValue} from '@/components/sodium/ui/status-strip';
import {NOT_PROOF} from '@/lib/copy';

/** Counts each number up once on load; under reduced motion the final numbers show at once. */
function useCountUp(targets: number[], ms = 1100) {
  const [v, setV] = useState(targets);
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const k = Math.min(1, (now - start) / ms), e = 1 - Math.pow(1 - k, 3);
      setV(targets.map(t => Math.round(t * e)));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    setV(targets.map(() => 0));
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return v;
}

export function Hero({n, hoursBefore, named, namedTotal}: {n: number; hoursBefore: number; named: number; namedTotal: number}) {
  const [a, b, c] = useCountUp([n, hoursBefore, named]);
  return <section aria-labelledby="hero-title" className="mx-auto flex min-h-[calc(100svh-var(--head))] w-full max-w-7xl flex-col justify-center gap-10 px-4 py-16 sm:px-6">
    <h1 id="hero-title" className="type-title max-w-3xl text-balance">
      One wallet bet on Maduro&apos;s fall before anyone knew. A screen written before the results ranked it first.
    </h1>
    <StatusStrip label="Headline results">
      <StatusStripCell className="gap-2 py-6">
        <StatusStripValue className="type-display"><span className="sr-only">Number 1 of {n.toLocaleString('en-US')} wallets</span><span aria-hidden>#1</span></StatusStripValue>
        <StatusStripLabel aria-hidden>of {a.toLocaleString('en-US')} wallets</StatusStripLabel>
      </StatusStripCell>
      <StatusStripCell className="gap-2 py-6">
        <StatusStripValue className="type-display"><span className="sr-only">{hoursBefore} hours</span><span aria-hidden>{b}<StatusStripUnit> h</StatusStripUnit></span></StatusStripValue>
        <StatusStripLabel>before the news</StatusStripLabel>
      </StatusStripCell>
      <StatusStripCell className="gap-2 py-6">
        <StatusStripValue className="type-display"><span className="sr-only">{named} of {namedTotal}</span><span aria-hidden>{c} of {namedTotal}</span></StatusStripValue>
        <StatusStripLabel className="whitespace-normal">publicly named wallets flagged</StatusStripLabel>
      </StatusStripCell>
    </StatusStrip>
    <p className="type-body text-text-2">{NOT_PROOF}</p>
    <a href="#step-1" className="w-fit type-label text-text-2 hover:text-text-1 focus-visible:focus-ring">Scroll to see how</a>
  </section>;
}
