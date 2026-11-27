---
license: cc-by-4.0
pretty_name: "PMITC: Prediction-Market Informed-Trading Casebook"
language: [en]
tags: [prediction-markets, polymarket, kalshi, market-integrity, anomaly-detection, tabular, finance]
task_categories: [tabular-classification]
size_categories: [10M<n<100M]
configs:
- config_name: cases
  data_files: "data/cases.parquet"
  default: true
- config_name: claims
  data_files: "data/claims.parquet"
- config_name: wallets
  data_files: "data/wallets.parquet"
- config_name: markets
  data_files: "data/markets.parquet"
- config_name: placebo_markets
  data_files: "data/placebo_markets.parquet"
- config_name: fills
  data_files: "data/fills_part*.parquet"
- config_name: positions
  data_files: "data/positions.parquet"
- config_name: episodes
  data_files: "data/episodes.parquet"
- config_name: controls
  data_files: "data/controls.parquet"
- config_name: weak_labels
  data_files: "data/weak_labels.parquet"
- config_name: market_minutes
  data_files: "data/market_minutes.parquet"
- config_name: contradictions
  data_files: "data/contradictions.parquet"
- config_name: edges
  data_files: "data/edges.parquet"
- config_name: twin_markets
  data_files: "data/twin_markets.parquet"
- config_name: hard_negatives
  data_files: "data/hard_negatives.parquet"
- config_name: claim_wallet_links
  data_files: "data/claim_wallet_links.parquet"
---

# PMITC v1.2: Prediction-Market Informed-Trading Casebook

PMITC is a source-traced register of **publicly documented, suspected** informed trading on prediction markets (Polymarket and Kalshi): 66 cases and 124 claims from courts, regulators, platforms, researchers, journalists and on-chain analysts, each graded E1 (adjudicated) to E6 (rule-based screen), joined to the trades. For every case market it ships every fill, every buyer before the news, matched controls, hard negatives, same-category "twin" markets and placebo markets where nobody can know the outcome early, so that detection methods can be trained and tested honestly. **Every label is an allegation by a named source ("flagged by <source>"), not a finding.** No table contains a personal name.

![Cases on a timeline by evidence grade](docs/cases_timeline.png)

> **Read first.** (1) Labels are allegations; only E1 is adjudicated, and E1 is mostly Kalshi discipline without public wallets. (2) Positives are few and clustered: 19 wallets in `label_strict`, 119 in `label_broad`, and two cases hold 74 of the 119 broad positives. (3) The collection over-represents fresh wallets making large, cheap, well-timed bets on viral markets; do not estimate prevalence from it.

## Quick start

```python
import pandas as pd; positions = pd.read_parquet("data/positions.parquet", filters=[("t_news_version", "==", "precise")])
from datasets import load_dataset; wallets = load_dataset("<hf-user>/pmitc", "wallets", split="train")   # Hugging Face
print(positions.groupby("market_set").label_strict.sum(), wallets.num_rows)
```

