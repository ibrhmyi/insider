# Changelog

## v1.2.2 (2026-11-28): docs only
No data table, benchmark result or rule changed; tables, fills and `baselines.json` are byte-identical to v1.2.1 (their SHA-256 in `MANIFEST.json` are unchanged).
- Dataset card: the benchmark target is `label_<set> & is_alleged_position`; `label_*` is also true on `labelled_other_position` rows. The leftover "mean ± SD" wording is gone (every cell is a range of fold values). n+ per strict fold, with folds under 5 positives marked not evaluable (strict has 2 evaluable folds in the headline tasks). 114 of 140 `label_standard` alleged positives sit in one group, which is why the time split is empty; the time split is retired for the alleged-position tasks. Only 44 of 140 alleged episodes have a same-side control in T2s.
- CODEBOOK: the same target note on `label_strict`, `label_standard` and `label_broad` in `episodes` and `positions`.
- EXTRACTION: extractor model filled in (Claude via Claude Code, `claude-opus-5-5`, for the session that finished run 11). CITATION: `cff-version` corrected to 1.2.0 (the CFF schema version), `version` 1.2.2.
- PROTOCOL: A50-A54 pre-registered for v1.3 (not used in this release) and the CL0079 open question.
- Unchanged: the notebooks and `benchmarks/pmitc_bench.py` still say v1.2.1, the version whose results they show.

