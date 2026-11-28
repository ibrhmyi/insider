# Collection protocol: documented suspected informed trading in prediction markets

Version 1.0, frozen 2026-11-26 before the systematic search. Changes after this date are listed in the amendments section at the end, with the date and the reason.

## 1. Question

Which trades, wallets and accounts on prediction markets (Polymarket, Kalshi, and others) have been publicly alleged, charged, sanctioned or analysed as trading on non-public information about the outcome, between 2020-01-01 and the search date?

## 2. Definitions

- **Claim:** one statement, by one source, at one time, that a specific account, wallet, cluster or market saw suspected informed trading. The unit of collection.
- **Case:** one underlying event (for example "US strikes Iran by Feb 28 2026"). Many claims can describe one case.
- **Subject:** what a claim points at: a wallet address, a username, a cluster, or a whole market.
- **Informed trading:** trading on material non-public information about the outcome, including the person's own planned action. Wash trading, oracle or resolution attacks, and reference-data tampering are recorded as separate families, not as informed trading.

## 3. Sources searched

| Code | Source class | How it is searched |
|---|---|---|
| S1 | Official: DOJ, CFTC, SEC, state AGs, foreign courts and police, Kalshi regulatory notices, Polymarket integrity statements, congressional letters | Site searches and press releases |
| S2 | Research: academic papers (arXiv, SSRN, NBER, journals), NGO and industry reports (ACDC, Inca Digital, Solidus Labs, Chainalysis) | Citation chasing from each paper |
| S3 | Press: wire services, national papers, crypto press | Web search, query list in `logs/search_log.csv` |
| S4 | On-chain analysts on X (Bubblemaps, Lookonchain, Polysights, DefiOasis, PolymarketStory, ZachXBT, others found) | Posts cited by S2 or S3, and direct X search where available |
| S5 | Code and data: GitHub, Hugging Face, Dune, Kaggle | Keyword search; every repo with a list of flagged wallets is cloned and its commit hash recorded |

Every query, its date, and the number of new claims it produced is logged in `logs/search_log.csv`. Searching stops for a topic when two consecutive queries return no new case.

## 4. Inclusion and exclusion

Include a claim when all hold:
1. It names a prediction-market platform.
2. It points at a specific subject (address, username, cluster, or market with a described trading pattern).
3. It alleges or analyses informed trading (or one of the separate families in section 2).
4. Its date and author or outlet can be recorded.

Exclude: anonymous forum posts with no traceable author; claims only about general risk; copies of an earlier claim with nothing new (logged as `duplicate_of`); paid copy-trading promotions.

## 5. Evidence grades (per claim)

| Grade | Meaning |
|---|---|
| E1 | Adjudicated: conviction, plea, or final regulatory or platform sanction |
| E2 | Charged or formally sanctioned: indictment, complaint, platform disciplinary notice |
| E3 | Official inquiry reported: referral, investigation, FOIA-confirmed inquiry |
| E4 | Analyst with transaction-level evidence: on-chain links, funding paths, fills |
| E5 | Analyst or journalist pattern claim: timing, account age, win rate, without transaction-level links |
| E6 | Rule-based flag: meets a published screening rule |

A case's grade is the strongest grade among its claims. A wallet's grade is the strongest claim that names that wallet directly. A wallet only linked to a graded wallet by money flows gets `link_only`.

## 6. Extraction fields (per claim)

claim_id, case_id, platform, family, subject_type, subject (address or handle or market), claim_text (our paraphrase, under 30 words), evidence_grade, amount_claimed_usd, n_accounts_claimed, event_date, claim_date, source_class, source_name, author, url, archive_url, accessed_date, cites (claim_ids or URLs it relies on), duplicate_of, extractor, verified_by, notes.

Addresses are copied from the source text and checked for 40 hex characters. A prefix only (for example 0x88e6) is stored as a prefix, never extended by guessing.

## 7. Verification

- Every address is checked twice: once at extraction, once by a script that re-reads the source file or page.
- A case's amounts are recorded per claim. Where sources disagree, all values are kept and the disagreement is flagged, not averaged.
- Wallet-to-person mapping is never made by us. Where a claim maps an account to a charged person, the mapping is recorded with its source and grade.
- A 20% random sample of claims is re-extracted blind from the source; agreement is reported.

## 8. Bias statement

The collection reflects what was noticed and published. It over-represents large, fresh-wallet, long-shot wins on geopolitical and viral markets, and under-represents informed trading that looks ordinary. Users must not estimate the prevalence of informed trading from it.

## 9. Ethics

No personal names in data tables. Court records are referenced by URL and case number. No attempt is made to identify the people behind wallets. Rows are removed when their only source is retracted.

## Amendments

**A1 (2026-11-26, during the first run).** X was not searched directly: the collection environment had no X access. X posts enter only when a press article, report or repository cites them (source class S4 via S3 or S5). A direct X sweep is listed as open work. This biases the collection toward claims that reached the press.

**A2 (2026-11-26).** Automated alert feeds (bots that post every fresh-wallet bet, such as PolyBeats) are excluded, because they make no human judgement. One such alert was seen and not recorded.

**A3 (2026-11-26).** Wikipedia and explainer sites (nextpredict.io, polymarkets.co.il) are used only to find cases. A claim taken from them is recorded with them as the source and graded no stronger than the primary source they cite.

**A4 (2026-11-26).** The 20% blind re-extraction in section 7 has not been done yet; it needs a second extractor who did not do the first pass. `verified_by` is empty until then.

**A5 (2026-11-26, before run 2).** Run 2 has no X API either. X posts are searched through web search engines (queries of the form `site:x.com <account> polymarket` and `site:x.com polymarket insider`) and through pages that quote them. Each such claim is recorded as source class S4 with `via=search_engine` in `notes`, and the post URL as `url`. This is a partial sweep: A1 stays open until X is searched directly.

**A6 (2026-11-26, before run 3; written before any run-3 data was pulled).** Verification status, provenance columns, partial dates, and the rules for the run-3 data build (markets, fills, money graph, rule labels, controls, episodes). Run 3 is the first run to build trade-level tables.

*A6.1 Claim status.* Run 2's X sweep reached posts only through search-result snippets: the quoting pages could not be opened and no post URL was recovered. `claims.csv` gets a column `verified`:
- `true`: the extractor read the source text (all run-1 rows, as recorded by the run-1 extractor; not re-checked, and not the same as the A4 blind re-extraction, which stays open);
- `pending`: snippet-only (CL0085 to CL0092). It becomes `true` only after the page is read and, for S4 rows, the post URL is recovered;
- `false`: the page was read and does not support the row.
Pages to read are listed in `logs/needs_page_read.csv`.

*A6.2 Run column.* `claims.csv` gets `run` (1, 2, 3, ...): the collection run in which the row was added. Run 1 = CL0001 to CL0084; run 2 = CL0085 to CL0092.