Notebooks: `notebooks/01_quickstart.ipynb` (load, join, plot), `02_case_study.ipynb` (the Maduro market: price path, the wallet's buys, matched controls), `03_benchmarks.ipynb`. Requirements: `requirements.txt` (pinned); rebuilding from scratch takes about 7 hours and 30 GB of disk (`docs/REBUILD.md`).

## Tables

| Table | Rows | One row is |
|---|---|---|
| `cases` | 66 | One row per case (underlying event). Derived from claims (build/build_cases.py) plus market and wallet counts. |
| `claims` | 124 | One row per claim: one statement by one source at one time (PROTOCOL 2, 6). Claims are never edited; contradictions go to contradictions. |
| `wallets` | 260 | One row per (wallet, case) label. Labels are allegations by the named source, not findings. |
| `markets` | 1,118 | One row per (case, market). Ladders are full Gamma events (A6.5). Titles withheld where they name the alleged trader (A12.6). |
| `placebo_markets` | 4,495 | One row per placebo market (A14) with its matched case market; case-market rows that could not be matched appear with NULL placebo fields. |
| `fills` | 81,559,246 | Every leg of every fill in case and placebo markets, plus every leg of labelled wallets elsewhere. Parquet only (split into parts). |
| `positions` | 11,737,142 | All-buyer positions before the cut (C2): the full population a detector must search, case and placebo markets. |
| `episodes` | 55,913 | Per (wallet, market, token) episode of documented wallets and their matched controls; pre-news features, then _post outcomes. |
| `controls` | 52,790 | Matched controls (A6.10, seed 192) with relaxation flags, per t_news version. |
| `weak_labels` | 2,651,672 | Per wallet in Polymarket-v1: ACDC reconstruction and Inca rule (A6.9, E6), and Gate 1/2 counts (A16). Rule outputs, never merged with claims. |
| `market_minutes` | 2,217,628 | One row per market, version and UTC minute with fills, cut - 48 h to + 24 h, Yes token (A9.3, A10.2, A14). |
| `contradictions` | 5 | Places where the trades disagree with a claim (the claim is never edited), incl. the run-7 amount checks (gap > 10%). |
| `edges` | 416 | Money links between addresses from the seed sources (funding, Relay handoff, Safe owner, cash-out). Not expanded (A12.2). |
| `twin_markets` | 3,922 | One row per twin market (A22): a resolved market of the same category, volume decile, duration band and year as a case market, in no claim; unmatched case-market rows have NULL twin fields. |
| `hard_negatives` | 10,053 | One row per hard negative (A21): a position or wallet that matches the suspect profile but is a negative. |
| `claim_wallet_links` | 64 | One row per (claim, wallet, link type): how a claim names a wallet (A20). Used for wallet_grade and label_strict. |

Every column has a type, unit, allowed values, source and leakage note in `docs/CODEBOOK.md`. Parquet for all tables; CSV for tables under 50 MB. Keys: every table has a declared primary key; ids are stable (`case_id`, `claim_id`, `condition_id`, `asset_id`, `wallet`, `episode_id`). Timestamps are UTC; amounts carry units in their names (`_usdc`, `_shares`, `_price_usdc`, `_unix`, `_days`, `_hours`).

## Label sets (PROTOCOL A20)

| Set | Definition | Wallets | Cases |
|---|---|---|---|
| `label_standard` (main training label) | trade-confirmed, informed trading, case grade E1-E4 (includes cluster members linked by money flows) | 112 | 11 |
| `label_strict` (evaluation only) | label_standard, linked to an E1-E3 claim or named by address or resolved handle in an E4 claim, with a buy before the precise news time | 19 | 7 |
| `label_broad` | trade-confirmed, informed trading, case grade E1-E5 (= `is_documented`) | 119 | 18 |

**`label_standard` is the main training label; `label_strict` is evaluation-only** (models are trained on `label_standard` and scored on strict positives, A26). `label_strict` also needs a buy before the market's precise news time; 0 wallet(s) meet the rest of the rule without one (`strict_no_prenews`). Other label columns are kept separate and never merged: `hard_negative` (A21: 10,053 rows; look-alike losers, look-alike winners in placebo markets, cleared cases), `coordinated_rule_fired` (rule output; about 1/3 expected by chance; may include copy-traders; not an allegation), `gate1`/`gate2a`/`gate2b` (frozen screens), `acdc_class` (reconstruction, not a label), `inca_flag` (published rule only; broader than Inca's list), `is_control`, `is_placebo_market`, `is_twin_market`.

## News times

Every time-dependent table exists for two cut times (`t_news_version`): `day` and `precise`. Cuts are **per market** (A25): a Gamma scheduled start (matches, earnings releases), a market deadline inside a coarse case date, or else the case time; the case-level `t_news_utc` (00:00 UTC of the earliest documented day) and `t_news_precise_utc` (a sourced minute- or hour-level time, A10, inside the coarse date, A18) are kept. 17 of 42 market-bearing cases have an exact time; the rest fall back to the day.

## Benchmarks (PROTOCOL A23, A26, A27; `benchmarks/`)

Leave-one-case-out over cases with at least 3 `label_standard` wallets, plus a time split (test = cases first claimed on or after 2026-03-01). Cells: case-weighted leave-one-case-out mean ± SD (number of folds) / time split; precise news times; seed 192. Models train on `label_standard` (`label_broad` for its own column); the `label_strict` column scores the same models on strict positives.

**Headline tasks control for how sources select cases (A27):** **T1s** ranks pre-news buyers only within the size band of the market's positives (size alone no longer separates them); **T2s** matches controls on account-age band as well as time, price and size; **T2-open** lets Orca/Inca-flagged wallets be controls. Secondary: T1 (all buyers), T2 (standard controls), T3 (case vs same-category twin markets), T3b (case vs crypto/weather placebo markets; market-type sensitive).

