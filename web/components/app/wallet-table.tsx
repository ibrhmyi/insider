'use client';

import {useMemo, useState} from 'react';
import {useRouter} from 'next/navigation';
import {DataTable, type ColumnDef} from '@/components/quartz/ui/table';
import {FilterBar, FilterBarClear, FilterBarCount, FilterBarSearch, FilterToggle} from '@/components/quartz/ui/filter-bar';
import {FlagChips, DocBadge} from './flag-chips';
import {FLAGS, FLAG_NAMES, usd} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

export type TableRow = {
  id: string; rank: number; score: number; flags: FlagId[]; usd: number; avg: number; hours: number; side: string;
  won: boolean; dormant: boolean | null;
  doc?: {handle: string | null; confidence: 'charged' | 'alleged'; publisher: string; source: string};
};

const DEFAULT: FlagId[] = ['F4'];

export function WalletTable({rows, market, marketName}: {rows: TableRow[]; market: string; marketName: string}) {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [need, setNeed] = useState<FlagId[]>(DEFAULT);
  const [docOnly, setDocOnly] = useState(false);
  const [highOnly, setHighOnly] = useState(false);

  const shown = useMemo(() => {
    const q = search.trim().toLowerCase();
    return rows.filter(r =>
      need.every(f => r.flags.includes(f)) && (!docOnly || r.doc) && (!highOnly || r.score >= 4) &&
      (!q || r.id.includes(q) || (r.doc?.handle ?? '').toLowerCase().includes(q)));
  }, [rows, need, docOnly, highOnly, search]);

  const columns = useMemo<ColumnDef<TableRow>[]>(() => [
    {accessorKey: 'rank', header: 'Rank', size: 64, meta: {numeric: true}, cell: ({getValue}) => <span className="data">{getValue<number>()}</span>},
    {
      id: 'wallet', accessorFn: r => r.id, header: 'Wallet', size: 240, enableSorting: false,
      cell: ({row: {original: r}}) => <span className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
        <span className="type-code-sm">{r.id}…</span>
        {r.doc && <>
          {r.doc.handle && <span className="type-label-sm text-text-2">{r.doc.handle}</span>}
          <DocBadge confidence={r.doc.confidence}/>
          <a href={r.doc.source} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()}
            className="type-label-sm text-text-2 underline underline-offset-4 hover:text-text-1 focus-visible:focus-ring rounded-inner">{r.doc.confidence === 'charged' ? 'CFTC complaint' : `${r.doc.publisher.split(' ')[0]} report`}</a>
        </>}
      </span>,
    },
    {accessorKey: 'score', header: 'Score', size: 72, meta: {numeric: true}, sortDescFirst: true, cell: ({getValue}) => <span className="data">{getValue<number>()} / 6</span>},
    {id: 'flags', accessorFn: r => r.flags.length, header: 'Flags', size: 196, enableSorting: false, cell: ({row}) => <FlagChips fired={row.original.flags}/>},
    {accessorKey: 'usd', header: 'Bought pre-news', size: 132, meta: {numeric: true}, sortDescFirst: true, cell: ({getValue}) => <span className="data">{usd(getValue<number>())}</span>},
    {accessorKey: 'avg', header: 'Avg price', size: 92, meta: {numeric: true, hideBelow: 760}, cell: ({getValue}) => <span className="data">{getValue<number>().toFixed(2)}</span>},
    {accessorKey: 'hours', header: 'Hours to news', size: 116, meta: {numeric: true, hideBelow: 880, label: 'Hours from median buy to news'}, cell: ({getValue}) => <span className="data">{getValue<number>().toFixed(1)}</span>},
    {accessorKey: 'side', header: 'Side', size: 64, meta: {hideBelow: 1180}},
    {id: 'won', accessorFn: r => (r.won ? 1 : 0), header: 'Won (post-hoc)', size: 128, meta: {hideBelow: 1320, label: 'Won, post-hoc, not in score'}, cell: ({row}) => <span className="text-text-2">{row.original.won ? 'Yes' : 'No'}</span>},
    {id: 'dormant', accessorFn: r => (r.dormant === null ? -1 : r.dormant ? 1 : 0), header: 'Dormant 30 d (post-hoc)', size: 180, meta: {hideBelow: 1500, label: 'Dormant 30 days, post-hoc, not in score'}, cell: ({row}) => <span className="text-text-2">{row.original.dormant === null ? 'Unknown' : row.original.dormant ? 'Yes' : 'No'}</span>},
  ], []);

  const toggle = (f: FlagId, on: boolean) => setNeed(n => on ? [...n, f] : n.filter(x => x !== f));
  const changed = search || docOnly || highOnly || need.join() !== DEFAULT.join();

  return <div className="flex flex-col gap-3">
    <FilterBar aria-label="Filter wallets">
      <FilterBarSearch value={search} onValueChange={setSearch} placeholder="Prefix or handle" aria-label="Search wallets by address prefix or reported handle"/>
      {FLAGS.map(f => <FilterToggle key={f} size="sm" pressed={need.includes(f)} onPressedChange={on => toggle(f, on)} aria-label={`Only wallets with ${f} ${FLAG_NAMES[f]}`}>{f} {FLAG_NAMES[f]}</FilterToggle>)}
      <FilterToggle size="sm" pressed={highOnly} onPressedChange={setHighOnly}>Score 4 or more</FilterToggle>
      <FilterToggle size="sm" pressed={docOnly} onPressedChange={setDocOnly}>Named in reporting</FilterToggle>
      {changed && <FilterBarClear onClick={() => { setSearch(''); setNeed(DEFAULT); setDocOnly(false); setHighOnly(false); }}>Reset filters</FilterBarClear>}
      <FilterBarCount shown={shown.length} total={rows.length} noun="wallets"/>
    </FilterBar>
    <DataTable<TableRow>
      aria-label={`Wallets that bought before the news, ${marketName}`}
      columns={columns}
      data={shown}
      getRowId={r => r.id}
      defaultSorting={[{id: 'rank', desc: false}]}
      enableRowSelection={false}
      enableColumnResizing={false}
      maxHeight={560}
      size="sm"
      empty="No wallet matches these filters. Turn off a flag filter to see more."
      onRowClick={r => { if (r.score >= 4) router.push(`/markets/${market}/wallet/${r.id}`); }}
      rowIndicator={r => r.score >= 4 ? <span className="sr-only">Opens the alert</span> : null}
    />
    <p className="type-body-sm text-text-2">Rows scoring 4 or more open their alert card (click, or Enter on a focused row). Won and dormant are measured after the news and never enter the score.</p>
  </div>;
}