*A6.3 Partial dates.* `event_date` and `claim_date` may be `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, or a range `A/B`. They are compared by their earliest possible day (a range by the earliest day of `A`). `cases.csv` reports a `*_precision` column (`year`, `month`, `day`, `range`).

*A6.4 Trade source.* Fills come from Polymarket-v1 on Hugging Face (`TimeSeventeen/Polymarket-v1`, commit recorded in the manifest), cleaned layers `daily_aligned/` and `daily_aligned_multi/` (relayer records removed), up to the last timestamp in that dataset (2026-04-28). After that, the Polymarket Data API v2 is used. Every row records `source` (`hf_polymarket_v1` or `data_api_v2`). The raw `OrderFilled/` layer is not used.
- Side convention: the taker is the aggressor. The taker's side is `taker_direction` on the traded token. The maker's side is the opposite on the same token.
- Because of mint and merge matching, a taker SELL of one outcome can economically be a BUY of the other; this is recorded, not corrected.

*A6.5 Case markets.* A case's markets are found by Gamma search (question text and dates), FFIC market-ID prefixes, and the markets that the case's own claimed wallets traded. Each market row records its `found_via`. The deadline ladder is every market in the same Gamma event. No market is attached to a case by guess: if the claims do not identify the market, the case is logged as `no_market_found`.

*A6.6 t_news.*
- If ForesightFlow `polymarket-tnews-tevent-recovery` has the market at tier 1 or tier 3, use it (`method=ff_tier1` or `ff_tier3`).
- Otherwise use `claim_min`: 00:00 UTC on the earliest possible day among the case's claims' `event_date` and `claim_date` (the event itself is the first public report for event markets). Precision is kept.
- ForesightFlow tier 2 (`resolved_at - 24h`, which its own README says is unsuitable for single cases) is stored in a separate column and not used.

*A6.7 Wallet checks.* A wallet "traded its case market" if it has at least one fill in any market attached to its case in `markets.csv`. Failing wallets are flagged, never deleted. A case-insensitive handle match (a run-2 failure) is accepted only if that profile bought the claimed outcome in a case market between the market's creation and the case `event_date` (inclusive). The evidence goes to `logs/handle_checks.csv`.

*A6.8 Money graph.*
- Polygon USDC.e (`0x2791bca1f2de4661ed88a30c99a7a9449aa84174`) and native USDC (`0x3c499c542cef5e3811e1192ce70d8cc03d5c3359`) `Transfer` logs to and from each suspected address, from a public Polygon RPC.
- Counterparty tags come only from listed sources: Polymarket contract addresses published in Polymarket's documentation, the seed `wallet_edges.csv` kinds, and the source repositories. Anything else is `unknown`.
- A counterparty with more than 500 distinct USDC counterparties is a `hub` and is not expanded. Counting stops at 501.
- One hop: a non-hub address that funded (sent to) or received cash-out from a suspected wallet links it to any other address it transacted with that has Polymarket trading activity (Data API v2 activity not empty). Such an address becomes `L4_graph_expanded`, `polarity=candidate`, never `suspected`.

*A6.9 Rule labels (E6, never merged with claims).*
- **ACDC longshot:** one wallet's BUY fills on one token within one clock hour (UTC), summing to $2,500 or more at a volume-weighted price of 0.35 or less, on a market resolved in the Hugging Face metadata. Clock hours replace a rolling window so the computation is exact per day file.
- **ACDC market type:** `category_refined`.
- **Orca:** longshots in 1 or 2 market types and a longshot win rate of 75% or more.
- **Military Orca:** an Orca with at least half of its longshots on markets whose slug matches `strike|military|attack|invade|invasion|ceasefire|missile|troops|war|bomb|airstrike|nuclear|drone|army|navy|forces|khamenei|regime`.
- **Validation:** compared with the published counts (78,496 longshot bets, 12,355 wallets, 556 Orcas, 152 military Orcas, data to 2026-05-05). Our data end 2026-04-28; the gap is reported. If any count differs by more than 5%, the reconstruction is published as a reconstruction but not used as a label.
- **Inca Digital:** 10 or fewer distinct markets and realised PnL of $30,000 or more. PnL = sell proceeds − buy cost + winning shares held at resolution, on resolved markets only. Splits, merges, redemptions and fees are ignored; the bias this causes is reported.

*A6.10 Controls.*
- An episode is (wallet, condition_id, outcome token) with at least one BUY before t_news. First buy = its first BUY fill. Size = BUY USDC on that token before t_news.
- Controls come from the same market and token, with first buy within 24 h of the episode's first buy, first-buy price within ±0.05, and size within 0.5× to 2×.
- Excluded: any address in `wallet_labels`, `wallet_labels_expanded`, or flagged Orca or Inca in `weak_labels`.
- If fewer than 10 qualify, relax in this order and record which relaxation was used: window 72 h, then price ±0.10, then size 0.25× to 4×.
- Plus up to 10 of the largest pre-t_news buyers of the other outcome token whose first buy is within 24 h.
- Sampling uses seed 192.

*A6.11 Episode features* follow `build/PIPELINE.md` step 7, computed from fills before t_news, except columns ending in `_post`.

**A7 (2026-11-26, run 3, after building `markets.csv` and before computing any feature, control or episode that uses t_news).** A6.6's `claim_min` changes to: t_news is the earliest of
- every day-precision `event_date` of the case's claims;
- every day-precision `claim_date`;
- if the case has no day-precision `event_date`, the earliest possible day of its coarser event dates.

Coarse (month, quarter, year, range) claim dates are ignored. Precision is kept.

*Reason:* a report cannot precede the event it describes, so the event date is the anchor, and a claim date can only move t_news earlier. Under A6.6, a month-only claim date put t_news on the first of the month. In the Maduro case that was 2026-01-01, two days before the operation, so the trades at issue would have counted as post-news.

*A rejected first draft* ("earliest day-precision date of either kind, else the earliest coarse date") was tried on `markets.csv` and not adopted. Where the event date is coarse, it moved t_news to a much later claim date: ftx-sbf, romania-2024 and biden-pardons to 2026, and kpmg-earnings to 2026-11. The changes are listed in `logs/run3_report.md`. No other part of A6 changes.

**A8 (2026-11-26, run 3, before any Polygon transfer data was pulled).** Details of the A6.8 money graph that A6 left open.
- *Reason:* the reachable public RPC (`polygon-bor-rpc.publicnode.com`) serves at most 10,000 blocks per `eth_getLogs` call, so all-time histories are not practical. A per-address window is set instead.
- *Window:* from the proxy's Gamma profile `createdAt` (or one day before its first Data API activity if it has no profile) to 30 days after its last Data API activity. Transfers outside the window are not seen; this is reported as a limitation.
- *Funder / cash-out:* a funder is an address that sent USDC or USDC.e to the suspected wallet in its window. A cash-out address received USDC or USDC.e from it.
- *Hub test:* for each funder or cash-out address, distinct counterparties are counted over the union of the windows of the suspected wallets it touches. Counting stops at 501, and such an address is a hub.
- *Polymarket contracts:* the addresses listed in Polymarket's developer documentation (docs.polymarket.com) are tagged `polymarket_contract` and are never hubs or candidates.
- *One hop:* every other address that transacted with a non-hub funder or cash-out address in that window, and has at least one Data API v2 activity row, is a candidate (`L4_graph_expanded`, `polarity=candidate`). Addresses already in `wallet_labels.csv` are not candidates.
- *Edges:* every edge records the transaction hash, block, token, amount and direction.

**A9 (2026-11-26, run 5, before computing the fields below).** Stance, investigation outcome, and minute-level market paths.

*A9.1 Stance.* `claims.csv` gets `stance`, one of:
- `alleges` (the default);
- `disputes`: argues against the inference of informed trading or against a wallet attribution;
- `clears`: says an investigation found no inside information, or the case is a declared negative control;
- `context`: describes the market or the event without alleging anything.

`clears` also records `clearing_party` in `notes`: `official`, `platform` or `analyst`. Stance is read from the claim text; it never changes the claim or its grade.

*A9.2 Investigation outcome.* `cases.csv` gets `investigation_outcome`, taken in this order of priority:
1. `sanctioned`: any E1 claim.
2. `charged`: any E2 claim.
3. `cleared_official`: a `clears` claim whose clearing party is an official body or the platform.
4. `cleared_analyst`: a `clears` claim from an analyst or repository, including negative controls.
5. `disputed`: any `disputes` claim.
6. `under_investigation`: any E3 claim.
7. `unresolved`: otherwise.

The order puts adjudication above everything else and a clearing statement above a mere dispute. Cleared and disputed cases are the closest thing to negatives in the collection; they are labels, not findings.

*A9.3 Minute-level market paths.* `out/market_minutes.parquet` has one row per case market per UTC minute, from 48 hours before t_news (A6.6 and A7, as in `markets.csv`) to 24 hours after.

| Column | Meaning |
|---|---|
| `n_fills` | fills in the minute |
| `usdc` | volume |
| `vwap` | volume-weighted price |
| `last_price` | last trade price |
| `taker_buy_usdc`, `taker_sell_usdc` | aggressor buy and sell volume (HF fills only; Data API fills have no aggressor) |
| `n_wallets` | distinct wallets |
| `n_new_wallets` | wallets whose first Polymarket-v1 fill was within the previous 7 days |

Minutes with no fills are left out. The table covers the outcome token of each market whose label is `Yes` (or the first outcome where no `Yes` exists).

**A10 (2026-11-26, run 7, before any run-7 table is computed). Exact news times (decision D1).**

*A10.1 Two news times.* Every market keeps the day-level `t_news` of A6.6/A7 unchanged. It also gets `t_news_precise`:
- the earliest `t_utc` among the case's rows in `data/event_times.csv` whose `t_precision` is `minute`, `approx_15min`, `approx_hour` or `window_<start>-<end>` (the window start is used), and whose `url` is not empty;
- if the case has no such row, `t_news_precise` = `t_news`, with `t_news_precise_source = day_fallback`. A day-start time is never later than a same-day exact time, so the fallback can only count fewer trades as pre-news.
- `t_news_precise_precision` is `minute`, `quarter_hour`, `hour`, `window` or `day_fallback`. `t_news_precise_verified` copies the row's `verified` value (`pending` rows are used, and flagged).
- If the exact time falls before the day-level `t_news` (for example a first report the evening before), it is used as is; it is a better estimate of the first public moment and makes the pre-news set smaller.

*A10.2 Every time-dependent table carries both.* Positions, episodes, controls, minute paths, coordinated-buyer candidates and the benchmark features are computed once per version. They carry `t_news_version` (`day` or `precise`), `t_news_utc`, `t_news_precise_utc` and `t_news_precision`. Neither version replaces the other.

*A10.3 Provenance of the times.* `data/event_times.csv` was compiled in run 4 (commit 6c68ee5) from search-result text, before any episode, control or feature under `t_news_precise` was computed (none had been). Run-7 rows are added and committed in a separate commit before the run-7 rebuild; each records `added_run`. A time is never chosen by looking at the trades: the source states it, or it is not added.

**A11 (2026-11-26, run 7, before re-checking any handle). Pseudonym matches (decision D6).**
- A handle from a claim resolves to a proxy address when (a) the Gamma profile's `name` matches exactly (as before), or (b) its `pseudonym` matches the handle exactly (same characters and case), **and** in case (b) the wallet's own fills confirm the claimed market (a market attached to the case), the claimed side (the outcome the claim says was bought, where it says one) and the window (at least one such BUY between the market's creation and the end of the case's `event_date`).
- Every handle in any claim is re-checked under this rule; every lookup, match and fill check goes to `logs/handle_checks.csv`. A pseudonym match that fails the fill check is logged as `rejected_pseudonym_no_fills` and resolves nothing.
- Case-insensitive name matches remain under A6.7.

**A12 (2026-11-26, run 7). Grade for employer findings, and run-7 decisions D2 to D7.**
- *A12.1 (D8).* E3 also covers disciplinary action by the trader's employer (dismissal, suspension, formal finding) when a named outlet reports it. The run-5 provisional E3 on the OpenAI firing claim stands under this rule; no claim text changes.
- *A12.2 (D2) Money graph.* Out of scope for v0.3/v1.0 unless `POLYGON_RPC` or an explorer key is set in the environment. At the start of run 7 neither was set (checked), so `build/money_graph.py` is not run; `edges` ships the seed links only.
- *A12.3 (D3) ACDC.* The A6.9 reconstruction is published exactly as computed, with its gap. No parameter is tuned after seeing the gap. It is not a label under A6.9 (`acdc_class` is shipped as a reconstruction column, not as a target).
- *A12.4 (D4) Inca.* `inca_flag` stays, described as "published rule only; broader than Inca's list (9,285 vs 39)".
- *A12.5 (D5) Trade confirmation.* `wallet_labels.csv` gets `trade_confirmed`: true when the address has at least one fill (either side, either source) in a market attached to its case in `markets.csv`; false otherwise. It is computed from the fills table, never from the claim. The label `is_documented` = `polarity == suspected` and `trade_confirmed`. Default analyses use `is_documented`; unconfirmed suspected wallets stay in the table.
- *A12.6 (D7) tweet-count-self-2026-03.* Its markets are attached by `condition_id` only. Every stored text field that would name the subject (question, slug, event slug, outcome labels taken from titles, fill `market_slug`) is NULL for these markets, and the market carries `title_withheld = true`. Selection: the subject's weekly post-count events on Gamma whose end date falls between the earliest day of the case's `event_date` and its claim date (2026-02-01 to 2026-03-10). The lookup query is not stored.

**A13 (2026-11-26, run 7, before any coordinated-buyer search). Coordinated buyers (B1).**
- *Triggers.* Every BUY leg of a `trade_confirmed` suspected wallet (A12.5) in a market attached to its own case, with `ts < t_news` of the version in use (A10.2). Computed separately for `day` and `precise`.
- *Rule.* Another wallet is a coordinated-buyer candidate for a trigger when all hold:
  1. its BUY legs on the same outcome token (`asset_id`) with `|ts - trigger_ts| <= 600` seconds and `ts < t_news` sum to between 0.5x and 2x the trigger leg's USDC;
  2. its Gamma public-profile `createdAt` is at or before its first BUY in that window and no more than 14 days before the trigger;
  3. it is not already in `wallet_labels.csv` (any polarity) and is not the trigger wallet.
- *Pre-filter (exact, not a relaxation).* A wallet whose first Polymarket-v1 fill is more than 14 days before the trigger cannot meet rule 2 (a profile exists before its first fill) and is not looked up. Wallets with no Polymarket-v1 history are looked up. A wallet with no Gamma profile is not a candidate (logged `profile_missing`).
- *Labels.* Each candidate becomes `label_tier = L4_coordinated`, `polarity = candidate`, one row per (wallet, case), with the triggering suspect, trigger fill id and version. Every (candidate, trigger) pair is kept in `data/coordinated_candidates.csv`. A candidate is never `suspected` and never `is_documented`; it is `is_candidate_coordinated`. Candidates are added to the control-pool exclusions (A6.10) from run 7.
- *Placebo windows (false-positive rate).* For each trigger, 5 window centres are drawn (seed 192) uniformly between the first fill in that market and `t_news - 600 s` of the version; the same rule is applied with the window centre in place of the trigger time and the trigger's USDC as the size reference. The report gives candidates per real trigger, candidates per placebo window, the share of windows with at least one candidate, and their ratio. Placebo hits are not labelled.

**A14 (2026-11-26, run 7, before any placebo market is selected). Placebo markets (C1).**
- *Universe.* Markets in the Polymarket-v1 catalog (`out/hf_market_catalog.parquet`) with `resolution_status = resolved`, a winning outcome, exactly two outcome tokens, and not attached to any case.
- *Categories where nobody can know the outcome early,* defined on the market slug (lower case) before selection:
  - `crypto_price`: slug names a coin (`bitcoin|btc|ethereum|eth|solana|sol|xrp|doge|dogecoin|bnb|cardano|ada|avax|link|ltc|litecoin|hype|sui`) **and** a price pattern (`up-or-down|updown|-above-|-below-|less-than|greater-than|price-of|-reach-|-dip-to-|-hit-|-between-`), and does not contain `etf|airdrop|launch|listing|list-on|fdv|market-cap|marketcap|token-sale|exploit|hack|hacked|reserve|treasury|approve|sec-|halving|fork|unlock|staking`. Price outcomes depend on many traders and cannot be learnt from a single insider.
  - `weather_reading`: slug contains `highest-temperature|lowest-temperature|precipitation|inches-of-rain|inches-of-snow|snowfall|hottest-day|temperature-in` and does not contain `hurricane|storm|landfall|named-storm|tornado|earthquake|wildfire`. Readings come from weather stations after the period ends.
  - No other category is used (sports, politics, entertainment and corporate markets can have insiders).
- *Matching.* Each case market is matched to up to 5 placebo markets with the same
  - volume decile (deciles of market USDC volume over the whole resolved two-token catalog; case markets use `volume_hf_usdc`, or `volume_gamma` when not in Polymarket-v1, flagged `volume_basis = gamma`);
  - duration band (`created_utc` to `resolved_utc`, or to `deadline_utc` if unresolved; bands `<1d`, `1-7d`, `7-30d`, `30-90d`, `90-365d`, `>365d`; placebos use catalog `opens_at` to `resolved_at`);
  - resolution month (`YYYY-MM`).
- *Relaxation* when fewer than 5 qualify, in this order, recorded in `relaxation`: month ±1, month ±3, month ±6, adjacent duration band (month ±6), any month (same decile and band), adjacent decile (any month). Case markets with zero volume are not matched (`not_matched_zero_volume`).
- *Sampling.* Seed 192. Case markets are processed in order of (`case_id`, `condition_id`). A placebo market is used at most once across the whole dataset, so no placebo can sit in two benchmark splits.
- *Reference time.* A placebo market gets `t_ref` per version: `opens_at + f * (resolved_at - opens_at)`, where `f = (t_news - created_utc) / (end - created_utc)` of the matched case market (end = resolved, else deadline), clipped to [0, 1]. Pre-news positions and flow of placebo markets are taken before `t_ref`.
- *Fills.* Placebo-market fills come from the same Polymarket-v1 pass (A6.4); `source = hf_polymarket_v1`.

**A15 (2026-11-26, run 7, before any split or baseline is computed). Benchmark splits.**
- Splits are grouped by case. `test` = cases whose `first_claim_date_earliest` is on or after **2026-03-01**; all other cases are `train`. Model selection uses case-grouped cross-validation inside `train` (5 folds, seed 192). A placebo market takes the split of the case market it was matched to (A14 makes this unique).
- T1 (within-market ranking), T2 (episode classification, documented vs matched controls) and T3 (case vs placebo market from pre-news flow) are defined in `benchmarks/README.md`. Each is run on both t_news versions; `precise` is the headline.
- Baselines: logistic regression (standardised features, L2, C = 1) and gradient boosting (scikit-learn `HistGradientBoostingClassifier`, default parameters), seed 192. No tuning on `test`.

**A14.1 (2026-11-26, run 7, after a first placebo selection attempt and before the selection that is used).** The first attempt was discarded for three reasons, none of which looks at case-market trades or outcomes:
1. All 33,504 weather-reading markets have no `resolved_at` in the catalog, so none entered the pool. For placebo markets, the end of the market is `resolved_at`, else `close_at` (the same fallback A14 gives case markets: resolved, else deadline). Resolution month and `t_ref` use that end.
2. Coin names were matched as substrings (for example `ada` inside `canada`, `eth` inside `methane`). A coin must be a whole hyphen-separated slug token. The price patterns keep their hyphens as written in A14.
3. A code error in the last relaxation step (operator precedence) ignored the decile condition. Fixed.

**A14.2 (2026-11-26, run 7).** Case markets attached after the placebo selection and the start of the Polymarket-v1 pass (the 4 markets of the new case `nvidia-ceo-return-2026-11`, all after the Polymarket-v1 end date) are not matched to placebos in v1.0; they are listed in `data/placebo_markets.csv` with `relaxation = not_matched_added_after_selection`. Re-sampling would have changed every later match.

**A16 (2026-11-26, run 7, before any gate column is computed). Gate columns in `weak_labels` (PIPELINE step 5).**
- *Scope.* Gates are computed for every wallet in the positions table (C2: case and placebo markets), not platform-wide; wallets outside those markets get NULL gate columns (`gate_scope = not_in_case_or_placebo_markets`).
- *Gate 1* = the frozen v1 Layer-1 screen (`rules/frozen_v1.md`, F1-F6, high score = score >= 4), one value per (wallet, market, version), taking T_news = `t_news` or `t_news_precise` (placebo: `t_ref`). Two inputs are substituted, because the user-stats and user-volume endpoints cannot be called for hundreds of thousands of wallets:
  - F1 account start = the wallet's first Polymarket-v1 fill (the rule's own fallback, "earliest first activity"), or its Gamma `createdAt` where looked up;
  - F2 denominator = the wallet's Polymarket-v1 USDC volume (all markets) up to the end of T_news's UTC day, from the day files; the market-count branch uses its Polymarket-v1 distinct markets up to that day (never more than lifetime, so it cannot flag more than the frozen rule).
  Gate 1 is NULL for markets with no Polymarket-v1 fills (Data API era). `gate1_inputs = substituted_f1_f2`.
- *Gate 2a* = Signal A of PIPELINE step 7 (a pre-news BUY at >= 1.5x the wallet's first pre-news price on that token). *Gate 2b* = Signal B (the wallet's largest pre-news BUY is on the shortest deadline that resolved Yes in its Gamma event).
- `weak_labels` reports counts per wallet: `gate1_n`, `gate2a_n`, `gate2b_n` (number of (market, token) positions that fire, `precise` version) and the same with `_day`. The frozen v0 ripple alert (seed, anchors, excess ripple) is not run in v1.0: it needs the taker-only feed with transaction keys for every market, which the cleaned Polymarket-v1 layers do not carry.

**A16.1 (2026-11-26, run 7, after a failed first computation that produced no gate value, before any gate value exists).** The F2 market-count branch uses the wallet's **lifetime** distinct Polymarket-v1 markets (`weak_labels.n_markets`), as `rules/frozen_v1.md` itself specifies ("lifetime distinct markets ... can only understate the flag ex-ante"), instead of the count up to the cut day that A16 proposed. Reason: the per-day market count needs a wallet x market x day table that exceeds the build environment's disk allowance. The F2 share denominator stays as in A16 (volume up to the end of the cut's UTC day).

**A12.7 (2026-11-26, run 7).** PROTOCOL 9 extended to market titles: any case market whose question, slug or event slug names a person who is alleged, charged or sanctioned in the sources (the list behind the name test, `tests/name_hashes.txt`, stored as hashes), in any case, is withheld as in A12.6 (`title_withheld = true`, text fields NULL, fill `market_slug` NULL). Found by the release name test (three markets, in the Google Year-in-Search, Super Bowl LX and CZ-pardon ladders: two name the tweet-count subject or a sanctioned former member of Congress as the subject of the market; one only shares a surname with a listed person and is withheld anyway, erring towards privacy).

**A17 (2026-11-27, run 8, before any run-8 table is rebuilt). Coordinated-buyer output is a rule label (R1).**
- The A13 output is a rule label, like ACDC or Gate 1, not a wallet label. The `L4_coordinated` rows leave `wallet_labels.csv` / `wallets`; `data/coordinated_candidates.csv` stays as the full record.
- `positions` gets `coordinated_rule_fired` (bool; the A13 rule fired for this wallet on this token, market, case and version), `triggering_suspect` (the documented wallet of the earliest trigger) and `placebo_rate` (the version's placebo-to-real ratio from `logs/coordinated_placebo.json`). `weak_labels` gets the same three columns per wallet (any case; precise version first) and `coordinated_rule_fired_day`.
- Wording everywhere: "rule output; about 1/3 expected by chance (placebo windows); may include copy-traders reacting to visible trades; not an allegation".
- Rule-fired wallets stay excluded from control pools (A13), read from `data/coordinated_candidates.csv`.
- `fills` `label_other` covers the wallets in `wallets` only, so the rule-fired wallets' histories outside case markets are no longer shipped.

**A18 (2026-11-27, run 8). Exact times must sit inside the coarse date (R5).**
- `t_news_precise` (A10) is used only if it falls inside the range of the date that set the day-level `t_news`: the UTC day for day precision, the calendar month, quarter or year for coarser precision, the stated range for ranges. Otherwise the exact time is not used (`t_news_precise_precision = day_fallback`, `t_news_precise_source = rejected_outside_coarse_date`) and a row goes to `contradictions` (field `t_news_precise`, the claim whose event date set the day).
- Applied to the 17 cases with exact times: one falls outside, `super-bowl-halftime-2026` (halftime 2026-02-09T01:12Z, the evening of 2026-02-08 in US Eastern time, outside the UTC day 2026-02-08). The rule is applied literally; the time-zone reason is recorded in the contradiction.
- Kalshi notices keep their printed years; the three notices that print "EFFECTIVE April 21, 2025" in files posted 2026-04-22 keep that year, with a note in `notes` (as run 7).

**A19 (2026-11-27, run 8). Label family (R4).**
- `wallets` gets `label_family`: `manipulation` for `polarity = manipulation`, otherwise the family of the case's claims (`informed_trading`, `public_data_leak`, `oracle_resolution`, `negative_control`, ...; ';'-joined if a case has several).
- `is_documented` = `polarity = suspected` and `trade_confirmed` and `label_family = informed_trading`. This drops one wallet (`spotify-wrapped-2025`, a public-data leak) from the positives: 119 documented wallets. Benchmarks and baselines are recomputed; the A15 split does not change.
- Benchmark results are reported per case and case-weighted (each case counts once) as well as pooled.

**A20 (2026-11-27, run 9, before any label set is computed). Three nested label sets.**
- *Claim-wallet links* (`data/claim_wallet_links.csv`, built from existing rows only; no claim is edited). A claim names a wallet when
  (a) the wallet's full address appears in the claim's subject, text or notes (`address_in_claim`);
  (b) the claim's subject contains a handle resolved to the wallet under A6.7 / A11 (`resolved_handle`), or the handle recorded with the wallet by its label source (`label_source_handle`);
  (c) the wallet's label `source_url` is the claim's `url` or `post_url`, i.e. the address was taken from that claim's own source (`source_url`);
  (d) a recorded check matched the wallet's fills to the figures of an official claim (`official_figures_match`, `logs/handle_checks.csv`).
  Aggregate and market claims never name a wallet.
- `wallet_grade` = the strongest grade among the claims that name the wallet; NULL (`link_only`) if none does (cluster members linked only by money flows).
- `label_broad` = `trade_confirmed` and `label_family = informed_trading` and `doc_grade` in E1-E5 (equals `is_documented`).
- `label_standard` = `label_broad` and `doc_grade` in E1-E4 (includes cluster members).
- `label_strict` = `label_standard` and (`wallet_grade` in E1-E3, or the wallet is named by (a), (b) or (c) in an E4 claim whose subject is an address, handle, account or cluster of named addresses). `strict_basis` records which.
- The sets are nested by construction (strict ⊆ standard ⊆ broad); a test checks it. They appear in `wallets` and in `episodes` (suspected rows) and `positions` (case markets).

**A21 (2026-11-27, run 9, before any hard negative is selected). Hard negatives.**
- *Suspect profile:* a position (wallet, market, token, version) with pre-cut BUY of at least $1,000 at a pre-cut VWAP of 0.35 or less, whose wallet's Gamma profile was created at most 14 days before its first pre-cut BUY on that token (A13 pre-filter: a wallet whose first Polymarket-v1 fill is more than 14 days before that BUY cannot qualify and is not looked up).
- Rules (`hard_negative_rule`), applied to wallets not in `wallets` and for which the A13 rule did not fire:
  - `lookalike_loser`: suspect profile on the **losing** token of a resolved case or twin market (A22);
  - `cleared_case_lookalike`: suspect profile, any outcome, in a market of a case whose `investigation_outcome` is `cleared_official` or `cleared_analyst` (ballon-dor-2026, railgun-venezuela-control, survivor-50-2026);
  - `placebo_lookalike_winner`: suspect profile on the **winning** token of a placebo market (A14).
  - `cleared_case_wallet`: every wallet in `wallets` of a cleared case (wallet level).
- `positions` gets `hard_negative` and `hard_negative_rule`; `wallets` gets them for `cleared_case_wallet`; all rows are in `data/hard_negatives.csv`. A hard negative is never a positive; it is a negative that looks like a positive before the news.

**A22 (2026-11-27, run 9, before any twin market is selected). Same-category comparison ("twin") markets.**
- *Pool:* resolved two-token markets of the Polymarket-v1 catalog that are not attached to any case, not placebo markets (A14), and not in the same Gamma event (`neg_risk_market_id`) as any case market, and whose slug shares no event slug with a case market. These are markets that appear in no claim.
- *Matching:* each case market with a catalog category is matched to up to 5 twins with the same `category_refined`, volume decile (A14 deciles), duration band (A14 bands) and resolution year. Relaxation, recorded in `relaxation`: year ±1, then adjacent duration band (year ±1), then adjacent decile (year ±1), then any year (same category, decile, band). Case markets with no catalog category (Data API era) or zero volume are not matched (recorded).
- Seed 192; case markets in (`case_id`, `condition_id`) order; each twin used at most once. `t_ref` per version as A14.
- Twin fills come from a Polymarket-v1 pass over the twin markets only (`build/hf_pass_v9.py`, layer B). Twins get positions and minute paths (`market_set = twin`).
- T3 becomes case vs twin markets; the A14 placebo version is kept as **T3b**, labelled market-type sensitive.

**A23 (2026-11-27, run 9, before any run-9 benchmark is computed). Benchmark protocol.**
- *Folds:* leave-one-case-out over every case with at least 3 `label_standard` wallets in the task's rows (the same case list for all label sets of a task), plus the A15 time split. Reported per fold, as mean, standard deviation, minimum and maximum over the leave-one-case-out folds, and the time split separately.
- *Label sets:* every task runs on `label_strict`, `label_standard`, `label_broad`. In a run on a smaller set, documented wallets outside the set are dropped from evaluation (neither positive nor negative).
- *Baselines:* prevalence (constant score; AP equals prevalence, AUC 0.5), the Gate 1 rule (`gate1_score`, ties by size), a one-feature heuristic (younger account = higher score, `account_age_days`), logistic regression (standardised, L2, C = 1). Gradient boosting is reported only with case-grouped hyperparameter tuning (inner leave-cases-out CV on the training cases over max_depth {3, none}, learning_rate {0.05, 0.1}, max_iter {100, 300}, l2_regularization {0, 1}); where it scores below the prevalence baseline, the report says so.
- The random baseline is dropped (its expectation is the prevalence); the run-9 report explains the run-7/run-8 random-baseline change from 100 random draws.
- T3 per label set uses the case markets where a wallet of the set bought before the cut; T3 "all" uses every matched case market.
- *Known shortcuts:* a feature that separates classes for a construction reason (how controls, placebos or twins were drawn) is listed in `benchmarks/README.md` and excluded; the univariate AUC of every feature is reported.

**A24 (2026-11-27, run 9). Consistency, schema and naming.**
- *Fills:* one schema for both sources. Columns a source does not provide are NULL, never filled: on Data API rows `wallet_role`, `aggressor_side`, `maker`, `taker`, `fee_usdc` are NULL and `role_fields_available = false`.
- *Units in names:* every numeric amount, size, price, time or duration column carries its unit (`_usdc`, `_shares`, `_price_usdc`, `_utc`, `_unix`, `_hours`, `_days`, `_minutes`); counts start with `n_`; ratios end in `_share`, `_rate` or `_ratio`.
- *Keys:* every table declares a primary key (a surrogate `*_id` where no natural key exists) and every key and foreign key is tested.
- *Boundary dedup:* no Data API case-market row at or before the Polymarket-v1 end time (2026-04-28 11:00:40 UTC) for a market present in Polymarket-v1, and no pair of legs across sources with the same market, wallet, side, size and time within 60 s of that boundary.
- *Right of reply:* `claims` gets a `right_of_reply` column (NULL unless a subject's reply is received; adding it edits no claim).
- *Neutral naming:* label values and titles use "suspected", "flagged by <source>", "documented"; no label value contains "insider"; no title contains "ultimate".

**A25 (2026-11-27, run 10, before any run-10 table is computed). Per-market news times.**
- Every case market gets `t_news_market_utc` (exact) and `t_news_market_method`:
  1. `scheduled_start`: the market's own scheduled event time from Gamma, `gameStartTime` (a match) or `eventStartTime` (for example an earnings release), when present;
  2. `market_deadline`: otherwise, if the case's day-level `t_news` is coarser than a day (month, quarter, year, range) and the market's Gamma deadline (`endDate`; catalog `close_at` for withheld markets) falls inside that coarse range, the deadline: the moment that resolves that market;
  3. `case_time`: otherwise the case time (`t_news_precise_utc`).
- The cut times used by every time-dependent table become per market: the `precise` version uses `t_news_market_utc`; the `day` version uses 00:00 UTC of that day for methods 1-2 and the case-level `t_news_utc` for method 3. The case-level columns `t_news_utc` and `t_news_precise_utc` are kept unchanged. A per-market time is used even when it is later than the case-level day (that is its purpose: a month-level case date can precede most of its matches or releases). Gamma's scheduled times are structural, not sourced by a press report; they are recorded as such.
- Placebo and twin `t_ref` follow from the case market's cut as in A14/A22 (the position of the cut in the case market's life).
- Everything time-dependent is rebuilt: coordinated-buyer rule, episodes, controls, positions, minute paths, hard negatives, label sets (A26), benchmarks.

**A25.2 (2026-11-27, run 10, after the first per-market tables and before the release tables and benchmarks).** A Gamma `gameStartTime`/`eventStartTime` on a market whose question has a deadline form ("by <date>", "before <month or year>") is the deadline, not a scheduled event: such a market goes to rule 2 (`market_deadline` only when the case date is coarser than a day and the time falls inside the coarse range), else rule 3 (`case_time`). Reason: "MicroStrategy sells any Bitcoin by May 31, 2026?" carries `gameStartTime` 2026-06-01, five months after the case's month-level date (December 2025), so rule 1 counted trades after the news as pre-news. Mechanical test: the regular expression `\b(by|before)\s+(<month name or abbreviation>|end of|<4-digit year>|q[1-4])`, case-insensitive, on `markets.question`. Affects 2 markets (mstr-btc-sale, uma-ukraine-minerals-2025). All time-dependent tables are rebuilt again. Scheduled starts after a coarse case range are otherwise kept (KPMG earnings releases, A25 rule 1: each release resolves its own markets).

**A26 (2026-11-27, run 10). Strict needs a pre-news buy; training and evaluation labels.**
- `label_strict` additionally requires at least one BUY by the wallet in a market of its case before that market's precise cut (A25). Wallets that meet the rest of A20's strict rule but have no such buy get `strict_no_prenews = true` and are not strict.
- Benchmarks: `label_standard` is the main training label. `label_strict` is evaluation-only: models are trained on `label_standard` positives and evaluated on `label_strict` positives (other documented wallets dropped from the test fold). `label_broad` trains and evaluates on itself. Results are reported case-weighted.

**A27 (2026-11-27, run 10, before any run-10 benchmark). Selection-controlled tasks.**
- **T1s** (headline): as T1, but in each case market the candidates are only the pre-news buyers (main token) whose pre-cut BUY USDC lies within [0.5 x the smallest, 2 x the largest] pre-cut BUY of that market's positives of the evaluated label set. It removes "size" as a free signal.
- **T2s** (headline): documented episodes vs controls drawn by A6.10 **plus the same account-age band** (days from the wallet's first Polymarket-v1 fill to its first pre-cut buy: unknown, < 1, 1-7, 7-30, 30-180, >= 180). The band is never relaxed; the A6.10 relaxations apply to the other criteria.
- **T2-open**: A6.10 controls where Orca- and Inca-flagged wallets may be controls (labelled, graph-expanded and coordinated-rule wallets stay excluded).
- `episodes` and `controls` get `control_design` (`standard`, `age_matched`, `open`), part of the primary key. Seed 192.
- T1 and T2 remain as secondary tasks (logistic regression and baselines only); gradient boosting with case-grouped tuning is run on T1s, T2s, T2-open and T3. Every task is reported per label set.

**A28 (2026-11-27, run 10). Multi-account family.**
- A source that alleges common control of several accounts (shared ownership, multi-accounting, wash or self-dealing) **without** alleging that the trades used non-public information gets `label_family = multi_account` for the wallets it names, by a stance note in a new claim (claims are never edited); `multi_account` is excluded from all label sets.
- Applied to `world-cup-2026-06` after reading the source in run 10: the source (Lookonchain via crypto.news, 2026-06-21) calls the trader "a suspected insider" and offers the shared Binance deposit address as evidence that one person controls the three wallets, plus their win records. That alleges informed trading with common control as supporting evidence, so the rule does not apply and the family stays `informed_trading`. The reading is recorded as a context claim.

**A25.1 (2026-11-27, run 10, after a first draft of the per-market times and before any table uses them).** A structural time (scheduled start or deadline) never moves a market's cut **later** than a sourced case-level exact time: where the case has a sourced `t_news_precise_utc` (not `day_fallback`), the per-market time is the earlier of the two, and the method is `case_time` when the case time is earlier. Reason: the draft moved the Gemini 3 ladder markets to their deadlines (for example 2025-11-22), after the sourced release (2025-11-18 16:00 UTC), which would count post-release trades as pre-news.

**Run 11 amendments (2026-11-27, run 11, committed before any run-11 table or benchmark is computed).** The run-11 request numbered these A28-A32; A28 was already used in run 10 (multi-account family), so they are A29-A33 here (request A28 = A29, A29 = A30, A30 = A31, A31 = A32, A32 = A33).

**A29. Reliability of coarse-dated news times.**
- `markets.t_news_reliable = false` for every market of a case whose day-level date has precision `month` or `year` (`markets.t_news_precision`) and that has no sourced exact time (`t_news_precise_precision = day_fallback`); otherwise true. The flag applies to all markets of such a case, whatever A25 method set their cut (deadline, scheduled start or case time).
- `markets.t_news_deadline_rule_utc` keeps the A25 rule-2 deadline time where rule 2 set the cut; NULL otherwise. Cuts are not changed.
- `positions`, `episodes` and `market_minutes` carry `t_news_reliable` (for placebo and twin rows: the flag of the case market they were matched to).
- Default analyses (card quick start, notebooks) and **every benchmark task** use only rows with `t_news_reliable = true`. The removed cases, markets and positives are reported in `baselines.json` (`excluded_unreliable`) and the run-11 report.
- Range-dated cases (`range`, e.g. tweet-count-self-2026-03) and quarter-dated cases are not covered by this rule as worded; they keep `t_news_reliable = true` and are named in the report.

**A30. Scheduled starts are checked against the market's close.** A25 rule 1 uses a Gamma `gameStartTime`/`eventStartTime` only if it is strictly before the market's Gamma `closedTime`, else before `markets.resolved_utc`. If it is not before, or neither time is known, the market falls back to the case time (rule 3; A25.1 and A25.2 still apply). Every market where rule 1 was considered is listed in `logs/scheduled_start_check.csv` with the start, the close used, its source and the decision; disagreements (start not before close, or no close known) are flagged.

**A31. Only allegations and confirmations create links.** `claim_wallet_links` rows are created only from claims with `stance` in (`alleges`, `confirms`). Claims with stance `context`, `clears` or `disputes` create no link (they stay in `claims`). `wallet_grade`, `label_strict` and `strict_basis` are recomputed from the restricted links; `doc_grade` (case level) is unchanged.

**A32. Strict results are fold-level only below 6 folds.** For any task and label set with fewer than 6 leave-one-case-out folds, `baselines.json` and the dataset card report per-fold values with their minimum and maximum (and the time-split value as one more fold), not a mean, SD or single headline number. Applies to `label_strict` in run 11; applies to any label set that falls below 6 folds.

**A33. T2w and adjacent-band relaxation.**
- New control design `winrate_matched` (task **T2w**, a headline task): as `age_matched`, and controls also share the episode's prior win-rate band, computed exactly as `episodes.prior_net_long_win_rate` (net-long resolved Polymarket-v1 markets before the first pre-cut buy, other markets only). Bands: `none` (no such market), `lt_0.25`, `0.25_0.5`, `0.5_0.75`, `ge_0.75`.
- Age-matched designs (`age_matched` = T2s, `winrate_matched` = T2w): when the exact band(s) give no same-side control after the full A6.10 ladder, the selection is repeated once with the adjacent band(s) also allowed (age: the neighbouring bands in `lt_1d < 1_7d < 7_30d < 30_180d < ge_180d`; win rate: the neighbouring bands in `lt_0.25 < 0.25_0.5 < 0.5_0.75 < ge_0.75`; `unknown`/`none` have no neighbour). Controls chosen this way, other-side controls included, have `relaxed_band = true`; all others false. An episode is dropped from same-side matching only after that second attempt.
- Coverage (episodes with and without same-side controls, relaxed counts) is reported per design and version.

**A29.1 (2026-11-27, run 11; clarification of A29's intended scope, written after seeing that the by-case application flagged all 90 checked scheduled starts, and before any release table, benchmark or report uses the flag).** `t_news_reliable` is set **per market**, not per case:
- `true` if the market's per-market time comes from a sourced exact time (`t_news_market_method = case_time` with `t_news_precise_precision` not `day_fallback`, or a structural time replaced by the sourced case time under A25.1), or from a scheduled start (`gameStartTime`/`eventStartTime`) that passed the A30 close check (`t_news_market_method = scheduled_start`);
- `false` only if its time came from the A25 deadline rule (`t_news_market_method = market_deadline`): a coarse case date and nothing better for that market. This holds for every coarse precision the deadline rule covers (month, quarter, year, range), so range-dated deadline markets are now flagged too;
- otherwise `true`: markets that fall back to the case-level date (`case_time`, `day_fallback`). Their cut is the start of the documented day, month or year, which is earlier than the news, never later. They are counted separately in the run-11 report.
- `positions` and `market_minutes` rows of placebo and twin markets carry the flag of the case market they were matched to (reliable if any matched case market of that case is reliable). `episodes` rows carry their own market's flag.
- A29's default-analysis and benchmark rule is unchanged: only `t_news_reliable = true` rows are used.

**A34 (2026-11-27, run 11, before any A34 table is computed). Economic-side exposure.**
- *Prompt.* Checking why 3 `label_standard` wallets have no pre-news position, wallet `0xcc32a117ac254fe51fd867b928e45492b1f6dc7e` in `us-iran-strike-2026-02-28` sold 881 "No" shares at 0.79 before the cut (05:44 UTC) without ever having bought "No", then sold "Yes" at 0.998 after the news. Under A6.10's BUY-only rule this is invisible. **The rule below follows from the market mechanics of binary outcome tokens (a full set of Yes + No redeems for 1 USDC; a token can only be sold if held, so a sale of a token never held implies it was minted together with its complement), not from any outcome, label or result.** It is applied to every wallet and every market (case, twin, placebo) alike.
- *Rule.* In a binary market (two outcome tokens), a SELL leg of token X by a wallet whose balance of X just before that leg, from its own earlier legs in that market, is zero or less (≤ 1e-6 shares), is an economic BUY of the complementary token at price `1 - p`, size `shares` shares, `econ_size_usdc = shares × (1 - p)`. Balances are built in time order (`ts`, then `leg_id`): a BUY of X adds its shares to X; a SELL of X held subtracts them; an inferred economic BUY adds its shares to the complementary token. The computation is iterated to a fixed point. A SELL with a positive balance smaller than its shares is left as it is (counted as `partial`). This covers the A6.4 case (a maker SELL of one outcome recorded for what is economically a BUY of the other through mint matching) wherever the maker holds none of the sold token; it is identified by the same test, and `wallet_role` is kept so both cases can be counted. BUY legs are never re-interpreted (a merge is not inferred).
- *Both views.* Raw fills are unchanged. Every leg gets `econ_side`, `econ_asset_id`, `econ_outcome_label`, `econ_price_usdc`, `econ_size_usdc` and `econ_inferred` (true only for re-interpreted legs; for all others the econ columns equal the raw ones). The complementary token comes from `markets.token_ids` (case markets) or from the two tokens seen in the market's legs (twin, placebo); a market with one known token gets no inference.
- *Default view.* `positions`, `episodes`, `controls`, `hard_negatives` and the coordinated-buyer rule (A13) use the econ view by default. The raw view stays comparable: `positions.econ_inferred_buy_usdc_pre` (the part of `buy_usdc_pre` from inferred legs), `positions.raw_view_prenews_buy` (the position also exists in the raw BUY-only view), and the same two columns in `episodes`. `market_minutes` stays on raw fills (market-level price paths and aggressor flows). Rule outputs computed platform-wide from the Polymarket-v1 pass (ACDC, Inca, wallet history) are unchanged.
- *Rebuild.* Everything time-dependent is rebuilt; label sets (A26 pre-news test) follow the econ view. Reported: changed legs and wallets per market set, labelled wallets gaining or losing a pre-news position, new pre-news positions in case vs twin vs placebo markets (a jump only in case markets would be a finding; the same jump everywhere is market mechanics), and benchmark changes against a pre-A34 quick run on the same tables.

**A34.1 (2026-11-27, run 11, after the first A34 econ pass and before positions or any later table uses it).**
- *Partial sells.* Prompted by the 0.66 M case-market SELL legs (0.41 M placebo, 0.32 M twin) that A34 left raw because the wallet held some, but fewer, shares than it sold. Same mint mechanics: shares cannot be sold unless held, so the shares beyond the holding were minted together with the complement. Rule: when a SELL of token X exceeds the wallet's current **econ** balance of X (`h`, with `0 < h < shares`), the held part (`h` shares) stays a SELL of X at `p`, and the excess (`shares - h`) is an inferred economic BUY of the complementary token at `1 - p` (`econ_size_usdc = (shares - h) × (1 - p)`). The X balance goes to zero, the complement's rises by the excess. The A34 test (no holding at all) is the case `h <= 1e-6`, which is unchanged.
- *Recording.* The leg's primary econ columns describe the held SELL part (`econ_side = SELL`, `econ_size_usdc = h × p`, `econ_partial = true`, `econ_inferred = false`), and `econ_excess_shares`, `econ_excess_asset_id`, `econ_excess_price_usdc`, `econ_excess_size_usdc` describe the inferred BUY. The econ view used by the builders expands such a leg into its two parts. Raw columns are unchanged.
- *Balances (confirmed, not changed).* Econ balances are built in one sequential pass per (wallet, market) in time order, and inferred BUYs add to the complement's balance, so a later SELL of the complement by the same wallet is a sale of held shares, not another inference.
- *Market-maker rule, for reporting only* (fixed here before any wallet is inspected). A wallet is a *market maker* if, over all its legs in case, twin and placebo markets (raw fills), it has at least 20 active (market, UTC minute) pairs and in more than 50% of them it has legs on both tokens of that market. It is not a label and not used by any table or benchmark; the run-11 report uses it to split the raw-vs-econ comparison, and five of these wallets (the five with the most case-market legs) are used to check that econ net exposure per market is near flat.

**A34.2 (2026-11-27, run 11, after A34.1 and before positions, episodes, the coordinated rule or any later table is rebuilt). Direction net of full sets.**
- *Prompt.* The A34.1 market-maker check left wallet `0x87ec6cd9…` long both tokens (71,745 full-set shares over 15 case markets) from raw BUYs of both tokens, most likely merges, which the fills do not show. A held full set (one Yes + one No) redeems for 1 USDC whatever the outcome, so it carries no view on the outcome. This follows from the same token mechanics as A34, not from outcomes.
- *Measure.* For each (market_set, case, market, `t_news_version`, wallet), from the **econ** legs before the cut: `H_yes`, `H_no` = econ BUY shares minus econ SELL shares of each token (clipped at 0); `full_sets_pre_shares = min(H_yes, H_no)`; the *directional token* is the token with the larger holding; `directional_shares_pre = |H_yes - H_no|`; `directional_cost_usdc_pre` = the cost basis of those excess shares under FIFO on econ BUYs: sells consume the oldest lots, full sets pair with the oldest remaining lots of the directional token, and the excess is the newest remaining lots (`sum price × shares` over that part).
- *Population.* A **pre-news position** for label sets (A26), benchmarks, episodes and controls (A6.10), hard negatives (A21) and the coordinated-buyer rule (A13) needs `directional_shares_pre > 1e-6` before the cut, on the directional token (`positions.is_directional_position`). `positions` keeps every token row with gross econ BUYs (the A34 population) and the gross columns (`buy_usdc_pre`, `buy_shares_pre`, `econ_inferred_buy_usdc_pre`, `raw_view_prenews_buy`), plus `full_sets_pre_shares`, `directional_shares_pre`, `directional_cost_usdc_pre` and `is_directional_position`. `episodes` carries the same three measures.
- *Market-maker flag.* `is_market_maker` (A34.1 definition) is exposed in `positions` and `weak_labels` as a **reporting flag, not a label**; no table rule or benchmark uses it.

**A34.3 (2026-11-27, run 11, columns only, before episodes or positions are rebuilt; no rule, population or label changes).**
- `positions` and `episodes` gain, per directional position (A34.2), from the econ BUYs of the directional token before the cut: `directional_first_buy_utc`, `directional_first_buy_price` (price of that first econ BUY), `directional_vwap_pre` (econ BUY USDC / econ BUY shares on the directional token) and `directional_hours_first_buy_to_cut`. NULL where the row is not a directional position.
- `directional_cost_usdc_pre` is a **FIFO accounting figure** (the cost of the newest remaining lots after sells and full-set pairing); it is not an entry time or entry price. Entry-timing and entry-price features should use the four columns above.

*Note to A34.3 (2026-11-28, run 11; naming only).* `directional_vwap_pre` is released as `directional_vwap_price_usdc_pre` in `positions` and `episodes`, because A24 requires a unit in every numeric column name (the existing `vwap_pre` is released as `vwap_price_usdc_pre`). The other A34.3 columns keep their names.

**Run-11 audit amendments (2026-11-28, run 11; reviewer findings; committed before any of them is computed).** A35-A38 as numbered in the request; the request's unnumbered items are A39-A45.

**A35. Alleged positions.**
- New table `claim_positions`: one row per (claim, market, side) that a claim describes, mapped **by hand from the claim text** (subject, claim text, notes) and the market questions, **without looking at outcomes, resolutions, prices or fills**. Columns: `claim_id`, `case_id`, `condition_id`, `side` (the outcome label the claim says was bought, e.g. Yes on "US strikes Iran by February 28?"), `mapping_basis` (`named_market`: the claim names the market or its question; `named_event_ladder_rung`: the claim names the event and the date or threshold that picks one rung; `only_case_market`: the case has a single market on the claimed event), `mapping_note`. Claims that name no market or side (aggregates, platform statements) get no row; a wallet without any mapped claim keeps no alleged position.
- `positions.is_alleged_position` and `episodes.is_alleged_position`: true only on rows of a labelled wallet in its own case whose (condition_id, token outcome) is in `claim_positions` for that case. Other positions of labelled wallets: `episodes.role = labelled_other_position` (a third suspected-side role; controls unchanged).
- Benchmarks use alleged positions as positives (`y = label set AND is_alleged_position`); the wallet-level version (any position of a labelled wallet) is reported as secondary. Reported: how many suspected positions are alleged, and how the losing ones (`won_post = false`) split.

**A36. One news time per market.** `t_news_market_utc` / `t_news_market_day_utc` become properties of `condition_id`: identical in every case that includes the market. For a market in several cases, the time comes from the case whose `claim_positions` row names that market (its resolving event); if none or several do, the earliest of the candidate per-market times (conservative: never later than any case's time). Placebo/twin `t_ref` follow (A14, A22). Gate: one distinct cut per (condition_id, version) in `markets` and `positions`.

**A29.2.** `t_news_reliable = false` also for `case_time` fallbacks whose case date has precision month, quarter, year or range and no sourced exact time (A29.1 kept them true). Before applying, exact times are sought for the affected cases (sourced as `event_times` rows under A10, verified against the page); a case with a sourced exact time leaves the rule.

**A37. Splits by connected component.** Cases that share any `condition_id` or Gamma `event_id` form one group (connected components of the case-market-event graph). Every split and fold assigns whole groups: the time split puts a group in `test` if its earliest first-claim date is on or after 2026-03-01, else `train`; leave-one-case-out becomes leave-one-group-out (groups with >= 3 `label_standard` wallets). `splits.csv` gains `group_id`. Gate: no `condition_id` or `event_id` in both train and test of the time split or of any fold.

**A38. Twins by question type.** Each case market and twin candidate gets `question_type` from its question by fixed keyword rules (military_action, award, corporate_release, election, crypto_project, legal_action, appointment, sports, other), written in `build/v1/question_type.py` before twins are re-matched. A twin must have the same `question_type` as its case market (in addition to A22's matching), never a placebo category (crypto price, weather), and never the same subject as the case (same-subject markets of a case are not twins). Twins are re-chosen from the markets whose fills are already in the release pass (no new fills can be pulled for new twins in this run); coverage is reported.

**A39. Names in every string column.** `tweet-count-self-2026-03` loses its twins (same-subject markets, A38). `category_refined` and slugs (`slug`, `event_slug`, `twin_slug`, `placebo_slug`, `market_slug`) that contain a withheld name are set to NULL in every table. The name gate scans every string column of every table (category, slug, question, notes included; URLs excluded as before) against `tests/name_hashes.txt`.

**A40. Known-answer tests.** The build fails if either is off by more than 1%: the Maduro case wallet in "Maduro out by January 31, 2026?" holds 436,759.61 Yes shares bought for 32,538.34 USDC before the cut (econ view); AlphaRaccoon's (Google Year in Search, d4vd market) Yes buys total 10,650.04 USDC. If a test fails, the build is investigated and reported, not adjusted to pass.

**A41. FTX market scope.** `ftx-sbf` keeps only the markets its claims name (pardon of SBF, FTX payouts, SBF sentence); the other Biden-pardon ladder markets leave `ftx-sbf` (they stay under `biden-pardons`).

**A42. Claim timing.** `claims.claim_timing` = `ex_ante` if `claim_date` < the resolution time of the claim's alleged market (`claim_positions`), else `ex_post`; `claims.alleged_side_won` = the alleged side won that market (NULL without a mapped market or an unresolved market). `cases` gets counts of ex-ante claims and their win rate. Ex-ante claims and their win rate are reported separately.

**A43. Null columns and lifetime share.** Columns that are NULL in every row are dropped from the release (the A8 funding fields until A8 runs) or, where a later run will fill them (`claims.right_of_reply`), kept and marked `not_built` in the CODEBOOK. `episodes.case_share_of_lifetime_volume` uses the same source for numerator and denominator (Polymarket-v1 raw legs only), so it lies in [0, 1].

**A44. Minor.** `claims.duplicate_of` (CL0124 duplicates CL0091's source and wallets; it stays a context claim and creates no link). `cases.event_date` is split into `event_occurred_utc` (the earliest documented occurrence, = `t_news_utc` of the case) and `market_deadline_utc` (the deadline of the case's alleged market, the earliest if several). The CODEBOOK states the token behind `market_minutes` prices (the Yes token, or the first listed outcome). T2 benchmarks deduplicate repeated controls: a control (case, market, token, wallet) matched to several episodes counts once per fold.

**A45. Rebuild.** Everything is rebuilt; all gates and benchmarks are rerun; every change is reported in `logs/run11_report.md` before v1.2.1 is frozen.

**A35.1 (2026-11-28, run 11; before claim_positions is built).** (1) A claim that names the event but no single market (for example "bet on the Feb 28 strikes", "Yes bets before the ceasefire post", "betting on Maduro's removal") maps to every Yes rung of that event's ladder whose Gamma deadline (`markets.deadline_utc`) is on or after the claim's `event_date`, with `mapping_basis = event_ladder_rungs_after_event_date`; rungs before that date, daily "on <date>" markets and other events are not mapped. Only the claim's own date and the structural deadline are used, never a price, fill or outcome. (2) A claim that names neither a market nor an event side (funding links, aggregate results, platform statements, "World Cup markets", "earnings-beat markets", an unnamed candidate) gets no row. (3) A labelled wallet's alleged positions come from the claims linked to it (`claim_wallet_links`); a wallet whose linked claims have no row takes the rows of its case's `cluster` claims (the claims that describe the group it was labelled through). (4) The mapping spec is a fixed list in `build/v1/claim_positions.py`, one entry per claim, written from the claim text and the market questions.

*Note to A36 (A36.1, 2026-11-28, run 11; written after the release gates flagged it, before any benchmark uses the tables).* A36 and A25.1 can conflict for shared markets: A36 gives the ceasefire markets their own resolving time (2026-04-07, from the ceasefire case's claims), which is later than the sourced exact time of another case that includes them (bubblemaps-military-cluster, 2026-02-28 06:15 UTC, the strike). A36 is the later and more specific rule: a market's cut is the time of its own resolving event. A25.1's bound ("never later than a sourced exact case time") applies to the case the market's time comes from, now recorded as `markets.t_news_market_source_case`.

*Note to A39 (2026-11-28, run 11; written after the release gates flagged it).* The string gate found an outcome label that is a withheld name (one market in `label_other` fills, slug already NULL). Outcome labels (`outcome_label`, `econ_outcome_label`, `econ_excess_outcome_label` in `fills`) that contain a withheld name are set to NULL as well; the token id keeps the leg identifiable.

**Run-11 finish amendments (2026-11-28, run 11, continued in a fresh build environment; committed before anything they govern is computed).**

**A46. Twin pool from the full Polymarket-v1 catalog.** A38 restricted twin candidates to markets whose fills were already in the release pass because the interrupted run could not pull new fills; that was a constraint of that run, not a matching rule. The finishing run rebuilds every intermediate from the pinned Polymarket-v1 tape, so the twin pool becomes A22's full pool (resolved two-token markets of `out/hf_market_catalog.parquet`, not case, placebo or same-event markets), with every A38 and A39 condition unchanged: same `category_refined`, volume decile, duration band and resolution year ladder as A22; same `question_type`; never a placebo type; never the same subject; no twins for `tweet-count-self-2026-03`. Seed 192, case markets in (`case_id`, `condition_id`) order, each twin used once; twin ids are re-assigned. Twin fills come from a new layer-B9 pass over the pinned tape (`build/hf_pass_v9.py`); twins are resolved inside Polymarket-v1, so they have no Data API rows. Case markets with no catalog category (Data API era, after 2026-04-28) stay unmatched, because A22 matches on `category_refined`, which Gamma does not carry; this is reported as a gap, not filled from Gamma tags. Coverage before (317 case markets, 1,485 twins) and after is reported. Everything twin-dependent is rebuilt: `t_ref` (A25 via `ref_times.py`), twin positions and minute paths, `lookalike_loser` hard negatives on twins, T3.

**A47. Rebuild from a fresh disk.** The data CSVs committed by run 11 (`markets`, `placebo_markets`, `coordinated_candidates`, `wallet_labels`, `claim_positions`, `claim_wallet_links`) are inputs and are not recomputed, except where A46 changes them (`twin_markets`, `hard_negatives`). The Data API v2 rows for case markets and labelled wallets are pulled again; the API is not hash-stable, so `source = data_api_v2` rows may differ from run 11's; row counts before and after are reported. The A40 known-answer tests must pass after the rebuild.
