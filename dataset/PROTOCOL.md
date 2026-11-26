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
