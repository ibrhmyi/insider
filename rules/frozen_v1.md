# Frozen v1 definitions: wallet-market suspicion screen (Layer 1) and follow-on test (Layer 2)

**Frozen:** see the git commit that adds this file (`git log rules/frozen_v1.md`) and the `FROZEN_UTC` line below.
Written BEFORE any v1 feature was computed, before `data/labels/documented_wallets.csv` was matched to trade data, and before validation.
Thresholds come from the literature as cited in the project brief. **None are tuned on Maduro, Nobel or Iran.**
Wording rule: a high score is **"consistent with informed trading" / "unusual activity for review"**, never "insider".

FROZEN_UTC: 2026-11-11T00:31:36Z

## Markets and T_news (first public news, from `data/news_events.csv`)
| market | T_news (UTC) | basis |
|---|---|---|
| Iran "US military action against Iran by Sunday?" | 2025-06-21 23:46 | Trump Truth Social post |
| Maduro "Maduro out by January 31, 2026?" | 2026-01-03 06:00 | first reports of explosions in Caracas (approx.) |
| Nobel "Will María Corina Machado win the Nobel Peace Prize in 2025?" | 2025-10-10 09:00 | official announcement |
BTC controls: appendix only (not screened).

## Data
- Trades: Data API v2 `/v2/trades?condition=...&taker_only=false` (maker + taker fills; each row is one wallet's side of a fill).
  Role (taker/maker) = taker if the row's composite key appears in the taker-only feed (`data/clean/trades_<m>.csv`), else maker.
- Wallet profile: `/v2/user-stats` (join_date, distinct markets traded = `trades`, lifetime volume_usdc and trade_count from `all_time_pnl`).
- Windowed volume: `/v2/user-volume?start&end` (whole UTC days).
- YES-exposure direction: BUY Yes or SELL No = +1; SELL Yes or BUY No = -1. YES price = price (Yes token) or 1 - price (No token).
- Price path: YES price of the last fill (any wallet, any role) at or before t. (No historical mid-price exists for these dates; the last-trade price is the proxy.)

## Population (unit = wallet x market)
Every wallet with at least one **BUY** fill (either token, either role) with timestamp < T_news.
- **Main side** = the outcome token with the largest pre-news BUY USD for that wallet.

## Ex-ante features (computed only from data with timestamp < T_news, except where stated)
| id | feature | definition | flag |
|---|---|---|---|
| F1 | Freshness | days from account start to the wallet's first fill in this market. Account start = `join_date` (user-stats); if null, earliest of (first `/v2/activity` row, first fill in this market). | <= 7 days |
| F2 | Focus | share = wallet's USD volume in this market before T_news / wallet's `/v2/user-volume` USD with end = T_news (day-floored window, includes the rest of T_news's UTC day); OR lifetime distinct markets (`user-stats.trades`) <= 2 | share >= 0.8 OR markets <= 2 |
| F3 | Longshot | volume-weighted average price paid on the main side, pre-news buys | <= 0.35 |
| F4 | Size | total pre-news BUY USD (both tokens) | >= $2,500 (sensitivity $1,000 and $10,000) |
| F5 | Conviction | abs(net YES-direction USD) / gross USD over all pre-news fills (buys and sells) | >= 0.8 |
| F6 | Timing | hours between the USD-weighted median time of main-side pre-news buys and T_news (continuous, recorded) | <= 72 h |

**Ex-ante score** = number of flags F1-F6 (0-6). **High score = score >= 4.**
Note on F2 market count: lifetime distinct markets is ex-post; it can only *understate* the flag ex-ante (a wallet with <= 2 lifetime markets had <= 2 at T_news), so it cannot leak toward flagging.

## Post-hoc features (never in the score; used only to evaluate it)
| id | feature | definition |
|---|---|---|
| F7 | Correctness | main side == winning outcome |
| F8 | Dormancy | `/v2/user-volume` trade_count == 0 for the window resolution+1 day .. resolution+30 days |

## Price impact per dollar
For each pre-news BUY fill where the wallet is **taker**: direction-signed change in the YES price path from just before the fill to t+5 min and t+60 min,
divided by fill USD, reported per $1,000. Wallet value = median over its fills. Compare high-score vs other wallets (Mann-Whitney U and medians, with n).

## Layer 1 null: timestamp permutation (adapted from Bock & Guenthoer 2026, as described in the brief)
For each market, 1,000 permutations. In each permutation, every wallet's pre-news BUY fills get new timestamps drawn i.i.d. from the empirical
distribution of **all** pre-news fill timestamps in that market (the market's activity profile). Held fixed: fill sizes, fill sides/tokens, the
market price path, account start, F2, F4, F5. Recomputed: F1 (first fill = earliest redrawn time; days floored at 0), F3 (price paid = price
path at the redrawn time on that token), F6. Statistic: number of wallets with score >= 4.
p-value = (1 + #{null >= observed}) / (1 + 1000), one-sided, per market.
Scorable-trade comparison vs v0: number of pre-news fills belonging to scored wallets vs v0's matched seeds.

## Validation against documented cases (`data/labels/documented_wallets.csv`)
- Built from public reporting only (source URL, claim, confidence alleged/charged). A wallet is never added because the screen flagged it.
- Matching rule: a reported **handle** matches if it equals (case-insensitive) the `name` or `pseudonym` field Polymarket serves on that
  wallet's fills in our market; a reported **address prefix** matches only if exactly one wallet in the market starts with it. Unmatched labels are reported as unmatched.
- Report: score, rank (descending score, ties broken by pre-news BUY USD), recall at score >= 4, and hours before T_news at which the wallet first
  reaches score >= 4 when features are recomputed using only its fills up to each of its own pre-news buy times.
- Precision proxy: win rate (F7) and dormancy (F8) of high-score wallets vs other wallets in the same F4 size band
  (< $1k, $1k-2.5k, $2.5k-10k, >= $10k).

## Layer 2: do others follow suspicious wallets?
- **Seed A** = a pre-news BUY fill (either role) by a high-score wallet; fills by the same wallet within 30 min are merged into one seed (first time, summed USD, main direction).
- **Seed B** = a pre-news BUY seed (same merge rule) by an **established** wallet (score <= 1 and user-stats `trades` >= 10 markets) in the same market,
  USD within +-30% of the A seed, time within +-6 h of the A seed. All eligible B seeds are kept; each A seed is compared with the mean of its B seeds.
- Outcomes after the seed, windows 30 min and 120 min: distinct **taker** wallets (excluding the seed wallet) trading in the seed's direction,
  their USD, and the direction-signed YES price change. Followers split into **whales** (top 1% of lifetime volume_usdc among all wallets in the three
  markets), **bots** (lifetime trade_count / days since join_date >= 50; join_date null -> not classified as bot), **others**.
- Exclusion: any A or B window overlapping T_news +-15 min is excluded and reported separately.
- Test: paired difference d = A - mean(B) per A seed with >= 1 B seed; sign-flip permutation (10,000), stratified by market (flips within market);
  95% CI by bootstrap over A seeds (5,000). Reported per market and pooled, with n.

## Alert card
Score and which flags fired, price impact, follow-on vs matched ordinary trades, news context, and the line
"Unusual activity for review — this does not identify an owner or prove insider trading."
