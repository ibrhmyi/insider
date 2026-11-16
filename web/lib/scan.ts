/**
 * Live scan: fetch a Polymarket market's metadata and recent fills server-side (no CORS in the browser),
 * then score the largest recent buyers with the frozen v1 flags F1-F5. F6 needs the news time, so it is not evaluated.
 * API facts (HANDOFF.md): Data API v2 only (v1 retired 2026-11-02), cursor pagination, `condition=`, newest first,
 * `taker_only` defaults to true; Gamma hides closed markets unless closed=true.
 */
import {computeFeatures, FROZEN, prefixes, type Fill} from '@/lib/flags';


const GAMMA = 'https://gamma-api.polymarket.com';
const DATA = 'https://data-api.polymarket.com/v2';
const MAX_PAGES = 3;          // up to 3,000 most recent fills
const MAX_WALLETS = 25;       // profiles fetched for the largest buyers only, to stay within API rate limits
const UA = {'User-Agent': 'insider-signal-web/0.1'};

type GammaMarket = {id: string; question: string; slug: string; conditionId: string; outcomes: string; closed: boolean; endDate?: string; volume?: string; volumeNum?: number; events?: {slug: string; title?: string}[]};
type RawFill = {proxy_wallet: string; side: 'BUY' | 'SELL'; outcome_index: number; size: number; price: number; timestamp: number; transaction_hash: string; token_id: string};

export class ScanError extends Error { constructor(msg: string, public status = 400) { super(msg); } }

async function getJson<T>(url: string, tries = 3): Promise<T> {
  let delay = 500;
  for (let a = 1; ; a++) {
    const r = await fetch(url, {headers: UA, cache: 'no-store'});
    if (r.ok) return r.json() as Promise<T>;
    if (a >= tries || (r.status < 500 && r.status !== 429)) throw new ScanError(`Polymarket answered ${r.status} for ${new URL(url).pathname}`, 502);
    await new Promise(res => setTimeout(res, delay));
    delay *= 2;
  }
}

export function parseSlug(input: string): string[] {
  const s = input.trim();
  if (!s) return [];
  try {
    const u = new URL(s.includes('://') ? s : `https://${s}`);
    if (u.hostname.endsWith('polymarket.com')) return u.pathname.split('/').filter(p => p && !['event', 'market', 'markets', 'sports'].includes(p)).reverse();
  } catch {}
  return /^[a-z0-9-]+$/i.test(s) ? [s.toLowerCase()] : [];
}

async function findMarket(input: string): Promise<{market: GammaMarket; siblings: number}> {
  const slugs = parseSlug(input);
  if (!slugs.length) throw new ScanError('Paste a polymarket.com market link or a market slug.');
  for (const slug of slugs) {
    for (const closed of ['false', 'true']) {
      const ms = await getJson<GammaMarket[]>(`${GAMMA}/markets?slug=${encodeURIComponent(slug)}&closed=${closed}`);
      if (ms.length) return {market: ms[0], siblings: 0};
    }
    const ev = await getJson<{markets?: GammaMarket[]}[]>(`${GAMMA}/events?slug=${encodeURIComponent(slug)}`);
    const markets = ev[0]?.markets ?? [];
    if (markets.length) {
      const open = markets.filter(m => !m.closed);
      const pool = open.length ? open : markets;
      const top = pool.reduce((a, b) => (Number(b.volumeNum ?? b.volume ?? 0) > Number(a.volumeNum ?? a.volume ?? 0) ? b : a));
      return {market: top, siblings: markets.length - 1};
    }
  }
  throw new ScanError(`No Polymarket market or event found for "${slugs[0]}".`, 404);
}

