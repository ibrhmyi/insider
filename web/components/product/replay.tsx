'use client';

import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {Button} from '@/components/sodium/ui/button';
import {SegmentedControl, SegmentedControlItem} from '@/components/sodium/ui/segmented-control';
import {Slider} from '@/components/sodium/ui/slider';
import {DISCLAIMER, FLAG_SHORT, FLAGS, usd} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

/** maduro_replay.json, written by src/export_web.py replay(). Row: [t, usd, price, side, wallet, score5, signs, wallet_usd_so_far, alert]. */
export type ReplayData = {
  t0: number; t_news: number; resolution: number; n_buyers: number;
  price: [number, number][];
  wallets: {id: string; doc: boolean; final_score: number; final_flags: FlagId[]; n_markets: number | null; rank: number}[];
  buys: [number, number, number, string, number, number, string, number, number][];
};

const RATE = 900;          // 1x = 15 market-minutes per second
const SPEEDS = [1, 10, 60];
const FEED_MIN = 500;      // the feed lists buys of $500 or more; every alert is listed
const signsOf = (s: string) => s.split('').map(d => `F${d}` as FlagId);
const clock = (t: number) => {
  const d = new Date(t * 1000);
  return `${d.toLocaleDateString('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'})}, ${d.toISOString().slice(11, 16)} UTC`;
};
const hoursBefore = (t: number, tn: number) => `${((tn - t) / 3600).toFixed(1)} h before the news`;

function useReducedMotion() {
  const [r, set] = useState(false);
  useEffect(() => { const m = window.matchMedia('(prefers-reduced-motion: reduce)'); set(m.matches); const f = () => set(m.matches); m.addEventListener('change', f); return () => m.removeEventListener('change', f); }, []);
  return r;
}

function Chart({d, now, alerts}: {d: ReplayData; now: number; alerts: ReplayData['buys']}) {
  const W = 1000, H = 520, P = {l: 70, r: 16, t: 20, b: 44};
  const x = (t: number) => P.l + ((t - d.t0) / (d.resolution - d.t0)) * (W - P.l - P.r);
  const y = (p: number) => P.t + (1 - p) * (H - P.t - P.b);
  const pts = d.price.filter(([t]) => t <= now);
  let path = '';
  pts.forEach(([t, p], i) => { path += i ? `H${x(t).toFixed(1)}V${y(p).toFixed(1)}` : `M${x(t).toFixed(1)},${y(p).toFixed(1)}`; });
  if (pts.length) path += `H${x(now).toFixed(1)}`;
  const last = pts.length ? pts[pts.length - 1][1] : null;
  const days = [86400, 2 * 86400].map(k => d.t0 + k).filter(t => t < d.resolution);
  return <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" role="img"
    aria-label={`Yes price from Jan 1. Now ${clock(now)}${last !== null ? `, price ${Math.round(last * 100)} cents` : ''}${now >= d.t_news ? '. The news broke at 06:00 UTC on Jan 3' : ''}.`}>
    {[0, 0.25, 0.5, 0.75, 1].map(p => <g key={p}>
      <line x1={P.l} x2={W - P.r} y1={y(p)} y2={y(p)} className="stroke-line" strokeWidth={1}/>
      <text x={P.l - 10} y={y(p)} dy="0.35em" textAnchor="end" className="fill-text-3 type-heading-sm">{Math.round(p * 100)}¢</text>
    </g>)}
    {days.map(t => <text key={t} x={x(t)} y={H - 12} textAnchor="middle" className="fill-text-3 type-heading-sm">{clock(t).split(',')[0]}</text>)}
    <text x={P.l} y={H - 12} className="fill-text-3 type-heading-sm">Jan 1</text>
    {now >= d.t_news && <g>
      <line x1={x(d.t_news)} x2={x(d.t_news)} y1={P.t} y2={H - P.b} className="stroke-text-1" strokeWidth={2} strokeDasharray="6 6"/>
      <text x={x(d.t_news) - 10} y={P.t + 22} textAnchor="end" className="fill-text-1 type-heading-sm">News, 06:00 UTC</text>
    </g>}
    <path d={path} className="fill-none stroke-text-1" strokeWidth={2.5}/>
    {alerts.map(a => <circle key={a[0]} cx={x(a[0])} cy={y(a[2])} r={9} className="fill-accent-text stroke-page" strokeWidth={2}/>)}
    <line x1={x(now)} x2={x(now)} y1={P.t} y2={H - P.b} className="stroke-text-3" strokeWidth={1}/>
  </svg>;
}

