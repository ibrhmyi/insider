# PMITC v1.2.1 benchmark tasks

Rules: PROTOCOL A15, A23, A26, A27, A29, A32 and A33. Run `python3 pmitc_bench.py` (writes `baselines.json`, seed 192; about an hour with gradient-boosting tuning) or `python3 pmitc_bench.py --quick`; `notebooks/03_benchmarks.ipynb` shows the results.

Labels are allegations by named sources. Positives are sparse and clustered: 74 of the 119 `label_broad` wallets come from two cases (52 Feb-28 2026 Iran strike, 22 KPMG), and 87 are cluster members linked by money flows. Every task therefore runs on three nested label sets (`label_strict` ⊆ `label_standard` ⊆ `label_broad`, A20) and every metric is reported per fold, per case and case-weighted. **Training and evaluation labels (A26):** every model is trained on `label_standard` (the main training label; `label_broad` for its own column) and scored on the label set of the column; `label_strict` is evaluation-only and is never used to fit or tune. In an evaluation on a smaller set, documented wallets outside the set are dropped from the test rows (neither positive nor negative). `label_strict` requires a buy before the market's precise news time; `wallets.strict_no_prenews` marks the wallets that meet the rest of the rule without one.

**Reliable news times only (A29, A29.1):** every task drops markets whose cut came from the deadline rule (`t_news_reliable = false`, per market); `baselines.json` (`excluded_unreliable`) lists what that removes.

**Few folds (A32):** a task and label set with fewer than 6 leave-one-case-out folds is summarised by its fold values with min and max only (`reporting = per_fold_only_A32`); no mean, SD or single headline number. This applies to every `label_strict` result.

News times are per market (A25): `positions.t_cut_ts` is the market's own cut (scheduled start, deadline or case time, `markets.t_news_market_method`).

## Folds
- **Leave-one-case-out** over every case with at least 3 `label_standard` wallets in the task's rows: the model is trained on all other cases and tested on that case. Reported as mean, SD, minimum and maximum over folds. A fold with no positive of the label set in its test case is skipped (strict has fewer folds).
- **Time split** (A15, `splits.csv`): train = cases first claimed before 2026-03-01, test = on or after.

## Baselines
- `prevalence`: constant score (AP equals prevalence; AUC 0.5). It replaces the random baseline, whose expectation is the prevalence and whose single draws vary widely (run 9 report: random AP over 100 seeds on the old test split had mean 0.020, SD 0.044).
- `gate1_rule`: the frozen Gate 1 score (ties by size); for T3 the market's Gate 1 rate.
- `account_age_heuristic`: younger account (first Polymarket-v1 fill) ranks higher (T1, T2).
- `logistic_regression`: standardised, L2, C = 1.
- `gradient_boosting_tuned`: HistGradientBoosting tuned by inner leave-cases-out CV on the training cases (grid in `baselines.json`), precise version only. Flagged `below_prevalence` when it scores under the prevalence baseline.

## Headline tasks: selection-controlled (A27)
Sources flag large bets on fresh wallets; T1 and T2 partly reward learning that selection rule. The headline tasks remove it by design.
- **T1s, size-banded ranking.** As T1, but each case market's candidates are only the pre-news buyers whose `buy_usdc_pre` lies within [0.5 × smallest, 2 × largest] positive in that market. Size alone no longer separates the classes. Metric: per-market AP, case-weighted.
- **T2s, age-matched episodes.** As T2, with controls from `episodes` rows of `control_design = age_matched`: controls also share the episode's account-age band (`lt_1d`, `1_7d`, `7_30d`, `30_180d`, `ge_180d`, `unknown`; never relaxed). Metric: AUC, case-weighted.
- **T2w, win-rate-matched episodes (A33).** As T2s, and controls also share the prior win-rate band (`none`, `lt_0.25`, `0.25_0.5`, `0.5_0.75`, `ge_0.75`; computed as `prior_net_long_win_rate`). It targets the run-10 finding that past wins separate the classes under every other design.
- **Adjacent-band retry (A33, T2s and T2w).** If the exact band(s) give no same-side control, the selection is repeated once with the neighbouring band(s); those controls have `relaxed_band = true`. Coverage per design is in `baselines.json` (`coverage`).
- **T2-open, open control pool.** As T2, with `control_design = open`: Orca- and Inca-flagged wallets may be controls (A6.10 exclusion lifted), which removes the construction part of the past-performance shortcut.

