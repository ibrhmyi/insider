'use client';

import {useEffect, useState} from 'react';
import {Button} from '@/components/sodium/ui/button';
import {Field, FieldDescription, FieldLabel} from '@/components/sodium/ui/field';
import {Input} from '@/components/sodium/ui/input';
import {Alert, AlertDescription, AlertTitle} from '@/components/sodium/ui/alert';
import {Empty, EmptyDescription, EmptyHeader, EmptyTitle} from '@/components/sodium/ui/empty-state';
import {Skeleton} from '@/components/sodium/ui/skeleton';
import {Switch} from '@/components/sodium/ui/switch';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/sodium/ui/table';
import {FlagMark} from './flag-marks';
import {DISCLAIMER, usd, utc} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

type Result = {
  market: {question: string; slug: string; closed: boolean; end_date: string | null; volume: number};
  window: {from: number | null; to: number | null; n_fills: number; n_buyers: number; n_scored: number};
  wallets: {id: string; score: number; fired: FlagId[]; side: string; F3_vwap: number; F4_buy_usd: number}[];
  scanned_at: number;
  choice?: string;
};
type State = {kind: 'loading'; q: string} | {kind: 'error'; message: string; q: string} | {kind: 'done'; data: Result; cached: boolean};

const LIVE: FlagId[] = ['F1', 'F2', 'F3', 'F4', 'F5'];
const MIN_SCORE = 3, MIN_USD = 2500;

