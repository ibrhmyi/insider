'use client';

import {useEffect, useMemo, useRef, useState, type ReactNode} from 'react';

/**
 * The investigation chart: YES price over a zoomed window, every pre-news buy as a dot, and a state that scroll steps
 * (or story slides) switch. All marks are drawn in SVG; colour comes only from Sodium roles. Yellow is reserved for
 * flagged activity (score >= 4 and >= $2,500 bought) and the focus wallet. Under reduced motion every change is instant.
 */

export type ChartState = {
  line: 'none' | 'pre' | 'full';
  dots: 'none' | 'faint' | 'flagged';
  focus: boolean;
  news: boolean;
  callout: boolean;
};

export const STATE_ALL: ChartState = {line: 'full', dots: 'flagged', focus: true, news: true, callout: true};

export type ChartBuy = {t: number; y: number; usd: number; flagged: boolean; focus: boolean};

type Props = {
  price: [number, number][];
  buys: ChartBuy[];
  tNews: number;
  x0: number;
  x1: number;
  state: ChartState;
  newsLabel: string;
  firstHighT?: number | null;
  firstHighLabel?: string;
  callout?: ReactNode;
  inset?: {price: [number, number][]; label: string};
  label: string;
  className?: string;
};

const PAD = {l: 44, r: 16, t: 20, b: 32};

function useSize<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [size, setSize] = useState({w: 800, h: 480});
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => {
      const {width, height} = e.contentRect;
      if (width > 0 && height > 0) setSize({w: Math.round(width), h: Math.round(height)});
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, size] as const;
}

function stepPath(pts: [number, number][], x: (t: number) => number, y: (p: number) => number) {
  if (!pts.length) return '';
  let d = `M${x(pts[0][0]).toFixed(1)},${y(pts[0][1]).toFixed(1)}`;
  for (let i = 1; i < pts.length; i++) d += `H${x(pts[i][0]).toFixed(1)}V${y(pts[i][1]).toFixed(1)}`;
  return d;
}

/** Points of a step line clipped to [a, b], starting from the last price before a. */
function slice(price: [number, number][], a: number, b: number): [number, number][] {
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

const fmtDay = (t: number) => new Date(t * 1000).toLocaleDateString('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'});
const fmtHour = (t: number) => new Date(t * 1000).toISOString().slice(11, 16);

