# PMITC v1.1 benchmark tasks

Rules: PROTOCOL A15 and A23. Run `python3 pmitc_bench.py` (writes `baselines.json`, seed 192; about an hour with gradient-boosting tuning) or `python3 pmitc_bench.py --quick`; `notebooks/03_benchmarks.ipynb` shows the results.

Labels are allegations by named sources. Positives are sparse and clustered: 74 of the 119 `label_broad` wallets come from two cases (52 Feb-28 2026 Iran strike, 22 KPMG), and 87 are cluster members linked by money flows. Every task therefore runs on three nested label sets (`label_strict` ⊆ `label_standard` ⊆ `label_broad`, A20) and every metric is reported per fold, per case and case-weighted. In a run on a smaller set, documented wallets outside the set are dropped (neither positive nor negative).

## Folds
- **Leave-one-case-out** over every case with at least 3 `label_standard` wallets in the task's rows: the model is trained on all other cases and tested on that case. Reported as mean, SD, minimum and maximum over folds. A fold with no positive of the label set in its test case is skipped (strict has fewer folds).
- **Time split** (A15, `splits.csv`): train = cases first claimed before 2026-03-01, test = on or after.

## Baselines
- `prevalence`: constant score (AP equals prevalence; AUC 0.5). It replaces the random baseline, whose expectation is the prevalence and whose single draws vary widely (run 9 report: random AP over 100 seeds on the old test split had mean 0.020, SD 0.044).
- `gate1_rule`: the frozen Gate 1 score (ties by size); for T3 the market's Gate 1 rate.
- `account_age_heuristic`: younger account (first Polymarket-v1 fill) ranks higher (T1, T2).
- `logistic_regression`: standardised, L2, C = 1.
- `gradient_boosting_tuned`: HistGradientBoosting tuned by inner leave-cases-out CV on the training cases (grid in `baselines.json`), precise version only. Flagged `below_prevalence` when it scores under the prevalence baseline.

## Tasks
- **T1, within-market ranking.** Unit: (case market, wallet) on the wallet's main token, from `positions`. Rank all pre-news buyers; positives = the label set. Metric: per-market AP (and P@10, R@10, R@100), averaged within case, then over cases.
- **T2, episode classification.** Unit: `episodes` rows, documented episodes vs their matched controls (same side and large other-side buyers). Metric: AUC within each test case, case-weighted. Base result: matched same-side controls win about as often as documented episodes, so outcomes cannot separate them.
- **T3, case vs twin markets** (A22): case markets where a wallet of the label set bought before the cut, vs their same-category, same-volume-decile, same-duration, same-year twins, from pre-cut flow (`market_minutes` before the cut, `positions`). Metric: AUC, case-weighted. `all_case_markets` runs every matched case market.
- **T3b, case vs placebo markets** (A14): the same with crypto-price and weather placebos. **Market-type sensitive**: placebos differ from case markets in kind, so a high score partly measures market type.

## Leakage: do not use
- T1: `is_documented`, `doc_grade`, `label_*`, `hard_negative*`, `coordinated_rule_fired`, `triggering_suspect`, `placebo_rate`, `is_control`, `is_placebo_market`, `is_twin_market`, `gate1` (a label), `gate2b` and `is_shortest_sufficient` (use the resolution), every `_post` column, ids, absolute times (`t_cut_unix`, `first_buy_unix`, `last_buy_unix`) except as differences to the cut, `source_pre`, `vol_to_day_usdc` (includes the rest of the cut's day).
- T2: `share_on_this_ladder_market`, `role`, `episode_id`, `control_of`, `wallet`, `label_*`, `case_share_of_lifetime_volume` (lifetime denominator), `is_shortest_sufficient`, `n_follower_wallets_60m` / `follower_buy_usdc_60m` (window can pass t_news), every `_post` column, the empty funding columns.
- T3/T3b: `market_set`, `is_placebo_market`, `is_twin_market`, any minute at or after the cut, `_post` columns, category fields, resolution, outcome and total-volume fields, question and slug text.

## Known shortcuts (features that separate classes for construction reasons)
- **T2 `share_on_this_ladder_market`**: controls are sampled one market at a time, so the value is 1 for every control; alone it gives AUC about 0.97. Excluded.
- **T2 `hours_first_buy_to_tnews`**: controls are matched on first-buy time (24-72 h), so this feature is controlled by design; its univariate AUC should be near 0.5 (reported).
- **T2 `prior_net_long_win_rate`, `n_prior_markets` (univariate AUC 0.82-0.88)**: partly construction: control pools exclude Orca- and Inca-flagged wallets (A6.10), which removes many strong past traders from the controls; partly selection: sources flag fresh wallets.
- **T2 `account_age_days_at_first_buy`**: the source bias, not construction: sources flag fresh wallets, so the one-feature account-age heuristic matches or beats the models. A detector that only learns "new wallet" learns the selection rule of the press.
- **T1 size features (`buy_usdc_pre`, `market_usdc_pre`, `n_buy_fills_pre`; univariate AUC 0.93-0.98)**: selection, not construction: sources flag large bets, so size alone ranks positives highly within a market.
- **T3b (all features)**: placebo markets are crypto and weather markets; volume shape and buyer mix differ by market type.
- **T3 volume features**: twins are matched on total-volume decile only; pre-cut volume can still differ by market age and by where the cut falls.
The univariate AUC of every feature per task and label set is in `baselines.json` (`univariate_auc`).

Results: `baselines.json` (both news-time versions, all label sets, per fold), summarised in the dataset card.
