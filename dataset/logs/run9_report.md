# Run 9 report (2026-11-27): PMITC v1.1, the public release

Run 9 turned v1.0.1 into the public release v1.1.0: three nested label sets, hard negatives, same-category twin markets, leave-one-case-out benchmarks, a cleaned schema, data-protection and contribution documents, a dataset card and upload copies. Rules first: amendments A20 to A24 were committed in `d27bdff` before any computation they govern. No claim was edited (one claim changed its `verified` status after its page was read, as the protocol allows). Nothing was uploaded. Package: the full `release/` (Polymarket terms checked by the owner); `release_safe/` is still built as an option.

## Amendments

| Amendment | Governs |
|---|---|
| A20 | Claim-wallet links (address in claim, resolved handle, label-source handle, source URL, official-figures match), `wallet_grade`, and the nested sets `label_strict` ⊆ `label_standard` ⊆ `label_broad` |
| A21 | Hard negatives: suspect profile (pre-cut buy ≥ $1,000 at VWAP ≤ 0.35, profile created ≤ 14 days before the first buy) that is a negative: losers in case and twin markets, look-alikes in cleared cases, winners in placebo markets, and the wallets of cleared cases |
| A22 | Twin markets: same `category_refined`, volume decile, duration band and year, in no claim and not in a case market's event; relaxation ladder; fills from a twin-only tape pass |
| A23 | Benchmarks: leave-one-case-out (cases with ≥ 3 `label_standard` wallets) plus the time split; three label sets; prevalence, Gate 1, account-age and logistic-regression baselines; gradient boosting only with case-grouped tuning; shortcut audit; random baseline dropped |
| A24 | Units in column names, a primary key on every table, NULL role fields with `role_fields_available` on Data API fills, boundary dedup, `claims.right_of_reply`, neutral naming |

## Phase 1: label sets (A20)

Claim-wallet links: 58 (source URL 26, resolved handle 14, address in claim 11, label-source handle 4, official-figures match 3), in `claim_wallet_links`.

| Set | Wallets | Cases | Largest cases |
|---|---|---|---|
| `label_strict` | 19 | 7 | Axiom 9, ceasefire (Apr 7) 3, World Cup 3, Google YIS 1, Maduro 1, Israel (Rising Lion) 1, Bubblemaps cluster 1 |
| `label_standard` | 112 | 11 | Feb-28 Iran strike 52, KPMG 22, Axiom 10, Nobel 8, Maduro 7, ceasefire 4, World Cup 3, Bubblemaps 2, Biden pardons 2, Google 1, Israel 1 |
| `label_broad` | 119 | 18 | standard plus 7 single-wallet E5 cases |

Strict basis: 3 wallets linked to an E2 claim (Maduro: its fills match the figures of the DOJ and CFTC claims; Google: its handle, as recorded by the label source, is in the indictment claim; Israel: the same, for the Tel Aviv indictment claim), 16 named by address or handle in an E4 claim. **None of the 87 cluster members is strict.** Episodes and positions carry the three columns; a test checks strict ⊆ standard ⊆ broad = `is_documented`.

## Phase 2: hard negatives (A21)

| Rule | Rows (both versions) | Wallets |
|---|---|---|
| `lookalike_loser` (case and twin markets) | 8,735 | 3,536 |
| `cleared_case_lookalike` (ballon-dor-2026, railgun-venezuela-control, survivor-50-2026) | 302 | 124 |
| `placebo_lookalike_winner` | 196 | 87 |
| `cleared_case_wallet` (wallet level) | 82 | 82 |
| **total** | **9,315** | **3,762** |

37,345 positions matched the size and price part of the profile; 11,503 passed the first-fill pre-filter; 4,209 new Gamma look-ups (createdAt only, cached in `logs/gamma_raw/profiles_created_run7.csv`). In `positions`: 3,182 case and 1,404 twin positions are hard negatives (precise).

## Phase 3: twin markets (A22)

3,508 twins for 596 case markets (each used once): exact 2,605, year ±1 420, adjacent band 375, adjacent decile 75, any year 33. Not matched: 203 case markets with no catalog category (Data API era), 211 with no twin left. Categories: Politics 1,400, Culture 455, Sports 300, Sci-Tech 275, Finance 215, other. Twin fills: 28,135,632 legs from a twin-only pass over the re-downloaded tape (deleted afterwards). Twin positions 1.83 M (precise), minute paths included. T3 is now case vs twin; the placebo version is T3b.

## Phase 4: benchmarks

### The T1 random-baseline change (0.052 → 0.005)

