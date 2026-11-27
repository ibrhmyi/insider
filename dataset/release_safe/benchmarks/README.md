# PMITC v1.0 benchmark tasks

Rules: PROTOCOL A15. `splits.csv` is frozen: splits are grouped by case (no case in two splits) and ordered in time
(`test` = cases whose first claim is on or after **2026-03-01**). Placebo markets take the split of their matched case
(each placebo is used once, A14). Every task runs on both news-time versions; `precise` (A10) is the headline.
Run: `python3 pmitc_bench.py` (writes `baselines.json`, seed 192), or `notebooks/02_baselines.ipynb`.

Labels are allegations by named sources (`is_documented` = suspected by a source, confirmed by the wallet's own fills, in an informed-trading case (A19)).
They are sparse and clustered: 74 of the 119 documented wallets come from two cases (52 Feb-28 Iran strike, 22 KPMG), and 87 are cluster members linked by money flows rather than flagged one by one. They are also biased toward what was noticed (PROTOCOL 8). Every metric is reported per case and case-weighted (each case counts once) next to the pooled value.
Treat scores as "how well a method finds wallets that sources flagged", not as insider-detection accuracy.

## T1: within-market ranking
- **Unit:** one row per (case market, wallet) from `positions` (`market_set = case`, `is_main_side = true`, one version).
- **Task:** rank all pre-news buyers of each case market. Positives: `is_documented`. Only markets with at least one positive are scored.
- **Metrics:** average precision, precision@k and recall@k (k = 10, 100) per market, averaged within each case, then over cases.
- **Baselines:** random, a rule (`gate1_score`, ties by size), logistic regression, gradient boosting (trained on `train` with negatives subsampled, seed 192).
- **Do not use (leakage):** `is_documented`, `doc_grade`, `coordinated_rule_fired`, `triggering_suspect`, `placebo_rate`, `is_control`, `gate1` (a label), `gate2b` and `is_shortest_sufficient` (use the resolution), every `_post` column, ids, absolute times (`t_cut_ts`, `first_buy_ts`, `last_buy_ts` except as differences to the cut), `source_pre`.

## T2: episode classification
- **Unit:** `episodes` rows: documented episodes (`role = suspected`) vs their matched controls (`control_same_side`, `control_other_side_large_buyer`).
- **Metrics:** AUC (pooled and case-weighted) and log loss, case-grouped 5-fold CV, and train -> test.
- **Base result to report:** matched same-side controls win about as often as documented episodes (`won_post` by role), so outcome-based features cannot separate them; the task asks whether behaviour before the news can.
- **Do not use:** `share_on_this_ladder_market` (construction artifact: controls are sampled one market at a time, so it is always 1 for them; alone it gives AUC 0.97), `role`, `episode_id`, `control_of`, `wallet`, `case_share_of_lifetime_volume` (lifetime denominator), `is_shortest_sufficient`, `follower_*_60m` (window can cross t_news), every `_post` column, and the empty funding columns.

## T3: market-level detection
- **Unit:** case markets with matched placebos vs those placebo markets (A14), features from pre-cut flow only (`market_minutes` with `minutes_from_cut < 0`, `positions` before the cut).
- **Metric:** AUC, pooled and case-weighted (case-grouped CV and train -> test).
- **Do not use:** `market_set` / `is_placebo_market` (the label), any minute at or after the cut, `_post` columns, `placebo_category`, total volume and resolution fields, question or slug text. Placebo categories (crypto prices, weather) differ from case markets in kind, so a high AUC partly measures market type; report it next to the matched-volume design, not as detection power.

Results: `baselines.json` (both versions), summarised in `../docs/README.md`.
