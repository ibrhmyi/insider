"""Writes the dataset card release/README.md (GitHub, Kaggle, Hugging Face; HF YAML header with one config per table) from the
built tables and benchmarks/baselines.json, and a copy at release/docs/README.md. Usage: python3 build/v1/card.py"""
import json, os, sys
import duckdb, numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from schema import TABLES  # noqa

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REL = os.path.join(D, "release"); DATA = os.path.join(REL, "data")
rp = lambda t: pd.read_parquet(os.path.join(DATA, f"{t}.parquet"))
n = lambda t: duckdb.sql(f"SELECT count(*) FROM read_parquet('{DATA}/{t}*.parquet')").fetchall()[0][0]
cases, claims, wallets, markets = rp("cases"), rp("claims"), rp("wallets"), rp("markets")
hn, tw, pl = rp("hard_negatives"), rp("twin_markets"), rp("placebo_markets")
B = json.load(open(os.path.join(REL, "benchmarks", "baselines.json")))
ls = {s: int(wallets[s].sum()) for s in ["label_strict", "label_standard", "label_broad"]}
lsc = {s: int(wallets[wallets[s]].case_id.nunique()) for s in ls}
exact = markets.groupby("case_id").t_news_precise_precision.first()
n_exact = int((exact != "day_fallback").sum())
fmt = lambda x: "n/a" if x is None else f"{x:.3f}"


def cell(task, s, model):
    r = B["precise"][s][task]["summary"].get(model)
    if not r or r["loco_mean"] is None:
        return "n/a"
    return f"{fmt(r['loco_mean'])} ± {fmt(r['loco_sd'])} ({r['n_loco_folds']}) / {fmt(r['time_split'])}"


bench_rows = []
for task, metric in [("T1", "AP, case-weighted"), ("T2", "AUC, case-weighted"), ("T3", "AUC, case-weighted"), ("T3b", "AUC, case-weighted")]:
    for model in ["prevalence", "gate1_rule", "account_age_heuristic", "logistic_regression", "gradient_boosting_tuned"]:
        if model in B["precise"]["label_strict"][task]["summary"] or model in B["precise"]["label_standard"][task]["summary"]:
            bench_rows.append(f"| {task} | {metric} | {model} | " + " | ".join(cell(task, s, model) for s in ["label_strict", "label_standard", "label_broad"]) + " |")
yaml_cfg = []
for t in TABLES:
    files = "data/fills_part*.parquet" if t == "fills" else f"data/{t}.parquet"
    yaml_cfg.append(f"- config_name: {t}\n  data_files: \"{files}\"" + ("\n  default: true" if t == "cases" else ""))
