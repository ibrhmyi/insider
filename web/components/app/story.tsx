'use client';

import {useCallback, useEffect, useRef, useState} from 'react';
import Link from 'next/link';
import {Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis} from 'recharts';
import {Button} from '@/components/quartz/ui/button';
import {Kbd} from '@/components/quartz/ui/kbd';
import {AlertCard, type AlertCardProps} from './alert-card';
import {FLAGS, FLAG_NAMES, FLAG_RULE, NOT_PROOF} from '@/lib/copy';
import type {V0Summary} from '@/lib/types';

export type StoryData = {
  v0: V0Summary;
  dist: {score: number; wallets: number; documented: number}[];
  headline: {rank: number; n_in_market: number; hours_before: number; documented_flagged: number; documented_total: number; n_high_total: number; n_high_under_1k: number};
  perm: {short: string; observed: number; null_mean: number; p: number}[];
  alert: AlertCardProps;
};

const TITLES = ['The problem', 'Attempt 1: ripples', 'A new method', 'The result', 'One alert: Maduro', 'What it cannot say'];

function Step({n, children}: {n: number; children: React.ReactNode}) {
  return <div className="flex w-full max-w-(--container) flex-col gap-8">
    <p className="type-label text-text-3">Step {n + 1} of {TITLES.length}</p>
    {children}
  </div>;
}

function Big({children}: {children: React.ReactNode}) {
  return <h1 className="type-display-lg max-w-5xl text-balance">{children}</h1>;
}

