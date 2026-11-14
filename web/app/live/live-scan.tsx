'use client';

import {useRef, useState} from 'react';
import {Button} from '@/components/quartz/ui/button';
import {Field, FieldDescription, FieldLabel} from '@/components/quartz/ui/field';
import {Input} from '@/components/quartz/ui/input';
import {Alert, AlertDescription, AlertTitle} from '@/components/quartz/ui/alert';
import {Empty, EmptyDescription, EmptyHeader, EmptyTitle} from '@/components/quartz/ui/empty-state';
import {Skeleton} from '@/components/quartz/ui/skeleton';
import {DataList, DataListItem, DataListLabel, DataListValue} from '@/components/quartz/ui/data-list';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/quartz/ui/table';
import {FlagChips} from '@/components/app/flag-chips';
import {DISCLAIMER, compactUsd, usd, utc} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

type ScanResult = {
  market: {question: string; slug: string; closed: boolean; end_date: string | null; volume: number; event_siblings: number};
  window: {from: number | null; to: number | null; n_fills: number; n_wallets: number; n_buyers: number; n_scored: number};
  wallets: {id: string; score: number; out_of: number; fired: FlagId[]; side: string; F1_days: number; F2_share: number | null; F2_markets: number | null; F3_vwap: number; F4_buy_usd: number; F5_conviction: number; n_fills: number}[];
  scanned_at: number;
  notes: string[];
};
type State = {kind: 'idle'} | {kind: 'loading'; q: string} | {kind: 'error'; message: string; q: string} | {kind: 'done'; data: ScanResult; cached: boolean};

const LIVE_FLAGS: FlagId[] = ['F1', 'F2', 'F3', 'F4', 'F5'];

export function LiveScan() {
  const [q, setQ] = useState('');
  const [state, setState] = useState<State>({kind: 'idle'});
  const [fieldError, setFieldError] = useState('');
  const result = useRef<HTMLHeadingElement>(null);

  async function run(input: string) {
    if (!input.trim()) { setFieldError('Paste a polymarket.com market link or a market slug first.'); return; }
    setFieldError('');
    setState({kind: 'loading', q: input});
    try {
      const r = await fetch(`/api/scan?q=${encodeURIComponent(input)}`);
      const js = await r.json();
      if (!r.ok) throw new Error(js.error ?? `Scan failed (${r.status}).`);
      setState({kind: 'done', data: js, cached: false});
    } catch (e) {
      setState({kind: 'error', message: e instanceof Error ? e.message : 'Scan failed.', q: input});
    }
    requestAnimationFrame(() => result.current?.focus());
  }

  async function cached() {
    setState({kind: 'loading', q: ''});
    try {
      const js = await (await fetch('/data/live_example.json')).json();
      setState({kind: 'done', data: js, cached: true});
    } catch {
      setState({kind: 'error', message: 'The cached example could not be loaded.', q: ''});
    }
    requestAnimationFrame(() => result.current?.focus());
  }

  const loading = state.kind === 'loading';
  return <div className="flex flex-col gap-8">
    <form className="flex flex-col gap-3" onSubmit={e => { e.preventDefault(); run(q); }}>
      <Field className="max-w-2xl">
        <FieldLabel>Polymarket market link or slug</FieldLabel>
        <Input value={q} onChange={e => { setQ(e.target.value); if (fieldError) setFieldError(''); }} placeholder="https://polymarket.com/event/…" autoComplete="off" spellCheck={false}
          aria-invalid={fieldError ? true : undefined} aria-describedby={fieldError ? 'scan-field-error' : undefined}/>
        {fieldError && <p id="scan-field-error" role="alert" className="type-body-sm text-fail-text">{fieldError}</p>}
        <FieldDescription>An event link scans its open market with the most volume.</FieldDescription>
      </Field>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" pending={loading && state.q !== ''} pendingLabel="Scanning">Scan market</Button>
        <Button type="button" variant="secondary" onClick={cached} disabled={loading}>Load cached example</Button>
      </div>
    </form>

    <section aria-labelledby="result-heading" aria-busy={loading || undefined} className="flex flex-col gap-4">
      <h2 id="result-heading" ref={result} tabIndex={-1} data-control className="type-heading">
        {state.kind === 'done' ? state.data.market.question : 'Result'}
      </h2>

      {state.kind === 'idle' && <Empty variant="plain">
        <EmptyHeader>
          <EmptyTitle>No market scanned yet</EmptyTitle>
          <EmptyDescription>Paste a link above, or load the cached example, which works offline. The largest recent buyers are scored on flags F1 to F5.</EmptyDescription>
        </EmptyHeader>
      </Empty>}

      {loading && <div className="flex flex-col gap-2" role="status">
        <span className="sr-only">Fetching trades and wallet profiles from Polymarket</span>
        <p className="type-body text-text-2">Fetching up to 3,000 recent fills and 25 wallet profiles from Polymarket. This takes a few seconds.</p>
        {Array.from({length: 6}, (_, i) => <Skeleton key={i} className="h-(--row) w-full"/>)}
      </div>}

      {state.kind === 'error' && <Alert status="fail">
        <AlertTitle>Scan failed</AlertTitle>
        <AlertDescription className="flex flex-col items-start gap-3">
          <span>{state.message}</span>
          <span className="flex flex-wrap gap-2">
            {state.q && <Button size="sm" variant="secondary" onClick={() => run(state.q)}>Retry scan</Button>}
            <Button size="sm" variant="secondary" onClick={cached}>Load cached example</Button>
          </span>
        </AlertDescription>
      </Alert>}

      {state.kind === 'done' && <Result data={state.data} cached={state.cached}/>}
    </section>
  </div>;
}

