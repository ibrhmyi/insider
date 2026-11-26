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
