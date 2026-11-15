'use client';

import {useState} from 'react';
import {SegmentedControl, SegmentedControlItem} from '@/components/quartz/ui/segmented-control';
import {DataTable, type ColumnDef} from '@/components/quartz/ui/table';
import {Badge} from '@/components/quartz/ui/badge';
import {CopyButton} from '@/components/quartz/ui/copy-button';
import {PriceTimeline, type Range} from './price-timeline';
import {DocBadge, FlagChips} from './flag-chips';
import {DISCLAIMER, FLAG_NAMES, hours, usd, utc} from '@/lib/copy';
import type {FlagId, MarketId, Timeline} from '@/lib/types';

export type XWallet = {
  id: string; addr: string | null; rank: number; score: number; flags: FlagId[]; usd: number; avg: number; hours: number; firstHigh: number | null;
  f1: number; f2share: number | null; f2markets: number | null; f5: number; side: string; won: boolean; dormant: boolean | null;
  doc?: {handle: string | null; confidence: 'charged' | 'alleged'; publisher: string; source: string; claim: string};
};
export type XMarket = {id: MarketId; short: string; question: string; t_news: number; n_wallets: number; n_high: number; timeline: Timeline; wallets: XWallet[]};

/** Value and threshold, side by side, for each frozen flag. */
function flagRows(w: XWallet): {f: FlagId; value: string; rule: string}[] {
  return [
    {f: 'F1', value: `${w.f1.toFixed(1)} days old`, rule: '7 days or less'},
    {f: 'F2', value: w.f2share !== null ? `${Math.round(w.f2share * 100)}% of its volume, ${w.f2markets ?? '?'} markets ever` : `${w.f2markets ?? '?'} markets ever`, rule: '80% or more, or 2 markets'},
    {f: 'F3', value: `${Math.round(w.avg * 100)}¢ average`, rule: '35¢ or less'},
    {f: 'F4', value: usd(w.usd), rule: '$2,500 or more'},
    {f: 'F5', value: `${Math.round(w.f5 * 100)}% one way`, rule: '80% or more'},
    {f: 'F6', value: `${hours(w.hours)} before news`, rule: '72 h or less'},
  ];
}

function WalletPanel({w, m}: {w: XWallet; m: XMarket}) {
  const fired = new Set(w.flags);
  return <section aria-labelledby="wallet-title" className="flex min-w-0 flex-col gap-4 rounded-frame bg-well p-4">
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <h3 id="wallet-title" className="type-heading-sm font-mono">{w.id}…</h3>
        {w.doc && <DocBadge confidence={w.doc.confidence}/>}
        {w.doc?.handle && <span className="type-label text-text-2">{w.doc.handle}</span>}
      </div>
      <p className="type-body text-text-2">
        Rank {w.rank} of {m.n_wallets.toLocaleString('en-US')}. Bought {usd(w.usd)} of {w.side}{w.firstHigh !== null ? `; flagged ${hours(w.firstHigh)} before the news` : ''}.
      </p>
    </div>
    <ol className="flex flex-col" aria-label={`${w.score} of 6 flags fired`}>
      {flagRows(w).map(({f, value, rule}) => <li key={f} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 border-t border-line-row py-2 first:border-t-0">
        <span className="flex min-w-0 flex-col">
          <span className="type-label">{FLAG_NAMES[f]}</span>
          <span className="type-body-sm text-text-2 data">{value} <span className="text-text-3">(rule: {rule})</span></span>
        </span>
        {fired.has(f) ? <Badge variant="outline">{f} fired</Badge> : <span className="type-label-sm text-text-3">{f} no</span>}
      </li>)}
    </ol>
    {w.doc && <p className="type-body-sm"><a href={w.doc.source} target="_blank" rel="noreferrer" className="underline underline-offset-4">{w.doc.confidence === 'charged' ? 'CFTC complaint' : w.doc.publisher.split(' (')[0].split(' via ')[0]}</a>: {w.doc.claim}</p>}
    {w.addr && <p className="flex min-w-0 items-center gap-1 type-code-sm text-text-2"><span className="break-all">{w.addr}</span><CopyButton value={w.addr} label="Copy address" size="icon-xs"/></p>}
    <p className="type-body-sm text-text-2">After resolution, not in the score: {w.won ? 'its side won' : 'its side lost'}{w.dormant === null ? '' : w.dormant ? ', then it went quiet for 30 days' : ', and it kept trading'}.</p>
    <p className="type-body-sm">{DISCLAIMER}</p>
  </section>;
}

export function Explorer({markets}: {markets: XMarket[]}) {
  const [mid, setMid] = useState<MarketId>(markets[0].id);
  const m = markets.find(x => x.id === mid)!;
  const [sel, setSel] = useState<Record<string, string>>(() => Object.fromEntries(markets.map(x => [x.id, x.wallets[0]?.id])));
  const [range, setRange] = useState<Range>('72h');
  const w = m.wallets.find(x => x.id === sel[mid]) ?? m.wallets[0];
  const pick = (id: string) => { if (m.wallets.some(x => x.id === id)) setSel(s => ({...s, [mid]: id})); };

  const columns: ColumnDef<XWallet>[] = [
    {accessorKey: 'rank', header: 'Rank', size: 64, meta: {numeric: true}, cell: ({getValue}) => <span className="data">{getValue<number>()}</span>},
    {id: 'wallet', accessorFn: r => r.id, header: 'Wallet', size: 170, enableSorting: false, cell: ({row: {original: r}}) => <span className="flex items-center gap-2"><span className="type-code-sm">{r.id}…</span>{r.doc && <DocBadge confidence={r.doc.confidence}/>}</span>},
    {id: 'flags', accessorFn: r => r.score, header: 'Flags', size: 200, cell: ({row}) => <FlagChips fired={row.original.flags}/>},
    {accessorKey: 'usd', header: 'Bought', size: 110, meta: {numeric: true, hideBelow: 520}, cell: ({getValue}) => <span className="data">{usd(getValue<number>())}</span>},
  ];

  return <div className="flex flex-col gap-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <SegmentedControl aria-label="Market" value={mid} onValueChange={v => setMid(v as MarketId)}>
        {markets.map(x => <SegmentedControlItem key={x.id} value={x.id}>{x.short}</SegmentedControlItem>)}
      </SegmentedControl>
      <p className="type-body-sm text-text-2"><span className="text-text-1">{m.question}</span> First news {utc(m.t_news)}.</p>
    </div>
    <PriceTimeline key={mid} data={m.timeline} range={range} onRange={setRange} selected={w?.id} onSelect={pick}/>
    <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <DataTable<XWallet>
        aria-label={`Flagged wallets, ${m.short}`}
        title={`${m.n_high} of ${m.n_wallets.toLocaleString('en-US')} pre-news buyers flagged`}
        columns={columns} data={m.wallets} getRowId={r => r.id}
        defaultSorting={[{id: 'rank', desc: false}]} enableRowSelection={false} enableColumnResizing={false}
        size="sm" maxHeight={460} count={false} activeRowId={w?.id} onRowClick={r => pick(r.id)}
      />
      {w && <WalletPanel w={w} m={m}/>}
    </div>
  </div>;
}