export function LiveScan() {
  const [q, setQ] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [state, setState] = useState<State>({kind: 'loading', q: ''});
  const [all, setAll] = useState(false);

  async function cached() {
    setState({kind: 'loading', q: ''});
    try { setState({kind: 'done', data: await (await fetch('/data/live_example.json')).json(), cached: true}); }
    catch { setState({kind: 'error', message: 'The cached example could not be loaded.', q: ''}); }
  }
  async function run() {
    if (!q.trim()) { setFieldError('Paste a polymarket.com link or a market slug first.'); return; }
    setFieldError('');
    setState({kind: 'loading', q});
    try {
      const r = await fetch(`/api/scan?q=${encodeURIComponent(q)}`);
      const js = await r.json();
      if (!r.ok) throw new Error(js.error ?? `Scan failed (${r.status}).`);
      setState({kind: 'done', data: js, cached: false});
    } catch (e) {
      setState({kind: 'error', message: e instanceof Error ? e.message : 'Scan failed.', q});
    }
  }
  useEffect(() => { cached(); }, []);

  return <div className="flex flex-col gap-8">
    <form className="flex flex-col gap-3" onSubmit={e => { e.preventDefault(); run(); }}>
      <Field className="max-w-2xl">
        <FieldLabel>Polymarket link or market slug</FieldLabel>
        <Input value={q} onChange={e => { setQ(e.target.value); setFieldError(''); }} placeholder="https://polymarket.com/event/..." autoComplete="off" spellCheck={false}
          aria-invalid={fieldError ? true : undefined} aria-describedby={fieldError ? 'scan-error' : undefined}/>
        {fieldError ? <p id="scan-error" role="alert" className="type-body-sm text-fail-text">{fieldError}</p>
          : <FieldDescription>An event link scans its open market with the most volume.</FieldDescription>}
      </Field>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" pending={state.kind === 'loading' && state.q !== ''}>Scan market</Button>
        <Button type="button" variant="secondary" onClick={cached} disabled={state.kind === 'loading'}>Load cached example</Button>
      </div>
    </form>

    <section aria-labelledby="live-result" aria-busy={state.kind === 'loading' || undefined} className="flex flex-col gap-4">
      {state.kind === 'loading' && <div role="status" className="flex flex-col gap-2">
        <h2 id="live-result" className="type-heading-sm">Scanning</h2>
        <p className="type-body-sm text-text-2">Reading up to 3,000 recent fills and 25 wallet profiles from Polymarket.</p>
        {Array.from({length: 4}, (_, i) => <Skeleton key={i} className="h-(--row) w-full"/>)}
      </div>}

      {state.kind === 'error' && <>
        <h2 id="live-result" className="type-heading-sm">Scan failed</h2>
        <Alert status="fail"><AlertTitle>{state.message}</AlertTitle>
          <AlertDescription><span className="flex flex-wrap gap-2 pt-2">
            {state.q && <Button size="sm" variant="secondary" onClick={run}>Retry scan</Button>}
            <Button size="sm" variant="secondary" onClick={cached}>Load cached example</Button>
          </span></AlertDescription>
        </Alert>
      </>}

      {state.kind === 'done' && (() => {
        const d = state.data;
        const over = d.wallets.filter(w => w.score >= MIN_SCORE && w.F4_buy_usd >= MIN_USD);
        const rows = all ? d.wallets : over;
        return <>
          <div className="flex flex-col gap-1">
            <h2 id="live-result" className="type-heading">{d.market.question}</h2>
            <p className="type-body-sm text-text-2">{state.cached ? `Cached example, scanned ${utc(d.scanned_at)}. ` : ''}{d.window.n_fills.toLocaleString('en-US')} most recent fills, {d.window.n_buyers} buyers; the {d.window.n_scored} largest are scored on 5 signs. Near news is not scored: the news time is unknown while a market is open.</p>
            {state.cached && d.choice && <p className="type-body-sm text-text-3">{d.choice}</p>}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="type-body"><span className="text-accent-text">{over.length}</span> {over.length === 1 ? 'wallet crosses' : 'wallets cross'} the line: 3 or more of 5 signs and {usd(MIN_USD)} or more.</p>
            <label className="flex items-center gap-2 type-label-sm text-text-2"><Switch checked={all} onCheckedChange={setAll}/>Show all {d.wallets.length} scored</label>
          </div>
          {rows.length === 0
            ? <Empty><EmptyHeader><EmptyTitle>No wallet crosses the line in this market right now.</EmptyTitle>
                <EmptyDescription>None of the {d.window.n_scored} largest recent buyers shows 3 or more signs with {usd(MIN_USD)} or more. Show all scored to see them.</EmptyDescription></EmptyHeader></Empty>
            : <Table aria-label="Live scores for the largest recent buyers" size="sm">
              <TableHeader><TableRow><TableHead>Wallet</TableHead><TableHead numeric>Live score</TableHead><TableHead>Signs</TableHead><TableHead numeric>Bought</TableHead><TableHead numeric>Avg price</TableHead><TableHead>Side</TableHead></TableRow></TableHeader>
              <TableBody>{rows.map(w => <TableRow key={w.id}>
                <TableCell mono>{w.id}…</TableCell>
                <TableCell numeric className={w.score >= MIN_SCORE && w.F4_buy_usd >= MIN_USD ? 'text-accent-text' : ''}>{w.score}/5</TableCell>
                <TableCell><span role="img" aria-label={`Signs: ${w.fired.join(', ') || 'none'}; near news not scored`} className="inline-flex flex-nowrap gap-x-2.5 whitespace-nowrap">
                  {LIVE.map(f => <span key={f} aria-hidden><FlagMark f={f} fired={w.fired.includes(f)}/></span>)}
                  <span aria-hidden className="type-micro text-text-3">Near news n/a</span></span></TableCell>
                <TableCell numeric>{usd(w.F4_buy_usd)}</TableCell>
                <TableCell numeric>{Math.round(w.F3_vwap * 100)}¢</TableCell>
                <TableCell>{w.side}</TableCell>
              </TableRow>)}</TableBody>
            </Table>}
          <p className="type-body-sm text-text-2">No live cut-off has been validated, so read a live score as a ranking for review, not an alert. {DISCLAIMER}</p>
        </>;
      })()}
    </section>
  </div>;
}
