'use client';

import {useEffect, useState} from 'react';
import {Button} from '@/components/sodium/ui/button';
import {WalletRows, overLine, type LiveWallet} from './wallet-rows';
import {WATCHLIST} from '@/lib/watchlist';
import {DISCLAIMER, clean, utc} from '@/lib/copy';

type Card = {slug: string; who: string; error?: string; market?: {question: string; yes_price?: number | null; closed: boolean}; wallets?: LiveWallet[]; scanned_at?: number};

/** Open markets decided by small groups. Loads the cached watchlist (refreshed every 6 h), falls back to the saved snapshot. */
export function Watchlist() {
  const [cards, setCards] = useState<Card[] | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    const take = (d: {scanned_at: number; markets: Card[]}) => setCards(d.markets.map(m => ({...m, scanned_at: m.scanned_at ?? d.scanned_at})));
    fetch('/api/watchlist').then(r => (r.ok ? r.json() : Promise.reject())).then(take)
      .catch(() => fetch('/data/watchlist.json').then(r => r.json()).then(take).catch(() => setCards([])));
  }, []);

  async function refresh() {
    for (const w of WATCHLIST) {
      setBusy(w.slug);
      try {
        const r = await fetch(`/api/scan?q=${encodeURIComponent(w.slug)}`);
        const js = await r.json();
        if (r.ok) setCards(cs => (cs ?? []).map(c => (c.slug === w.slug ? {...c, ...js, error: undefined} : c)));
      } catch { /* keep the previous scan for this card */ }
    }
    setBusy(null);
  }

  const sel = cards?.find(c => c.slug === open);
  return <div className="flex flex-col gap-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="type-product text-text-2">Six open markets whose answer a small group decides. Each is scanned on its largest recent buyers.</p>
      <Button variant="secondary" onClick={refresh} pending={busy !== null} disabled={!cards}>Refresh scans</Button>
    </div>
    {!cards ? <p className="type-product text-text-3">Loading the latest scans.</p> : <ul className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {cards.map(c => {
        const over = (c.wallets ?? []).filter(overLine);
        const on = open === c.slug;
        return <li key={c.slug}>
          {/* Native button (Sodium lint exception in sodium.eslint.config.mjs): a multi-line card, focus ring and aria-expanded kept. */}
          <button type="button" onClick={() => setOpen(on ? null : c.slug)} aria-expanded={on} aria-controls="watch-detail"
            className={`flex h-full w-full flex-col gap-3 border p-5 text-start transition-colors duration-(--dur-state) hover:bg-hover focus-visible:focus-ring ${on ? 'border-text-2 bg-panel' : 'border-line'}`}>
            <span className="type-product text-text-1">{c.market ? clean(c.market.question) : c.slug}</span>
            <span className="type-product text-text-3">{c.who}</span>
            <span className="mt-auto flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <span className="type-product text-text-2">{c.market?.yes_price != null ? `Yes ${Math.round(c.market.yes_price * 100)}¢` : ''}</span>
              <span className="type-code text-text-3">{busy === c.slug ? 'Scanning' : c.scanned_at ? `Scanned ${utc(c.scanned_at)}` : ''}</span>
            </span>
            <span className={`type-product ${c.error ? 'text-fail-text' : over.length ? 'text-accent-text' : 'text-text-1'}`}>
              {c.error ? 'Scan failed' : over.length ? `${over.length} ${over.length === 1 ? 'wallet' : 'wallets'} worth a look` : 'Nothing unusual'}
            </span>
          </button>
        </li>;
      })}
    </ul>}
    {sel && <div id="watch-detail" className="flex flex-col gap-3 border-t border-line pt-6">
      <h3 className="type-product text-text-1">{sel.market ? clean(sel.market.question) : sel.slug}</h3>
      {sel.error ? <p className="type-product text-fail-text">{sel.error}</p> : <WalletRows wallets={(sel.wallets ?? []).filter(overLine)}/>}
      <p className="type-product text-text-3">{DISCLAIMER}</p>
    </div>}
  </div>;
}
