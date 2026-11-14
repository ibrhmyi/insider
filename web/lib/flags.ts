/**
 * TypeScript port of the frozen v1 Layer 1 features (rules/frozen_v1.md, src/v1_03_layer1.py `features`).
 * Thresholds are the frozen ones; do not change them here. tests/flags.test.ts checks this file against the
 * Python results for 20 wallets (tests/fixtures/flags_20.json, written by src/export_web.py).
 */
import type {FlagId} from './types';

export const FROZEN = {F1_days: 7, F2_share: 0.8, F2_markets: 2, F3_price: 0.35, F4_usd: 2500, F5_conv: 0.8, F6_hours: 72, HIGH: 4} as const;

/** One fill: [timestamp (s), side, outcome_index (0 = Yes token), size (shares), price]. */
export type Fill = [number, 'BUY' | 'SELL', number, number, number];

export type WalletInput = {
  /** Every fill of this wallet in this market with timestamp before T (the news time, or "now" when live). */
  fills: Fill[];
  /** T: the cut-off. Fills at or after it are ignored. */
  t: number;
  join_date: number | null;
  /** Lifetime distinct markets (`/v2/user-stats` `trades`). */
  n_markets: number | null;
  /** Wallet's `/v2/user-volume` USD from start to T (F2 denominator). */
  vol_to_t: number | null;
  /** First `/v2/activity` row, used only when join_date is null. */
  first_activity: number | null;
};

export type Features = {
  main_outcome_index: number;
  F1_days: number; F2_share: number | null; F2_markets: number | null; F3_vwap: number; F4_buy_usd: number; F5_conviction: number;
  F6_hours: number | null;
  flags: Record<FlagId, boolean | null>;
  fired: FlagId[];
  score: number;
  /** Number of flags that could be evaluated (6 with a news time, 5 live). */
  out_of: number;
};

/**
 * Returns null when the wallet has no BUY before T (not in the population).
 * withTiming=false leaves F6 unevaluated (null): live, nobody knows when the news will break.
 */
export function computeFeatures(w: WalletInput, withTiming = true): Features | null {
  const g = w.fills.filter(f => f[0] < w.t);
  const buys = g.filter(f => f[1] === 'BUY');
  if (!buys.length) return null;
  const usd = (f: Fill) => f[3] * f[4];

  // main side = token with the largest pre-T BUY USD (ties -> lower outcome index, as pandas idxmax on a sorted groupby)
  const byTok = new Map<number, number>();
  for (const b of buys) byTok.set(b[2], (byTok.get(b[2]) ?? 0) + usd(b));
  let main = -1, best = -Infinity;
  for (const k of [...byTok.keys()].sort((a, b) => a - b)) if (byTok.get(k)! > best) { best = byTok.get(k)!; main = k; }
  const bm = buys.filter(b => b[2] === main);

  // F1 freshness
  const firstM = Math.min(...g.map(f => f[0]));
  const acct = w.join_date ?? Math.min(firstM, ...(w.first_activity !== null ? [w.first_activity] : []));
  const f1 = Math.max(firstM - acct, 0) / 86400;

  // F2 focus
  const gUsd = g.reduce((a, f) => a + usd(f), 0);
  const share = w.vol_to_t !== null && w.vol_to_t > 0 ? Math.min(gUsd / w.vol_to_t, 1) : null;

  // F3 longshot: volume-weighted average price on the main side
  const vwap = bm.reduce((a, f) => a + usd(f), 0) / bm.reduce((a, f) => a + f[3], 0);

  // F4 size
  const buyUsd = buys.reduce((a, f) => a + usd(f), 0);

  // F5 conviction: |net YES-direction USD| / gross USD, all fills. BUY Yes or SELL No = +1.
  const net = g.reduce((a, f) => a + ((f[2] === 0) === (f[1] === 'BUY') ? 1 : -1) * usd(f), 0);
  const conv = Math.abs(net) / gUsd;

  // F6 timing: USD-weighted median time of main-side buys (numpy searchsorted 'left' on the cumulative sum)
  let hrs: number | null = null;
  if (withTiming) {
    const o = bm.map(f => [f[0], usd(f)] as const).sort((a, b) => a[0] - b[0]);
    const c: number[] = [];
    o.reduce((a, x) => { const s = a + x[1]; c.push(s); return s; }, 0);
    const half = c[c.length - 1] / 2;
    let j = c.findIndex(v => v >= half);
    if (j < 0) j = c.length - 1;
    hrs = (w.t - o[j][0]) / 3600;
  }

  const flags: Record<FlagId, boolean | null> = {
    F1: f1 <= FROZEN.F1_days,
    F2: (share !== null && share >= FROZEN.F2_share) || (w.n_markets !== null && w.n_markets <= FROZEN.F2_markets),
    F3: vwap <= FROZEN.F3_price,
    F4: buyUsd >= FROZEN.F4_usd,
    F5: conv >= FROZEN.F5_conv,
    F6: hrs === null ? null : hrs <= FROZEN.F6_hours,
  };
  const fired = (Object.keys(flags) as FlagId[]).filter(k => flags[k] === true);
  return {
    main_outcome_index: main, F1_days: f1, F2_share: share, F2_markets: w.n_markets, F3_vwap: vwap, F4_buy_usd: buyUsd,
    F5_conviction: conv, F6_hours: hrs, flags, fired, score: fired.length, out_of: withTiming ? 6 : 5,
  };
}

/** Shortest unique address prefix (0x + at least 4 hex), as in src/export_web.py. */
export function prefixes(wallets: string[]): Map<string, string> {
  const ws = [...new Set(wallets)].sort();
  const out = new Map<string, string>();
  ws.forEach((w, i) => {
    let n = 4;
    const neigh = [ws[i - 1], ws[i + 1]].filter(Boolean);
    while (neigh.some(o => o.slice(0, 2 + n) === w.slice(0, 2 + n))) n++;
    out.set(w, w.slice(0, 2 + n));
  });
  return out;
}
