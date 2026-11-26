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