## Secondary tasks
- **T1, within-market ranking.** Unit: (case market, wallet) on the wallet's main token, from `positions`. Rank all pre-news buyers; positives = the label set. Metric: per-market AP (and P@10, R@10, R@100), averaged within case, then over cases.
- **T2, episode classification.** Unit: `episodes` rows of `control_design = standard`, documented episodes vs their matched controls (same side and large other-side buyers). Metric: AUC within each test case, case-weighted. Base result: matched same-side controls win about as often as documented episodes, so outcomes cannot separate them.
- **T3, case vs twin markets** (A22): case markets where a wallet of the label set bought before the cut, vs their same-category, same-volume-decile, same-duration, same-year twins, from pre-cut flow (`market_minutes` before the cut, `positions`). Metric: AUC, case-weighted. `all_case_markets` runs every matched case market.
- **T3b, case vs placebo markets** (A14): the same with crypto-price and weather placebos. **Market-type sensitive**: placebos differ from case markets in kind, so a high score partly measures market type.

## Leakage: do not use
- T1: `is_documented`, `doc_grade`, `label_*`, `hard_negative*`, `coordinated_rule_fired`, `triggering_suspect`, `placebo_rate`, `is_control`, `is_placebo_market`, `is_twin_market`, `gate1` (a label), `gate2b` and `is_shortest_sufficient` (use the resolution), every `_post` column, ids, absolute times (`t_cut_unix`, `first_buy_unix`, `last_buy_unix`) except as differences to the cut, `source_pre`, `vol_to_day_usdc` (includes the rest of the cut's day).
- T2: `share_on_this_ladder_market`, `role`, `episode_id`, `control_of`, `wallet`, `label_*`, `case_share_of_lifetime_volume` (lifetime denominator), `is_shortest_sufficient`, `n_follower_wallets_60m` / `follower_buy_usdc_60m` (window can pass t_news), every `_post` column, the empty funding columns.
- T3/T3b: `market_set`, `is_placebo_market`, `is_twin_market`, any minute at or after the cut, `_post` columns, category fields, resolution, outcome and total-volume fields, question and slug text.

## Known shortcuts (features that separate classes for construction reasons)
- **T2 `share_on_this_ladder_market`**: controls are sampled one market at a time, so the value is 1 for every control; alone it gives AUC about 0.97. Excluded.
- **T2 `hours_first_buy_to_tnews`**: controls are matched on first-buy time (24-72 h), so this feature is controlled by design; its univariate AUC should be near 0.5 (reported).
- **T2 `prior_net_long_win_rate`, `n_prior_markets` (univariate AUC 0.82-0.88)**: selection (run 10): allowing Orca/Inca-flagged wallets as controls (T2-open) leaves `prior_net_long_win_rate` at univariate AUC 0.88, so the construction explanation was mostly wrong; sources find wallets that won before. T2w matches on the win-rate band; T2s on account age.
- **T2 `account_age_days_at_first_buy`**: the source bias, not construction: sources flag fresh wallets, so the one-feature account-age heuristic matches or beats the models. A detector that only learns "new wallet" learns the selection rule of the press.
- **T1 size features (`buy_usdc_pre`, `market_usdc_pre`, `n_buy_fills_pre`; univariate AUC 0.93-0.98)**: selection, not construction: sources flag large bets, so size alone ranks positives highly within a market (T1s restricts to the positives' size band).
- **T3b (all features)**: placebo markets are crypto and weather markets; volume shape and buyer mix differ by market type.
- **T3 volume features**: twins are matched on total-volume decile only; pre-cut volume can still differ by market age and by where the cut falls.
The univariate AUC of every feature per task and label set is in `baselines.json` (`univariate_auc`).

Results: `baselines.json` (both news-time versions, all label sets, per fold), summarised in the dataset card.
