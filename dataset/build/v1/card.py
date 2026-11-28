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
    if not r or r.get("loco_min") is None:
        return "n/a"
    if r.get("reporting") == "per_fold_only_A32":  # A32: fewer than 6 folds -> range of fold values only
        return f"folds {fmt(r['loco_min'])}-{fmt(r['loco_max'])} ({r['n_loco_folds']}) / {fmt(r['time_split'])}"
    return f"{fmt(r['loco_mean'])} ± {fmt(r['loco_sd'])} ({r['n_loco_folds']}) / {fmt(r['time_split'])}"


XU = B["excluded_unreliable"]
EC = json.load(open(os.path.join(D, "logs", "econ_positions_compare.json")))  # A34 comparison (build/v1/econ_compare.py)
ec = lambda ms: f"{EC[ms + '/precise']['all']['directional_econ_only_share']:.0%}"
LBL = pd.read_csv(os.path.join(D, "logs", "econ_labelled_prenews.csv"))
n_std_dir = int(LBL[LBL.label_standard.astype(str).str.lower() == "true"].econ_pre.sum())
# Maduro strict fold (one positive): tasks where logistic regression ranks the wallet below all its controls
MAD = sorted(t for t in ["T1s", "T2s", "T2w", "T2open", "T1", "T2"] if B["precise"]["label_strict"][t]["summary"].get("logistic_regression", {}).get("fold_values", {}).get("loco:maduro-2026-01") == 0.0)
MAD_TXT = (f"- In the strict leave-one-case-out fold for Maduro (one positive: the wallet in the charged, E2 case), logistic regression ranks that wallet below all of its matched controls (AUC 0.0 in {', '.join(MAD)}): the pattern learned from the cluster-heavy training cases does not match the strongest-evidence case."
           if MAD else "- In the strict Maduro fold (one positive), results rest on a single wallet; see the per-fold values in `baselines.json`.")


A35 = json.load(open(os.path.join(D, "logs", "a35_report.json")))["precise"]  # build/v1/a35_report.py
a35l = A35["label_sets"]
HEAD = ["T1s", "T2s", "T2w", "T2open"]
nf = {s: {t: B["precise"][s][t]["summary"].get("logistic_regression", {}).get("n_loco_folds", 0) for t in HEAD} for s in ["label_strict", "label_standard", "label_broad"]}
sf = sorted(set(nf["label_strict"].values()))
STRICT_FOLDS = (f"**`label_strict` has fewer than 4 usable leave-one-group-out folds** ({', '.join(f'{t}: {nf['label_strict'][t]}' for t in HEAD)}; plus the time split): strict results are anecdotal, one fold can move the range by more than any model difference, and no strict number should be read as a detector's accuracy."
                if max(sf) < 4 else f"`label_strict` has {', '.join(f'{t}: {nf['label_strict'][t]}' for t in HEAD)} usable leave-one-group-out folds (plus the time split); below 6 folds results are per fold only (A32).")
ea = claims[claims.claim_timing == "ex_ante"]; eaw = ea[ea.alleged_side_won.notna()]
ea_full = eaw[eaw.claim_day_contains_resolution == False]  # noqa: E712  (A49)
TW_CM = int(tw[tw.twin_id.notna()].case_condition_id.nunique())
bench_rows = []
for task, metric in [("T1s", "AP"), ("T2s", "AUC"), ("T2w", "AUC"), ("T2open", "AUC"), ("T1", "AP"), ("T2", "AUC"), ("T3", "AUC"), ("T3b", "AUC")]:
    for model in ["prevalence", "gate1_rule", "account_age_heuristic", "logistic_regression", "gradient_boosting_tuned"]:
        if model in B["precise"]["label_strict"][task]["summary"] or model in B["precise"]["label_standard"][task]["summary"]:
            bench_rows.append(f"| {task} | {metric} | {model} | " + " | ".join(cell(task, s, model) for s in ["label_standard", "label_strict", "label_broad"]) + " |")
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

# PMITC v1.2.1: Prediction-Market Informed-Trading Casebook

