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

### 2026-11-14 - Handoff
- Wrote `HANDOFF.md` for agents taking over (rules, what was done, weaknesses, prioritized open tasks, API facts, repo map).
- Raw API cache (`data/raw/`, ~71 MB, rejected SOL control pages included) is now committed so the pipeline re-runs without re-downloading.
- **Push blocked:** the session's GitHub token is invalid and no repository is attached. The repo is committed locally on `main`, waiting for a GitHub repository to push to.

### 2026-11-14 - Live scan: F6 is not evaluated live (decision)
- **Problem.** F6 (timing <= 72 h) is measured against T_news, the first public news. While a market is open, nobody knows when (or whether) news will break, so F6 cannot be computed honestly in real time. Using "now" as T_news would make every recent buyer fire F6.
- **Decision.** The live scan (`web/lib/scan.ts`, route `/api/scan`) computes F1-F5 exactly as frozen and leaves F6 unevaluated. It is shown as "n/a — needs news time" and the score as "live score /5". No frozen rule or threshold changed; this is a reduced use of v1, not a new version.
- **Consequence.** No live threshold is validated: the frozen high-score line is 4 of 6, and nothing says what the equivalent out of 5 is. The page presents live scores as a ranking for review, not as alerts.
- **Other live-scan limits, stated on the page.** Only the 3,000 most recent fills are read (`/v2/trades` is newest-first), so F1 uses the first fill *in that window*, and F3-F5 use that window only; profiles (`/v2/user-stats`, `/v2/user-volume`) are fetched for the 25 largest buyers to stay within rate limits; `first_activity` is not fetched, so a wallet without `join_date` uses its first fill in the window.
- **Check.** `web/lib/flags.ts` ports `features()` from `src/v1_03_layer1.py`. `web/tests/flags.test.ts` reproduces the Python score, flags and features (to the stored rounding) for 20 wallets (all 7 documented plus 13 others across scores 0-6) from `web/tests/fixtures/flags_20.json`: 23/23 tests pass.

