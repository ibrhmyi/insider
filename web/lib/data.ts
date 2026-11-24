import 'server-only';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import type {Alerts, MarketsFile, Timeline, Validation, WalletRow, Layer2, V0Summary, MarketId, BuysFile} from './types';

const dir = join(process.cwd(), 'public', 'data');
const cache = new Map<string, unknown>();

function read<T>(name: string): T {
  if (!cache.has(name)) cache.set(name, JSON.parse(readFileSync(join(dir, name), 'utf8')));
  return cache.get(name) as T;
}

export const MARKET_IDS: MarketId[] = ['maduro', 'nobel', 'iran'];
export const getMarkets = () => read<MarketsFile>('markets.json');
export const getMarket = (id: string) => getMarkets().markets.find(m => m.id === id);
export const getTimeline = (id: MarketId) => read<Timeline>(`${id}_timeline.json`);
export const getWallets = (id: MarketId) => read<WalletRow[]>(`${id}_wallets.json`);
export const getBuys = (id: MarketId) => read<BuysFile>(`${id}_buys.json`);
export const getAlerts = (id: MarketId) => read<Alerts>(`${id}_alerts.json`);
export const getValidation = () => read<Validation[]>('validation.json');
export const getLayer2 = () => read<Layer2>('layer2.json');
export const getV0 = () => read<V0Summary>('v0_summary.json');

export function isMarketId(id: string): id is MarketId {
  return (MARKET_IDS as string[]).includes(id);
}

export interface V2 {
  learned: {train_markets: number; val_markets: number; train_wallets: number; modelled_markets: number; modelled_wallets: number};
  persistence: {n_top: number; top_2025: number; n_top_2026: number; top_2026: number[]; others_2026: number[]; n_others_2026: number; diff: number[]};
  validation: {verdict: string; n_points: number; n_markets: number; brier_market: number; brier_market_ci: number[]; brier_model: number; brier_model_ci: number[]; diff: number; diff_ci: number[];
    unit: {n_units: number; brier_market: number; brier_model: number; diff_ci: number[]}};
  coefficients: {feature: string; plain: string; coef: number; lo: number; hi: number; excludes_zero: boolean; direction: string}[];
  model: {lam: number; lambda_grid: Record<string, number>; n_train_units: number; n_val_units: number;
    all_coefs: {feature: string; coef: number; lo: number; hi: number; excludes_zero: boolean}[];
    n_hours: number; gamma: number; unit_logloss_market: number; unit_logloss_model: number};
  forward: {snapshot_utc: string; commit: string; commit_url: string; commit_time: string; sha256: string;
    predictions: {question: string; slug: string; market: number; model: number; status: string}[]};
}
export const getV2 = () => read<V2>('v2.json');