export function Story({data}: {data: StoryData}) {
  const [i, setI] = useState(0);
  const heading = useRef<HTMLDivElement>(null);
  const go = useCallback((d: number) => setI(x => Math.max(0, Math.min(TITLES.length - 1, x + d))), []);

  useEffect(() => {
    const s = Number(new URLSearchParams(window.location.search).get('step'));
    if (s >= 1 && s <= TITLES.length) setI(s - 1);
  }, []);
  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('step', String(i + 1));
    window.history.replaceState(null, '', url);
    heading.current?.focus({preventScroll: true});
  }, [i]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); go(1); }
      else if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); go(-1); }
      else if (e.key === 'Home') { e.preventDefault(); setI(0); }
      else if (e.key === 'End') { e.preventDefault(); setI(TITLES.length - 1); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [go]);

  const {v0, headline: h} = data;
  const ip = v0.pooled['insider-possible'], ctl = v0.pooled['insider-impossible'];
  const steps = [
    <Step n={0} key={0}>
      <Big>Some traders may know how a prediction market ends before anyone else does.</Big>
      <p className="type-body-lg max-w-(--measure) text-text-2">A strike order, a captured leader, a prize decided behind closed doors: a small group knows first. Can public trade data alone show who bet on that knowledge, before the news broke?</p>
      <p className="type-body-lg max-w-(--measure) text-text-2">Three Polymarket markets: the June 2025 US strike on Iran, Maduro out by January 31, 2026, and María Corina Machado&apos;s 2025 Nobel Peace Prize.</p>
    </Step>,
    <Step n={1} key={1}>
      <Big>Attempt 1 looked for ripples after large trades. It found nothing.</Big>
      <div className="grid gap-8 md:grid-cols-2">
        <div className="flex flex-col gap-4">
          {[{l: 'Insider-possible markets', v: ip}, {l: 'Bitcoin price controls', v: ctl}].map(r => <div key={r.l} className="flex flex-col gap-1">
            <span className="flex items-baseline justify-between gap-4 type-body"><span>{r.l}</span><span className="data">+{r.v.mean_excess.toFixed(2)} extra wallets (n = {r.v.n_seeds} large trades)</span></span>
            <span className="block h-(--space-3) w-(--pct) bg-chart-ink-2" style={{'--pct': `${(r.v.mean_excess / 2.5) * 100}%`} as React.CSSProperties} aria-hidden/>
          </div>)}
          <p className="type-body text-text-2">Permutation p = {v0.p_value.toFixed(2)}. Followers after a large trade were no more common where insiders were possible.</p>
        </div>
        <div className="flex flex-col gap-2">
          <p className="type-heading-sm">Blind test on Maduro</p>
          <p className="type-body-lg text-text-2">{v0.maduro_blind.alerts_pre_news} alert before the news: {v0.maduro_blind.hours_before_news} hours early, and pointing the wrong way. The busiest final hours could not be scored at all.</p>
        </div>
      </div>
    </Step>,
    <Step n={2} key={2}>
      <Big>Score the wallet, not the trade: six flags, frozen before any result.</Big>
      <ol className="grid gap-x-8 gap-y-4 md:grid-cols-2">
        {FLAGS.map(f => <li key={f} className="flex flex-col gap-0.5">
          <span className="type-heading-xs"><span className="text-text-3">{f}</span> {FLAG_NAMES[f]}</span>
          <span className="type-body text-text-2">{FLAG_RULE[f]}</span>
        </li>)}
      </ol>
      <p className="type-body-lg max-w-(--measure) text-text-2">Score = flags fired, 0 to 6. Four or more is a high score. The rules were committed to git before a single feature was computed.</p>
    </Step>,
    <Step n={3} key={3}>
      <Big>All {h.documented_total} wallets named in public reporting score 4 or more.</Big>
      <div className="grid gap-8 lg:grid-cols-[3fr_2fr]">
        <figure className="flex flex-col gap-2" aria-label={`Wallets by score across 3 markets: ${data.dist.map(d => `score ${d.score}: ${d.wallets} wallets, ${d.documented} documented`).join('; ')}`}>
          <div className="h-80" data-kind="model">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart accessibilityLayer={false} data={data.dist} margin={{top: 28, right: 8, bottom: 8, left: 0}}>
                <CartesianGrid vertical={false} stroke="var(--line-row)"/>
                <XAxis dataKey="score" stroke="var(--line-row)" tick={{fill: 'var(--text-3)', fontSize: 13}} tickLine={false} label={{value: 'Score (flags fired)', position: 'insideBottom', offset: -2, fill: 'var(--text-3)', fontSize: 12}} height={48}/>
                <YAxis scale="log" domain={[1, 4000]} ticks={[1, 10, 100, 1000]} allowDataOverflow stroke="var(--line-row)" tick={{fill: 'var(--text-3)', fontSize: 12}} tickLine={false} axisLine={false} width={44}/>
                <Bar dataKey="wallets" isAnimationActive={false} fill="var(--chart-ink-2)" radius={[2, 2, 0, 0]}>
                  <LabelList dataKey="documented" position="top" formatter={(v: unknown) => (Number(v) ? `${v} named` : '')} fill="var(--accent-label)" fontSize={13}/>
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <figcaption className="type-body-sm text-text-2">Wallets per score, all 3 markets, n = {data.dist.reduce((a, d) => a + d.wallets, 0).toLocaleString('en-US')} wallet-markets; log scale. Labels count wallets named in public reporting.</figcaption>
        </figure>
        <div className="flex flex-col gap-4">
          <p className="type-heading-sm">The CFTC-charged wallet ranks {h.rank} of {h.n_in_market.toLocaleString('en-US')}, and crossed 4 flags {h.hours_before} hours before the news.</p>
          <p className="type-body text-text-2">Against random timing (1,000 timestamp permutations per market):</p>
          <ul className="flex flex-col gap-1">
            {data.perm.map(p => <li key={p.short} className="type-body data">{p.short}: {p.observed} high scores vs {p.null_mean} expected, p = {p.p.toFixed(3)}</li>)}
          </ul>
          <p className="type-body text-text-2">Only Nobel beats chance.</p>
        </div>
      </div>
    </Step>,
    <Step n={4} key={4}>
      <h1 className="type-heading-lg">The alert card for the top Maduro wallet</h1>
      <AlertCard {...data.alert} compact/>
    </Step>,
    <Step n={5} key={5}>
      <Big>A tool for review, not a verdict.</Big>
      <ul className="grid gap-x-8 gap-y-5 md:grid-cols-2">
        <li className="flex flex-col gap-1"><span className="type-heading-xs">Circular validation</span><span className="type-body text-text-2">Journalists found these wallets with similar cues, so catching them is partly by construction.</span></li>
        <li className="flex flex-col gap-1"><span className="type-heading-xs">Precision unproven</span><span className="type-body text-text-2">{h.n_high_total} wallet-markets score high; {h.n_high_under_1k} bought under $1,000. How many were informed is unknown.</span></li>
        <li className="flex flex-col gap-1"><span className="type-heading-xs">F6 needs the news time</span><span className="type-body text-text-2">Live, nobody knows when the news will break, so a live score uses only 5 flags.</span></li>
        <li className="flex flex-col gap-1"><span className="type-heading-xs">Three markets only</span><span className="type-body text-text-2">Followers did not pile in after high-score buys, except on Nobel. More markets are the way to power.</span></li>
      </ul>
      <p className="type-heading-sm">{NOT_PROOF}</p>
    </Step>,
  ];

  return <div className="fixed inset-0 z-(--z-cover) flex flex-col bg-page">
    <div className="flex h-(--topbar) shrink-0 items-center justify-between gap-4 px-(--gutter-sm) sm:px-(--gutter)">
      <span className="type-label">Insider Signal</span>
      <span className="hidden items-center gap-2 type-label-sm text-text-3 sm:flex"><Kbd>←</Kbd><Kbd>→</Kbd> to move</span>
      <Button variant="ghost" size="sm" nativeButton={false} render={<Link href="/"/>}>Exit story</Button>
    </div>
    <div ref={heading} tabIndex={-1} data-control aria-live="polite" aria-label={`${TITLES[i]}, step ${i + 1} of ${TITLES.length}`}
      className="flex min-h-0 flex-1 flex-col overflow-y-auto px-(--gutter-sm) py-8 sm:px-(--gutter)">
      <div key={i} className="my-auto flex w-full justify-center motion-safe:animate-[story-in_var(--dur-slow)_var(--ease-step)]">{steps[i]}</div>
    </div>
    <nav aria-label="Story steps" className="flex shrink-0 items-center justify-between gap-4 px-(--gutter-sm) py-4 sm:px-(--gutter)">
      <Button variant="secondary" size="sm" onClick={() => go(-1)} disabled={i === 0}>Previous step</Button>
      <ol className="flex items-center gap-1">
        {TITLES.map((t, k) => <li key={t}>
          <Button variant="ghost" size="icon-xs" onClick={() => setI(k)} aria-label={`Step ${k + 1}: ${t}`} aria-current={k === i ? 'step' : undefined}>
            <span aria-hidden className={`block h-(--space-1) w-(--space-6) rounded-inner ${k === i ? 'bg-ink' : 'bg-cell-quiet'}`}/>
          </Button>
        </li>)}
      </ol>
      <Button size="sm" onClick={() => go(1)} disabled={i === TITLES.length - 1}>Next step</Button>
    </nav>
  </div>;
}