`logs/run9_random_baseline.json`. The test rows were identical in runs 7 and 8 (4 cases, 102,109 rows, 32 positives, 20 markets; pooled prevalence 0.00031, mean per-market prevalence 0.0013). The script drew a training negative subsample from the seeded generator before drawing the random scores; A19 removed the Spotify Wrapped rows from the training data, so the generator stream shifted and the test rows received different random scores. Over 100 seeds the random AP has mean 0.020, SD 0.044, range 0.0035 to 0.255: 0.052 sits at the 93rd percentile, 0.005 at the 22nd. **Not a metric bug, but a fragile baseline**: a few small test markets with one positive (121, 210, 214 rows) dominate the case-weighted mean. A23 replaces it with the deterministic prevalence baseline.
## Benchmarks (A23; precise news times; seed 192)

Cells: leave-one-case-out mean ± SD [min, max] (folds) / time split. T1 metric: per-market AP averaged per case, then over cases. T2, T3, T3b: AUC within each test case, case-weighted. `gb_tuned` = gradient boosting with case-grouped tuning.

### T1

| Model | label_strict | label_standard | label_broad |
|---|---|---|---|
| prevalence | 0.001 ± 0.001 [0.000, 0.001] (2) / 0.000 | 0.002 ± 0.000 [0.001, 0.002] (5) / 0.003 | 0.002 ± 0.000 [0.001, 0.002] (5) / 0.003 |
| Gate 1 rule | 0.095 ± 0.088 [0.008, 0.183] (2) / 0.005 | 0.238 ± 0.204 [0.036, 0.549] (5) / 0.065 | 0.238 ± 0.204 [0.036, 0.549] (5) / 0.065 |
| account age | 0.008 ± 0.007 [0.000, 0.015] (2) / 0.001 | 0.026 ± 0.029 [0.002, 0.081] (5) / 0.010 | 0.026 ± 0.029 [0.002, 0.081] (5) / 0.010 |
| logistic regression | 0.119 ± 0.038 [0.080, 0.157] (2) / 0.078 | 0.256 ± 0.183 [0.058, 0.593] (5) / 0.091 | 0.270 ± 0.171 [0.059, 0.580] (5) / 0.106 |
| gb_tuned | 0.091 ± 0.006 [0.084, 0.097] (2) / 0.074 | 0.319 ± 0.214 [0.032, 0.506] (5) / 0.090 | 0.265 ± 0.152 [0.085, 0.481] (5) / 0.060 |

### T2

| Model | label_strict | label_standard | label_broad |
|---|---|---|---|
| prevalence | 0.500 ± 0.000 [0.500, 0.500] (3) / 0.500 | 0.500 ± 0.000 [0.500, 0.500] (6) / 0.500 | 0.500 ± 0.000 [0.500, 0.500] (6) / 0.500 |
| Gate 1 rule | 0.844 ± 0.126 [0.693, 1.000] (3) / 0.704 | 0.680 ± 0.268 [0.109, 0.919] (6) / 0.569 | 0.680 ± 0.268 [0.109, 0.919] (6) / 0.569 |
| account age | 0.869 ± 0.115 [0.720, 1.000] (3) / 0.841 | 0.852 ± 0.085 [0.680, 0.936] (6) / 0.688 | 0.852 ± 0.085 [0.680, 0.936] (6) / 0.688 |
| logistic regression | 0.743 ± 0.064 [0.661, 0.817] (3) / 0.738 | 0.775 ± 0.070 [0.685, 0.891] (6) / 0.827 | 0.781 ± 0.080 [0.682, 0.891] (6) / 0.824 |
| gb_tuned | 0.859 ± 0.113 [0.724, 1.000] (3) / 0.817 | 0.862 ± 0.131 [0.584, 1.000] (6) / 0.808 | 0.860 ± 0.132 [0.588, 1.000] (6) / 0.714 |

### T3

| Model | label_strict | label_standard | label_broad |
|---|---|---|---|
| prevalence | 0.500 ± 0.000 [0.500, 0.500] (3) / 0.500 | 0.500 ± 0.000 [0.500, 0.500] (6) / 0.500 | 0.500 ± 0.000 [0.500, 0.500] (6) / 0.500 |
| Gate 1 rule | 0.696 ± 0.095 [0.600, 0.825] (3) / 0.687 | 0.675 ± 0.185 [0.400, 0.975] (6) / 0.494 | 0.675 ± 0.185 [0.400, 0.975] (6) / 0.494 |
| logistic regression | 0.892 ± 0.105 [0.750, 1.000] (3) / 0.872 | 0.702 ± 0.231 [0.200, 0.885] (6) / 0.687 | 0.683 ± 0.312 [0.000, 0.925] (6) / 0.672 |
| gb_tuned | 0.946 ± 0.041 [0.900, 1.000] (3) / 0.849 | 0.691 ± 0.246 [0.200, 0.900] (6) / 0.669 | 0.678 ± 0.308 [0.000, 0.868] (6) / 0.665 |