guide = "\n".join(f"| `{t}` | {n(t if t != 'fills' else 'fills_part'):,} | {TABLES[t]['desc']} |" for t in TABLES)
grade = cases.case_grade.value_counts().sort_index().to_dict(); outc = cases.investigation_outcome.value_counts().to_dict()
card = f"""---
license: cc-by-4.0
pretty_name: "PMITC: Prediction-Market Informed-Trading Casebook"
language: [en]
tags: [prediction-markets, polymarket, kalshi, market-integrity, anomaly-detection, tabular, finance]
task_categories: [tabular-classification]
size_categories: [10M<n<100M]
configs:
{chr(10).join(yaml_cfg)}
---

# PMITC v1.1: Prediction-Market Informed-Trading Casebook

PMITC is a source-traced register of **publicly documented, suspected** informed trading on prediction markets (Polymarket and Kalshi): {len(cases)} cases and {len(claims)} claims from courts, regulators, platforms, researchers, journalists and on-chain analysts, each graded E1 (adjudicated) to E6 (rule-based screen), joined to the trades. For every case market it ships every fill, every buyer before the news, matched controls, hard negatives, same-category "twin" markets and placebo markets where nobody can know the outcome early, so that detection methods can be trained and tested honestly. **Every label is an allegation by a named source ("flagged by <source>"), not a finding.** No table contains a personal name.

![Cases on a timeline by evidence grade](docs/cases_timeline.png)

> **Read first.** (1) Labels are allegations; only E1 is adjudicated, and E1 is mostly Kalshi discipline without public wallets. (2) Positives are few and clustered: {ls['label_strict']} wallets in `label_strict`, {ls['label_broad']} in `label_broad`, and two cases hold 74 of the {ls['label_broad']} broad positives. (3) The collection over-represents fresh wallets making large, cheap, well-timed bets on viral markets; do not estimate prevalence from it.

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
{guide}

Every column has a type, unit, allowed values, source and leakage note in `docs/CODEBOOK.md`. Parquet for all tables; CSV for tables under 50 MB. Keys: every table has a declared primary key; ids are stable (`case_id`, `claim_id`, `condition_id`, `asset_id`, `wallet`, `episode_id`). Timestamps are UTC; amounts carry units in their names (`_usdc`, `_shares`, `_price_usdc`, `_unix`, `_days`, `_hours`).

## Label sets (PROTOCOL A20)

| Set | Definition | Wallets | Cases |
|---|---|---|---|
| `label_strict` | trade-confirmed, informed trading, and either linked to an E1-E3 claim or named by address or resolved handle in an E4 claim | {ls['label_strict']} | {lsc['label_strict']} |
| `label_standard` | trade-confirmed, informed trading, case grade E1-E4 (includes cluster members linked by money flows) | {ls['label_standard']} | {lsc['label_standard']} |
| `label_broad` | trade-confirmed, informed trading, case grade E1-E5 (= `is_documented`) | {ls['label_broad']} | {lsc['label_broad']} |

Lead with `label_strict`. Other label columns are kept separate and never merged: `hard_negative` (A21: {len(hn):,} rows; look-alike losers, look-alike winners in placebo markets, cleared cases), `coordinated_rule_fired` (rule output; about 1/3 expected by chance; may include copy-traders; not an allegation), `gate1`/`gate2a`/`gate2b` (frozen screens), `acdc_class` (reconstruction, not a label), `inca_flag` (published rule only; broader than Inca's list), `is_control`, `is_placebo_market`, `is_twin_market`.

## News times

Every time-dependent table exists for two cut times (`t_news_version`): `day` (00:00 UTC on the earliest documented day) and `precise` (a sourced minute- or hour-level time, A10; used only inside the coarse date, A18). {n_exact} of {markets.case_id.nunique()} market-bearing cases have an exact time; the rest fall back to the day.

## Benchmarks (PROTOCOL A23; `benchmarks/`)

Leave-one-case-out over cases with at least 3 `label_standard` wallets, plus a time split (test = cases first claimed on or after 2026-03-01). Cells: leave-one-case-out mean ± SD (number of folds) / time split; precise news times; seed 192. T1 ranks all pre-news buyers in a case market; T2 separates documented episodes from matched controls; T3 separates case markets from same-category twin markets; T3b from crypto/weather placebo markets (market-type sensitive).

| Task | Metric | Model | label_strict | label_standard | label_broad |
|---|---|---|---|---|---|
{chr(10).join(bench_rows)}

Base result for T2: matched same-side controls win about as often as documented episodes, so outcomes cannot separate them. Full per-fold results, leakage lists and the known shortcuts are in `benchmarks/README.md` and `benchmarks/baselines.json`.

## Coverage

- Cases by grade: {", ".join(f"{k} {v}" for k, v in grade.items())}. Investigation outcome: {", ".join(f"{k} {v}" for k, v in outc.items())}.
- Claims: {len(claims)} ({int((claims.verified == 'true').sum())} verified by reading the source page, {int((claims.verified == 'pending').sum())} pending).
- Twin markets: {int(tw.twin_id.notna().sum()):,}; placebo markets: {int(pl.placebo_id.notna().sum()):,}.
- Trades: Polymarket-v1 (Hugging Face, 746 M fills to 2026-04-28) and the Polymarket Data API v2 after that. Kalshi trades and accounts are not public here.

## Limitations

- Labels are allegations by sources; grades say how strong the source is, not whether trading was informed.
- Selection bias (PROTOCOL 8): what was noticed and published. Ordinary-looking informed trading is missing.
- Few, clustered positives; results on 1-6 test cases are noisy. Report per case and case-weighted.
- Cluster members (`label_standard`) are linked by money flows, not flagged one by one.
- The money graph is not built (no archive Polygon RPC); funding features are empty.
- {int((claims.verified == "pending").sum())} claims are pending (pages blocked or unread); the blind second-extractor check (A4) is pending.
- Rule outputs (coordinated-buyer rule, Gate 1, ACDC, Inca) are screens with known false-positive rates, not labels.

## Ethics, data protection and removal

No personal names; no identity work; market titles naming listed people are withheld. Pseudonymous addresses can be personal data: see `docs/DATA_PROTECTION.md` (lawful basis, minimisation, retention, rights). To submit a case, correct a row or request removal, see `CONTRIBUTING.md`. A subject's reply is recorded in `claims.right_of_reply`. How claims were extracted (an AI model under a written protocol) and the blind-check status: `docs/EXTRACTION.md`.

## Licence

CC-BY-4.0 for PMITC tables and docs; MIT for code. Polymarket-v1 (TimeSeventeen, CC-BY-4.0) for `source = hf_polymarket_v1` fills. Upstream licences: `docs/LICENSES_UPSTREAM.md`.

## How to cite

> Yildiz, I. (2026). *Prediction-Market Informed-Trading Casebook (PMITC)*, version 1.1.0 [dataset]. Protocol v1.0 with amendments A1 to A24. https://github.com/ibrhmyi/insider

See `docs/CITATION.cff`. Please also cite Polymarket-v1 for the fills.
"""
open(os.path.join(REL, "README.md"), "w").write(card)
open(os.path.join(REL, "docs", "README.md"), "w").write(card.split("---\n", 2)[2].lstrip().replace("](docs/", "]("))
print("card written")
