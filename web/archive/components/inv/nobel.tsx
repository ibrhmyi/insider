'use client';

import {Scrolly, type Step} from './scrolly';
import type {ChartBuy} from './chart';
import {DISCLAIMER} from '@/lib/copy';

export type NobelData = {
  price: [number, number][]; buys: ChartBuy[]; tNews: number; resolution: number;
  jumpH: number; flaggedWallets: number; earliestFlaggedH: number;
  perm: {observed: number; nullMean: number; p: number};
  follow: {diff: number; n: number; ci: [number, number]};
};

const H = 3600;

export function NobelStory({d}: {d: NobelData}) {
  const steps: Step[] = [
    {id: 'nobel-1', title: 'A long shot for days', state: {line: 'pre', dots: 'none', focus: false, news: false, callout: false},
      body: <p>Will María Corina Machado win the 2025 Nobel Peace Prize? For days the market said almost certainly not: about 1¢.</p>},
    {id: 'nobel-2', title: 'Then, overnight, a jump', state: {line: 'pre', dots: 'faint', focus: false, news: false, callout: false},
      body: <p>About {d.jumpH.toFixed(0)} hours before the announcement the price leapt past 50¢, with no public news. Every dot is a buy.</p>},
    {id: 'nobel-3', title: 'Flagged wallets were in the jump', state: {line: 'pre', dots: 'flagged', focus: false, news: false, callout: false},
      body: <p>{d.flaggedWallets} wallets with 4 or more signs and $2,500 or more bought in the last {d.earliestFlaggedH.toFixed(0)} hours. Two of them were later named in reporting (alleged).</p>},
    {id: 'nobel-4', title: 'Announcement, 09:00 UTC', state: {line: 'full', dots: 'flagged', focus: false, news: true, callout: false},
      body: <p>The committee names Machado. The price goes to 100¢.</p>},
    {id: 'nobel-5', title: 'Both tests point the same way', state: {line: 'full', dots: 'flagged', focus: false, news: true, callout: false},
      body: <><p>Shuffle test: {d.perm.observed} wallets flagged against {d.perm.nullMean} expected from random timing, p = {d.perm.p.toFixed(3)}.</p>
        <p>Follow-on test: {d.follow.diff.toFixed(1)} more traders bought the same side within 30 minutes of a flagged buy than after a matched ordinary buy (95% CI {d.follow.ci[0].toFixed(1)} to {d.follow.ci[1].toFixed(1)}, n = {d.follow.n}).</p>
        <p>Nobel is the only one of the three markets where either test shows an effect.</p>
        <p className="type-body-sm">{DISCLAIMER}</p></>},
  ];
  return <Scrolly label="Nobel Peace Prize 2025, Machado: Yes price and pre-news buys, last 48 hours" steps={steps}
    chart={{price: d.price, buys: d.buys, tNews: d.tNews, x0: d.tNews - 48 * H, x1: d.resolution, newsLabel: 'Announcement 09:00 UTC', inset: {price: d.price, label: 'Whole market'}}}/>;
}