### 2026-11-14 - Web app "Insider Signal" (presentation only; no re-analysis)
- **What.** Next.js 15 (App Router, TypeScript) in `web/`: Overview, Market view (`/markets/[id]`), Wallet alert (`/markets/[id]/wallet/[prefix]`, 271 static pages, one per wallet-market scoring >= 4), Live scan (`/live` + `/api/scan`), Method, Story. `src/export_web.py` writes compact JSON from the frozen outputs; re-running it reproduces the committed files byte for byte.
- **Design system.** Quartz from design.how, as asked. `npx shadcn add https://design.how/r/quartz/theme.json` could not run: the design.how host is refused by this environment's network policy (proxy 403). Quartz's source and lint were installed by hand from the public GitHub repository (`arla6ka/design.how`, `systems/quartz`), and the skills (`quartz`, `build-design-system`, `ui-review`) with `npx skills add`, which worked. The registry also serves the font files for "Quartz Sans"/"Quartz Mono"; they are not in the repository, so those names are mapped by `@font-face` to Inter and JetBrains Mono (variable weight, tnum/zero/ss04), with no token changed. TanStack Table pinned to v8 (Quartz's table targets v8).
- **Charts.** Quartz's own line chart has a category x-axis and no scatter layer, so the price timeline (time axis, USD-sized buy marks, T_news line) uses Recharts inside Quartz's `ChartFrame`, colored only with Quartz tokens, with a table view as the keyboard and screen-reader path. Hue use follows Quartz: one kind hue for high-score buys, another for documented wallets; warm colors only for errors.
- **Data decisions.** Price = YES price of the last fill (the frozen proxy), downsampled to <= 2,000 points by keeping the last fill per equal time bin. High-score buys merge one wallet's fills within 30 min (the Layer 2 seed rule). Wallets are identified by their shortest unique prefix (0x + >= 4 hex) within a market; full addresses and handles only for wallets in `documented_wallets.csv` (HANDOFF rule 7). v0 pooled numbers are read from the frozen summary table, not re-pooled (re-pooling rounded per-market means gave +1.59 instead of the reported +1.58).
- **Wording decisions.** The HANDOFF disclaimer appears word for word on every page that shows a wallet. F7/F8 appear only in clearly labelled post-hoc places and never in a score. Flag sources say only what the log supports (ACDC, Bock and Guenthoer, or "project brief" for F2/F6), and the Method page repeats that thresholds were not verified against the papers. The headline says "CFTC-charged" (charged, not adjudicated).
- **Wallet table default.** Filtered to F4 (size) fired, as asked; rows scoring >= 4 open their alert (click or Enter).
- **Quality.** Quartz lint clean except one deliberate warning (the requested "n/a — needs news time" uses an em dash, which Quartz discourages; the mandated disclaimer does too). ui-review run on every route at 390 and 1280 px with measured probes; 7 should-fix findings fixed (nav cut off at 390, chart tab stop with a meaningless name, empty submit shown as a failed scan, 13 lint errors, overflowing flags table, clipped story step, focus ring on the story region). Notes in `web/REVIEW.md`; screenshots in `figures/app_*.png`.
- **Not done.** Deployment to Vercel needs the owner's Vercel account; steps are in `web/README.md`. No dark theme.

### 2026-11-14 - Deployed the web app to Vercel
- Vercel was blocked by the session's network policy. Created a personal cloud environment `insider` (Polymarket hosts plus `api.vercel.com`, `vercel.com`); the Vercel token is stored as a network secret on that environment, never in the repo.
- `npx vercel link --project insider-signal` then `npx vercel deploy --prod` from `web/`. Production: https://insider-signal-rho.vercel.app (state READY, framework Next.js). `.vercel/` and `.env.local` are gitignored.
- **Open:** the project has Vercel Authentication on for all non-custom domains (Vercel's default), so visitors who are not signed in to the owner's Vercel team see a login page. The owner decides whether to turn it off (Project Settings, Deployment Protection) or attach a custom domain.

### 2026-11-15 - Web app redesigned as one page
- **Why.** Owner feedback: the multi-page app was too complicated; it should be one concise page that tells a story and shows working features rather than explaining them.
- **What changed.** Removed the market, wallet, method, story and live routes. `/` now runs: hook (the CFTC-charged Maduro wallet, rank 1 of 2,608, flagged 30 h before the news) -> explorer (market switch, price chart with every buy by a flagged wallet, click a buy or a row to see the six flags against thresholds) -> cut-off slider (flagged wallets vs named wallets caught: 4 -> 7/7 and 271; 5 -> 5/7 and 68; 6 -> 1/7 and 5) -> timing-shuffle histograms -> live scan (cached example shown on arrival) -> four limits. Kept: `/api/scan`, the data export, the TypeScript flag port and its tests. No frozen rule or number changed; the slider only shows the trade-off around the frozen line of 4 and labels it.
- **Wording check.** The hook first read "three days before Maduro fell"; the wallet's first fill was 3 days early but its USD-weighted median buy was 4.4 h before the news, so it now reads "Hours before Maduro fell, an account opened days earlier had bet $32,538 at 7¢".

### 2026-11-16 - Web app redesigned as a scrollytelling investigation (presentation only)
- **Why.** Owner feedback on the one-page version: the result did not land visually, the chart hid the key trade, the table listed $1 wallets as "flagged", flag chips were unreadable, the live demo was weak, a section went blank while scrolling, and there was no story mode.
- **Unchanged.** Frozen rules, numbers and wording rules; `lib/flags.ts` (23/23 tests still pass); the existing export outputs (byte-identical). Nothing was re-scored.
- **One export addition.** `src/export_web.py` now also writes `{m}_buys.json`: every pre-news BUY in the last 72 h, merged per wallet within 30 min (the existing timeline rule), each pointing at its wallet's frozen score and pre-news USD. Needed to draw "all pre-news buys as faint dots".
- **Design system.** Switched from Quartz to Sodium (dark), as asked. design.how is still blocked by the network policy, so Sodium's source came from the design.how GitHub repository and the skill via `npx skills add`; Sodium's font URLs fall back to `/fonts/sodium/`, served with open stand-ins (Inter variable with optical sizes, Commit Mono). Quartz removed.
- **Definition used for "flagged" in the UI.** Score >= 4 (the frozen high score) AND >= $2,500 bought before the news (the frozen F4 threshold). This is a display filter on frozen fields, not a rule change; the 271 high-score wallet-markets are still reported, and small ones are one switch away with their count.
- **Copy checked against the data.** The brief's "5-8 cents" became "around 6 cents, never above 11" (48 h median and max). The charged wallet's figures ($32,538 at 7 cents, 4.7 days old, 96% of its money here, crossed 4 signs 30 h before, median buy 4.4 h before) and Nobel's (price jump 9.3 h before the announcement; 28 flagged wallets in the last 10.3 h; shuffle 137 vs 88.2, p = 0.001; follow-on +8.9 followers in 30 min, n = 109) come from the frozen files. The price chart uses a square-root scale so the 5-11 cent run is visible; the axis says so.
- **Rule conflicts, decided.** HANDOFF's disclaimer keeps its em dash although Sodium bans em dashes. The callout's "·" separators became separate lines (Sodium bans dot separators). The three hero numbers are one ruled status strip (Sodium bans rows of equal stat cards). Step text never fades in on scroll (Sodium bans scroll reveal); only the chart changes.
- **Live example.** Replaced the Israel-Iran ceasefire example (no wallet over the line) with TIME Person of the Year 2026, Zohran Mamdani: chosen on 2026-11-16 from 26 open markets scanned across TIME Person of the Year, The Game Awards, Grammy and Oscar nominations, Israel-Lebanon and US-Iran military markets, as the one with the most wallets at >= 3/5 and >= $2,500 with longshot buying (2 wallets). The live view shows only those by default and says "No wallet crosses the line in this market right now." when none do.
- **Bugs found and fixed.** The blank-section bug was step text hidden under the sticky chart on phones; fixed and checked with an automated blank-frame probe at 1440x900, 1920x1080 and 390x844 (0 blank frames). Also: an empty Nobel chart state (client-module constant spread on the server), table page overflow at 390, header covered by the sticky chart, a slide-wide focus ring, 17 Sodium lint errors (including containers with no width limit), heading order.
- **Quality.** Sodium lint exit 0; Lighthouse mobile performance 93-99 and accessibility 100 on every page (desktop home 100/100); ui-review notes in `web/REVIEW.md`; 23 screenshots in `figures/app_*.png`.
