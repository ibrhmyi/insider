'use client';

import {Bar, BarChart, ReferenceLine, ResponsiveContainer, XAxis, YAxis} from 'recharts';

/** Permutation null: how many wallets score 4+ when buy times are redrawn at random (1,000 runs), with the observed count marked. */
export function NullHist({hist, observed, label}: {hist: [number, number][]; observed: number; label: string}) {
  const lo = Math.min(hist[0][0], observed) - 2, hi = Math.max(hist[hist.length - 1][0], observed) + 2;
  const counts = new Map(hist);
  const data = Array.from({length: hi - lo + 1}, (_, i) => ({x: lo + i, n: counts.get(lo + i) ?? 0}));
  return <figure className="flex flex-col gap-1" aria-label={`${label}: random timing gives between ${hist[0][0]} and ${hist[hist.length - 1][0]} high scores; observed ${observed}.`}>
    <div className="h-32">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{top: 4, right: 8, bottom: 0, left: 8}} barCategoryGap={1}>
          <XAxis dataKey="x" type="number" domain={[lo, hi]} stroke="var(--line-row)" tick={{fill: 'var(--text-3)', fontSize: 11}} tickLine={false} tickCount={5}/>
          <YAxis hide/>
          <Bar dataKey="n" fill="var(--chart-ink-2)" isAnimationActive={false}/>
          <ReferenceLine x={observed} stroke="var(--text-1)" strokeWidth={2} label={{value: `Observed ${observed}`, position: observed > (lo + hi) / 2 ? 'insideTopRight' : 'insideTopLeft', fill: 'var(--text-1)', fontSize: 12}}/>
        </BarChart>
      </ResponsiveContainer>
    </div>
    <figcaption className="type-label-sm text-text-2">{label}</figcaption>
  </figure>;
}
