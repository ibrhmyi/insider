'use client';

import {useState} from 'react';
import {Button} from '@/components/sodium/ui/button';
import {Input} from '@/components/sodium/ui/input';
import {Alert, AlertTitle} from '@/components/sodium/ui/alert';
import {Skeleton} from '@/components/sodium/ui/skeleton';
import {FLAG_SHORT, usd, utc} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

type Result = {
  market: {question: string};
  window: {n_fills: number; n_scored: number};
  wallets: {id: string; score: number; fired: FlagId[]; F1_days: number | null; F2_markets: number | null; F3_vwap: number; F4_buy_usd: number; side: string}[];
  scanned_at: number;
};
type State = {kind: 'idle'} | {kind: 'loading'} | {kind: 'error'; message: string} | {kind: 'done'; data: Result; cached: boolean};

/** Live score: five signs (timing is left out, nobody knows when news will break); only buyers of $2,500 or more. */
const LIVE: FlagId[] = ['F1', 'F2', 'F3', 'F4', 'F5'];
const MIN_SCORE = 3, MIN_USD = 2500;

export function TryIt() {
  const [q, setQ] = useState('');
  const [err, setErr] = useState('');
  const [st, setSt] = useState<State>({kind: 'idle'});

  async function load(url: string, cached: boolean) {
    setSt({kind: 'loading'});
    try {
      const r = await fetch(url);
      const js = await r.json();
      if (!r.ok) throw new Error(js.error ?? 'The scan failed.');
      setSt({kind: 'done', data: js, cached});
    } catch (e) { setSt({kind: 'error', message: e instanceof Error ? e.message : 'The scan failed.'}); }
  }
  const scan = () => { if (!q.trim()) { setErr('Paste a market link first.'); return; } setErr(''); load(`/api/scan?q=${encodeURIComponent(q)}`, false); };

  return <div className="flex max-w-3xl flex-col gap-8">
    <form className="flex flex-col gap-4" onSubmit={e => { e.preventDefault(); scan(); }}>
      <label htmlFor="market" className="type-story text-text-2">Paste an open Polymarket market</label>
      <Input id="market" size="lg" value={q} onChange={e => { setQ(e.target.value); setErr(''); }} placeholder="polymarket.com/event/..." autoComplete="off" spellCheck={false}
        aria-invalid={err ? true : undefined} aria-describedby={err ? 'market-error' : undefined}/>
      {err && <p id="market-error" role="alert" className="type-story text-fail-text">{err}</p>}
      <div className="flex flex-wrap gap-3">
        <Button type="submit" size="lg" variant="secondary" pending={st.kind === 'loading'}>Scan market</Button>
        <Button type="button" size="lg" variant="secondary" onClick={() => load('/data/live_example.json', true)} disabled={st.kind === 'loading'}>Load cached example</Button>
      </div>
    </form>

    <div aria-live="polite" aria-busy={st.kind === 'loading' || undefined} className="flex flex-col gap-5">
      {st.kind === 'loading' && <><p className="type-story text-text-2">Reading recent trades from Polymarket.</p>{[0, 1, 2].map(i => <Skeleton key={i} className="h-12 w-full"/>)}</>}
      {st.kind === 'error' && <Alert status="fail"><AlertTitle>{st.message}</AlertTitle></Alert>}
      {st.kind === 'done' && (() => {
        const over = st.data.wallets.filter(w => w.score >= MIN_SCORE && w.F4_buy_usd >= MIN_USD);
        return <>
          <p className="type-story text-text-1">{st.data.market.question}</p>
          <p className="type-story text-text-2">{st.cached ? `Saved scan from ${utc(st.data.scanned_at).slice(0, 10)}. ` : ''}Score out of 5, buyers of {usd(MIN_USD)} or more only.</p>
          {over.length === 0
            ? <p className="type-story-sign">No wallet crosses the line in this market right now.</p>
            : <ul className="flex flex-col">{over.map(w => <li key={w.id} className="flex flex-wrap items-baseline gap-x-8 gap-y-2 border-t border-line py-5">
              <span className="type-story-sign">{w.score} of 5</span>
              <span className="type-story text-text-2">{usd(w.F4_buy_usd)} on {w.side} at {Math.round(w.F3_vwap * 100)}¢</span>
              <span className="type-story text-text-3">{LIVE.filter(f => w.fired.includes(f)).map(f => FLAG_SHORT[f]).join(', ')}</span>
              <span className="type-code text-text-3">{w.id}…</span>
              <span className="basis-full type-story text-text-3">
                Markets traded: {w.F2_markets === null ? 'unknown' : w.F2_markets.toLocaleString('en-US')}.
                {' '}{w.F1_days === null ? 'Account age unknown' : `Account age: ${w.F1_days.toFixed(1)} days at its earliest trade in this scan`}.
              </span>
            </li>)}</ul>}
        </>;
      })()}
    </div>
  </div>;
}
