# Changelog

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
