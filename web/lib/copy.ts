import type {FlagId} from './types';

/**
 * HANDOFF rule 1: every card or figure that shows a wallet carries this line. Same words as HANDOFF.md; the em dash
 * became a colon on 2026-11-17 because the owner banned em dashes from the UI (see log/process_log.md).
 */
export const DISCLAIMER = 'Unusual activity for review: this does not identify an owner or prove insider trading.';
export const NOT_PROOF = 'Unusual activity for review, not proof of insider trading.';

/** Text from outside (market titles from Polymarket) can carry em dashes; show them as a colon or comma instead. */
export const clean = (s: string) => s.replace(/\s+\u2014\s+/g, ': ').replace(/\u2014/g, ', ');

export const FLAG_NAMES: Record<FlagId, string> = {
  F1: 'Fresh account',
  F2: 'Focused on this market',
  F3: 'Longshot price',
  F4: 'Large size',
  F5: 'One-sided',
  F6: 'Close to the news',
};

export const FLAG_RULE: Record<FlagId, string> = {
  F1: 'Account 7 days old or less at its first fill here',
  F2: '80% or more of its volume here, or 2 markets or fewer in its lifetime',
  F3: 'Average price paid 0.35 or less on its main side',
  F4: '$2,500 or more bought before the news',
  F5: '80% or more of its trading in one direction',
  F6: 'Median buy 72 hours or less before the news',
};

export const FLAG_SOURCE: Record<FlagId, string> = {
  F1: 'ACDC: first longshot bet within 2 days of account creation (we use 7 days)',
  F2: 'Project brief: concentration in a single market',
  F3: 'ACDC: bets at 35 cents or less',
  F4: 'ACDC: $2,500 floor; Bock and Guenthoer (2026): $1,000 floor, used as a sensitivity check',
  F5: 'Bock and Guenthoer (2026): conviction above 0.8',
  F6: 'Project brief: timing relative to the first public news',
};

/** Short words for the flag marks (the brief's labels). */
export const FLAG_SHORT: Record<FlagId, string> = {F1: 'New account', F2: 'All-in on one market', F3: 'Cheap price', F4: 'Big bet', F5: 'One direction', F6: 'Close to the news'};

/** One plain line per sign, with the frozen threshold (rules/frozen_v1.md). */
export const FLAG_PLAIN: Record<FlagId, string> = {
  F1: '7 days old or less when it first bet here.',
  F2: '80% or more of its money in this market, or 2 markets or fewer in total.',
  F3: 'Bought at 35¢ or less.',
  F4: '$2,500 or more.',
  F5: '80% or more of its trading one way.',
  F6: 'Main buying within 72 hours of the news.',
};

export const FLAGS: FlagId[] = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6'];

export const usd = (v: number, digits = 0) => `$${v.toLocaleString('en-US', {maximumFractionDigits: digits, minimumFractionDigits: digits})}`;
export const compactUsd = (v: number) => v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v / 1e3).toFixed(v >= 1e4 ? 0 : 1)}k` : `$${Math.round(v)}`;
export const pct = (v: number, digits = 0) => `${(v * 100).toFixed(digits)}%`;
export const hours = (h: number) => h >= 48 ? `${(h / 24).toFixed(1)} d` : `${h.toFixed(h < 10 ? 1 : 0)} h`;
export const utc = (epoch: number) => new Date(epoch * 1000).toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
export const shortId = (id: string) => `${id}…`;
