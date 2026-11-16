import {FLAG_SHORT, usd} from '@/lib/copy';
import {LIVE_MIN_SCORE, LIVE_MIN_USD} from '@/lib/watchlist';
import type {FlagId} from '@/lib/types';

export type LiveWallet = {id: string; score: number; fired: FlagId[]; F1_days: number | null; F2_markets: number | null; F3_vwap: number; F4_buy_usd: number; side: string};

const LIVE: FlagId[] = ['F1', 'F2', 'F3', 'F4', 'F5'];
export const overLine = (w: LiveWallet) => w.score >= LIVE_MIN_SCORE && w.F4_buy_usd >= LIVE_MIN_USD;

/** Live results: score out of 5 (timing is unknown until news), what it bought, which signs, and context. */
export function WalletRows({wallets}: {wallets: LiveWallet[]}) {
  if (!wallets.length) return <p className="type-product text-text-1">No wallet crosses the line in this market right now.</p>;
  return <ul className="flex flex-col">
    {wallets.map(w => <li key={w.id} className="grid gap-x-8 gap-y-1 border-t border-line py-4 sm:grid-cols-[auto_minmax(0,1fr)]">
      <span className="type-product text-accent-text">{w.score} of 5</span>
      <span className="flex flex-col gap-1">
        <span className="type-product text-text-1">{usd(w.F4_buy_usd)} on {w.side} at {Math.round(w.F3_vwap * 100)}¢ <span className="type-code text-text-3">{w.id}…</span></span>
        <span className="type-product text-text-2">{LIVE.filter(f => w.fired.includes(f)).map(f => FLAG_SHORT[f]).join(', ')}</span>
        <span className="type-product text-text-3">Markets traded: {w.F2_markets === null ? 'unknown' : w.F2_markets.toLocaleString('en-US')}. {w.F1_days === null ? 'Account age unknown.' : `Account age: ${w.F1_days.toFixed(1)} days at its earliest trade in this scan.`}</span>
      </span>
    </li>)}
  </ul>;
}