### T3b

| Model | label_strict | label_standard | label_broad |
|---|---|---|---|
| prevalence | 0.500 ± 0.000 [0.500, 0.500] (3) / 0.500 | 0.500 ± 0.000 [0.500, 0.500] (6) / 0.500 | 0.500 ± 0.000 [0.500, 0.500] (6) / 0.500 |
| Gate 1 rule | 0.483 ± 0.301 [0.200, 0.900] (3) / 0.497 | 0.613 ± 0.295 [0.268, 1.000] (6) / 0.505 | 0.613 ± 0.295 [0.268, 1.000] (6) / 0.505 |
| logistic regression | 0.929 ± 0.091 [0.800, 1.000] (3) / 0.866 | 0.931 ± 0.054 [0.844, 1.000] (6) / 0.923 | 0.930 ± 0.057 [0.844, 1.000] (6) / 0.929 |
| gb_tuned | 0.996 ± 0.006 [0.988, 1.000] (3) / 0.733 | 0.956 ± 0.045 [0.863, 1.000] (6) / 0.947 | 0.868 ± 0.212 [0.400, 1.000] (6) / 0.849 |

- T3, all matched case markets (598 case vs 2837 comparison markets): logistic regression 0.734 ± 0.105 (7 folds) / 0.761; gb_tuned 0.745 ± 0.275 / 0.692.
- T3b, all matched case markets (581 case vs 2818 comparison markets): logistic regression 0.811 ± 0.144 (7 folds) / 0.786; gb_tuned 0.855 ± 0.184 / 0.786.

**Reading the benchmarks.**
- `label_strict` has only 2-3 leave-one-case-out folds (cases with ≥ 3 standard wallets that also hold strict positives): its spreads are wide and its means rest on Axiom and the April ceasefire. Do not compare strict and standard numbers as if they measured the same thing.
- **T1:** every model beats prevalence by two orders of magnitude, but the Gate 1 rule is close to the models, and the time-split numbers (0.06-0.11) are far below leave-one-case-out (0.24-0.32): the test-period cases are harder. Size features alone separate positives (univariate AUC 0.93-0.98): sources flag big bets.
- **T2:** the **one-feature account-age heuristic matches or beats logistic regression** and is close to tuned gradient boosting. Documented wallets are new wallets; that is how sources find them. Base result: same-side controls win 83.4% of the time, documented episodes 83.9%.
- **T3 (twins):** with all matched case markets, AUC 0.73 (LR) and 0.75 (GB, SD 0.28); the strict subset (32 case markets, 3 folds) scores higher but is tiny. **T3b (placebo)** scores 0.81-0.96: much of it is market type, as A14/A23 warned.
- Gradient boosting never fell below the prevalence baseline; its fold spread is the largest of all models.
- Known shortcuts (`benchmarks/README.md`, `baselines.json`): T2 `share_on_this_ladder_market` (construction, excluded); T2 `prior_net_long_win_rate` / `n_prior_markets` (partly construction: control pools exclude Orca/Inca-flagged wallets); T2 account age and T1 size (selection by sources, not construction); T3b market type; T3 volume only coarsely matched.
- The day-version results (logistic regression and baselines, no tuning) are in `baselines.json`.

## Phase 5: coverage

