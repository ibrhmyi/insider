'use client';

import {useState} from 'react';
import {Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis} from 'recharts';
import {Slider} from '@/components/quartz/ui/slider';

type Props = {dist: {score: number; wallets: number; documented: number; under1k: number}[]; total: number; documentedTotal: number; frozen: number};

/** Where to draw the line: move the cut-off and watch flagged wallets and documented cases trade off. */
export function Threshold({dist, total, documentedTotal, frozen}: Props) {
  const [k, setK] = useState(frozen);
  const above = dist.filter(d => d.score >= k);
  const flagged = above.reduce((a, d) => a + d.wallets, 0);
  const caught = above.reduce((a, d) => a + d.documented, 0);
  const small = above.reduce((a, d) => a + d.under1k, 0);

  return <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-center">
    <figure className="flex flex-col gap-2" aria-label={`Wallets per number of flags; ${flagged} have ${k} or more.`}>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart accessibilityLayer={false} data={dist} margin={{top: 8, right: 4, bottom: 0, left: 0}}>
            <XAxis dataKey="score" stroke="var(--line-row)" tick={{fill: 'var(--text-3)', fontSize: 12}} tickLine={false} tickFormatter={v => `${v} flags`}/>
            <YAxis scale="log" domain={[1, 4000]} ticks={[1, 10, 100, 1000]} allowDataOverflow stroke="var(--line-row)" tick={{fill: 'var(--text-3)', fontSize: 12}} tickLine={false} axisLine={false} width={40}/>
            <Bar dataKey="wallets" isAnimationActive={false} radius={[2, 2, 0, 0]}>
              {dist.map(d => <Cell key={d.score} data-kind="run" className={d.score >= k ? 'fill-accent-line' : 'fill-cell-quiet'}/>)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="type-label-sm text-text-3">Wallets by number of flags, all three markets, n = {total.toLocaleString('en-US')}; log scale.</figcaption>
    </figure>
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-2">
        <span className="type-label" id="cutoff-label">Flag a wallet at {k} or more of 6{k === frozen ? ' (the frozen line)' : ''}</span>
        <Slider aria-labelledby="cutoff-label" min={1} max={6} step={1} value={k} onValueChange={v => setK(Array.isArray(v) ? v[0] : v)}/>
      </div>
      <dl className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1"><dt className="type-label-sm text-text-3">Named wallets caught</dt><dd className="type-stat-lg">{caught}<span className="type-heading-sm text-text-3"> / {documentedTotal}</span></dd></div>
        <div className="flex flex-col gap-1"><dt className="type-label-sm text-text-3">Wallets flagged</dt><dd className="type-stat-lg">{flagged.toLocaleString('en-US')}</dd></div>
      </dl>
      <p className="type-body text-text-2">{small.toLocaleString('en-US')} of the flagged bought under $1,000. Nobody knows how many of the unnamed ones were informed.</p>
    </div>
  </div>;
}