function AlertCard({row, d, now}: {row: ReplayData['buys'][number]; d: ReplayData; now: number}) {
  const w = d.wallets[row[4]];
  const fired = new Set(signsOf(row[6]));
  const after = now >= d.t_news;
  return <li className="flex flex-col gap-3 border border-accent-edge bg-panel p-5 motion-safe:animate-[alert-in_var(--dur-overlay)_var(--ease-out)]">
    <div className="flex flex-wrap items-baseline justify-between gap-3">
      <span className="type-label text-accent-text">Worth a look</span>
      <span className="type-code text-text-3">{clock(row[0])}</span>
    </div>
    <p className="type-product text-text-1">Wallet <span className="type-code">{w.id}…</span> has bought {usd(row[7])} so far, now at {Math.round(row[2] * 100)}¢.</p>
    <ul className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Signs">
      {FLAGS.map(f => {
        const unknown = f === 'F6' && !after;
        // before the news: signs as they stood at the alert; after: the wallet's final signs, matching its 6-sign score
        const on = after ? w.final_flags.includes(f) : f !== 'F6' && fired.has(f);
        return <li key={f} className="flex items-center gap-2">
          <span aria-hidden className={`size-3 border ${on ? 'border-accent-edge bg-accent-text' : 'border-text-3'}`}/>
          <span className={`type-product ${on ? 'text-text-1' : 'text-text-3'}`}>{FLAG_SHORT[f]}{unknown ? ': unknown until news' : on ? '' : ': no'}</span>
        </li>;
      })}
    </ul>
    <p className="type-product text-text-2">{after ? `Score ${w.final_score} of 6. Alert came ${hoursBefore(row[0], d.t_news)}.` : `Score ${row[5]} of 5 so far.`}</p>
  </li>;
}

