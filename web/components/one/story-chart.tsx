'use client';

import {useEffect, useRef, useState} from 'react';

/**
 * Maduro "Out by Jan 31" Yes price over the last 48 hours, linear 0-100 cents.
 * stage 0: price line up to the news. 1: other buys (faint grey) and the one wallet's buys as one yellow dot.
 * 2: the news line. 3: the price after the news. Yellow marks only that wallet. Every change is instant under
 * reduced motion; with `still` the chart shows its end state.
 */
export type StoryChartData = {
  price: [number, number][];
  others: [number, number, number][]; // [time, price, usd]
  tNews: number;
  x1: number;
  dot: {t: number; y: number; label: string};
};

const PAD = {l: 84, r: 24, t: 28, b: 60};

function useSize<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [s, set] = useState({w: 1100, h: 700});
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const ro = new ResizeObserver(([e]) => { const {width, height} = e.contentRect; if (width && height) set({w: Math.round(width), h: Math.round(height)}); });
    ro.observe(el); return () => ro.disconnect();
  }, []);
  return [ref, s] as const;
}

function path(pts: [number, number][], x: (t: number) => number, y: (p: number) => number) {
  if (!pts.length) return '';
  let d = `M${x(pts[0][0]).toFixed(1)},${y(pts[0][1]).toFixed(1)}`;
  for (let i = 1; i < pts.length; i++) d += `H${x(pts[i][0]).toFixed(1)}V${y(pts[i][1]).toFixed(1)}`;
  return d;
}

function clip(price: [number, number][], a: number, b: number): [number, number][] {
  const out: [number, number][] = [];
  let last: number | null = null;
  for (const [t, p] of price) {
    if (t < a) { last = p; continue; }
    if (t > b) break;
    if (!out.length && last !== null) out.push([a, last]);
    out.push([t, p]);
  }
  if (out.length) out.push([b, out[out.length - 1][1]]);
  return out;
}

const day = (t: number) => new Date(t * 1000).toLocaleDateString('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'});

export function StoryChart({d, stage, still = false}: {d: StoryChartData; stage: number; still?: boolean}) {
  const [ref, {w, h}] = useSize<HTMLDivElement>();
  const s = still ? 3 : stage;
  const small = w < 640;
  const lab = small ? 'type-heading-sm' : 'type-heading';
  const x0 = d.tNews - 48 * 3600;
  const pl = w < 640 ? 56 : PAD.l;
  const iw = w - pl - PAD.r, ih = h - PAD.t - PAD.b;
  const x = (t: number) => pl + ((t - x0) / (d.x1 - x0)) * iw;
  const y = (p: number) => PAD.t + (1 - p) * ih;
  const pre = clip(d.price, x0, d.tNews), post = clip(d.price, d.tNews, d.x1);
  const T = 'transition-[opacity,stroke-dashoffset] duration-(--dur-pending) ease-out motion-reduce:transition-none';
  const show = (on: boolean) => (on ? 'opacity-100' : 'opacity-0');
  const ticks = [x0 + 12 * 3600, x0 + 36 * 3600].map(t => Math.floor(t / 86400) * 86400 + 12 * 3600).filter((t, i, a) => a.indexOf(t) === i);
  const dx = x(d.dot.t), dy = y(d.dot.y);
  const labelLeft = dx > pl + iw * 0.6;

  return <div ref={ref} className="relative size-full">
    <svg viewBox={`0 0 ${w} ${h}`} className="absolute inset-0 size-full overflow-visible" role="img"
      aria-label={`Yes price, last 48 hours before the news: flat near 7 cents${s >= 1 ? `; the wallet bought ${d.dot.label}` : ''}${s >= 2 ? '; news at 06:00 UTC on January 3' : ''}${s >= 3 ? '; then the price jumps to 100 cents' : ''}.`}>
      {[0, 0.25, 0.5, 0.75, 1].map(p => <g key={p}>
        <line x1={pl} x2={w - PAD.r} y1={y(p)} y2={y(p)} className="stroke-line" strokeWidth={1}/>
        <text x={pl - 10} y={y(p)} dy="0.35em" textAnchor="end" className={`fill-text-3 ${lab}`}>{Math.round(p * 100)}¢</text>
      </g>)}
      {ticks.map(t => <text key={t} x={x(t)} y={h - 14} textAnchor="middle" className={`fill-text-3 ${lab}`}>{day(t)}</text>)}

      <g className={`${T} ${show(s >= 1)}`}>
        {d.others.map(([t, p, usd], i) => <circle key={i} cx={x(t)} cy={y(p)} r={Math.max(2, Math.min(9, Math.sqrt(usd) / 16))} className="fill-text-3 opacity-25"/>)}
      </g>

      <path d={path(pre, x, y)} pathLength={1} strokeDasharray="1 1" strokeDashoffset={0} className={`fill-none stroke-text-1 ${T}`} strokeWidth={3}/>
      <path d={path(post, x, y)} pathLength={1} strokeDasharray="1 1" strokeDashoffset={s >= 3 ? 0 : 1} className={`fill-none stroke-text-1 ${T}`} strokeWidth={3}/>

      <g className={`${T} ${show(s >= 2)}`}>
        <line x1={x(d.tNews)} x2={x(d.tNews)} y1={PAD.t} y2={PAD.t + ih} className="stroke-text-1" strokeWidth={2} strokeDasharray="6 6"/>
        <text x={x(d.tNews) - 12} y={PAD.t + (small ? 48 : 28)} textAnchor="end" className={`fill-text-1 ${lab}`}>{small ? 'News' : 'News, 06:00 UTC Jan 3'}</text>
      </g>

      <g className={`${T} ${show(s >= 1)}`}>
        <circle cx={dx} cy={dy} r={20} className="fill-accent-text stroke-page" strokeWidth={3}/>
        <line x1={dx} x2={dx} y1={dy - 24} y2={dy - 92} className="stroke-accent-edge" strokeWidth={2}/>
        <text x={labelLeft ? dx - 12 : dx + 12} y={dy - 104} textAnchor={labelLeft ? 'end' : 'start'} className="fill-accent-text type-title">{d.dot.label}</text>
      </g>
    </svg>
  </div>;
}