## v1.2.1 (2026-11-28, run 11): last fixes
Amendments A29-A49 (the run-11 request numbered them A28-A32; A28 was already taken by the run-10 multi-account family).
- A29, A29.1: `t_news_reliable` per market in `markets`, `positions`, `episodes` and `market_minutes`: false only where the cut came from the A25 deadline rule (285 markets in 9 cases, range-dated tweet-count markets included); sourced exact times and checked scheduled starts are reliable (World Cup and KPMG stay in). `markets.t_news_deadline_rule_utc` keeps the deadline time. Default analyses and every benchmark use reliable rows only. (A29 as first applied, by case, flagged all 90 checked scheduled starts; A29.1 corrected the scope before any release table used it.)
- A30: a scheduled start is used only if it is before the market's close (Gamma `closedTime`, else `resolved_utc`); all 91 candidates checked in `logs/scheduled_start_check.csv` (0 disagreements; no cut changed).
- A31: only claims with stance `alleges` or `confirms` create `claim_wallet_links` (6 links from context claim CL0124 removed; no label changed).
- A32: below 6 leave-one-case-out folds, results are reported per fold with min and max only (all `label_strict` results).
- A33: control design `winrate_matched` (task T2w, headline): controls also share the prior win-rate band; age-matched designs (T2s, T2w) retry with the adjacent band before dropping an episode (`relaxed_band` in `episodes` and `controls`).
- A34: economic-side exposure. A SELL of a token the wallet holds none of is an economic BUY of the other token at 1 - p (split or mint inferred; covers the A6.4 maker-sell case). New `fills` columns `econ_side`, `econ_asset_id`, `econ_outcome_label`, `econ_price_usdc`, `econ_size_usdc`, `econ_inferred`; raw columns unchanged. Positions, episodes, controls, hard negatives, label sets and the coordinated rule use the economic view; `raw_view_prenews_buy` and `econ_inferred_buy_usdc_pre` keep the raw view comparable. Prompted by a wallet in us-iran-strike-2026-02-28 that sold "No" it never held before the news.
- A34.1: a SELL larger than the economic holding splits into a held SELL and an inferred BUY of the excess (`econ_partial`, `econ_excess_*`).
- A34.2: direction net of full sets: `full_sets_pre_shares`, `directional_shares_pre`, `directional_cost_usdc_pre` (FIFO) and `is_directional_position`, which defines a pre-news position for label sets, benchmarks, episodes, hard negatives and the coordinated rule. `is_market_maker` (reporting flag, not a label) in `positions` and `weak_labels`.
- A34.3: directional entry columns `directional_first_buy_utc`, `directional_first_buy_price`, `directional_vwap_price_usdc_pre`, `directional_hours_first_buy_to_cut`; `directional_cost_usdc_pre` is a FIFO accounting figure, not an entry measure.
- A35, A35.1: alleged positions. New table `claim_positions` (the market and side each claim describes, mapped from claim text and market questions only); `positions.is_alleged_position`, `episodes.is_alleged_position`; other positions of labelled wallets get `episodes.role = labelled_other_position`. Benchmarks use alleged positions as positives; the wallet-level version is secondary.
- A36, A36.1: one news time per `condition_id` (shared markets take the time of their own resolving event; `markets.t_news_market_source_case`).
- A29.2: case-date fallbacks with a coarse date and no sourced exact time are unreliable too (exact times searched first; `logs/exact_time_search_run11.md`).
- A37: benchmark folds and the time split by connected case group (`splits.csv` `group_id`); no market or Gamma event in both train and test.
- A38: twins must share the case market's `question_type`, never a placebo type and never the same subject. A39: no twins for the tweet-count case; withheld names are scrubbed from every string column (slugs, categories, outcome labels included).
- A40: known-answer tests (Maduro wallet 436,759.61 Yes shares for 32,538.34 USDC; AlphaRaccoon d4vd Yes buys 10,650.04 USDC); both match exactly.
- A41: `ftx-sbf` keeps only the markets its claims name (11 Biden-pardon markets moved out, with their 55 placebo markets).
- A42: `claims.claim_timing`, `claims.alleged_side_won`; `cases.n_claims_ex_ante`, `cases.ex_ante_win_rate`.
- A43: all-NULL columns dropped (funding fields), `claims.right_of_reply` kept as `not_built`; `episodes.case_share_of_lifetime_volume` in [0, 1].
- A44: `claims.duplicate_of` (CL0124 duplicates CL0091); `cases.event_occurred_utc` and `cases.market_deadline_utc` replace `event_date`; the CODEBOOK names the token behind `market_minutes` prices; T2 benchmarks count a repeated control once.
- A46: twins re-chosen from the full Polymarket-v1 catalog (A38 had restricted them to already-downloaded markets): 2,486 twins for 464 case markets (was 1,485 for 317), with a new twin pass over the pinned tape.
- A47: the finishing run rebuilt every intermediate from the pinned tape on a fresh disk. The case-market fill parts (Data API part included) are byte-identical to run 11; the placebo parts no longer contain the 55 placebo markets A41 had removed (746,440 legs that run 11's parts still held).
- A48: `claim_positions` completeness audit (prompted by the March 31 ceasefire flag, CL0031, which had no row): 10 claims gain 28 rows, 40 stay without a row; every decision is in `logs/claim_positions_audit.csv`. No alleged position of a labelled wallet changes.
- A49: `claims.claim_day_contains_resolution` flags ex-ante claims dated on their market's resolution day.
- Blind check: `logs/blind_check_sample.csv` gains a second section, a seed-192 20% sample of `claim_positions` rows (claim text only) for the human second extractor.

## v1.2.0 (2026-11-27, run 10): final fixes
- A25: per-market news times. `markets.t_news_market_utc` (precise) and `markets.t_news_market_day_utc` (day) with `t_news_market_method`: a Gamma scheduled start (matches, earnings releases), a market deadline inside a coarse case date, else the case time; never later than a sourced exact case time (A25.1); a deadline-form question ("by <date>") never takes a scheduled-start cut (A25.2). Case-level `t_news_utc` and `t_news_precise_utc` are kept. Every time-dependent table (positions, minute paths, episodes, controls, coordinated rule, label sets, hard negatives, placebo and twin `t_ref`) is rebuilt with the per-market cut. This also fixes stale precise `t_ref` values for the Maduro and Railgun-Venezuela placebos and twins left by run 9.
- A26: `label_strict` additionally requires a buy before the precise news time; `wallets.strict_no_prenews` marks the rest. `label_standard` is the main training label (case-weighted); `label_strict` is evaluation-only.
- A27: selection-controlled headline benchmarks: T1s (size-banded ranking), T2s (controls matched on account-age band too), T2-open (Orca/Inca-flagged wallets allowed as controls); `episodes` and `controls` gain `control_design` (`standard`, `age_matched`, `open`) in their primary keys. T1, T2, T3, T3b kept as secondary.
- A28: `label_family = multi_account` for allegations of shared ownership or multi-accounting without an informed-trading claim (excluded from label sets). The World Cup 2026 source was re-read: it alleges a suspected insider and uses a shared deposit address as evidence of common control, so the case stays `informed_trading` (context claim CL0124).
- Issue templates copied to the repository root `.github/ISSUE_TEMPLATE/`. Contact e-mail and upload ids remain placeholders for the owner.

## v1.1.0 (2026-11-27, run 9): public release
- A20: three nested label sets in `wallets`, `episodes`, `positions`: `label_strict` (linked to an E1-E3 claim, or named in an E4 claim), `label_standard` (case grade E1-E4, includes cluster members), `label_broad` (E1-E5 = `is_documented`); `wallet_grade` and the new table `claim_wallet_links`.
- A21: hard negatives (`hard_negatives` table; `positions.hard_negative`, `wallets.hard_negative`): look-alike losers in case and twin markets, look-alikes in cleared cases, look-alike winners in placebo markets, wallets of cleared cases.
- A22: same-category twin markets (`twin_markets`), with fills, positions and minute paths; T3 is now case vs twin, the placebo version is T3b.
- A23: leave-one-case-out benchmarks plus the time split, three label sets, prevalence / Gate 1 / account-age / logistic-regression baselines, tuned gradient boosting, univariate audit and known shortcuts. The random baseline is dropped (explained in the run-9 report).
- A24: units in column names, a primary key on every table, Data API fills with NULL role fields and `role_fields_available`, boundary dedup test, `claims.right_of_reply`, neutral naming.
- Exact time for the Caracas first reports (05:30 UTC) for the Maduro and Railgun-Venezuela cases; CL0088 verified.
- Docs: dataset card with HF configs, `DATA_PROTECTION.md`, `EXTRACTION.md`, `CONTRIBUTING.md` and issue templates, pinned `requirements.txt`, three notebooks, upload copies for Kaggle, Hugging Face and Zenodo.

## v1.0.1 (2026-11-27, run 8): release fixes
- A17: the coordinated-buyer rule (A13) is a rule label, not a wallet label. The 1,338 `L4_coordinated` rows left `wallets`; `positions` and `weak_labels` gain `coordinated_rule_fired`, `triggering_suspect`, `placebo_rate`. Rule-fired wallets' histories outside case markets are no longer in `fills`.
- A18: an exact news time must fall inside the coarse date that set the day-level time; Super Bowl LX's (01:12 UTC on the next day) does not, so its day date is kept and a contradiction is recorded (CX005). Kalshi notices keep their printed years.
- A19: `label_family` in `wallets`; `is_documented` only for informed trading (119 wallets; the Spotify Wrapped public-data-leak wallet is no longer a positive). Benchmarks recomputed, reported per case and case-weighted.
- `cases.n_documented_by_case`; docs state that 74 of 119 documented wallets come from two cases and 87 are money-flow cluster members.
- `__pycache__` removed from the package and the manifest; `*.pyc` ignored.
- Two packages: `release/` (all files) and `release_safe/` (without the Data API fill files, with `scripts/rebuild_data_api_fills.py`).

## v1.0.0 (2026-11-26, run 7)
- Exact news times (PROTOCOL A10): every time-dependent table in two versions, `day` and `precise`; 7 new sourced times (16 cases with an exact time).
- Pseudonym handle rule (A11): `Burdensome-Mix` resolved by pseudonym plus fills; every claim handle re-checked (`logs/handle_checks_run7.csv`).
- E3 covers employer disciplinary action (A12.1); `trade_confirmed` and `is_documented` labels (A12.5); post-count markets attached by condition id with titles withheld (A12.6).
- Coordinated-buyer candidates (A13) with a placebo-window false-positive rate.
- Kalshi notice sweep: 10 E1 claims, one per notice; CFTC, Senate and Polymarket statements; new case `nvidia-ceo-return-2026-11`.
- Placebo markets (A14, A14.1): crypto-price and weather-reading markets matched by volume decile, duration band and resolution month.
- All-buyer positions before the news (C2) with Gate 1 (frozen v1 Layer 1, A16 substitutions) and Gate 2a/2b.
- Final schema: 13 typed tables, parquet plus CSV under 50 MB, CODEBOOK per column, MANIFEST with SHA-256.
- Benchmarks T1-T3 with a frozen, case-grouped, time-ordered split (A15) and baselines; notebooks; quality-gate tests.

## v0.3 (run 6): read claim source pages; 9 new wallets confirmed by fills; X post URLs recovered.
## v0.3 (run 5): handle hunt, stance (A9.1), investigation outcome (A9.2), minute-level market paths (A9.3).
## v0.3 (run 4): deeper data search; event-time list (not yet used); modelling backlog.
## v0.3 (run 3): markets, fills (Polymarket-v1, 746 M fills, plus Data API v2), wallet checks, ACDC and Inca rule labels, matched controls, episode features (A6-A8).
## v0.2 (run 2): X sweep through search engines (A5), Gamma handle resolution.
## v0.1 (run 1): systematic search under PROTOCOL v1.0; 84 claims.
