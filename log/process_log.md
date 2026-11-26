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

### 2026-11-17 - Web app reduced to one simple page (presentation only)
- **Why.** Owner: a stranger should understand the project in 60 seconds of scrolling; one story (Maduro), plain English, no jargon or p-values on the page.
- **What.** `/` is seven full-screen steps: hook, question, sticky chart (flat line at about 7 cents, the wallet's buys as one yellow dot "$32,538 at 7¢", the news line at 06:00 UTC Jan 3, the jump to 100 cents), six signs lit one by one with the wallet's values, three big numbers, the catch, and the live scan (score out of 5, buyers of $2,500 or more only, cached example). Footer links the GitHub repository and points to the written report for method and limits. Nav, `/cases`, `/method`, `/story` and `/live` are moved to `web/archive/` (excluded from the build); data, rules, `lib/flags.ts`, its tests and `/api/scan` stay.
- **Wording changed from the brief, and why.** (1) "A soldier bet ... 30 hours later, he did" became "A wallet bet $32,538 that Maduro would fall. Hours later, he did.": 30 h is when the wallet first reached 4 signs; its USD-weighted median buy was 4.4 h before the news and its last buy about 3 h before; and the screen does not identify an owner (HANDOFF rule 1), so the owner appears only as the CFTC's allegation: "In April 2026 the CFTC charged its alleged owner, a US soldier. Charged, not convicted." (2) The "Early" sign shows 4.4 h (what that sign measures), not 30 h; 30 h stays in the result as "30 h early". (3) "7 of 7 publicly named suspects" became "publicly named wallets" (no insider-type labels). (4) "271 wallets nobody has accused" became 264, since 271 includes the 7 named ones. (5) "Rules taken from published research" became "Rules based on published research": two of the six thresholds come from the project brief, not a paper.
- **The yellow dot** stands for all of the wallet's pre-news buys: placed at its USD-weighted median buy time and its average price (7.45 cents), labelled with the total.
- **Design.** Sodium dark. Three page-level type roles were added (22px+ body, 96px+ numbers) because Sodium's scale stops at 56px and 15px body; same faces and tracking tokens. The yellow primary button became secondary so yellow marks only the wallet.
- **Checks.** Sodium lint clean (one kept em dash in the owner's catch line); 23/23 tests; Lighthouse mobile 96/100/96, desktop 100/100/96; a 1920x1080 Playwright screen recording of a full scroll; 390 px stacked layout with a static chart; reduced motion shows end states.

### 2026-11-16 - Bug fix: live scan set "new account" (F1) age to 0 when join_date was missing
- **Bug.** In `/api/scan` (`web/lib/scan.ts`), when `/v2/user-stats` returned no `join_date`, the live scan passed no `/v2/activity` row, so `computeFeatures` (`web/lib/flags.ts`) fell back to the wallet's earliest fill *in the scanned window* as its account start. That fill is not the wallet's first fill in the market (the live scan reads only the ~3,000 most recent fills), so the account age came out as about 0 days and F1 fired falsely. Example: wallet 0xa0f2... in "Will Zohran Mamdani be TIME Person of the Year 2026?", with 7,437 lifetime markets, showed F1 fired and a live score of 4/5.
- **Fix, matching rules/frozen_v1.md and src/v1_03_layer1.py.** Account start = `join_date`; if missing, the earliest of (the wallet's first `/v2/activity` row, its first fill in this market). The live scan now fetches the first `/v2/activity` row (same call as `src/v1_01_fetch.py _first_activity`) when `join_date` is missing, and tells `computeFeatures` that its earliest fill is not the wallet's first fill in the market (`first_fill_known: false`). If none of these is known, F1 is unknown: `F1_days = null`, the sign is not fired and not counted, and the UI shows "Account age unknown". It is never defaulted to 0. The frozen pipeline's behaviour is unchanged: with every fill available, the first fill in the market still counts, as in the Python code.
- **Tests.** `web/tests/flags-join-missing.test.ts` (4 cases: activity row present; all unknown in live mode; Python fallback parity; join_date present). All 27 tests pass, including the 20-wallet parity fixture, one of whose wallets has no `join_date`.
- **Display only.** Each live result now shows "Markets traded: N" (lifetime distinct markets from `/v2/user-stats`) and the account age at the wallet's earliest trade in the scan. No rule changed.
- **Cached demo regenerated** (`web/public/data/live_example.json`, re-scanned 2026-11-16). 0xa0f2...: account start from its first activity row, 238.2 days old, F1 not fired; live score 4/5 -> 3/5 (cheap, big, one-way). 0x5c29...: unchanged at 3/5 (join_date known, 3.5 days old). Both still cross the live line (3 or more of 5 and $2,500 or more), so the demo's market choice stands.

### 2026-11-17 - Product page: replay, watchlist, scan (presentation only)
- **Why.** Owner: product-first and calmer; plain modest copy; no em dashes anywhere in the UI.
- **What.** `/` is now: the problem, the six signs, a replay of the Maduro market (Jan 1 to resolution), a watchlist of six open markets decided by small groups, a scan box, and one line of limits with the GitHub link. The scrollytelling page is in `web/archive/`.
- **Replay data (`src/export_web.py replay()`, `maduro_replay.json`).** Every pre-news buy from 2026-01-01 00:00 UTC, merged per wallet within 30 min, with the wallet's score at that moment: the frozen `features()` from `src/v1_03_layer1.py`, run on the wallet's own fills up to that buy (the same recomputation the frozen pipeline uses for "first reached score >= 4"). Only F1-F5 are counted until the news; F6 shows "unknown until news". An alert is the first buy at which a wallet has 4 or more of those 5 signs and $2,500 or more bought. Result: four alerts in the window, at 30.0, 8.3, 2.3 and 0.4 h before the news; the first three are the CFTC/Lookonchain wallets and match the validation table's "first score >= 4" times. The first alert's wallet ranks 1st of 2,608. F2's denominator is the wallet's volume up to the news day, as in the frozen recomputation. Existing export outputs are unchanged.
- **Watchlist.** `web/lib/watchlist.ts` lists six open markets (TIME Person of the Year: Mamdani and Trump; Game Awards GOTY: GTA VI; Oscars Best Picture nomination: Dune Part Three; US invades Iran before 2027; Israel military action against Lebanon on Nov 26). `/api/watchlist` scans them with the fixed live scan and is cached for 6 hours (incremental regeneration); a snapshot is committed for offline use, and a Refresh button rescans in the browser. Snapshot of 2026-11-16: Mamdani 2 wallets worth a look, US invades Iran 1, the other four nothing unusual. The Grammy nomination market first chosen had already closed and was replaced. "Markets traded" is shown next to each wallet.
- **Em dash rule.** `tests/no-em-dash.test.ts` (source, shared copy, and data text after `clean()`) and `scripts/check-copy.mjs` (rendered HTML) run in `npm run build`; a planted em dash fails the build (checked). HANDOFF rule 1's disclaimer keeps its words with a colon instead of the em dash: "Unusual activity for review: this does not identify an owner or prove insider trading." HANDOFF.md itself still shows the em dash and may be updated to match.
- **Copy adjusted to stay accurate.** "Some Polymarket bets may be placed by people who already know the answer" (the brief had no "may"); "In the days before Jan 3, 2026" instead of "In January 2026" (its first buys were on Dec 31, 2025); "Rules based on published research" instead of "taken from" (two thresholds come from the project brief).
- **Design.** Yellow only for alerts: Sodium's yellow selected/checked/primary roles are remapped to its neutral roles inside a `neutral-controls` scope. One Sodium lint exception: the multi-line watchlist card is a native button. Body text 20px or more.
- **Checks.** 31 tests; Sodium lint clean; Lighthouse mobile 98/100/96; replay checked at 1920x1080 (10x), by keyboard, with reduced motion (manual steps) and at 390 px.

### 2026-11-17 - Decision: one flagging rule everywhere (4 or more of the signs that can be checked)
- **Problem.** The page said "Four or more: worth a look", but the live watchlist and scan flagged wallets at 3 of 5 (plus $2,500 or more), and the replay alert also required $2,500. Viewers would see two rules.
- **Decision.** One rule: worth a look = 4 or more of the signs that can be checked. With the news time known (research, the replay after the news) that is 4 of 6, the frozen high score. While a market is open, close-to-the-news cannot be checked, so live it is 4 of the other 5. No separate dollar floor: size is already one of the signs (Big bet, $2,500 or more). No frozen rule changed; this only removes the extra display filters added on 2026-11-16 and 2026-11-17.
- **Effect on the replay** (`src/export_web.py replay()`, alert = first buy with 4 or more of 5): 8 wallets reach 4 signs between Jan 1 and the news instead of 4. The new four are small wallets (about $780 to $860, flagged 51.4, 45.9, 32.7 and 22.2 h before the news); all are among the frozen high-score wallets. The CFTC-charged wallet is still flagged 30.0 h before the news and ranks 1st of 2,608. The closing line now says so, and that 5 of the 8 have never been publicly accused.
- **Effect live.** Watchlist snapshot (2026-11-16): no wallet reaches 4 of 5 in any of the six markets, so all six say "Nothing unusual" (before: 2 markets with wallets at 3 of 5). The scan and the watchlist detail then show the three highest scores in grey, with their signs as words and markets traded.
- **Copy.** Each sign now has a one-line rule with its frozen threshold; a worked example shows the Maduro wallet's six signs and values, "6 of 6. Ranked 1st of 2,608 wallets." ("ranked 1st" rather than "the highest": two Maduro wallets scored 6 of 6; rank breaks ties by money). "Every trade is public, but nobody is watching" became "Every trade is public." (journalists, Lookonchain and paid tools do watch). "New account" reads "7 days old or less" (the frozen rule is <= 7 days).
- **Also fixed.** After the news, the replay's alert card showed the final 6-sign score next to the signs as they stood at the alert; it now shows the final signs.
- **Checked.** Played the replay start to finish at 10x (26.6 s, 8 alerts in order, closing lines correct), 31 tests, Sodium lint clean.

### 2026-11-16 - Page rebuilt as one research story: who, where, how, model, findings, demo, limits
- **Why.** The owner asked for the page to carry the whole 5-minute presentation: define an insider, show where and how insiders trade, then the model and a live demo, with minimal text. The product page had the demo but no research behind the six signs.
- **Research added (all paraphrased, each line links its source; facts in `web/lib/research.ts`).**
  - *Who.* CFTC enforcement advisory (25 Feb 2026): insider trading is misappropriation of confidential information in breach of a duty of trust. Four cases, described by role and marked charged or indicted, not convicted: a US Army soldier (Maduro raid, over $404k, CFTC and DOJ, Apr 2026), a Google engineer (Year in Search, about $1.2M, May 2026), an Israeli air force reservist and a civilian (Iran strike, about $152k, indicted Feb 2026), a YouTube channel editor on Kalshi ($5.4k profit, fined and suspended, Feb 2026).
  - *Where.* ACDC: long-shot bets ($2,500 or more at 35 cents or less) win 14% of the time overall, 25% in political markets, 52% in military and defense markets. Markets decided by small groups show the most risk; markets decided by the public show the least.
  - *How.* Six behaviours with one line of evidence each (ACDC; Gomez-Cram et al.; the Google and Israel cases as reported). One stated exception: the Google engineer used an account opened in May 2024 across 23 markets, so the new-account and all-in signs would miss him.
- **Findings section (no new analysis; computed from the frozen exports at build time).** Headline numbers from `markets.json`; a new chart of how often each sign fires among the 7 distinct named wallets against all 7,139 pre-news buyers (new account 4 of 7 vs 13%, all-in 4 of 7 vs 2%, cheap price 6 of 7 vs 26%, big bet 7 of 7 vs 4%, one direction 6 of 7 vs 52%, close to the news 7 of 7 vs 41%); the v0 null in one sentence.
- **Limits stated on the page.** A flag is not proof; 264 flagged wallets have never been accused; the 7 of 7 is partly circular; old-account insiders are missed. The learned-weights model and the 10-market forward test are labelled "planned next", not done.
- **Kept.** Frozen rules, results, the replay, the watchlist, the scan, the 4-or-more rule, the no-em-dash test (now also covers `lib/research.ts`), wording rules (no wallet is called an insider; named people are not named, only roles).
- **Checks.** `npm run build` (31 tests, em-dash check) and the Sodium lint pass; rendered at 1920x1080 and 390 wide, no horizontal overflow; replay stepped to the end; outline anchors land under the sticky bar.
- **Not done.** Deployment (needs the owner's Vercel token): from `web/`, `npx vercel deploy --prod`.

### 2026-11-16 - Presentation fixes after the page moved into the 680px research column
- The owner's agent fitted the page to iyildiz.me/research (one 680px reading column, smaller type, no outline bar). Three layouts built for a wide screen broke inside it; fixed without changing any number or rule.
- **Replay.** The chart had shrunk to about 350px with unreadable axis labels. From 1024px up, the chart and its alerts now sit in a figure wider than the column (`.wide-figure`, up to 1080px, centred on the column); below that they stack in the column. When the replay ends, the wallet ranked 1st leads the alert list so its card is on screen.
- **Cases.** The five-column case rows wrapped badly; each case is now two lines: who and alleged profit, then the secret, status and source.
- **Watchlist.** Three cramped columns became two.
- **Presenting.** Body text is 16px, so present at 150% browser zoom on a 1920-wide screen; checked at that zoom, at 100% and at 390px wide, no horizontal overflow. Build, 31 tests and the em-dash check pass.

### 2026-11-17 - Page additions after proposal feedback: target group, gap, importance, public data
- **Why.** The proposal feedback asked the page to say who it is for, what gap it fills, why it matters and which public data it rests on. These are copy additions only; no number, threshold, rule, the replay, the watchlist or the scan changed.
- **Header.** One muted line under the intro: who the page is for (journalists, researchers and traders who watch these markets).
- **New section "The trades are public. The check is missing." (id `why`).** Three ruled rows, each sourced: why it matters (CFTC, Apr 2026 case), what is public (Polymarket docs, order lifecycle), what is missing (Bock and Guenthoer; Nechepurenko, arXiv 2605.00459). Text and links live in `web/lib/research.ts` (`WHY`, `SRC`).
- **Findings: "Four checks, one that held up".** Replaces the single v0 sentence with four ruled rows read at build time from the frozen exports, nothing hardcoded: v0 ripple 1.98 vs 1.58 extra wallets, p = 0.72 (No); named wallets 7 of 7 flagged, charged wallet ranks 1st of 2,608 (Yes, partly circular); timestamp permutation, 1,000 shuffles, Nobel 137 vs 88 expected, p = 0.001, Maduro and Iran no better than chance (Nobel only); layer 2 at 30 min, mean_diff -1.88 pooled and +8.93 Nobel, so fewer followers except in Nobel (Nobel only). All values matched the expected numbers.
- **Sources.** Polymarket docs and Nechepurenko (2026) added to the footer list.
- **Checks.** `npm run build` passes (31 tests, em-dash test already covers `lib/research.ts`, rendered-copy check). Rendered at 1280x720 at 150% zoom, 1920x1080 and 390 wide: no horizontal overflow; the replay figure stays wider than the column from 1024px up; p-values kept on one line. All four new source links opened and loaded (CFTC 9217-26, Polymarket docs order lifecycle, arXiv 2605.00459).

### 2026-11-17 - Faint background swirl
- Added the ASCII swirl from iyildiz.me/yvonne behind the page (`web/components/product/swirl.tsx`), white at 3% opacity so the page stays black and text contrast is unchanged. Runs at about 24 fps, pauses in hidden tabs, draws one still frame under reduced motion. Decoration only; no copy, number or rule changed.
- Swirl opacity raised from 3% to 6% on request.

### 2026-11-17 - Page rewritten as a short first-person article
- **Why.** Feedback: the page read as generic, with too many features and no story. It now reads like the other research articles on iyildiz.me/research: question, what the cases have in common, the check, what happened, why that is less than it sounds, what I take away, sources.
- **Removed from the page:** the live watchlist, the scan box, the headline tiles, the sign-rate bars, the long-shot bars and the ruled-row sections (why, who, where, how, four checks, limits). Their facts are kept as prose with the same `<Source>` links. The components and data files stay in the repo, unused by the page.
- **Kept:** the Maduro replay as the one figure, the sources list, the GitHub link and the "not proof" line.
- **No number, threshold or rule changed.** Every number is still read from the frozen exports at build time (rank 1st of 2,608; 30 h; 7 of 7; 264 others; Nobel 137 vs 88, p = 0.001; v0 1.98 vs 1.58, p = 0.72; layer 2 pooled fewer followers, Nobel more).
- **Checks.** Build passes (31 tests, em-dash check). At 1024, 1280, 1920 and 390 wide there is no overflow; the replay is 976 to 1080 px wide from 1024 up, column width on phones.

### 2026-11-18 - Model v2 started (data-driven detector + forward test)
- **Decision.** Task is a learned model v2 plus a pre-registered forward test. Rules from HANDOFF.md kept (wording "informed flow"/"worth a look", freeze before test, nulls reported plainly). `web/` not touched.
- **Decision.** Universe rule written and committed to `rules/model_v2_universe.md` before any v2 pull. Practical limits (min volume 20k, max 400 fill pages per market) are stated there in advance.
- **Process.** Branch is `claude/peaceful-gauss-q31p61`; `git pull origin claude/hopeful-mendel-tado7n` merged cleanly.

### 2026-11-18 - v2 step 1: market list
- **Problem.** Gamma `volume_num_min` is ignored; 3-day windows hit the 2,000-row offset cap in 95 of 224 windows (Nov 2025 onward). **Fix:** re-pulled those days one by one ordered by `volumeNum` desc (285 days, 298,700 rows). One day (2025-12-31) still hit the cap: a possible small gap among markets >= $20k.
- **Decision (Amendment A, universe rule).** Sample showed election/market-cap questions passing the keyword screen; added exclusion words and a cap of 3 markets per event. Done before any trade pull.
- **Decision (Amendment B).** Markets > $12M volume excluded up front (page-cap proxy); rank the rest by volume; fetch down the list until 160 succeed.
- **Count.** 4,309 text-qualified markets; 117 over $12M; 4,192 ranked. Exclusions per reason in `data/v2/exclusions.csv`. The keyword screen is imperfect (some non-qualifying questions pass, some qualifying ones missed); a read-through of the final set is in the summary.

### 2026-11-18 - v2 step 1: data pulled
- **Counts.** 165 markets fetched OK (all under 400 pages; none dropped, 0 HTTP errors in fills), 5,798,770 fill rows (maker+taker), 590,721 wallet x market x side units with a net-long position at close minus 1 h, 306,168 wallets. Category mix: 108 military/government, 35 company, 16 appointment, 3 award, 3 central bank. Fetch stopped at 165 not 160 because 6 workers were in flight.
- **Selection bias, stated.** Ranking by volume under the $12M cap means every market has $3.7M-$11.9M volume; no small markets. Fed meetings and the biggest war markets were excluded by the cap.
- **Data gap.** Wallet stats (join date, markets, lifetime volume) were fetched only for the 59,074 wallets with at least $100 bought in some unit (of 306,168); smaller wallets are not in the model. Fills after the cutoff: 8,938 (dropped). 244,312 units had buys but net position <= 0 at cutoff (sold out) and are not units.
- **Problem / decision (closedTime lag).** Gamma `closedTime` lags the real event: median market is already at 0.001/0.999 at close minus 1 h. Position at close minus 1 h is stored as asked (`*_cut`), but those buys are mostly after the outcome is public. I therefore also compute a decision time T_dec (rolling-median Yes price leaves (0.05, 0.95) for good) and the same position aggregates up to T_dec (`*_dec`). The model uses `*_dec`. T_dec uses the price path, so it is an ex-post marker of "news time", like v1's news timestamps; it is never a model feature.
- **Problem.** Wallet-stats script was O(n^2) after a restart (set rebuilt per item); fixed. A worker restart killed one fetch; the cache resumed with no loss.
- **Deviation (stricter than the brief).** Prior excess win rate uses only markets resolved before the wallet's FIRST BUY in this market (not before this market's resolution), so it is known at trade time. Shrinkage: mean excess x n/(n+5), n = prior units.
- **Approximations stated.** "Share of the wallet's volume in this event" = wallet's USD in this event's markets / its USD across all dataset markets up to its last pre-decision buy (dataset only, 165 markets). "Prior markets" = count in the dataset, not lifetime. "Hours before close" = hours from first buy to the scheduled `endDate`, because closedTime is unknown ahead and lags.

### 2026-11-18 - v2 steps 2-4: results, freeze
- **Result (stated plainly).** Unit-level model with price offset does not beat price on validation (log loss +0.0014 vs market, CI -0.0020 to +0.0043; n = 33,431 units, 49 markets). Market-level adjustment: Brier 0.1656 vs 0.1740 (n = 114 points, 47 markets) but the CI of the difference (-0.031 to +0.011) spans zero. Fitted gamma is negative. Treated as no demonstrated edge.
- **Persistence.** Top-5% 2025 wallets (n = 89; mean excess +0.30) -> 2026: +0.037 (n = 57 wallets, CI -0.047 to +0.115) vs other wallets -0.016. Difference +0.053, CI -0.030 to +0.128. Not distinguishable from zero; heavy regression to the mean.
- **Decision.** Market-level evaluation points = 25/50/75% of life at which price still in 0.03-0.97 (only undecided markets are scorable, as in the forward test). Unit scores in the training-set market-level fit are 5-fold out-of-fold by market.
- **Caveat.** Features share_event and size ratios use positions as built up to T_dec, so market-level scoring at earlier evaluation points leaks a little future position-building; stated limitation.
- **Freeze.** `rules/frozen_v2.md/.json` written after seeing validation results (stated in the file). No parameter changed afterwards. Forward test is the only clean test.

### 2026-11-18 - v2 step 5: forward test locked
- **Decision.** Pre-registration (`prereg/forward_test.md`) committed before selection. Selection by rule: 300 open markets pulled, 28 pass screen (1 per event), top 10 by volume with price in 0.03-0.97 (5 skipped for price outside the band). Snapshot 2026-11-18T00:58:42Z. Locked CSV SHA-256 b0c2eec2...e480fb written into the prereg file; pushed right away.
- **Problem.** First push was rejected (GitHub 100 MB limit): a 1.6 GB intermediate `data/raw/v2_gamma_all.json` had been committed locally. Removed from the unpushed local history with filter-branch and added to .gitignore; only unpushed commits were rewritten. Commit times of the pushed commits therefore come from the push, not the original local commit.
- **Note.** The selection includes one election-like market (Spanish PM) because the mechanical screen allowed it; not removed after the fact. `scripts/score_forward_test.py` written, not run.
- **Summary** in `data/results/v2_summary.md`: verdict is no demonstrated edge.

### 2026-11-18 - web: v2 and forward-test sections
- **Change.** Added `src/export_web_v2.py` (writes `web/public/data/v2.json` from `data/results/v2_analysis.json`, `data/v2/units.csv.gz`, `prereg/forward_test_locked.csv` and the git commit of the locked file; no hand-typed numbers). Page: replaced the "Next I want to learn..." sentence with section `v2` ("Next model: let the data choose the weights.") and added section `forward` ("Ten predictions, locked before the outcome."). Layout and 680px column unchanged.
- **Decision.** Verdict shown is "No", as `v2_summary.md` says (the model does not beat the market price). The market-level Brier difference is -0.008 with an interval from -0.031 to +0.011, shown as is. Persistence shown as a null: the gap between 2025 winners and others in 2026 has an interval that includes zero. Largest coefficient (conviction) is negative; the other two largest have intervals that include zero, and the page says so.
- **Note.** "Wallets learned from" is the training split only (106 markets, 32,624 wallets); 49 later markets were used for validation. Training wallet count is computed in the exporter from the units table.
- **Checks.** `npm run build` passes (tests, build, em dash check). No horizontal overflow at 1280, 1920 or 390 wide.

### 2026-11-24 - Page rewritten as a methods paper
- **Why.** Feedback: the page should show the methodology, not only the story, and match the other research write-ups on iyildiz.me/research (formal title, numbered sections, equations, tables, figures, code).
- **What.** Title from the README ("Detecting Potential Insider Trading on Polymarket"). Eleven numbered sections: background, data and pre-registration timeline, v0 ripple (not supported), Layer 1 features and score, validation against documented wallets (with the replay), timestamp permutation null, precision proxies and sensitivity, Layer 2 sign-flip design, v2 model with the price offset and ridge penalty, the forward-test pre-registration, limitations. Equations typeset on the server with KaTeX; code cells are excerpts of `src/v1_03_layer1.py`, `src/v1_04_layer2.py` and `src/v2_06_analysis.py`, highlighted on the server with Prism. Figures 2, 4, 5 and 6 from `figures/` with their titles removed (the page numbers its own figures) and the two footnotes that contained an em dash cut.
- **Data.** `src/export_web_v2.py` now also writes a `model` block to `v2.json` (all eight frozen coefficients with their bootstrap intervals, the lambda grid, N and gamma). Rerun; every other field of `v2.json` is byte-for-byte identical in content. No number, threshold or rule changed; every number on the page is read from the exported files at build time.
- **Removed from the page** (code kept): the Why/Who/Where/How row components and the plain-language v2 coefficient list; their facts are in the prose with the same `<Source>` links. The watchlist and scan box were already off the page.
- **Checks.** `npm run build` passes (31 tests, rendered-copy em-dash check). At 1280x720 @1.5, 1920x1080 and 390 wide: no horizontal overflow, the replay is 1080 px wide from 1024 up, all figures load, 14 equations rendered.

### 2026-11-24 - Gate 1 feasibility check (draft episode definition, counts and power only)
- **Blindness.** Outcomes were not looked at. No won/lost flag, outcome price, payout, PnL or win rate was loaded, joined, printed or computed. Outcome columns (`yes_won`, `won`, `excess`, `prior_excess`, `yes_px_at_cutoff`, `yes_px_at_dec`, `resolution`, `after_resolution`) are dropped at load in `src/feasibility_gate1.py`, which asserts they are absent. Resolution dates are used only to assign the period. `web/` not touched. Nothing fetched.
- **Problem (data).** The v2 fill cache `data/raw/v2_fills/` is git-ignored and was never committed, so it is not in this container. **Decision:** no re-fetch (the brief says fetch nothing new). v1 markets (Maduro, Nobel, Iran) are exact from `data/clean/v1_fills_*.csv`, with T_dec = first news time. For the 165 v2 markets, counts come from a stated PROXY on `data/v2/positions.csv.gz`: net-long-at-close units only; all pre-T_dec buys within 24 h; no sells; t_a = last pre-T_dec buy; p_a = the wallet's own buy VWAP. The proxy undercounts, and its p_a is not the specified p_a. The script switches to exact results by itself once the 165 fill files are back. Re-pulling them takes about 5,881 pages, about 21 worker-minutes.
- **Definition choices (the draft left these open).** Net buys = buy USD minus sell USD of the same token by the same wallet in the 24 h window. VWAP = the wallet's buy VWAP in that window. A trigger is a rising edge at a buy fill. Episodes chain same-side triggers that are <= 24 h apart. p_a is taken from fills strictly after t_a; the fallback is the last fill strictly before t_a, then the trigger fill.
- **Result (main definition, t_a < T_dec; v2 proxy plus v1 exact).** 111 markets with at least one episode, 211 episodes. Pooled MDE of the market-level mean excess is 0.084 if episodes are independent and 0.099 if they are fully correlated within a market. Military/government is the only category with real power (81 markets, MDE 0.10 to 0.12). Company: 21 markets, MDE about 0.20. Appointment, award and central bank are underpowered (<= 6 markets each; central bank has 0). The 2026-05-06 to 2026-10-31 period is thin in every category. With t_a < T_dec - 24 h: 73 markets, MDE 0.10 to 0.13.
- **Integrity.** All 165 fetches 'ok', max 160 pages (cap 400), T_dec present for all. 14 v2 markets have T_dec less than 24 h after the first fill (no usable pre-decision period); 2 of these also have their last fill more than 2 days before close. The Gamma open date was not saved for v2, so first fill stands in for the open.
- **More markets.** 4,027 of the 4,192 ranked candidates are not fetched: 1,835 military/government, 1,596 company, 212 appointment, 143 award, 241 central bank. The estimate is about 9,300 pages, under 1 worker-hour (allow 2x). Another 117 markets over $12M were excluded by Amendment B.
- **Output.** `data/results/feasibility_gate1.md` and `.json`.
### 2026-11-24 - Methods page simplified
- **Why.** Feedback: the methods page was too dense (fourteen equations, bright repo figures, formal phrasing) and read unlike the other research write-ups.
- **What.** Ten shorter sections in plain first-person prose; three equations (the score, the permutation p-value, the offset logit model); two new server-drawn charts in the site's greys (the permutation null per market, and Layer 2 follow-on differences with intervals) replace the four repo figures; three code cells kept. Dropped from the page: the v0 ripple formula and table, the firing-rate, precision, sensitivity and Layer 2 tables, the market-level gamma formula and the pre-registration timeline table (the rule files remain the record). No number, threshold or rule changed; every number is still read from the exported files.
- **Checks.** Build passes (31 tests, em-dash check); 1280 @1.5, 1920 and 390 wide: no overflow, replay 1080 px wide from 1024 up.

### 2026-11-25 - v3 data step: fills re-pulled and extended; Gate 1 feasibility rerun on exact fills
- **Blindness.** Outcomes were not looked at. No outcome, resolution, payout, PnL or win rate was loaded, printed or computed. Gamma JSON is read through a whitelist that drops `outcomePrices` and every other outcome field on parse. The FFIC file's `resolution_outcome` column is dropped at load, and the parenthetical notes in three FFIC labels (which mention a result) are stripped. T_dec uses the price path but no post-T_dec price is stored. Resolution dates are used for periods only. `web/` not touched. Gate 1 was not run.
- **Targets** (`src/v3_00_targets.py` -> `data/v3/targets.csv`): 2,080 markets. They are the 165 v2 markets (re-pull), 1,835 military/government markets in v2's ranked list not fetched by v2, 58 military/government markets over $12M (Amendment B exclusions, no page cap), v1 Maduro/Nobel/Iran (Maduro and Nobel overlap the sets above), and the FFIC markets. Event id = Gamma event id. Series id = the Gamma series of that event where one exists (Gamma often gives "by Friday" and "by Sunday" separate events in one series). Gamma metadata: 1,635 requests, 0 errors.
- **FFIC** (ForesightFlow/datasets, `ffic-inventory/ffic-v1.csv`, commit 5ba4127, CC-BY-4.0, companion to Nechepurenko 2026; public repo, read by anonymous clone). 32 markets in 8 cases, given as 8-hex prefixes. **All 32 matched** to full condition ids: 14 via v2's candidate list, 18 via Gamma `public-search` (the 4 US-2024-election markets needed the case title as the query). Detail in `data/v3/ffic_match.csv`. 11 FFIC markets are also in the core set. The other 21 (2024 elections, Romania, Bitcoin ETF, SBF/FTX, Iran Oct 2024, some Venezuela markets) are fetched and reported in their own block, not in the core tables. Elections are outside the v2 universe rule.
- **Fetch** (`src/v3_01_fetch.py`, same request settings as `src/v2_02_fetch.py`: `/v2/trades?condition=&taker_only=false`, limit 1000, newest-first cursor). 6 workers; any error pauses all workers with doubling backoff. **30,753 requests, 2 errors (network ProxyError, both retried fine), 4 s of pause, 2,330 s (39 min) total.** All 2,080 'ok'. Largest page count: 5,110 (FFIC "Will Donald Trump win the 2024 US Presidential Election?", 5.1M fills); largest in the over-$12M military set: 386; no v2-rule market reached 400 pages. 29.5M fills after de-duplication, 978 MB on disk.
- **Check.** The 165 re-pulled v2 markets have exactly the raw row counts v2 logged (165 of 165 identical).
- **Storage (decision).** Fills stay outside git in `data/raw/v2_fills/` (git-ignored). The committed manifest is `data/v2/fills_manifest.csv` (market id, source, event id, series id, category, page cap, status, pages, rows, first and last fill, exclusion). `python src/v3_01_fetch.py --manifest` re-fetches every file that is missing or whose row count differs. It is resumable (cursor saved after every page). Tested: "0 of 2080 files missing or different".
- **Exclusions** (`src/v3_02_markets.py` -> `data/v3/market_info.csv`). T_dec within 24 h of the first fill -> excluded, "no usable pre-decision period". That is 245 markets (238 core, of them 14 of the 165, 223 of the new military set; plus 7 FFIC-only). No other exclusion was needed.
- **Fix.** The first Gate 1 report counted Nobel twice: it is a v1 market and one of the 165. Each market is now counted once; v1 markets keep T_dec = first news time.
- **Gate 1 feasibility rerun** (`src/feasibility_gate1.py`). The episode code is unchanged. Changes: exact fills only (proxy removed), the new markets, exclusions applied, and power with the event as the unit (episodes pooled within a Gamma event, then averaged across events). A series row is added as a sensitivity check. Main definition, t_a < T_dec, core universe: 556 markets in 443 events with at least one episode, 2,083 episodes. Pooled MDE: market 0.036 to 0.046, event 0.039 to 0.052, series 0.063 (corr.). Military/government: 517 markets in 411 events, MDE 0.041 to 0.054 by event. In P2 alone (2026-05-06 to 2026-10-31): 73 events, MDE 0.080 to 0.123 by event. Company: 23 events, MDE 0.15 to 0.23. Appointment, award and central bank stay underpowered (<= 7 events each). With t_a < T_dec - 24 h: 371 events, MDE 0.043 to 0.058 by event.
- **Still not pulled.** 2,188 of v2's ranked candidates, none military/government: company 1,593, appointment 212, award 142, central bank 241. Plus 59 over $12M in non-military categories.
- **Output.** `data/results/feasibility_gate1.md`/`.json`, `data/v2/fills_manifest.csv`, `data/v3/{targets,ffic_match,market_info,fetch_log}.csv`, `data/v3/fetch_run_log.json`, `data/v3/gamma_meta_log.json`.

### 2026-11-25 - Gate 1 frozen (before any outcome was loaded)
- **Decision (user: "freeze and run Gate 1").** The frozen test is written to `rules/frozen_gate1.md`/`.json` and committed and pushed before `src/gate1_run.py` loads any outcome.
- **Frozen.** Primary: core universe, main definition, t_a < T_dec, event as the unit, mean of (outcome - p_a), 95% event bootstrap CI (10,000 resamples, seed 20261125). POSITIVE if CI > 0, NEGATIVE if CI < 0, otherwise NULL. Secondary analyses are listed in advance and decide nothing.
- **Inputs fixed by hash.** `src/feasibility_gate1.py` now also writes the blind episode table `data/v3/episodes.csv.gz` (no outcome). The feasibility report is byte-identical after this change. Hashes of the episode table, `market_info.csv` and the script are in the freeze file; the run script checks them before loading outcomes.
- **Stated.** The 165 v2 markets' outcomes were used in the v2 model work (2026-11-18). A secondary row separates them from the markets new in v3.

### 2026-11-25 - Gate 1 run (once, as frozen)
- **Run.** `src/gate1_run.py` was run once after the freeze commit b7b8d63 was pushed. Input hashes matched. No code, parameter or data was changed after the outcomes were loaded.
- **Primary result: NULL.** 443 events, 556 markets, 2,083 episodes. Event-level mean excess -0.008, 95% CI -0.038 to +0.023, t-test p = 0.61. Alert sides do not win more often than the price right after the alert implies, at an MDE of about 0.04 to 0.05.
- **Stated plainly.** At the episode level the alert side won 0.231 vs a mean p_a of 0.206 (+0.025). Weighting each event equally gives -0.008. The frozen estimator is the event one; the episode-level gap is driven by events with many episodes and is not the test.
- **Secondary (decide nothing).** Every CI includes zero: market unit, series unit, 24 h-before-T_dec, the three variants, every category and both periods. Markets new in v3 (out of sample): -0.021 (CI -0.055 to +0.014). v2's 165 markets: +0.034 (CI -0.022 to +0.093); these were seen in the v2 work. Calibration bands 0.2-0.4 show +0.05; descriptive only.
- **FFIC (descriptive only).** The 2026 US-Iran cluster shows +0.69 mean excess (5 markets, 33 episodes with outcome). Venezuela/Maduro cluster: -0.12 (30 episodes); SBF/FTX: -0.05 (9). These are hindsight-selected documented cases, not a test. FFIC markets outside v2's candidate list have no outcome in this data and were not looked up.
- **Output.** `data/results/gate1_result.md`/`.json`.

### 2026-11-26 - Gate 2 frozen (two behavioural signals; no Gate 2 outcome loaded)
- **Blind step.** `src/gate2_signals.py` builds the ladders and the Signal A, Signal B and B_last episodes for $1,000, $2,500 and $10,000 in std and live modes. It then computes counts and power from p_a only; no outcome is loaded. It writes `data/v3/gate2_ladders.csv`, `data/v3/gate2_episodes.csv.gz` and `data/results/gate2_power.md`/`.json`. The cache was intact (2,080 files); no fetch.
- **Ladders.** 73 ladders, 311 markets. Only "by/before" questions count; "in <month>", "on <day>" and "between" are separate periods. A ladder is one Gamma series (else event) with the same question stem, overlapping lives and >= 3 deadlines. **Limitation:** only cached rungs; v2's 3-per-event cap hides some later deadlines.
- **Blind power ($2,500, std, event unit, MDE at 97.5% two-sided / 80%).**
  - A: 242 events, 537 episodes, MDE 0.073 to 0.087.
  - B: 110 events, 645 episodes, MDE 0.078 to 0.114.
  - B_last: 26 events, MDE 0.18 to 0.26.
- **Definition choices (the brief left these open).**
  - "Before the trigger" sums use fills with a strictly earlier timestamp, and the higher-price buy must have a timestamp strictly after the first buy. This keeps one order sweeping the book from triggering itself.
  - Sells < 10% and net buys are in USD.
  - The B trigger is a rising edge.
  - p_a fallback as in Gate 1.
  - "Live-realistic" = fills up to resolution - 1 h, excluded markets included, no t_a < T_dec rule.
  - Gate 1 overlap = same market and side within 24 h.
  - Examples are picked by wallet count before outcomes.
- **PASS rule.** Estimate > 0 and lower bound of the 97.5% interval (percentiles 1.25 and 98.75, seed 192) > 0.
- **Stated.** These signals were proposed after the Gate 1 NULL on the same markets.
