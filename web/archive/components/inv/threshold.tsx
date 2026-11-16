'use client';

import {useState} from 'react';
import {Slider} from '@/components/sodium/ui/slider';
import {StatusStrip, StatusStripCell, StatusStripLabel, StatusStripValue} from '@/components/sodium/ui/status-strip';
import {ScoreBars} from './score-bars';

type Row = {score: number; wallets: number; documented: number; under1k: number};

/** Move the cut-off and watch flagged wallets and named wallets caught trade off. The frozen line is 4. */
export function Threshold({dist, namedTotal, frozen}: {dist: Row[]; namedTotal: number; frozen: number}) {
  const [k, setK] = useState(frozen);
  const above = dist.filter(d => d.score >= k);
  const sum = (f: (d: Row) => number) => above.reduce((a, d) => a + f(d), 0);
  return <div className="grid gap-6 lg:grid-cols-2 lg:items-center">
    <ScoreBars dist={dist} cutoff={k}/>
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3">
        <span id="cutoff" className="type-label">Flag at {k} or more signs{k === frozen ? ', the frozen line' : ''}</span>
        <Slider aria-labelledby="cutoff" min={1} max={6} step={1} value={k} onValueChange={v => setK(Array.isArray(v) ? v[0] : v)}/>
      </div>
      <StatusStrip label="At this cut-off">
        <StatusStripCell><StatusStripLabel>Named wallets caught</StatusStripLabel><StatusStripValue>{sum(d => d.documented)} of {namedTotal}</StatusStripValue></StatusStripCell>
        <StatusStripCell><StatusStripLabel>Wallets flagged</StatusStripLabel><StatusStripValue>{sum(d => d.wallets).toLocaleString('en-US')}</StatusStripValue></StatusStripCell>
        <StatusStripCell><StatusStripLabel>Of those, under $1,000</StatusStripLabel><StatusStripValue>{sum(d => d.under1k).toLocaleString('en-US')}</StatusStripValue></StatusStripCell>
      </StatusStrip>
      <p className="type-body-sm text-text-2">Counts are wallet-markets across all three markets, n = {dist.reduce((a, d) => a + d.wallets, 0).toLocaleString('en-US')}. Moving the line here does not change the frozen rule.</p>
    </div>
  </div>;
}
