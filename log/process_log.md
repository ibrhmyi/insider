# Process log: Detecting Potential Insider Trading on Polymarket (CP191 Nano Capstone)

All times UTC. Wording rule throughout: flagged activity is **"unusual activity for review"**, never a claim that any wallet is an insider. No wallet addresses appear in reports or figures.

## Original vs. revised design (summary)

| Aspect | Original design | Revised design (this week) | Why |
|---|---|---|---|
| Comparison | Single-market anomaly detection | Insider-possible markets vs matched insider-impossible controls | Without controls, "large trade then herding" is not distinguishable from normal market behaviour |
| Labelling | Implicit / by topic | Written rule on resolution mechanism only, timestamped before analysis (`rules/labeling_rule.md`) | Prevents labelling markets by their trading pattern (circularity) |
| Data source | Dome API | Polymarket Data API **v2** + Gamma + price history | Dome shut down April 2026; Data API v1 retired 2 Nov 2026 |
| Detector tuning | On the markets of interest | On controls only, then frozen with code hash (`rules/frozen_v0.md`) | Avoids fitting the detector to the answer |
| News | Not handled | Windows within +-30 min of public news excluded; post-news seeds reported separately | Separates reaction to public information from pre-news activity |
| Validation | None | Blind run of the frozen rules on Maduro market | Tests the frozen detector on a case it was not tuned on |

## Dated entries

### 2026-11-09: Environment / access
- **Problem:** every Polymarket host (gamma-api, data-api, clob, docs) refused by the cloud session's network policy (proxy 403).
  **Decision:** added exactly those four hosts to the environment allowlist (user approved). **Why:** smallest change that unblocks the project.
- **Problem:** `matplotlib` missing. **Decision:** `pip install matplotlib pandas requests tabulate`.

### 2026-11-09: API behaviour (read docs.polymarket.com first)
- **Problem:** `GET data-api.polymarket.com/trades` returns **HTTP 410** `"Data API v1 has been retired"` (retired 2026-11-02).
  **Decision:** use `/v2/trades` per the migration guide (`data/raw/docs/migrate_v1_v2.md`, OpenAPI saved in `data/raw/docs/`).
  v2 differences that matter: cursor pagination (`next_cursor`, no 10,000-row offset cap), `condition=` not `market=`, snake_case fields, `offset` param is a 400 error.
- **Finding:** `/v2/trades?condition=` **ignores start/end** (fixed three-year window). **Decision:** fetch everything, filter by time locally (as planned).
- **Finding:** feed is newest-first; no unique trade id field. **Decision:** dedupe on composite key (tx hash, wallet, token, timestamp, size, price). Result: **0 duplicates** in all six markets.
- **Finding:** `taker_only` defaults to true (each fill once, taker side). **Decision:** analyse taker rows (the initiator of each fill). Maker+taker rows fetched separately only for the completeness check.
- **Problem:** Gamma `/markets?condition_ids=` returned `[]` for the Iran market. **Cause:** closed markets are hidden unless `closed=true`. **Decision:** always pass `closed=true` / use `/markets/{id}`.
- **Problem (my bug):** Gamma market search returned exactly 100 rows per window. **Cause:** Gamma silently caps `limit` at 100; my loop expected 500 and stopped. **Fix:** page by 100.
- **Problem:** Gamma returns **HTTP 422** beyond offset ~2,000. **Decision:** results are sorted by volume desc, so top 2,000 is sufficient; treat 422 as end-of-results.
- **Finding:** price history for 2025 / early-2026 markets is only at 12-hour grain (1-minute data kept ~7 days; asked for 3 h, got 12 h). **Decision:** price history is used only for control matching; Figure 1's price line is rebuilt from trades.
- **Rate limits:** 0 non-200 responses across all extraction runs (logged in `data/raw/trades/http_events_*.json`); client sleeps 0.2-0.25 s between pages and honours `Retry-After` on 429/503.
- **Not used:** Dome API (shut down). Dune / on-chain fallback **not used**: no Dune API key is available in this session. All trade data comes from Data API v2.

