export type MarketId = 'iran' | 'maduro' | 'nobel';
export type FlagId = 'F1' | 'F2' | 'F3' | 'F4' | 'F5' | 'F6';

export type Thresholds = {
  F1_days: number; F2_share: number; F2_markets: number; F3_price: number; F4_usd: number; F5_conv: number; F6_hours: number; HIGH: number;
};

export type Market = {
  id: MarketId; short: string; question: string; slug: string; condition_id: string; open_utc: string;
  resolution: string; resolution_utc: string; volume_usd: number; why_insider_possible: string;
  t_news: number; t_news_utc: string; t_news_basis: string; t_news_source: string;
  news_events: {utc: string; epoch: number; description: string; source: string}[];
  n_wallets: number; n_high: number; n_documented: number;
  permutation: {observed: number; null_mean: number; null_p95: number; null_min: number; null_max: number; p_value: number; n_perm: number; hist: [number, number][]};
  firing_rates: Record<FlagId, number>;
  score_dist: Record<string, number>;
  pre_news_buy_fills: number;
};

export type MarketsFile = {
  flags: Thresholds;
  headline: {rank: number; n_in_market: number; market: MarketId; hours_before: number; documented_flagged: number; documented_total: number; n_high_total: number; n_high_under_1k: number; n_wallet_markets: number};
  markets: Market[];
  sensitivity: Record<string, number>[];
  precision: {size_band: string; is_high: boolean; n: number; win_rate: number; dormant_rate: number}[];
  impact: Record<string, {high_n: number; high_median: number; other_n: number; other_median: number; p_mwu: number; other_ge2500_n: number; other_ge2500_median: number; p_mwu_vs_ge2500: number}>;
};

export type HighBuy = {t: number; usd: number; side: string; yes: number; w: string; score: number; flags: string; doc: boolean};
export type Timeline = {market: MarketId; t_news: number; resolution_epoch: number; price: [number, number][]; high_buys: HighBuy[]; n_fills: number; n_points: number; note: string};

export type WalletRow = {
  id: string; addr: string | null; handle: string | null; doc: boolean; rank: number; score: number; flags: FlagId[];
  usd: number; avg_price: number; hours: number; first_high_h: number | null;
  f1_days: number; f2_share: number | null; f2_markets: number | null; f5: number; side: string; n_buys: number;
  first_fill: string; acct_src: string; imp5: number | null; imp60: number | null;
  sens: Record<'1000' | '2500' | '10000', number>;
  post: {f7_won: boolean; f8_dormant: boolean | null; f8_trades_30d: number | null};
};

export type Seed = {t: number; H: number; usd: number; dir: number; h_before: number; n_B: number; A_wallets: number; B_wallets: number | null; A_whales: number; B_whales: number; A_bots: number; B_bots: number; A_price: number; B_price: number};
export type Alerts = Record<string, Seed[]>;

export type Validation = {
  label_id: string; market: MarketId; identifier: string; identifier_type: string; confidence: 'charged' | 'alleged';
  wallet_id: string; addr: string; score: number; flags: FlagId[]; rank: number; n: number; first_high_h: number; usd: number;
  claim: string; amount: string; publisher: string; source: string; date: string; notes: string;
  sens: Record<string, number>; post: {f7_won: boolean; f8_dormant: boolean | null};
};

export type L2Test = {H: number; outcome: string; scope: string; n_A_seeds: number; n_A_wallets: number; mean_A: number; mean_B: number; mean_diff: number; ci95: [number, number]; p_signflip: number; wallet_clustered_mean_diff: number; wallet_clustered_p: number};
export type Layer2 = {whale_cut_usd: number; n_whales: number; n_bots: number; n_A_seeds_total: number; tests: L2Test[]};

export type V0Summary = {
  quantile: number; p_value: number; placebo_bias: number;
  pooled: Record<'insider-possible' | 'insider-impossible', {n_seeds: number; n_markets: number; mean_excess: number}>;
  per_market: {market: string; label: string; n_compared: number; mean_excess: number | null; n_alerts: number}[];
  maduro_blind: {alerts_pre_news: number; hours_before_news: number; direction: string; note: string};
};
