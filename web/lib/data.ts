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
