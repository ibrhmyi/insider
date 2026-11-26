# PMITC v1.0: Prediction-Market Informed-Trading Casebook

A source-traced register of publicly documented cases of **suspected** informed trading on prediction markets (court and regulator actions, platform sanctions, analyst investigations, press reports, rule-based screens), joined to trade-level Polymarket data so that the cases can be analysed and used for machine learning: every fill in the case markets, all buyers before the news, matched controls, placebo markets where nobody can know the outcome early, minute paths, and three benchmark tasks.

**Version 1.0.0 (2026-11-26).** Collected under `PROTOCOL.md` v1.0 and amendments A1 to A16.1. Every column is in `CODEBOOK.md`; the datasheet is `DATASHEET.md`; file hashes are in `../MANIFEST.json`.

> **Labels are allegations, not findings.** A wallet in this dataset is "flagged by <source>", never "an insider". Only E1 claims are final outcomes, and most E1 claims are Kalshi platform discipline. No table contains a personal name.

## Contents (`data/`)

| Table | Rows | One row is |
|---|---|---|
| `cases` | 66 | one underlying event: strongest grade, investigation outcome, counts, benchmark split |
| `claims` | 123 | one statement by one source at one time: grade, stance, verified flag, source URL |
| `wallets` | 1,598 | one (wallet, case) label: tier, polarity, `trade_confirmed`, `is_documented`, `is_candidate_coordinated` |
| `markets` | 1,118 | one (case, market): Gamma ladder, dates, outcome, volume, `t_news_utc`, `t_news_precise_utc` |
| `placebo_markets` | 4,495 | one placebo market (4,227) with its matched case market, or an unmatched case-market row |
| `fills` (8 parquet parts) | 58,060,526 | one wallet leg of one fill: case markets, placebo markets, and labelled wallets elsewhere |
| `positions` | 6,074,515 | one (market, token, wallet, version) for every buyer before the cut: the population a detector must search |
| `episodes` | 17,671 | one documented episode or matched control, pre-news features and `_post` outcomes, both versions |
| `controls` | 16,767 | one matched control with its relaxation flag |
| `weak_labels` | 2,651,672 | one Polymarket-v1 wallet: ACDC reconstruction, Inca rule, Gate 1/2 counts |
| `market_minutes` | 1,239,464 | one market, version and minute with fills, 48 h before to 24 h after the cut |
| `contradictions` | see file | a claim contradicted by the trades (claims are never edited) |
| `edges` | 416 | a money link from the seed sources (not expanded; no archive RPC was available) |

CSV copies exist for every table under 50 MB; parquet for all. Types are explicit (`CODEBOOK.md`): UTC timestamps, lower-case `0x` addresses, NULL for missing, stable ids (`case_id`, `claim_id`, `condition_id`, `asset_id`, `wallet`, `episode_id`).

## Label columns (never merged)

`is_documented` (suspected by a source **and** confirmed by the wallet's own fills; the default positive), `doc_grade`, `is_candidate_coordinated` (rule A13, never documented), `acdc_class` (reconstruction, not a label: it misses its 5% validation bar), `inca_flag` (published rule only; broader than Inca's list, 9,285 vs 39), `gate1`, `gate2a`, `gate2b` (frozen screens, A16), `is_control`, `is_placebo_market`.

## Two news times

Every time-dependent table exists twice (`t_news_version`):
- `day`: 00:00 UTC on the earliest day-precision event or claim date (A6.6, A7);
- `precise`: an hour- or minute-level time from `data/event_times.csv` with a source URL (A10), or the day time where none is sourced. 17 of 42 market-bearing cases have an exact time.

Day-start times count every trade on the news day as post-news; the precise version fixes that (for example the Nobel wallets bought between 00:44 and 03:29 UTC before the 09:00 UTC announcement). Use `precise` by default and report `day` as a sensitivity.

## Benchmarks (`benchmarks/`)