export function Replay({d}: {d: ReplayData}) {
  const reduced = useReducedMotion();
  const [now, setNow] = useState(d.t0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(10);
  const raf = useRef(0);

  useEffect(() => {
    if (!playing || reduced) return;
    let last = performance.now();
    const tick = (ts: number) => {
      const dt = (ts - last) / 1000; last = ts;
      setNow(n => { const next = Math.min(d.resolution, n + dt * RATE * speed); if (next >= d.resolution) setPlaying(false); return next; });
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [playing, speed, reduced, d.resolution]);

  const feedAll = useMemo(() => d.buys.filter(b => b[1] >= FEED_MIN || b[8]).sort((a, b) => a[0] - b[0] || a[8] - b[8]), [d.buys]);
  const alertsAll = useMemo(() => d.buys.filter(b => b[8]), [d.buys]);
  const feed = feedAll.filter(b => b[0] <= now).slice(-6).reverse();
  const alerts = alertsAll.filter(b => b[0] <= now).reverse();
  const stops = useMemo(() => [...new Set([d.t0, ...alertsAll.map(a => a[0]), d.t_news, d.resolution])].sort((a, b) => a - b), [alertsAll, d]);
  const step = useCallback((dir: 1 | -1) => {
    setPlaying(false);
    setNow(n => (dir > 0 ? stops.find(s => s > n + 1) ?? d.resolution : [...stops].reverse().find(s => s < n - 1) ?? d.t0));
  }, [stops, d]);
  const done = now >= d.resolution;
  // The story's wallet: the one ranked 1st of all pre-news buyers (the CFTC-charged wallet in this market).
  const first = alertsAll.find(a => d.wallets[a[4]].rank === 1);
  const firstW = first ? d.wallets[first[4]] : null;
  const unnamed = alertsAll.filter(a => !d.wallets[a[4]].doc).length;

  return <div className="flex flex-col gap-6">
    <div className="neutral-controls flex flex-wrap items-center gap-3">
      {!reduced && <Button variant="secondary" size="lg" onClick={() => { if (done) setNow(d.t0); setPlaying(p => !p); }}>{playing ? 'Pause replay' : done ? 'Play again' : 'Play replay'}</Button>}
      <Button variant="ghost" size="lg" onClick={() => step(-1)} disabled={now <= d.t0}>Previous event</Button>
      <Button variant="ghost" size="lg" onClick={() => step(1)} disabled={done}>Next event</Button>
      {!reduced && <SegmentedControl aria-label="Replay speed" value={String(speed)} onValueChange={v => setSpeed(Number(v))}>
        {SPEEDS.map(s => <SegmentedControlItem key={s} value={String(s)}>{s}×</SegmentedControlItem>)}
      </SegmentedControl>}
      <span className="type-code ms-auto text-text-2" aria-live="off">{clock(now)}</span>
    </div>
    <div className="neutral-controls"><Slider aria-label="Replay time" thumbLabels={["Replay time"]} min={d.t0} max={d.resolution} step={300} value={Math.round(now)}
      onValueChange={v => { setPlaying(false); setNow(Array.isArray(v) ? v[0] : v); }}/></div>
    {reduced && <p className="type-product text-text-3">Animation is off: use Next event or the time slider to step through.</p>}

    <div className="grid gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
      <Chart d={d} now={now} alerts={alerts}/>
      <div className="flex min-w-0 flex-col gap-4">
        <ul aria-live="polite" aria-label="Alerts" className="flex flex-col gap-3">
          {alerts.map(a => a[0] === (done && first ? first[0] : alerts[0]?.[0])
            ? <AlertCard key={a[0]} row={a} d={d} now={now}/>
            : <li key={a[0]} className="flex flex-wrap items-baseline gap-x-4 border border-accent-edge px-4 py-2">
              <span className="type-label text-accent-text">Worth a look</span>
              <span className="type-product text-text-1"><span className="type-code">{d.wallets[a[4]].id}…</span> {usd(a[7])} at {Math.round(a[2] * 100)}¢</span>
              <span className="type-code text-text-3">{now >= d.t_news ? hoursBefore(a[0], d.t_news) : clock(a[0])}</span>
            </li>)}
        </ul>
        <div className="flex flex-col">
          <h3 className="type-label text-text-3">Buys of {usd(FEED_MIN)} or more, as they happened</h3>
          <ul className="flex flex-col" aria-label="Recent buys">
            {feed.length === 0 && <li className="type-product py-3 text-text-3">Press play to start the market at Jan 1, 00:00 UTC.</li>}
            {feed.map(b => <li key={`${b[0]}-${b[4]}`} className="grid grid-cols-[auto_1fr_auto] items-baseline gap-x-4 border-b border-line py-2">
              <span className="type-code text-text-3">{new Date(b[0] * 1000).toISOString().slice(11, 16)}</span>
              <span className="type-product text-text-1">{usd(b[1])} {b[3]} at {Math.round(b[2] * 100)}¢</span>
              <span aria-label={`Score ${b[5]} of 5`} className={`type-code ${b[8] ? 'text-accent-text' : 'text-text-3'}`}>{b[5]}/5</span>
            </li>)}
          </ul>
        </div>
      </div>
    </div>

    {done && first && firstW && <div className="flex flex-col gap-2">
      <p className="type-product-title max-w-measure">In this replay, {alertsAll.length} wallets reached 4 signs before the news. The one later charged by the CFTC was flagged {Math.round((d.t_news - first[0]) / 3600)} hours early and ranks 1st of {d.n_buyers.toLocaleString('en-US')} buyers.</p>
      <p className="type-product text-text-2">{unnamed} of the {alertsAll.length} have never been publicly accused.</p>
    </div>}
    <p className="type-product text-text-3">{DISCLAIMER}</p>
  </div>;
}
