'use client';

import {useMemo, useState} from 'react';
import {CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Scatter, Tooltip, XAxis, YAxis, ZAxis} from 'recharts';
import {ChartFrame} from '@/components/quartz/ui/chart';
import {SegmentedControl, SegmentedControlItem} from '@/components/quartz/ui/segmented-control';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/quartz/ui/table';
import {FLAG_NAMES, usd, utc} from '@/lib/copy';
import type {FlagId, HighBuy, Timeline} from '@/lib/types';

const DAY = 86400;
type Range = 'all' | '72h';

function fmtTick(t: number, span: number) {
  const d = new Date(t * 1000);
  const md = d.toLocaleDateString('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'});
  if (span > 4 * DAY) return md;
  return `${md} ${d.toISOString().slice(11, 16)}`;
}

function BuyTooltip({active, payload}: {active?: boolean; payload?: {payload: HighBuy & {kind?: string}}[]}) {
  const p = payload?.find(x => (x.payload as HighBuy).w)?.payload;
  if (!active || !p) return null;
  const flags = p.flags.split(',') as FlagId[];
  return <div className="flex max-w-(--popover) flex-col gap-1 rounded-soft bg-raised p-3 frame type-body-sm">
    <span className="type-code-sm">{p.w}…</span>
    <span>Score {p.score} of 6, bought {p.side}</span>
    <span className="data">{usd(p.usd)} at YES {p.yes.toFixed(2)}</span>
    <span className="text-text-2">{flags.map(f => `${f} ${FLAG_NAMES[f]}`).join(', ')}</span>
    <span className="text-text-3 data">{utc(p.t)}</span>
    {p.doc && <span className="text-text-2">Named in public reporting</span>}
  </div>;
}

/** Legend glyph: the same round mark the chart draws, always next to its text label. */
function Swatch({kind}: {kind: 'run' | 'model'}) {
  return <svg aria-hidden viewBox="0 0 10 10" className="size-2.5"><circle cx={5} cy={5} r={4} data-kind={kind} className="fill-accent-mark stroke-accent-line"/></svg>;
}

function Dot(props: {cx?: number; cy?: number; size?: number; payload?: HighBuy}) {
  const {cx = 0, cy = 0, size = 40, payload} = props;
  const r = Math.sqrt(size / Math.PI);
  return payload?.doc
    ? <circle cx={cx} cy={cy} r={r} data-kind="model" className="fill-accent-mark stroke-accent-line" strokeWidth={2}/>
    : <circle cx={cx} cy={cy} r={r} data-kind="run" className="fill-accent-mark stroke-accent-line opacity-80" strokeWidth={1}/>;
}

export function PriceTimeline({data, title}: {data: Timeline; title: string}) {
  const [range, setRange] = useState<Range>('all');
  const lo = range === '72h' ? data.t_news - 3 * DAY : data.price[0][0];
  const hi = range === '72h' ? Math.min(data.resolution_epoch, data.t_news + 6 * 3600) : data.resolution_epoch;
  const price = useMemo(() => data.price.filter(([t]) => t >= lo && t <= hi).map(([t, p]) => ({t, p})), [data, lo, hi]);
  const buys = useMemo(() => data.high_buys.filter(b => b.t >= lo && b.t <= hi).map(b => ({...b, p: b.yes})), [data, lo, hi]);
  const docBuys = buys.filter(b => b.doc);
  const otherBuys = buys.filter(b => !b.doc);
  const span = hi - lo;

  const table = <Table aria-label={`High-score buys, ${title}`} size="sm">
    <TableHeader><TableRow>
      <TableHead>Time (UTC)</TableHead><TableHead>Wallet</TableHead><TableHead>Score</TableHead>
      <TableHead className="text-end">USD</TableHead><TableHead>Side</TableHead><TableHead className="text-end">YES price</TableHead>
    </TableRow></TableHeader>
    <TableBody>{buys.map((b, i) => <TableRow key={i}>
      <TableCell className="data">{utc(b.t)}</TableCell><TableCell className="type-code-sm">{b.w}…</TableCell>
      <TableCell className="data">{b.score}</TableCell><TableCell className="text-end data">{usd(b.usd)}</TableCell>
      <TableCell>{b.side}</TableCell><TableCell className="text-end data">{b.yes.toFixed(2)}</TableCell>
    </TableRow>)}</TableBody>
  </Table>;

  return <ChartFrame
    title="Price and high-score buys"
    height={340}
    shape="line"
    table={table}
    actions={<SegmentedControl size="xs" aria-label="Time range" value={range} onValueChange={v => setRange(v as Range)}>
      <SegmentedControlItem value="all">Whole market</SegmentedControlItem>
      <SegmentedControlItem value="72h">Last 72 h</SegmentedControlItem>
    </SegmentedControl>}
    footer={<div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-2 type-label-sm text-text-2">
      <span className="inline-flex items-center gap-1.5"><Swatch kind="run"/>Buy by a wallet scoring 4 or more, sized by USD ({otherBuys.length})</span>
      <span className="inline-flex items-center gap-1.5"><Swatch kind="model"/>Wallet named in public reporting ({docBuys.length})</span>
      <span>Line: YES price of the last fill</span>
    </div>}
  >
    <figure className="size-full" aria-label={`YES price over time with ${buys.length} high-score buys; the first public news is at ${utc(data.t_news)}. Switch to the table view for the values.`}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart accessibilityLayer={false} margin={{top: 16, right: 12, bottom: 0, left: -12}}>
          <CartesianGrid vertical={false} stroke="var(--line-row)"/>
          <XAxis dataKey="t" type="number" domain={[lo, hi]} allowDataOverflow tickFormatter={t => fmtTick(t, span)} tickCount={6}
            stroke="var(--line-row)" tick={{fill: 'var(--text-3)', fontSize: 12}} tickLine={false}/>
          <YAxis dataKey="p" type="number" domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} tickFormatter={v => v.toFixed(2)}
            stroke="var(--line-row)" tick={{fill: 'var(--text-3)', fontSize: 12}} tickLine={false} axisLine={false}/>
          <ZAxis dataKey="usd" type="number" range={[24, 900]} scale="sqrt" domain={[0, 40000]}/>
          <Line data={price} dataKey="p" type="stepAfter" dot={false} isAnimationActive={false} stroke="var(--chart-ink-2)" strokeWidth={1.5} activeDot={false}/>
          <Scatter data={otherBuys} isAnimationActive={false} shape={<Dot/>}/>
          <Scatter data={docBuys} isAnimationActive={false} shape={<Dot/>}/>
          <ReferenceLine x={data.t_news} stroke="var(--text-1)" strokeDasharray="4 3"
            label={{value: 'First news', position: 'insideTopRight', fill: 'var(--text-1)', fontSize: 12}}/>
          <Tooltip content={<BuyTooltip/>} cursor={false} isAnimationActive={false}/>
        </ComposedChart>
      </ResponsiveContainer>
    </figure>
  </ChartFrame>;
}