### 2026-11-09: Labelling rule
- Rule written and timestamped **16:11:20Z** (`rules/labeling_rule.md`).
- **Honesty note:** while testing API connectivity, one page (1,000 rows) of Iran trades was retrieved *before* the rule was written. The rule only uses resolution mechanics, so this could not inform it, but the order of events is recorded here.

### 2026-11-09: Market selection
- Iran market confirmed: resolution 2025-06-22 02:41:50 UTC from `/v2/resolutions` matches the brief exactly.
- **Maduro:** the "Maduro out by...?" event (id 16180) has four sibling markets that resolved Yes on 2026-01-03. **Decision:** use "Maduro out by January 31, 2026?" (highest volume, $10.97M). Siblings are the same event and are not used as separate samples.
- **Nobel:** "Will María Corina Machado win the Nobel Peace Prize in 2025?". **Discrepancy:** on-chain resolution 11:03:30 UTC vs Gamma `closedTime` 12:11:22 UTC. **Decision:** use the `/v2/resolutions` time.
- **News timestamps** (`data/news_events.csv`):
  - Iran 2025-06-21 23:46 UTC: Trump Truth Social post; sources disagree by ~4 min (7:46 vs 7:50 pm EDT); earliest used. Secondary sources only (no primary Truth Social archive found).
  - Maduro 2026-01-03 06:00 UTC (approximate: first reports of explosions in Caracas ~2 am local) and 09:21 UTC (Trump post, 4:21 am ET). Earliest used for "before public news".
  - Nobel 2025-10-10 09:00 UTC (11:00 CEST announcement): **the minute is single-sourced**; 11:00 is the committee's standard slot.
- **Control matching:** score = |ln(vol ratio)| + 5 x |median pre-resolution YES price diff| + 0.1 x days apart, over crypto "price above" markets within +-7 days.
- **Problem:** best Nobel control (Solana > $280 on Oct 10, score 0.09) had a feed starting 133 h after market open, maker+taker notional = 1.98x Gamma volume, and **0% of taker notional at contested prices** (all activity was No bought at 0.999, i.e. carry). **Every** October-2025 "price above" candidate screened showed the same pattern (ratio ~1.9, contested share ~0).
  **Decision:** reject that family for October; added a screen (feed ratio ~1, contested share > 0); substitute **"Bitcoin Up or Down - October 14, 5PM ET"** (ratio 1.003, contested 0.99). **Cost:** it trades near 0.5 rather than Machado's low band, and is 0.41x the volume. Rejected market's data kept in `data/rejected/`.
  **Open item:** the 1.9x ratio could be a Gamma accounting difference or missing trades in the API feed; on-chain data would settle it.
- Iran and Maduro controls are **weak matches on volume** (3.8x and 9.4x smaller); no larger crypto-threshold markets existed in those weeks. See `data/control_match_table.md`.
- For the Up/Down control the 1-hour candle opens at 21:00 UTC, when the outcome starts becoming public. **Decision:** record 21:00 as an additional "news" time (done before freezing).

### 2026-11-09: Extraction and audit
- Batch checks per page: row count, min/max timestamp, sorted newest-first, overlap/gap vs previous page (`data/raw/trades/<market>/batch_log.csv`). All pages sorted; no overlaps; no negative gaps.
- **Problem (my bug):** audit reported the "largest gap" as starting at the last trade. **Cause:** `argmax` over a diff series whose first value is NaN. **Fix:** `nanargmax`.
- **Completeness check:** maker+taker notional / Gamma volume: Iran 1.011, Nobel 0.961, BTC Jun 17 1.068, BTC Jan 5 0.994, Up/Down 1.003, **Maduro 0.885** (up to ~11% of Maduro activity may be missing from the API feed; flagged).
- Core fields (timestamp, wallet, side, size, price, tx hash, token) have **no missing values**. Only profile fields (name, bio, images) are missing.
- Post-resolution trades flagged (kept, not used): Iran 1, Nobel 16, others 0.