function Result({data: d, cached}: {data: ScanResult; cached: boolean}) {
  return <div className="flex flex-col gap-6">
    <DataList size="sm" className="max-w-2xl">
      {cached && <DataListItem><DataListLabel>Source</DataListLabel><DataListValue>Cached example, scanned {utc(d.scanned_at)}</DataListValue></DataListItem>}
      <DataListItem><DataListLabel>Status</DataListLabel><DataListValue>{d.market.closed ? 'Closed' : 'Open'}{d.market.end_date ? `, ends ${d.market.end_date.slice(0, 10)}` : ''}</DataListValue></DataListItem>
      <DataListItem><DataListLabel>Volume</DataListLabel><DataListValue numeric>{compactUsd(d.market.volume)}</DataListValue></DataListItem>
      <DataListItem><DataListLabel>Fills read</DataListLabel><DataListValue numeric>{d.window.n_fills.toLocaleString('en-US')}{d.window.from && d.window.to ? `, ${utc(d.window.from)} to ${utc(d.window.to)}` : ''}</DataListValue></DataListItem>
      <DataListItem><DataListLabel>Buyers in that window</DataListLabel><DataListValue numeric>{d.window.n_buyers}, of which the largest {d.window.n_scored} are scored</DataListValue></DataListItem>
    </DataList>

    {d.wallets.length === 0
      ? <Empty variant="plain"><EmptyHeader><EmptyTitle>No buyers in the recent fills</EmptyTitle><EmptyDescription>This market has no BUY fills in the window read, so there is nothing to score.</EmptyDescription></EmptyHeader></Empty>
      : <Table aria-label="Live scores for the largest recent buyers" size="sm">
        <TableHeader><TableRow>
          <TableHead>Wallet</TableHead><TableHead>Live score</TableHead><TableHead>Flags</TableHead><TableHead>F6: n/a — needs news time</TableHead>
          <TableHead className="text-end">Bought</TableHead><TableHead className="text-end">Avg price</TableHead><TableHead>Side</TableHead>
        </TableRow></TableHeader>
        <TableBody>{d.wallets.map(w => <TableRow key={w.id}>
          <TableCell className="type-code-sm">{w.id}…</TableCell>
          <TableCell className="data">{w.score} / 5</TableCell>
          <TableCell><FlagChips fired={w.fired} of={LIVE_FLAGS}/></TableCell>
          <TableCell className="text-text-3">n/a</TableCell>
          <TableCell className="text-end data">{usd(w.F4_buy_usd)}</TableCell>
          <TableCell className="text-end data">{w.F3_vwap.toFixed(2)}</TableCell>
          <TableCell>{w.side}</TableCell>
        </TableRow>)}</TableBody>
      </Table>}
    <ul className="flex flex-col gap-1 max-w-(--measure)">{d.notes.map(n => <li key={n} className="type-body-sm text-text-2">{n}</li>)}</ul>
    <p className="type-body-sm text-text-2 max-w-(--measure)">The historical screen calls 4 or more of 6 a high score. Without F6, no live threshold has been validated; read a live score as a ranking, not an alert.</p>
    <p className="type-body text-text-1">{DISCLAIMER}</p>
  </div>;
}