PMITC is a source-traced register of **publicly documented, suspected** informed trading on prediction markets (Polymarket and Kalshi): {len(cases)} cases and {len(claims)} claims from courts, regulators, platforms, researchers, journalists and on-chain analysts, each graded E1 (adjudicated) to E6 (rule-based screen), joined to the trades. For every case market it ships every fill, every buyer before the news, matched controls, hard negatives, same-category "twin" markets and placebo markets where nobody can know the outcome early, so that detection methods can be trained and tested honestly. **Every label is an allegation by a named source ("flagged by <source>"), not a finding.** No table contains a personal name.

![Cases on a timeline by evidence grade](docs/cases_timeline.png)

> **Read first.** (1) Labels are allegations; only E1 is adjudicated, and E1 is mostly Kalshi discipline without public wallets. (2) Positives are few and clustered: {ls['label_strict']} wallets in `label_strict`, {ls['label_broad']} in `label_broad`, and two cases hold 74 of the {ls['label_broad']} broad positives. (3) The collection over-represents fresh wallets making large, cheap, well-timed bets on viral markets; do not estimate prevalence from it.

## Quick start

```python
import pandas as pd; positions = pd.read_parquet("data/positions.parquet", filters=[("t_news_version", "==", "precise"), ("t_news_reliable", "==", True)])  # A29 default
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
| `label_standard` (main training label) | trade-confirmed, informed trading, case grade E1-E4 (includes cluster members linked by money flows) | {ls['label_standard']} | {lsc['label_standard']} |
| `label_strict` (evaluation only) | label_standard, linked to an E1-E3 claim or named by address or resolved handle in an E4 claim, with a buy before the precise news time | {ls['label_strict']} | {lsc['label_strict']} |
| `label_broad` | trade-confirmed, informed trading, case grade E1-E5 (= `is_documented`) | {ls['label_broad']} | {lsc['label_broad']} |

**`label_standard` is the main training label; `label_strict` is evaluation-only** (models are trained on `label_standard` and scored on strict positives, A26). `label_strict` also needs a buy before the market's precise news time; {int(wallets.strict_no_prenews.sum())} wallet(s) meet the rest of the rule without one (`strict_no_prenews`). Other label columns are kept separate and never merged: `hard_negative` (A21: {len(hn):,} rows; look-alike losers, look-alike winners in placebo markets, cleared cases), `coordinated_rule_fired` (rule output; about 1/3 expected by chance; may include copy-traders; not an allegation), `gate1`/`gate2a`/`gate2b` (frozen screens), `acdc_class` (reconstruction, not a label), `inca_flag` (published rule only; broader than Inca's list), `is_control`, `is_placebo_market`, `is_twin_market`.

**Positives are alleged positions (A35).** A wallet's alleged positions are the (market, side) pairs its own claims, or its cluster's claims, describe (`claim_positions`, mapped from claim text and market questions only; A35.1, A48). Of {A35['suspected_side_positions']} pre-news positions of labelled wallets in their own cases (precise cut), {A35['alleged_positions']} are alleged; the other {A35['labelled_other_positions']} are `role = labelled_other_position` in `episodes` and are not positives. All {A35['losing_positions']} losing suspected-side positions are labelled-other positions; no alleged position lost. On alleged positions: `label_strict` {a35l['label_strict']['alleged_positions']} positions from {a35l['label_strict']['wallets_with_alleged_position']} wallets in {a35l['label_strict']['cases_with_alleged_position']} cases, `label_standard` {a35l['label_standard']['alleged_positions']} from {a35l['label_standard']['wallets_with_alleged_position']} wallets in {a35l['label_standard']['cases_with_alleged_position']} cases, `label_broad` {a35l['label_broad']['alleged_positions']} from {a35l['label_broad']['wallets_with_alleged_position']} wallets in {a35l['label_broad']['cases_with_alleged_position']} cases. {A35['dropouts']['wallets']} labelled wallets drop out ({A35['dropouts']['by_reason'].get('no_linked_or_cluster_claim_names_market_or_side', 0)} because no claim names a market or side, e.g. all of `kpmg-earnings-2025-26` and `world-cup-2026-06`; {A35['dropouts']['by_reason'].get('alleged_market_or_side_not_held_before_cut', 0)} because they held no alleged market and side before the cut; `logs/a35_dropouts.csv`). The wallet-level version (any position of a labelled wallet) is reported as secondary (`baselines.json`, `wallet_level`).

## News times

Every time-dependent table exists for two cut times (`t_news_version`): `day` and `precise`. Cuts are **per market** (A25): a Gamma scheduled start (matches, earnings releases), a market deadline inside a coarse case date, or else the case time; the case-level `t_news_utc` (00:00 UTC of the earliest documented day) and `t_news_precise_utc` (a sourced minute- or hour-level time, A10, inside the coarse date, A18) are kept. {n_exact} of {markets.case_id.nunique()} market-bearing cases have an exact time; the rest fall back to the day. A scheduled start is used only if it is before the market's close (A30).

**`t_news_reliable` (A29, A29.1).** A market whose cut came from the deadline rule (a coarse case date and nothing better for that market) has no trustworthy cut: `t_news_reliable = false` (the deadline time is kept as `markets.t_news_deadline_rule_utc`). Sourced exact times and checked scheduled starts are reliable; markets that fall back to the case date keep `true` (their cut is the start of the documented period, earlier than the news). **Default analyses and every benchmark use `t_news_reliable = true` only.** This removes {XU['n_markets']} of {XU['n_markets_total']} markets: whole cases {", ".join(f"`{c}`" for c in XU['cases_fully_removed'])}; part of {", ".join(f"`{c}`" for c in XU['cases_partly_removed'])}. Of the documented wallets with a pre-news position it keeps {XU['positives']['label_strict']['kept']} of {XU['positives']['label_strict']['with_prenews_position']} strict, {XU['positives']['label_standard']['kept']} of {XU['positives']['label_standard']['with_prenews_position']} standard and {XU['positives']['label_broad']['kept']} of {XU['positives']['label_broad']['with_prenews_position']} broad.

## Benchmarks (PROTOCOL A23, A26, A27, A29, A32, A33, A34; `benchmarks/`)

Leave-one-group-out over connected case groups (A37: cases sharing a market or Gamma event are one group) with at least 3 `label_standard` wallets, plus a time split by group (test = groups first claimed on or after 2026-03-01). Positives are alleged positions (A35). Only `t_news_reliable = true` markets (A29) and directional pre-news positions in the economic view (A34-A34.2). Cells: case-weighted leave-one-case-out mean ± SD (number of folds) / time split; precise news times; seed 192. **With fewer than 6 folds (A32) a cell gives only the range of fold values** ("folds min-max (n) / time split"); per-fold values are in `baselines.json`. This applies to every `label_strict` cell. {STRICT_FOLDS} Models train on `label_standard` (`label_broad` for its own column); the `label_strict` column scores the same models on strict positives.

**Headline tasks control for how sources select cases (A27):** **T1s** ranks pre-news buyers only within the size band of the market's positives (size alone no longer separates them); **T2s** matches controls on account-age band as well as time, price and size; **T2w** matches on account-age and prior win-rate bands (A33); both retry with the adjacent band before dropping an episode (`relaxed_band`); **T2-open** lets Orca/Inca-flagged wallets be controls. Secondary: T1 (all buyers), T2 (standard controls), T3 (case vs same-category twin markets), T3b (case vs crypto/weather placebo markets; market-type sensitive).

| Task | Metric | Model | label_standard | label_strict (eval only) | label_broad |
|---|---|---|---|---|---|
{chr(10).join(bench_rows)}

Base result for T2: matched same-side controls win about as often as documented episodes, so outcomes cannot separate them. Full per-fold results, leakage lists and the known shortcuts are in `benchmarks/README.md` and `benchmarks/baselines.json`.

## Coverage

- Cases by grade: {", ".join(f"{k} {v}" for k, v in grade.items())}. Investigation outcome: {", ".join(f"{k} {v}" for k, v in outc.items())}.
- Claims: {len(claims)} ({int((claims.verified == 'true').sum())} verified by reading the source page, {int((claims.verified == 'pending').sum())} pending).
- Twin markets: {int(tw.twin_id.notna().sum()):,} for {TW_CM} case markets (A46: chosen from the full Polymarket-v1 catalog with the A38 question-type and subject rules; Data-API-era case markets have no catalog category and get no twins); placebo markets: {int(pl.placebo_id.notna().sum()):,}.
- Claim timing (A42, A49): {len(ea)} claims were published before their alleged market resolved (`ex_ante`); the alleged side won in {int((eaw.alleged_side_won == True).sum())} of {len(eaw)}. Only {len(ea_full)} of them are dated a full day before the resolution ({int((ea_full.alleged_side_won == True).sum())} won); the others are dated on the resolution day (`claim_day_contains_resolution`). The March 31 ceasefire flag (CL0031) is the clearest ex-ante claim, and its market resolved No.
- Trades: Polymarket-v1 (Hugging Face, 746 M fills to 2026-04-28) and the Polymarket Data API v2 after that. Kalshi trades and accounts are not public here.

## Limitations

- Labels are allegations by sources; grades say how strong the source is, not whether trading was informed.
- Selection bias (PROTOCOL 8): what was noticed and published. Ordinary-looking informed trading is missing.
- Few, clustered positives; results on 1-6 test cases are noisy. Report per case and case-weighted.
- Cluster members (`label_standard`) are linked by money flows, not flagged one by one.
- The money graph is not built (no archive Polygon RPC); funding features are empty.
- {int((claims.verified == "pending").sum())} claims are pending (pages blocked or unread); the blind second-extractor check (A4) is pending.
- Rule outputs (coordinated-buyer rule, Gate 1, ACDC, Inca) are screens with known false-positive rates, not labels.
{MAD_TXT}
- Positions are economic and net of full sets (A34-A34.2): a SELL of a token the wallet did not hold is read as a BUY of the other token, and a held Yes + No pair counts as no direction. The raw fills are unchanged and the raw view stays comparable (`raw_view_prenews_buy`, `econ_inferred_buy_usdc_pre`). Merges cannot be inferred from fills, so some full sets come from buys of both tokens. In this view {n_std_dir} of {ls['label_standard']} `label_standard` wallets have a directional pre-news position in their case. The share of directional pre-news positions that exist only in the economic view is {ec('case')} in case markets, {ec('twin')} in twins and {ec('placebo')} in placebos (precise cut; the same for non-market-makers): the re-reading is market mechanics, not a case-market signal.
- `is_market_maker` is a reporting flag with a simple rule (both tokens traded in most active minutes); it also flags some large one-way buyers (see the run-11 report).

## Ethics, data protection and removal

No personal names; no identity work; market titles naming listed people are withheld. Pseudonymous addresses can be personal data: see `docs/DATA_PROTECTION.md` (lawful basis, minimisation, retention, rights). To submit a case, correct a row or request removal, see `CONTRIBUTING.md`. A subject's reply is recorded in `claims.right_of_reply`. How claims were extracted (an AI model under a written protocol) and the blind-check status: `docs/EXTRACTION.md`.

## Licence

CC-BY-4.0 for PMITC tables and docs; MIT for code. Polymarket-v1 (TimeSeventeen, CC-BY-4.0) for `source = hf_polymarket_v1` fills. Upstream licences: `docs/LICENSES_UPSTREAM.md`.

## How to cite

> Yildiz, I. (2026). *Prediction-Market Informed-Trading Casebook (PMITC)*, version 1.2.1 [dataset]. Protocol v1.0 with amendments A1 to A49. https://github.com/ibrhmyi/insider

See `docs/CITATION.cff`. Please also cite Polymarket-v1 for the fills.
"""
open(os.path.join(REL, "README.md"), "w").write(card)
open(os.path.join(REL, "docs", "README.md"), "w").write(card.split("---\n", 2)[2].lstrip().replace("](docs/", "]("))
print("card written")