### 2026-11-09: Version 0 tuning (controls only)
- Definitions as in `rules/frozen_v0.md`. Seed size measured as USD notional; direction in YES-exposure terms.
- **Decision before tuning:** exclude "carry" seeds (bets on the side already priced > 0.98), motivated by the October control screen. *Disclosure:* from the matching step I already knew Machado traded at low prices; the rule was written to keep low-price lottery-side bets eligible in every market.
- **Problem:** the 24 h warm-up made the 11-hour Up/Down market unusable. **Fix:** no warm-up; the min-prior-trades rule guards against thin history.
- **Placebo calibration** (random ordinary trades as pseudo-seeds should give excess ~0):
  1. Iteration 1 (grid vs trade anchors x k x min-prior): mean placebo excess **+16** wallets. Fail.
  2. Iteration 2 (added burst + time-to-expiry features): still **+15**. Fail.
  3. **Bug found:** placebo trades blanked out +-30 min of anchors like real seeds, removing the busy-period anchors. Fixed; mean +10, median ~0.3.
  4. Added a +-2 h time caliper (local baseline): **mean +2.45, median 0.10**. Chosen. Residual bias reported with all results.
- Chosen: trade-anchored baseline, k=10, min 20 prior trades, features price + log trades 1 h + log trades 5 min + log hours-to-reference, caliper +-2 h; alert threshold = 95th pct of control excess = **+12.91 wallets**.
- **Frozen 2026-11-09T16:31:34Z**, `measures.py` sha256 recorded; `04_run_frozen.py` refuses to run if the code changes.

