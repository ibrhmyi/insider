'use client';

import {useState} from 'react';
import {InvestigationChart, type ChartBuy} from './chart';
import {FlagMark, FLAG_RULE_SHORT, flagValue} from './flag-marks';
import {WalletTable, DocTag, type CaseWallet} from './wallet-table';
import {DISCLAIMER, FLAGS, usd} from '@/lib/copy';
import {STATE_ALL} from '@/lib/chart-state';

type ChartData = {price: [number, number][]; tNews: number; x0: number; x1: number; newsLabel: string};

function Detail({w, nWallets}: {w: CaseWallet; nWallets: number}) {
  const fired = new Set(w.flags);
  return <section aria-labelledby="detail-title" className="panel flex flex-col">
    <div className="panel-head">
      <h2 id="detail-title" className="type-label">Wallet <span className="type-code">{w.id}…</span></h2>
      {w.doc && <DocTag doc={w.doc}/>}
    </div>
    <div className="flex flex-col gap-4 p-4">
      <p className="type-body text-text-2">Rank {w.rank} of {nWallets.toLocaleString('en-US')}. Bought {usd(w.usd)} of {w.side} before the news{w.firstHigh !== null ? `, flagged ${w.firstHigh.toFixed(0)} h before it` : ''}.</p>
      <ul className="flex flex-col">
        {FLAGS.map(f => <li key={f} className="flex items-center justify-between gap-3 border-t border-line py-2 first:border-t-0">
          <FlagMark f={f} fired={fired.has(f)} value={flagValue(f, w)}/>
          <span className="type-body-sm text-end text-text-3">{FLAG_RULE_SHORT[f]}</span>
        </li>)}
      </ul>
      {w.doc && <p className="type-body-sm text-text-2">{w.doc.claim}</p>}
      <p className="type-body-sm text-text-3">After resolution, never in the score: {w.won ? 'its side won' : 'its side lost'}{w.dormant === null ? '.' : w.dormant ? ', then it went quiet for 30 days.' : ', and it kept trading.'}</p>
      <p className="type-body-sm text-text-2">{DISCLAIMER}</p>
    </div>
  </section>;
}

export function CaseExplorer({chart, buys, rows, nWallets, flaggedMin, market}: {
  chart: ChartData; buys: (ChartBuy & {w: string})[]; rows: CaseWallet[]; nWallets: number; flaggedMin: number; market: string;
}) {
  const [sel, setSel] = useState((rows.find(r => r.usd >= flaggedMin) ?? rows[0])?.id);
  const w = rows.find(r => r.id === sel) ?? rows[0];
  const chartBuys = buys.map(b => ({...b, focus: b.w === sel}));
  return <div className="flex min-w-0 flex-col gap-6">
    <div className="h-[56svh] min-h-80 border border-line p-3">
      <InvestigationChart {...chart} buys={chartBuys} state={{...STATE_ALL, callout: false}} inset={{price: chart.price, label: 'Whole market'}}
        label={`${market}: Yes price and pre-news buys, last 48 hours; flagged buys in yellow, the selected wallet ringed`}/>
    </div>
    <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,8fr)_minmax(0,4fr)]">
      <WalletTable rows={rows} flaggedMin={flaggedMin} selected={sel} onSelect={setSel} market={market}/>
      {w && <Detail w={w} nWallets={nWallets}/>}
    </div>
  </div>;
}
