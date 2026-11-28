# Run 8 report (2026-11-27): release fixes, v1.0.1

Run 8 applied six release fixes (R1 to R6). Rule changes were written as amendments A17, A18 and A19 and committed before any table was rebuilt. Nothing was uploaded. Branch `claude/pmitc-v1`.

## Amendments

| Amendment | Fix | Rule |
|---|---|---|
| A17 | R1 | The coordinated-buyer output (A13) is a rule label, not a wallet label: `L4_coordinated` rows leave `wallets`; `positions` and `weak_labels` get `coordinated_rule_fired`, `triggering_suspect`, `placebo_rate`; rule-fired wallets stay out of control pools; `fills.label_other` covers `wallets` only |
| A18 | R5 | An exact time is used only if it falls inside the coarse date that set the day-level `t_news`; otherwise a contradiction is recorded and the coarse date kept. Kalshi notices keep their printed years |
| A19 | R4 | `label_family` in `wallets`; `is_documented` requires `informed_trading`; benchmarks reported per case and case-weighted |

## R1: coordinated output as a rule label (A17)

- 1,338 `L4_coordinated` rows removed from `data/wallet_labels.csv` and `wallets` (now 260 rows). The full record stays in `data/coordinated_candidates.csv`.
- New columns: `positions.coordinated_rule_fired` (1,210 rows day, 1,455 precise; every rule hit maps to a position), `triggering_suspect`, `placebo_rate`; `weak_labels.coordinated_rule_fired` (1,305 wallets, precise), `coordinated_rule_fired_day` (1,090), `triggering_suspect`, `placebo_rate`.
- The rule was rerun because A19 removed one documented wallet and A18 moved one cut time: 13,025 triggers (precise), 0.447 candidates per trigger, 0.147 per placebo window, placebo/real ratio 0.33 (day 0.29).
- Wording in README, DATASHEET, CODEBOOK and the Kaggle column descriptions: "rule output; about 1/3 expected by chance; may include copy-traders; not an allegation".
- `fills` shrinks from 58.06 M to 53.43 M legs: the rule-fired wallets' histories outside case markets (4.6 M Data API legs) are no longer shipped.
- 2,157 new Gamma profile lookups (the placebo window draws shifted with the trigger set). Only `createdAt` is kept, in `logs/gamma_raw/profiles_created_run7.csv`; raw profiles are not committed.

## R2: concentration of the positives

- README, DATASHEET and `benchmarks/README.md` now state that 74 of the 119 documented wallets come from two cases (52 Feb-28 2026 Iran strike, 22 KPMG), and that 87 are cluster members linked by money flows.
- `cases.n_documented_by_case` replaces `n_wallets_documented`; `n_wallets_coordinated_rule` replaces `n_wallets_candidate`.
- Benchmarks report per-case values and case-weighted means (each case counts once) next to pooled values, for T1, T2 and T3.

## R3: bytecode

`release/benchmarks/__pycache__` deleted; the manifest generator skips `__pycache__` and `.pyc`; `dataset/.gitignore` ignores `*.pyc` and `__pycache__/`. A new test checks that neither package nor manifest contains them.

## R4: label family (A19)

- `label_family`: informed_trading 151, negative_control 71, manipulation 37, public_data_leak 1.
- `is_documented`: 120 → **119** wallets in 18 cases (the Spotify Wrapped public-data-leak wallet is no longer a positive).
- Episodes rebuilt: 423 (day, was 425) and 475 (precise, was 479; −2 Spotify, −2 Super Bowl LX from A18). Controls 16,650.

## R5: exact times inside the coarse date (A18)

- Checked all 17 cases with an exact time. One falls outside: `super-bowl-halftime-2026` (2026-02-09T01:12Z, outside the UTC day 2026-02-08; it is the evening of Feb 8 in US Eastern time). The coarse date is kept and **CX005** records it. 16 cases use an exact time.
- Gemini 3 (month precision, Nov 2025; exact time 2025-11-18) falls inside its month and is kept.
- Kalshi notices KE-2026-0003, KDA-2026-0004 and KDA-2026-0005 keep the printed "EFFECTIVE April 21, 2025" with the note already in `notes`.
- Fix found on the way: re-running the markets builder reset the A12.7 `title_withheld` flags (the titles stayed blank). It now keeps earlier decisions; 135 markets are withheld, as in run 7.