- **5.1 Exact times.** One new time: first reports of explosions in Caracas, 2026-01-03 ~05:30 UTC (El Diario; AP ~2 a.m. local), for `maduro-2026-01` and `railgun-venezuela-control`; it replaces the 09:21 UTC post as the earliest public moment (the frozen v1 rules already used ~06:00). Searches for the Fed-chair post, Biden pardons, the Walz scoop, GPT-5.2, Year in Search, Super Bowl LIX and the March ceasefire found no minute-level time (logged). **17 of 42 market-bearing cases have an exact time (minute 7, quarter-hour 6, hour 3, window 1); 25 remain at day level**: 1 rejected by A18 (Super Bowl LX, UTC day), 1 deliberately left at day (election night: results came in over hours), the rest because no source gives a time of day (most are month- or year-precision cases, aggregates or scheduled releases without a stated time).
- **5.2 Pending claims.** All 46 `needs_page_read` entries were re-tried with plain requests (no user-agent changes): 35 still blocked (proxy or HTTP 403), 5 already read in earlier runs, 1 resolved (**CL0088 now verified**: the page supports every part of the claim), 1 reachable but rendering no article text (CL0090, pending), 4 reachable leads not re-read this run. Claims: 108 verified, 15 pending.
- **5.3 Kalshi market data.** The Kalshi trade API (`api.elections.kalshi.com`, `trading-api.kalshi.com`) is not reachable from this environment (proxy). No `kalshi_market_trades` table; listed as missing.
- **5.4 New cases.** The Kalshi notice bucket has no new disciplinary notice since 2026-08-31 (latest files 2026-11-24/25 are contract amendments). Two press queries for anything after 2026-11-26 found nothing new; topic stopped.
- **5.5 Money graph.** No `POLYGON_RPC` or explorer key is set; still missing. No candidate siblings.

## Phase 6: data consistency

- One fills schema: Data API rows have `wallet_role`, `aggressor_side`, `maker`, `taker`, `fee_usdc` NULL and `role_fields_available = false` (tested).
- Every table has a declared primary key (new surrogate keys: `placebo_row_id`, `twin_row_id`, `hard_negative_id`, `edge_id`; `episodes` keyed by (`row_id`, `t_news_version`)); keys and foreign keys tested, **no skipped checks** in the full package.
- Units in names (A24): 42 columns renamed (for example `ts` → `ts_unix`, `price` → `price_usdc`, `vwap_pre` → `vwap_price_usdc_pre`, `run` → `run_number`); a test checks every numeric column.
- Boundary dedup at 2026-04-28 11:00:40 UTC: no Data API case row at or before the boundary for a market in Polymarket-v1, and no cross-source leg pair within 60 s (tested).
- `claims.right_of_reply` added (NULL). Neutral naming: no label value contains "insider"; one case title reworded (`solidus-multichain`); `build/ULTIMATE.md` renamed `build/TARGET_SCHEMA.md`. Claim texts are unchanged (never edited); some quote "insider" from their sources.

## Phase 7: legal, ethics, trust

`docs/DATA_PROTECTION.md` (addresses as personal data, lawful basis, minimisation, what is not stored, retention, removal and right of reply), `docs/EXTRACTION.md` (AI extractor under a written protocol, run summaries, verification status, A4 blind check pending), `CONTRIBUTING.md` with three issue templates in `release/.github/ISSUE_TEMPLATE/` (submit a case, correct a row, request removal), response policy and an owner-contact placeholder.

## Phase 8: usability

