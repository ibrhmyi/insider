'use client';

import {Scrolly, type Step} from './scrolly';
import {FlagMark, flagValue, type FlagValues} from './flag-marks';
import type {ChartBuy} from './chart';
import {DISCLAIMER, FLAGS} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

export type MaduroData = {
  price: [number, number][];
  buys: ChartBuy[];
  tNews: number;
  resolution: number;
  firstHighH: number;
  wallet: FlagValues & {id: string; handle: string; fired: FlagId[]; nWallets: number};
  counts: {buys48: number; wallets48: number; flaggedWallets48: number};
  priceStats: {median: number; max: number};
  source: {url: string; publisher: string};
};

const H = 3600;

export function MaduroInvestigation({d}: {d: MaduroData}) {
  const x0 = d.tNews - 48 * H;
  const firstHighT = d.tNews - d.firstHighH * H;
  const w = d.wallet;
  const cents = (p: number) => `${Math.round(p * 100)}¢`;

  const steps: Step[] = [
    {id: 'step-1', title: 'The market said: unlikely', state: {line: 'pre', dots: 'none', focus: false, news: false, callout: false},
      body: <p>For the two days before the news, &ldquo;Maduro out by January 31&rdquo; traded around {cents(d.priceStats.median)}, never above {cents(d.priceStats.max)}. Buyers of Yes were betting on a long shot.</p>},
    {id: 'step-2', title: 'Every buy, as a dot', state: {line: 'pre', dots: 'faint', focus: false, news: false, callout: false},
      body: <p>{d.counts.buys48.toLocaleString('en-US')} buys by {d.counts.wallets48.toLocaleString('en-US')} wallets in those 48 hours. Bigger dot, more money. Most are small and ordinary.</p>},
    {id: 'step-3', title: 'Six signs, scored per wallet', state: {line: 'pre', dots: 'flagged', focus: false, news: false, callout: false},
      body: <><p>The screen scores each wallet on six signs from published research, fixed before any result was seen.</p>
        <p>Yellow: wallets showing 4 or more signs that bought $2,500 or more. {d.counts.flaggedWallets48} wallets light up.</p></>},
    {id: 'step-4', title: 'One wallet stands out', state: {line: 'pre', dots: 'flagged', focus: true, news: false, callout: true},
      body: <p>Wallet <span className="type-code">{w.id}…</span> crossed the line {d.firstHighH.toFixed(0)} hours before the news, then kept buying. Of all {w.nWallets.toLocaleString('en-US')} pre-news buyers, it ranks first.</p>},
    {id: 'step-5', title: '06:00 UTC, January 3', state: {line: 'full', dots: 'flagged', focus: true, news: true, callout: true},
      body: <p>First reports of explosions over Caracas. Within hours the price runs to 100¢ and the market resolves Yes.</p>},
    {id: 'step-6', title: 'All six signs, for this wallet', state: {line: 'full', dots: 'flagged', focus: true, news: true, callout: false},
      body: <p>A new account, nearly all its money in this one market, longshot prices, a large total, one direction only, and its buys bunched hours before the news.</p>},
    {id: 'step-7', title: 'Then the public record', state: {line: 'full', dots: 'flagged', focus: true, news: true, callout: false},
      body: <><p className="type-heading-sm text-text-1">In April 2026 the CFTC charged its alleged owner.</p>
        <p>Charged, not convicted. <a href={d.source.url} target="_blank" rel="noreferrer" className="text-text-1 underline underline-offset-4 focus-visible:focus-ring">Read the CFTC complaint summary</a> ({d.source.publisher}).</p>
        <p className="type-body-sm">{DISCLAIMER}</p></>},
  ];

  const callout = <div className="flex flex-col gap-1">
    <span className="type-code text-accent-text">{w.handle}</span>
    <span className="type-body-sm text-text-1">${Math.round(w.usd).toLocaleString('en-US')} at {cents(w.avg)}</span>
    <span className="type-body-sm text-text-1">Account {w.f1.toFixed(1)} days old</span>
    <span className="type-body-sm text-text-1">{Math.round((w.f2share ?? 0) * 100)}% of its money in this market</span>
  </div>;

  const aside = (active: number) => {
    const lit = active >= 5;
    return <div aria-label={`Signs for wallet ${w.id}`} className="grid grid-cols-2 gap-x-6 gap-y-2 border-t border-line pt-3 sm:grid-cols-3">
      {FLAGS.map((f, i) => <span key={f} style={{'--flag-delay': lit ? `${i * 140}ms` : '0ms'} as React.CSSProperties}>
        <FlagMark f={f} fired={lit && w.fired.includes(f)} value={flagValue(f, w)} size="lg"/>
      </span>)}
    </div>;
  };

  return <Scrolly label="Maduro out by January 31, 2026: Yes price and pre-news buys, last 48 hours" steps={steps} aside={aside}
    chart={{price: d.price, buys: d.buys, tNews: d.tNews, x0, x1: d.resolution, newsLabel: 'First news 06:00 UTC', firstHighT, firstHighLabel: `Crossed 4 signs, ${d.firstHighH.toFixed(0)} h before`, callout,
      inset: {price: d.price, label: 'Whole market'}}}/>;
}