| Task | Metric | Model | label_standard | label_strict (eval only) | label_broad |
|---|---|---|---|---|---|
| T1s | AP | prevalence | 0.134 ± 0.192 (7) / 0.166 | 0.161 ± 0.246 (4) / 0.199 | 0.134 ± 0.192 (7) / 0.166 |
| T1s | AP | gate1_rule | 0.423 ± 0.208 (7) / 0.406 | 0.518 ± 0.372 (4) / 0.277 | 0.423 ± 0.208 (7) / 0.406 |
| T1s | AP | account_age_heuristic | 0.425 ± 0.227 (7) / 0.326 | 0.545 ± 0.375 (4) / 0.283 | 0.425 ± 0.227 (7) / 0.326 |
| T1s | AP | logistic_regression | 0.514 ± 0.238 (7) / 0.458 | 0.457 ± 0.267 (4) / 0.329 | 0.515 ± 0.236 (7) / 0.453 |
| T1s | AP | gradient_boosting_tuned | 0.476 ± 0.240 (7) / 0.438 | 0.551 ± 0.381 (4) / 0.316 | 0.488 ± 0.253 (7) / 0.394 |
| T2s | AUC | prevalence | 0.500 ± 0.000 (7) / 0.500 | 0.500 ± 0.000 (4) / 0.500 | 0.500 ± 0.000 (7) / 0.500 |
| T2s | AUC | gate1_rule | 0.755 ± 0.123 (7) / 0.772 | 0.840 ± 0.149 (4) / 0.803 | 0.755 ± 0.123 (7) / 0.772 |
| T2s | AUC | account_age_heuristic | 0.568 ± 0.101 (7) / 0.532 | 0.495 ± 0.116 (4) / 0.582 | 0.568 ± 0.101 (7) / 0.532 |
| T2s | AUC | logistic_regression | 0.703 ± 0.150 (7) / 0.788 | 0.490 ± 0.180 (4) / 0.797 | 0.753 ± 0.127 (7) / 0.795 |
| T2s | AUC | gradient_boosting_tuned | 0.715 ± 0.098 (7) / 0.760 | 0.684 ± 0.136 (4) / 0.682 | 0.763 ± 0.101 (7) / 0.746 |
| T2open | AUC | prevalence | 0.500 ± 0.000 (7) / 0.500 | 0.500 ± 0.000 (4) / 0.500 | 0.500 ± 0.000 (7) / 0.500 |
| T2open | AUC | gate1_rule | 0.724 ± 0.126 (7) / 0.662 | 0.754 ± 0.181 (4) / 0.636 | 0.724 ± 0.126 (7) / 0.662 |
| T2open | AUC | account_age_heuristic | 0.795 ± 0.146 (7) / 0.676 | 0.771 ± 0.190 (4) / 0.709 | 0.795 ± 0.146 (7) / 0.676 |
| T2open | AUC | logistic_regression | 0.733 ± 0.155 (7) / 0.824 | 0.629 ± 0.120 (4) / 0.834 | 0.768 ± 0.098 (7) / 0.837 |
| T2open | AUC | gradient_boosting_tuned | 0.847 ± 0.095 (7) / 0.760 | 0.818 ± 0.138 (4) / 0.744 | 0.847 ± 0.098 (7) / 0.720 |
| T1 | AP | prevalence | 0.004 ± 0.005 (7) / 0.004 | 0.001 ± 0.000 (4) / 0.000 | 0.004 ± 0.005 (7) / 0.004 |
| T1 | AP | gate1_rule | 0.233 ± 0.173 (7) / 0.144 | 0.362 ± 0.380 (4) / 0.089 | 0.233 ± 0.173 (7) / 0.144 |
| T1 | AP | account_age_heuristic | 0.051 ± 0.075 (7) / 0.046 | 0.005 ± 0.006 (4) / 0.001 | 0.051 ± 0.075 (7) / 0.046 |
| T1 | AP | logistic_regression | 0.363 ± 0.228 (7) / 0.352 | 0.214 ± 0.200 (4) / 0.226 | 0.377 ± 0.221 (7) / 0.317 |
| T2 | AUC | prevalence | 0.500 ± 0.000 (7) / 0.500 | 0.500 ± 0.000 (4) / 0.500 | 0.500 ± 0.000 (7) / 0.500 |
| T2 | AUC | gate1_rule | 0.731 ± 0.130 (7) / 0.666 | 0.760 ± 0.180 (4) / 0.647 | 0.731 ± 0.130 (7) / 0.666 |
| T2 | AUC | account_age_heuristic | 0.800 ± 0.147 (7) / 0.677 | 0.777 ± 0.189 (4) / 0.725 | 0.800 ± 0.147 (7) / 0.677 |
| T2 | AUC | logistic_regression | 0.761 ± 0.111 (7) / 0.842 | 0.677 ± 0.069 (4) / 0.859 | 0.793 ± 0.078 (7) / 0.845 |
| T3 | AUC | prevalence | 0.500 ± 0.000 (7) / 0.500 | 0.500 ± 0.000 (4) / 0.500 | 0.500 ± 0.000 (7) / 0.500 |
| T3 | AUC | gate1_rule | 0.754 ± 0.156 (7) / 0.665 | 0.763 ± 0.143 (4) / 0.780 | 0.754 ± 0.156 (7) / 0.665 |
| T3 | AUC | logistic_regression | 0.883 ± 0.087 (7) / 0.915 | 0.922 ± 0.084 (4) / 0.985 | 0.883 ± 0.082 (7) / 0.929 |
| T3 | AUC | gradient_boosting_tuned | 0.872 ± 0.069 (7) / 0.913 | 0.967 ± 0.053 (4) / 1.000 | 0.861 ± 0.106 (7) / 0.891 |
| T3b | AUC | prevalence | 0.500 ± 0.000 (7) / 0.500 | 0.500 ± 0.000 (4) / 0.500 | 0.500 ± 0.000 (7) / 0.500 |
| T3b | AUC | gate1_rule | 0.529 ± 0.273 (7) / 0.423 | 0.456 ± 0.265 (4) / 0.456 | 0.529 ± 0.273 (7) / 0.423 |
| T3b | AUC | logistic_regression | 0.873 ± 0.099 (7) / 0.909 | 0.925 ± 0.116 (4) / 0.953 | 0.881 ± 0.094 (7) / 0.914 |
| T3b | AUC | gradient_boosting_tuned | 0.958 ± 0.042 (7) / 0.924 | 0.967 ± 0.058 (4) / 0.944 | 0.865 ± 0.180 (7) / 0.878 |