### 2026-11-09: Frozen run, comparison, validation
- Primary (q=0.99, pre-news, matched): insider-possible mean excess **+1.98** wallets (n=147 seeds, 3 markets) vs controls **+1.58** (n=50, 2 markets). Permutation p=0.72 (treats seeds as independent; they are not). **No detectable difference** in this pilot.
- Up/Down control contributes **0 usable seeds** (its large trades fall inside the candle/news window), so the comparison has effectively 2 control markets.
- **Limitation found:** many seeds have no matched baseline (Nobel 38/85; Maduro's final pre-news hours). The +-2 h caliper is too strict in quiet or fast-changing periods.
- **Maduro blind validation:** 1 pre-news alert (Dec 30, 96 h before news, toward NO). No alert in the final 24 h; the last-hours YES-direction seeds were unscorable. The large repricing (0.12 to 0.51) began after ~06:00 UTC public reports. Descriptive profile appended to `data/results/maduro_blind_validation.md` (not detector output).
- **Example alert card (Figure 3):** Nobel, 2025-10-09 22:42:57 UTC, toward YES, excess +13.3 wallets (threshold +12.9), only 6 matched windows. Chosen because it is the earliest alert in the documented pre-announcement price spike; it is shown as an example of the output format, not as evidence.

### Not finished / next steps
- On-chain (Dune/Polygon) cross-check of Maduro (0.885 ratio) and of the October-2025 "price above" feeds; needs a Dune API key.
- Better controls for Iran and Maduro (volume), and more than one control per target.
- Fix baseline coverage (unmatched seeds): e.g. widen caliper adaptively. Requires a new version (v1), re-tuned on controls and re-frozen.
- Market-level inference (seeds are clustered within markets); more markets per arm.

---

## 2026-11-11 - Method change: v0 (ripple after large trades) -> v1 (wallet-market suspicion screen + follow-on test)

**Why.** v0 found no difference in follow-on ripples between insider-possible markets and BTC controls
(+1.98 vs +1.58 extra wallets, n = 147 vs 50 seeds, permutation p = 0.72). Diagnosis:
1. Ripples measure *visibility*, not information: traders copy any big trade.
2. The size-percentile seed rule selects whales and market makers; it ignores price, wallet history and correctness.
3. The matched-window baseline cannot score pre-news run-ups (38/85 Nobel seeds and Maduro's final pre-news hours were unscorable), a selection bias toward quiet windows.
4. BTC controls carry continuous public information and bot flow, and were volume-mismatched (3.8x-9.4x smaller).
5. 3 vs 2 markets gives almost no statistical power.

**Decision.** Keep all v0 outputs unchanged. The v0 null result is **Finding #1** and motivates v1.
v1 asks, *within* each insider-possible market: (a) can a literature-based wallet screen identify wallets whose trading is
consistent with informed trading, validated against publicly documented cases; (b) do other traders follow those wallets
more than equally large trades by established wallets? BTC controls are dropped from the main analysis (appendix only).

### 2026-11-11 - Sources for thresholds
- Thresholds are taken from the project brief, which cites ACDC ($2,500 at <= 35c, longshot win rate, first longshot within 2 days of account creation),
  Bock & Guenthoer (2026) (conviction > 0.8, $1,000 floor, timestamp permutation) and Gomez-Cram et al. (2026) (price impact per dollar).
- **Could not verify against the papers:** the Bock & Guenthoer PDF host (vernimmen.com) is not reachable from this session; no public source for the
  ACDC figures was found by web search. Gomez-Cram et al. was found (working paper, LSE/LBS/Yale, 2026; reported 7-12x larger price impact for suspected insider accounts).
- Thresholds were written to `rules/frozen_v1.md` and committed to git **before** any v1 feature was computed and before validation.

### 2026-11-11 - v1 order of operations (for audit)
1. `rules/frozen_v1.md` written and committed (`f39e644`, FROZEN_UTC 2026-11-11T00:31:36Z) before any v1 feature existed.
2. `data/labels/documented_wallets.csv` built from public reporting and matched to wallets by the frozen handle/prefix rule; committed (`add4bcd`) before scoring.
3. Data fetched, then Layer 1, Layer 2, figures, summary. No threshold was changed after step 1.

### 2026-11-11 - v1 problems, decisions, data gaps
- **Re-download (necessary):** v0 kept taker fills only; wallet-level features need every fill incl. limit orders. Fetched `/v2/trades?taker_only=false` for the 3 markets (cached in `data/raw/trades_allsides/`). Taker counts match v0 exactly (2,291 / 9,367 / 6,143); maker rows 4,355 / 16,617 / 9,441.
- **Duplicate ambiguity:** with maker rows the composite key removed 199 / 420 / 14 rows. The API has no log index, so some may be genuine identical fills. Kept the brief's rule; possible undercount <= 2.9%.
- **Wallet profiles:** 8,309 wallets via `/v2/user-stats` (0 errors); 7,139 pre-news-buyer wallet-markets via `/v2/user-volume` windows (0 errors). `join_date` null for 235 wallets; first-activity fallback fetched for 132 pre-news buyers.
- **Web access:** this session can run web searches but cannot open external pages (news sites, arXiv, vernimmen.com, Polygonscan all fail DNS). Consequences: thresholds not verified against Bock & Guenthoer / ACDC; documented wallets built from search-result summaries of public reporting (sources listed per row); no on-chain funding analysis.
- **Documented wallets:** 8 labels -> 7 distinct wallets. The CFTC complaint's handle "Burdensome-Mix" and Lookonchain's prefix 0x31a5 independently resolve to the same wallet.
- **Bug:** pandas refused NaN in a boolean column for F8 (dormancy unknown). Fixed by storing F8 as float (1/0/NaN).
- **Permutation consistency fix (before running):** observed F1 uses a wallet's first fill of any side; the null initially redrew only buys. Fixed so sells keep their real times, as the frozen text implies.
- **Finding - F6 uninformative in Iran:** Iran traded ~49 h before T_news, so F6 (<= 72 h) fires for 100% of buyers; the Iran permutation null cannot test timing. F5 fires for 71-73% of buyers in Iran/Maduro. Recorded as a v1 limitation (not changed, rules frozen).
- **Finding - F7 confounded:** all three markets resolved toward the long-time longshot. Among longshot buyers, high-score wallets win *less* often than others, so F7 does not support precision. Dormancy (F8) among larger winners is the informative proxy.
- **Price impact:** no historical mid-price; last-fill YES price used. Fills whose 5/60-min window crosses T_news dropped.
- **Layer 2 limitation:** B seeds matched on size/time window but not local activity. Added a wallet-clustered sign-flip as a robustness check (not in the frozen text; reported alongside, not instead).
- **Not done:** on-chain funding (no access), 2-3 additional markets (time), event-cluster F2 (single-market only).