- `release/README.md` is the dataset card (HF YAML header, one config per table; checked with `datasets.load_dataset(<path>, "<table>")`), with the headline figure `docs/cases_timeline.png`, quick start, table guide, label sets, benchmarks, limitations and citation. `docs/README.md` is a copy without the YAML header.
- Notebooks `01_quickstart`, `02_case_study` (Maduro: price path, the CFTC-described wallet's buys, its matched controls), `03_benchmarks`: all executed end to end on the released files.
- `requirements.txt` (pinned) and `docs/REBUILD.md` (about 7 h and 30 GB peak disk on 4 CPUs / 15 GB RAM).
- Upload copies in `dataset/upload/` (git-ignored, not uploaded): `hf/` (folders kept), `kaggle/` (flat, folder-prefixed names, metadata resources), `zenodo/` (2.6 GB zip + SHA-256). Every copy matches the manifest; the quality gates pass on `upload/hf` (80/80), on `release/` (80/80) and on `release_safe/` (79 + 1 skipped boundary test, whose Data API rows are withheld).

## Counts

- **Cases (66)** by grade: E1 4, E2 3, E3 10, E4 13, E5 28, E6 8. Outcome: unresolved 44, under investigation 10, sanctioned 4, charged 3, cleared (analyst) 2, disputed 2, cleared (official) 1.
- **Claims (123)** by grade: E1 17, E2 5, E3 14, E4 24, E5 54, E6 9. Verified 108, pending 15 (pending by grade: E1 1, E3 5, E4 1, E5 8).
- **Wallets:** 260 labels; `label_strict` 19, `label_standard` 112, `label_broad` 119; coordinated-rule wallets 1,305 (precise; rule output, not labels).
- **Hard negatives:** 9,315 rows, 3,762 wallets. **Twin markets:** 3,508. **Placebo markets:** 4,227.
- **Exact-time coverage:** 17 of 42 market-bearing cases.
- **Fills:** 81,559,246 legs (case 23.1 M, placebo 30.3 M, twin 28.1 M, labelled wallets elsewhere 0.06 M). **Positions:** 9,668,364. **Episodes:** 423 (day) and 473 (precise) documented episodes with 16,603 controls.

## Contradictions with earlier claims or reports

- Claims (unchanged): CX001 Walz amount (-4%, within the 10% threshold, kept from run 3), CX002 Super Bowl claim misfiled (run 6), CX003 Fed-chair bet date (run 6), CX004 Google amount (17.6% gap), CX005 Super Bowl LX exact time outside the UTC day (A18).
- Earlier reports: the Maduro exact time is now 05:30 UTC (first reports of explosions), not the 09:21 UTC post used since run 7; Maduro and Railgun precise-version tables changed accordingly. The run-8 report's "17 of 42 cases with exact times" was 16 after A18; it is 17 again with the Railgun row. The run-7 statement that the random baseline was 0.052 was a single draw (see above).

## The 10 biggest remaining weaknesses (ranked) and what would fix each

1. **Very few strict positives** (19 wallets, 7 cases; 9 from Axiom): strict benchmarks rest on 2-3 folds. *Fix:* more official cases that publish addresses (court dockets, Kalshi/CFTC orders), reading the 35 blocked pages, and a second extractor.
2. **Selection bias:** sources flag new wallets making big bets, and the account-age heuristic matches the models. *Fix:* cases found by other means (platform referrals with addresses, regulator data), and evaluation on hard negatives and twins rather than random buyers.
3. **Labels are allegations; adjudicated wallets are 1-3.** Only Maduro (E2, charged), Google (E2) and Israel (E2) link a wallet to an official claim; none is adjudicated. *Fix:* follow the SDNY and Israeli dockets (CourtListener blocked here) and record outcomes as new claims.
4. **The blind second-extractor check (A4) is still pending**, and the extractor is an AI model. *Fix:* a human re-extracts the 18-claim sample and the agreement is published.
5. **87 of 112 standard positives are cluster members** from third-party repositories, linked by money flows we cannot check (no money graph). *Fix:* an archive Polygon RPC or explorer key to run A8 and verify the links.
6. **Kalshi is a blind spot:** 10 E1 notices, no trades or accounts. *Fix:* access to Kalshi's public market-trade API (blocked here) for minute paths; accounts will stay private.
7. **News times:** 25 of 42 cases at day level, and A18's UTC rule rejects evening US events. *Fix:* a local-time amendment, and a person reading the blocked press pages for timestamps.
8. **Comparison markets are imperfect:** 414 case markets have no twin (Data API era, no catalog category), categories are coarse (`Politics`), and T3b mostly measures market type. *Fix:* Gamma-based twins for post-April 2026 markets and finer categories (tags).
9. **Controls are built with exclusions that leak** (Orca/Inca-flagged wallets excluded from control pools) and `share_on_this_ladder_market` is an artifact. *Fix:* a control-sampling amendment that keeps flagged wallets as eligible controls, re-run T2.
10. **Reproducibility of API data and side conventions:** Data API pulls are not hash-stable, and Polymarket-v1 records some economic buys as maker sells of the other token (A6.4), which distorts stake amounts. *Fix:* snapshot the API pulls with the release, and add the CTF layer (mints/merges) to rebuild economic sides.

## Decisions needed

1. **Owner contact and extractor details:** fill in the contact e-mail in `CONTRIBUTING.md` and `DATA_PROTECTION.md`, and the extractor model name and version in `EXTRACTION.md` (left as placeholders: this session does not write model identifiers into repository files).
2. **Issue templates:** they are in `release/.github/ISSUE_TEMPLATE/` (for a standalone dataset repository). To use them on `ibrhmyi/insider`, copy them to the repository root `.github/` (outside `dataset/`).
3. **A18 in local time?** Evening US events are rejected in UTC (Super Bowl LX). A new amendment could read the coarse date in the event's time zone.
4. **Control sampling (weakness 9):** keep the A6.10 exclusions, or amend so flagged wallets can be controls.
5. **Blind check:** who does the A4 re-extraction?
6. **Money graph and Kalshi data:** provide an archive Polygon RPC or explorer key, and Kalshi API access, for a later run.
7. **Hugging Face id:** the card's quick start uses `<hf-user>/pmitc`; the Kaggle id is `<kaggle-username>/pmitc-prediction-market-informed-trading`. Fill in before upload.
