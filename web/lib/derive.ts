import 'server-only';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {MARKET_IDS, getBuys, getMarkets, getTimeline, getValidation, getWallets} from './data';
import type {ChartBuy} from '@/components/inv/chart';
import type {FlagId, MarketId} from './types';

/** Flagged activity = the frozen high score (>= 4) AND at least the frozen size threshold ($2,500) bought before the news. */
export function isFlagged(score: number, usd: number) {
  const f = getMarkets().flags;
  return score >= f.HIGH && usd >= f.F4_usd;
}

export function chartBuys(id: MarketId, focusId?: string): ChartBuy[] {
  const b = getBuys(id);
  return b.buys.map(([t, y, usd, i]) => ({t, y, usd, flagged: isFlagged(b.wallets[i].score, b.wallets[i].usd), focus: !!focusId && b.wallets[i].id === focusId}));
}

export function chartBase(id: MarketId) {
  const tl = getTimeline(id);
  return {price: tl.price, tNews: tl.t_news, x0: tl.t_news - 48 * 3600, x1: tl.resolution_epoch};
}

/** Wallet-markets by score across the three markets, with publicly named wallets counted once. */
export function scoreDist() {
  const val = getValidation();
  const named = [...new Map(val.map(v => [`${v.market}:${v.wallet_id}`, v.score])).values()];
  const all = MARKET_IDS.flatMap(id => getWallets(id));
  return {
    total: all.length,
    namedTotal: named.length,
    dist: Array.from({length: 7}, (_, s) => ({
      score: s,
      wallets: all.filter(w => w.score === s).length,
      documented: named.filter(x => x === s).length,
      under1k: all.filter(w => w.score === s && w.usd < 1000).length,
      under2500: all.filter(w => w.score === s && w.usd < 2500).length,
    })),
  };
}

export type LiveExample = {
  market: {question: string; slug: string; closed: boolean; end_date: string | null; volume: number};
  window: {from: number | null; to: number | null; n_fills: number; n_wallets: number; n_buyers: number; n_scored: number};
  wallets: {id: string; score: number; out_of: number; fired: FlagId[]; side: string; F1_days: number; F2_share: number | null; F2_markets: number | null; F3_vwap: number; F4_buy_usd: number; F5_conviction: number}[];
  scanned_at: number;
  choice?: string;
};

export function liveExample(): LiveExample {
  return JSON.parse(readFileSync(join(process.cwd(), 'public', 'data', 'live_example.json'), 'utf8'));
}