Base result for T2: matched same-side controls win about as often as documented episodes, so outcomes cannot separate them. Full per-fold results, leakage lists and the known shortcuts are in `benchmarks/README.md` and `benchmarks/baselines.json`.

## Coverage

- Cases by grade: E1 4, E2 3, E3 10, E4 13, E5 28, E6 8. Investigation outcome: unresolved 44, under_investigation 10, sanctioned 4, charged 3, cleared_analyst 2, disputed 2, cleared_official 1.
- Claims: 124 (109 verified by reading the source page, 15 pending).
- Twin markets: 3,508; placebo markets: 4,227.
- Trades: Polymarket-v1 (Hugging Face, 746 M fills to 2026-04-28) and the Polymarket Data API v2 after that. Kalshi trades and accounts are not public here.

## Limitations

- Labels are allegations by sources; grades say how strong the source is, not whether trading was informed.
- Selection bias (PROTOCOL 8): what was noticed and published. Ordinary-looking informed trading is missing.
- Few, clustered positives; results on 1-6 test cases are noisy. Report per case and case-weighted.
- Cluster members (`label_standard`) are linked by money flows, not flagged one by one.
- The money graph is not built (no archive Polygon RPC); funding features are empty.
- 15 claims are pending (pages blocked or unread); the blind second-extractor check (A4) is pending.
- Rule outputs (coordinated-buyer rule, Gate 1, ACDC, Inca) are screens with known false-positive rates, not labels.

## Ethics, data protection and removal

No personal names; no identity work; market titles naming listed people are withheld. Pseudonymous addresses can be personal data: see `docs/DATA_PROTECTION.md` (lawful basis, minimisation, retention, rights). To submit a case, correct a row or request removal, see `CONTRIBUTING.md`. A subject's reply is recorded in `claims.right_of_reply`. How claims were extracted (an AI model under a written protocol) and the blind-check status: `docs/EXTRACTION.md`.

## Licence

CC-BY-4.0 for PMITC tables and docs; MIT for code. Polymarket-v1 (TimeSeventeen, CC-BY-4.0) for `source = hf_polymarket_v1` fills. Upstream licences: `docs/LICENSES_UPSTREAM.md`.

## How to cite

> Yildiz, I. (2026). *Prediction-Market Informed-Trading Casebook (PMITC)*, version 1.2.0 [dataset]. Protocol v1.0 with amendments A1 to A28. https://github.com/ibrhmyi/insider

See `docs/CITATION.cff`. Please also cite Polymarket-v1 for the fills.
