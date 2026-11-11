# Frozen v0 detector definitions

**Frozen:** 2026-11-09T16:31:34Z (UTC), BEFORE any insider-possible market was run through the measures.
**Tuned on:** control (insider-impossible) markets only: `ctrl_btc110k_jun17`, `ctrl_btc94k_jan5`, `ctrl_btcupdown_oct14`.
**Code fingerprint:** `src/measures.py` sha256 `b47a1a4b0a5a1e7061fa085438061ee496e75000e760c6904b84954028547682` (checked by `src/04_run_frozen.py`; the run aborts if it differs).
**Machine-readable copy:** `rules/frozen_v0.json`.

## Data unit
Taker-side trades from Data API v2 `/v2/trades` (`taker_only=true`), one row per fill, deduplicated on
(transaction_hash, proxy_wallet, token_id, timestamp, size, price). Trades after resolution are excluded from seeds/anchors.
- **Direction** (YES-exposure): BUY Yes or SELL No = +1 (toward YES); SELL Yes or BUY No = -1.
- **YES price**: price if the Yes token traded, else 1 - price. **Size** = USD notional = shares x execution price.

## Seed trade
A trade is a seed if ALL hold:
1. notional > the **99th percentile** of notional of all trades in the same market in the previous **24 h** (strictly earlier timestamps);
2. at least **20** trades exist in that 24 h look-back (else no threshold);
3. not after resolution;
4. not a **carry** trade: not betting on the side already priced above **0.98** (direction +1 with YES price > 0.98, or -1 with YES price < 0.02);
5. repeat seeds by the same wallet in the same direction within 30 min collapse to the first (split orders).
Sensitivity versions (reported, not primary): 95th and 99.5th percentile.

## Ripple (observed)
In (seed time, seed time + **30 min**], same direction as the seed, seed wallet excluded:
- **distinct wallets** (primary), trade count, USD volume.

## Expected ripple (matched no-seed windows, same market)
- Anchor pool: ordinary (non-seed) trades before resolution, before (first news - 30 min - window), with no seed within +-30 min, not overlapping news +-30 min, with >= 1 trade in the prior hour; the anchor trade's own wallet is excluded from its window.
- Matching features (standardised, Euclidean): price, log_cnt_1h, log_cnt_5m, log_h_to_ref
  (YES price; log(1+trades in previous 1 h); log(1+trades in previous 5 min); log(1+hours to first news/reference time)).
- Only anchors within **+-2 h** of the seed; **k = 10** nearest; expected = mean over matches, measured in the seed's direction.
- **Excess ripple** = observed - expected (primary: distinct wallets; also trades, volume; secondary log((1+obs)/(1+exp))).
- Seeds with no eligible anchor inside the caliper get no expected value and are reported as "unmatched".

## News exclusion
- Any seed whose window [t, t+30 min] overlaps a news timestamp +-30 min is **excluded** and listed separately.
- News timestamps: `data/news_events.csv`. Control markets: price reference time (and candle open for the 1-hour Up/Down market).
- Seeds after (first news - 30 min) that do not overlap are labelled **post-news** and reported separately; the main comparison uses **pre-news** seeds only.

## Alert (for the example card and the blind validation)
A pre-news seed whose excess distinct-wallet ripple > **12.91**
= 95th percentile of control excess_wallets at q=0.99 (n=50 control seeds).
Wording rule: an alert is **"unusual activity for review"** only; it is never evidence that any wallet is an insider.

## Calibration evidence (controls only)
Placebo test: 300 random ordinary trades on controls treated as pseudo-seeds. Chosen setting: mean excess **+2.45** wallets (median 0.10, SD 8.35; mean log-ratio 0.03; 268 of 300 had anchors within the caliper).
The baseline therefore still **under-predicts by ~2.5 wallets on average**. This is a known v0 bias; comparisons should be read relative to the control distribution, not to zero.
Tuning history (4 iterations, incl. one bug fix) is in `log/process_log.md`; grids in `data/audit/tuning_grid_controls.csv`, seed counts in `data/audit/tuning_seed_counts_controls.csv`.