## R6: two packages

| | `release/` | `release_safe/` |
|---|---|---|
| fills parts | 8 (53,430,556 legs) | 6 (Polymarket-v1 only, 51,292,692 legs) |
| Data API fill files | included | withheld; `scripts/rebuild_data_api_fills.py` rebuilds them from the public API |
| other tables | | identical (hard links); derived tables keep their Data API aggregates |
| MANIFEST | 45 files | 44 files, `withheld_sources = [data_api_v2]`, plus the 14 wallets whose trade confirmation rests only on withheld rows |
| quality gates | 48 passed, 3 skipped | 48 passed, 3 skipped |

The 3 skipped tests are the primary-key checks of the tables without a declared key (placebo_markets, episodes, edges). In the safe package, the leakage recomputation uses positions whose pre-cut legs are all Polymarket-v1, and the count reconciliation drops the withheld source. The rebuild script was written and syntax-checked but not run end to end here (it would pull about 2.1 M market rows and the labelled wallets' activity); its output will not hash-match the full package because the API keeps adding rows.

Kaggle metadata regenerated for both (`dataset-metadata.json`; the safe one has id suffix `-safe` and lists the rebuild script). CHANGELOG has the v1.0.1 entry.

## Benchmarks (precise; seed 192; `release/benchmarks/baselines.json`)

| Task | Metric | Random | Gate 1 rule | Logistic regression | Gradient boosting |
|---|---|---|---|---|---|
| T1 test (4 cases, 20 markets, 32 positives) | AP, case-weighted | 0.005 | 0.065 | 0.075 | 0.005 |
| T1 train grouped CV (12 cases) | AP, case-weighted | | | 0.323 | 0.101 |
| T2 test (4 cases) | AUC case-weighted / pooled | | | 0.829 / 0.794 | 0.743 / 0.700 |
| T2 grouped CV (16 cases) | AUC case-weighted / pooled | | | 0.749 / 0.802 | 0.795 / 0.874 |
| T3 test (15 cases) | AUC case-weighted / pooled | | | 0.787 / 0.752 | 0.792 / 0.852 |
| T3 grouped CV (35 cases) | AUC case-weighted / pooled | | | 0.827 / 0.760 | 0.871 / 0.859 |

T2 base result: matched same-side controls win 83.5% of the time, documented episodes 84.0%. Compared with run 7, T1 test AP for logistic regression is about the same (0.076 → 0.075). The random baseline moved from 0.052 to 0.005: it depends on the random draw in a few small test markets, which shows how fragile 4-case test numbers are. T2 per test case (LR): biden-pardons 0.78, bubblemaps-military-cluster 0.96, kpmg-earnings 0.89, us-iran-ceasefire 0.69.

## Quality gates

Both packages: schema and dtypes, allowed values (token-wise for `label_family`), primary keys, foreign keys, wallets in fills or flagged, address format, hashed name list and the reviewed "Name Surname" scan, leakage (both versions, recomputed from fills), manifest SHA-256, counts reconcile, amount checks, plus three new tests: no bytecode, no rule rows in `wallets` and the A19 definition of `is_documented`, and withheld sources absent. Contradictions: 5 (CX004 kept its id after a renumbering bug in the amount check was fixed).

## Decisions needed

1. **Polymarket API terms** (unchanged from run 7): they decide which package to publish. `release_safe/` is ready if the terms forbid redistribution.
2. **A18 and time zones.** The rule is applied in UTC, so evening events in US time are rejected (Super Bowl LX). Decide whether the coarse date should be read in the event's local time zone. That would be a new amendment.
3. **Rebuild script.** Run `release_safe/scripts/rebuild_data_api_fills.py` once with network access to confirm it end to end before publishing the safe package.
4. **Hard links.** `release_safe/` shares files with `release/`. Rebuild it with `build/v1/package_safe.py` after any change to `release/`, and copy it with link-dereferencing (for example `cp -rL`) before uploading.
5. Still open from run 7: the 46 unread pages, the A4 blind check, the money graph, and checking Kaggle's limits.