export function InvestigationChart({price, buys, tNews, x0, x1, state, newsLabel, firstHighT, firstHighLabel, callout, inset, label, className}: Props) {
  const [ref, {w, h}] = useSize<HTMLDivElement>();
  const iw = w - PAD.l - PAD.r, ih = h - PAD.t - PAD.b;
  const x = (t: number) => PAD.l + ((t - x0) / (x1 - x0)) * iw;
  // square-root price scale: the pre-news action at 5 to 11 cents gets room, and 100 cents still fits
  const y = (p: number) => PAD.t + (1 - Math.sqrt(Math.max(0, p))) * ih;
  const pre = useMemo(() => slice(price, x0, tNews), [price, x0, tNews]);
  const post = useMemo(() => slice(price, tNews, x1), [price, tNews, x1]);
  const ticks = useMemo(() => {
    const out: number[] = [];
    const step = (x1 - x0) > 4 * 86400 ? 86400 : iw < 520 ? 24 * 3600 : 12 * 3600;
    for (let t = Math.ceil(x0 / step) * step; t <= x1; t += step) out.push(t);
    return out;
  }, [x0, x1, iw]);
  const visible = buys.filter(b => b.t >= x0 && b.t <= x1);
  const focusBuys = visible.filter(b => b.focus);
  const biggest = focusBuys.reduce<ChartBuy | null>((a, b) => (!a || b.usd > a.usd ? b : a), null);
  const r = (usd: number) => Math.max(1.6, Math.min(14, Math.sqrt(usd) / 13));

  const dotClass = (b: ChartBuy) => {
    if (state.dots === 'none') return 'opacity-0';
    if (state.focus && b.focus) return 'fill-accent-fill stroke-text-1 opacity-100';
    if (state.dots === 'flagged' && b.flagged) return state.focus ? 'fill-accent-fill stroke-page opacity-50' : 'fill-accent-fill stroke-page opacity-100';
    return state.dots === 'flagged' ? 'fill-text-3 stroke-page opacity-20' : 'fill-text-3 stroke-page opacity-50';
  };
  // draw order: faint first, then flagged, then the focus wallet on top
  const order = [...visible].sort((a, b) => Number(a.flagged) - Number(b.flagged) || Number(a.focus) - Number(b.focus) || b.usd - a.usd);
  const lineT = 'transition-[stroke-dashoffset] duration-(--dur-pending) ease-out motion-reduce:transition-none';
  const fade = 'transition-opacity duration-(--dur-wipe) ease-out motion-reduce:transition-none';

  // callout placement: beside the biggest focus buy, flipped to stay inside the plot
  const cx = biggest ? x(biggest.t) : 0, cy = biggest ? y(biggest.y) : 0;
  const flip = cx > PAD.l + iw * 0.55;

  return <div ref={ref} className={`relative size-full min-h-64 ${className ?? ''}`}>
    <svg role="img" aria-label={label} viewBox={`0 0 ${w} ${h}`} className="absolute inset-0 size-full overflow-visible">
      {[0, 0.05, 0.1, 0.25, 0.5, 1].map(p => <g key={p}>
        <line x1={PAD.l} x2={w - PAD.r} y1={y(p)} y2={y(p)} className="stroke-line" strokeWidth={1}/>
        <text x={PAD.l - 8} y={y(p)} dy="0.32em" textAnchor="end" className="fill-text-3 type-micro">{Math.round(p * 100)}¢</text>
      </g>)}
      <text x={PAD.l - 36} y={PAD.t - 8} textAnchor="start" className="fill-text-3 type-micro">Yes price, square-root scale</text>
      {ticks.map(t => <text key={t} x={x(t)} y={h - 10} textAnchor="middle" className="fill-text-3 type-micro">{(x1 - x0) > 4 * 86400 ? fmtDay(t) : `${fmtDay(t)} ${fmtHour(t)}`}</text>)}

      {firstHighT != null && firstHighT >= x0 && <g className={`${fade} ${state.callout ? 'opacity-100' : 'opacity-0'}`}>
        <line x1={x(firstHighT)} x2={x(firstHighT)} y1={PAD.t} y2={PAD.t + ih} className="stroke-accent-edge" strokeWidth={1} strokeDasharray="2 4"/>
        <text x={x(firstHighT) + 6} y={PAD.t + 12} className="fill-accent-text type-micro">{firstHighLabel}</text>
      </g>}

      <path d={stepPath(pre, x, y)} pathLength={1} strokeDasharray="1 1" strokeDashoffset={state.line === 'none' ? 1 : 0}
        className={`fill-none stroke-text-2 ${lineT}`} strokeWidth={1.5}/>
      <path d={stepPath(post, x, y)} pathLength={1} strokeDasharray="1 1" strokeDashoffset={state.line === 'full' ? 0 : 1}
        className={`fill-none stroke-text-1 ${lineT}`} strokeWidth={1.5}/>

      <g>{order.map((b, i) => <circle key={i} cx={x(b.t)} cy={y(b.y)} r={r(b.usd) + (state.focus && b.focus ? 2 : 0)}
        className={`${fade} ${dotClass(b)}`} strokeWidth={state.focus && b.focus ? 2 : 1}/>)}</g>

      <g className={`${fade} ${state.news ? 'opacity-100' : 'opacity-0'}`}>
        <line x1={x(tNews)} x2={x(tNews)} y1={PAD.t} y2={PAD.t + ih} className="stroke-text-1" strokeWidth={1.5}/>
        <text x={x(tNews) - 6} y={PAD.t + 12} textAnchor="end" className="fill-text-1 type-micro">{newsLabel}</text>
      </g>
    </svg>

    {inset && <InsetChart price={inset.price} x0={x0} x1={x1} label={inset.label}/>}

    {callout && biggest && <div aria-hidden={!state.callout}
      className={`pointer-events-none absolute w-48 border border-accent-edge bg-panel p-2 sm:w-60 sm:p-3 ${fade} ${state.callout ? 'opacity-100' : 'opacity-0'}`}
      style={{left: flip ? undefined : Math.min(cx + 18, w - 248), right: flip ? Math.max(w - cx + 18, 8) : undefined, top: Math.max(PAD.t, cy - (w < 640 ? 120 : 150))}}>
      {callout}
    </div>}
  </div>;
}

/** Whole-market context: the full price path with the zoomed window marked. */
function InsetChart({price, x0, x1, label}: {price: [number, number][]; x0: number; x1: number; label: string}) {
  const W = 168, H = 64, a = price[0][0], b = price[price.length - 1][0];
  const x = (t: number) => ((t - a) / (b - a)) * W, y = (p: number) => 4 + (1 - p) * (H - 8);
  return <figure className="absolute start-16 top-1/4 hidden border border-line bg-panel p-2 sm:block" aria-label={label}>
    <figcaption className="type-micro text-text-3">{label}</figcaption>
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} aria-hidden className="mt-1 block">
      <rect x={x(x0)} y={0} width={Math.max(2, x(x1) - x(x0))} height={H} className="fill-hover stroke-text-3" strokeWidth={1}/>
      <path d={stepPath(price, x, y)} className="fill-none stroke-text-2" strokeWidth={1}/>
    </svg>
  </figure>;
}