async function pool<T, R>(items: T[], n: number, fn: (x: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let i = 0;
  await Promise.all(Array.from({length: Math.min(n, items.length)}, async () => { while (i < items.length) { const k = i++; out[k] = await fn(items[k]); } }));
  return out;
}

export async function scan(input: string) {
  const {market, siblings} = await findMarket(input);
  const fills: RawFill[] = [];
  let cursor: string | undefined;
  for (let p = 0; p < MAX_PAGES; p++) {
    const q = cursor ? `cursor=${encodeURIComponent(cursor)}` : 'limit=1000';
    const js = await getJson<{data?: RawFill[]; pagination?: {has_more?: boolean; next_cursor?: string}}>(`${DATA}/trades?condition=${market.conditionId}&taker_only=false&${q}`);
    fills.push(...(js.data ?? []));
    cursor = js.pagination?.next_cursor;
    if (!js.pagination?.has_more || !cursor) break;
  }
  // same composite-key dedup as the frozen pipeline
  const seen = new Set<string>();
  const uniq = fills.filter(f => { const k = [f.transaction_hash, f.proxy_wallet, f.token_id, f.timestamp, f.size, f.price].join('|'); if (seen.has(k)) return false; seen.add(k); return true; });
  const now = Math.floor(Date.now() / 1000);
  const t = uniq.length ? Math.max(...uniq.map(f => f.timestamp)) + 1 : now;
  const byW = new Map<string, Fill[]>();
  for (const f of uniq) {
    const a = byW.get(f.proxy_wallet) ?? [];
    a.push([f.timestamp, f.side, f.outcome_index, Number(f.size), Number(f.price)]);
    byW.set(f.proxy_wallet, a);
  }
  const buyUsd = (fs: Fill[]) => fs.filter(f => f[1] === 'BUY').reduce((a, f) => a + f[3] * f[4], 0);
  const buyers = [...byW.entries()].filter(([, fs]) => fs.some(f => f[1] === 'BUY'));
  const top = buyers.sort((a, b) => buyUsd(b[1]) - buyUsd(a[1])).slice(0, MAX_WALLETS);
  const pref = prefixes([...byW.keys()]);

  const rows = await pool(top, 6, async ([w, fs]) => {
    const [st, vol] = await Promise.all([
      getJson<{data?: {trades?: number; join_date?: number | null}}>(`${DATA}/user-stats?user=${w}`),
      getJson<{data?: {volume_usdc?: number | null}}>(`${DATA}/user-volume?user=${w}&start=1&end=${t}`),
    ]);
    // join_date missing: fall back to the wallet's first /v2/activity row (src/v1_01_fetch.py _first_activity).
    // The window's earliest fill is not the wallet's first fill in this market, so it is not used (first_fill_known: false).
    const join = st.data?.join_date ?? null;
    let firstActivity: number | null = null;
    if (join === null) {
      const act = await getJson<{data?: {timestamp?: number}[]}>(`${DATA}/activity?user=${w}&start=1&sort_direction=ASC&limit=1`).catch(() => ({data: []}));
      firstActivity = act.data?.[0]?.timestamp ?? null;
    }
    const r = computeFeatures({fills: fs, t, join_date: join, n_markets: st.data?.trades ?? null, vol_to_t: vol.data?.volume_usdc ?? null, first_activity: firstActivity, first_fill_known: false}, false)!;
    return {
      id: pref.get(w)!, score: r.score, out_of: r.out_of, fired: r.fired,
      side: (JSON.parse(market.outcomes || '["Yes","No"]') as string[])[r.main_outcome_index] ?? String(r.main_outcome_index),
      F1_days: r.F1_days, F2_share: r.F2_share, F2_markets: r.F2_markets, F3_vwap: r.F3_vwap, F4_buy_usd: r.F4_buy_usd, F5_conviction: r.F5_conviction,
      n_fills: fs.length, join_known: join !== null,
      account_start: join !== null ? 'join_date' : firstActivity !== null ? 'first_activity' : 'unknown',
    };
  });
  rows.sort((a, b) => b.score - a.score || b.F4_buy_usd - a.F4_buy_usd);
  const ts = uniq.map(f => f.timestamp);
  return {
    market: {question: market.question, slug: market.slug, closed: market.closed, end_date: market.endDate ?? null, volume: Number(market.volumeNum ?? market.volume ?? 0), event_siblings: siblings},
    window: {from: ts.length ? Math.min(...ts) : null, to: ts.length ? Math.max(...ts) : null, n_fills: uniq.length, n_wallets: byW.size, n_buyers: buyers.length, n_scored: rows.length},
    thresholds: FROZEN,
    wallets: rows,
    scanned_at: now,
    notes: [
      `Only the ${uniq.length.toLocaleString('en-US')} most recent fills are read (at most ${MAX_PAGES * 1000}); F1, F3, F4 and F5 use those fills only.`,
      `Profiles are fetched for the ${rows.length} largest buyers in that window.`,
      'F6 is not evaluated: it needs the time of the first public news, which is unknown while a market is live.',
    ],
  };
}

