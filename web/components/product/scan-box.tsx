'use client';

import {useState} from 'react';
import {Button} from '@/components/sodium/ui/button';
import {Input} from '@/components/sodium/ui/input';
import {Alert, AlertTitle} from '@/components/sodium/ui/alert';
import {Skeleton} from '@/components/sodium/ui/skeleton';
import {WalletRows, overLine, type LiveWallet} from './wallet-rows';
import {clean, utc} from '@/lib/copy';

type Result = {market: {question: string; yes_price?: number | null}; window: {n_fills: number; n_scored: number}; wallets: LiveWallet[]; scanned_at: number};
type State = {kind: 'idle'} | {kind: 'loading'} | {kind: 'error'; message: string} | {kind: 'done'; data: Result; cached: boolean};

export function ScanBox() {
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

  return <div className="flex flex-col gap-6">
    <form className="flex flex-col gap-3 sm:flex-row sm:items-start" onSubmit={e => { e.preventDefault(); scan(); }}>
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <label htmlFor="market" className="sr-only">Polymarket market link or slug</label>
        <Input id="market" size="lg" value={q} onChange={e => { setQ(e.target.value); setErr(''); }} placeholder="Paste a Polymarket market link" autoComplete="off" spellCheck={false}
          aria-invalid={err ? true : undefined} aria-describedby={err ? 'market-error' : undefined}/>
        {err && <p id="market-error" role="alert" className="type-product text-fail-text">{err}</p>}
      </div>
      <Button type="submit" size="lg" variant="secondary" pending={st.kind === 'loading'}>Scan market</Button>
      <Button type="button" size="lg" variant="ghost" onClick={() => load('/data/live_example.json', true)} disabled={st.kind === 'loading'}>Load cached example</Button>
    </form>
    <div aria-live="polite" aria-busy={st.kind === 'loading' || undefined} className="flex flex-col gap-4">
      {st.kind === 'loading' && <><p className="type-product text-text-2">Reading recent trades from Polymarket.</p>{[0, 1, 2].map(i => <Skeleton key={i} className="h-12 w-full"/>)}</>}
      {st.kind === 'error' && <Alert status="fail"><AlertTitle>{st.message}</AlertTitle></Alert>}
      {st.kind === 'done' && <>
        <p className="type-product text-text-1">{clean(st.data.market.question)}</p>
        <p className="type-product text-text-3">{st.cached ? `Saved scan from ${utc(st.data.scanned_at).slice(0, 10)}. ` : ''}The {st.data.window.n_scored} largest recent buyers, scored out of 5. Showing 3 or more, $2,500 or more.</p>
        <WalletRows wallets={st.data.wallets.filter(overLine)}/>
      </>}
    </div>
  </div>;
}