Frozen split (`splits.csv`): grouped by case, ordered in time; `test` = cases first claimed on or after 2026-03-01.
- **T1, within-market ranking** of all pre-news buyers (positives = documented wallets). Test (precise): logistic regression AP 0.076 vs random 0.052 and the Gate 1 rule 0.065; gradient boosting overfits the train cases (AP 0.012). Case-grouped CV inside train: AP 0.35 (LR).
- **T2, documented episodes vs matched controls.** Base result: matched same-side controls win as often as documented episodes (83.5% vs 83.9%), so outcome-based features do not separate them. Pre-news behaviour separates them partly: test AUC 0.79 (logistic regression) and 0.70 (gradient boosting); case-grouped CV 0.80 and 0.88. Account age and prior activity carry most of it (documented wallets are new). One feature, `share_on_this_ladder_market`, is a construction artifact (AUC 0.97 alone) and is on the leakage list; see `benchmarks/README.md`.
- **T3, case markets vs placebo markets** from pre-cut flow only: AUC about 0.72 (LR) to 0.84 (gradient boosting) on test. Placebo markets differ from case markets in kind (crypto prices, weather), so part of this is market type.

Full results: `benchmarks/baselines.json` (both versions). Notebooks: `notebooks/01_explore.ipynb`, `notebooks/02_baselines.ipynb`.

## Rules for use

1. A label is an allegation, not a finding. Report results as "wallets flagged by sources".
2. One case is one event. The US strike on Iran (Feb 2026) holds about 40% of documented wallets; group by case.
3. The collection reflects what was noticed and published (PROTOCOL 8): mostly fresh wallets making large, cheap, well-timed bets on viral markets. Do not estimate prevalence from it, and do not train a detector only on it.
4. Freeze before you test: these cases were public before you built your method; report test-split results separately.
5. No identity work: do not use the data to identify the people behind wallets.

## Ethics

- No personal names in any data field (tested with a name list stored as hashes and a reviewed "Name Surname" scan; `tests/`). Official records are referenced by URL and notice or docket number; URLs chosen by sources may contain names.
- Market titles that name a person alleged, charged or sanctioned in the sources are withheld (A12.6, A12.7).
- No attempt is made to identify people behind wallets; wallet-to-person mappings are never made by us.
- Raw Gamma profiles of the A13 lookups are not published (only `createdAt` is used).
- **Removal requests:** open an issue at https://github.com/ibrhmyi/insider with the row id (`claim_id`, `wallet` + `case_id`) and the reason; rows whose only source is retracted are removed (PROTOCOL 9).
- **Bias statement (PROTOCOL 8):** the collection over-represents large, fresh-wallet, long-shot wins on geopolitical and viral markets and under-represents informed trading that looks ordinary. It reflects what analysts and journalists noticed, which is itself shaped by the screens they ran.

## Licensing

PMITC tables: CC-BY-4.0. Polymarket-v1 fills (`source = hf_polymarket_v1`): CC-BY-4.0 (TimeSeventeen). Data API v2 rows (`source = data_api_v2`) are public on-chain trades; Polymarket's API terms could not be verified from the build environment, so these rows are in separate files (`fills_part*_data_api_v2.parquet`) and can be dropped and rebuilt with `dataset/build/pull_market_trades.py` and `build/v1/fills.py`. Repositories without a licence contribute only facts (addresses) with links. Details: `LICENSES_UPSTREAM.md`, `LICENSE.md`.

## Known gaps

- The money graph (A6.8, A8) is not built: no archive Polygon RPC or explorer key (A12.2). `edges` holds seed links only; funding features are empty.
- The 20% blind re-extraction (A4) is pending: `blind_check_sample.csv` in the repository stays blank for a second extractor.
- 16 claims are `verified = pending` (search-result text). 22 pages could not be read here (proxy or site bot protection) and are listed in the repository's `dataset/logs/needs_page_read.csv`; none was worked around.
- Kalshi accounts and trades are not public: Kalshi cases have claims but no wallets or fills.
- The ACDC reconstruction misses its validation bar (Orcas +188%); `inca_flag` is far broader than Inca's published list.
- A13 candidates are noisy: the same rule fires in random placebo windows at about a third of the real-trigger rate (precise: 0.145 vs 0.446 candidates per window).
- Polymarket-v1 records some economic buys as maker sells of the other token (mint matching, A6.4); fills keep the leg sides as recorded.

## How to cite

> Yildiz, I. (2026). *Prediction-Market Informed-Trading Casebook (PMITC)*, version 1.0.0 [dataset]. Collected under protocol v1.0 with amendments A1 to A16.1. https://github.com/ibrhmyi/insider

BibTeX and CFF: `CITATION.cff`. Please also cite Polymarket-v1 (TimeSeventeen, Hugging Face) for the fills.
