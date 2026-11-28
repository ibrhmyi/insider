# Run 11 report (2026-11-28): PMITC v1.2.1, finish and freeze

Run 11 was interrupted after the reviewer audit (A35-A45), before its benchmarks, report and freeze. It was finished in a fresh environment with no build intermediates on disk, so everything was rebuilt from the pinned Polymarket-v1 tape (A47). Nothing was uploaded. Every new rule was committed as a dated PROTOCOL amendment before the tables it governs were computed (A46-A49 and one dated note to A48). No claim was edited. Branch `claude/pmitc-v1`; no tag.

## 1. Rebuild and reproducibility (A47)
- **Tape and catalog.** 2,105 day files of `TimeSeventeen/Polymarket-v1` @ 6d1bcd52 (746,110,412 fills, matching the documented count) and the market catalog (1,538,514 tokens).
- **Data API.** The same 267 case markets were pulled again. Per-case Data API row counts are unchanged.
- **Byte-identical outputs.** The three case-market fill parts, Data API part included, have the same SHA-256 as run 11's. The case econ view (3,529,319 inferred legs), label sets, claim-wallet links and coordinated candidates also reproduce run 11 (candidates to 1e-4 USDC, with freshly fetched profile dates), as do all eight control summaries.
- **Known differences:**
  - Precise episodes have one more pre-cut row (1,498,543 vs 1,498,542).
  - `prior_net_long_win_rate` differs by at most 0.0065 in 143 control rows. Those are wallets with hundreds to thousands of prior markets, and `prior_markets` is identical. The most likely cause is the non-deterministic `any_value()` over outcome labels in the catalog join; this is not confirmed.
- **Stale rows found.** Run 11's released placebo parts still held the 55 placebo markets that A41 had removed (746,440 legs; matched exactly against the catalog fill counts). The rebuild drops them.
- **Known answers (A40), exact.** Maduro wallet 436,759.61 Yes shares for 32,538.34 USDC; AlphaRaccoon d4vd Yes buys 10,650.04 USDC.
- **Fills parts.** Disjoint: 65,595,598 legs, 65,595,598 distinct `leg_id`, and no `condition_id` in two parts of the same set and source. `case_share_of_lifetime_volume` lies in [1.2e-8, 1.0].

## 2. Gates
| Copy | Result |
|---|---|
| `release/` | 121 passed (A32 gate included) |
| `release_safe/` | 119 passed, 2 skipped (boundary dedup and known answers need the withheld Data API part) |
| `upload/hf/` | 121 passed |
| `upload/kaggle/` (folder view of symlinks) | 120 passed, 1 expected failure: `dataset-metadata.json` is rewritten with flat names by design |
| `upload/zenodo/pmitc-v1.2.1.zip` (3.57 GB; SHA-256 verified, unpacked) | 121 passed |

The A32 gate was extended to the A35 `wallet_level` block, which it had not been checking. Bytecode left by notebook 03 was removed before the gates ran.

## Amendments applied in run 11 and what each changed
| Id | Rule | Effect in v1.2.1 |
|---|---|---|
| A29, A29.1 | `t_news_reliable` per market; false for deadline-rule cuts | 284 deadline-rule markets unreliable; benchmarks and default analyses use reliable rows only |
| A29.2 | coarse-dated `case_time` fallbacks without a sourced exact time are unreliable too | 355 of 1,107 market rows unreliable (11 cases touched); exact-time search for 2 cases found no first-report time (`logs/exact_time_search_run11.md`) |
| A30 | scheduled start only if before the market's close | 91 checked, 0 disagreements, no cut changed |
| A31 | links only from `alleges`/`confirms` claims | 6 links from CL0124 removed; no label changed |
| A32 | fewer than 6 folds: per-fold values with min and max only | every `label_strict` result (and any set below 6 folds) |
| A33 | T2w (win-rate band) and adjacent-band retry | new control design `winrate_matched`; `relaxed_band` |
| A34-A34.3 | economic-side exposure, partial sells, direction net of full sets, entry columns | 3,529,319 case legs re-read as economic buys; positions and everything downstream in the econ, directional view |
| A35, A35.1 | alleged positions; `claim_positions`; `labelled_other_position` role | positives of every benchmark are alleged positions |
| A36, A36.1 | one cut per `condition_id`; source case recorded | 38 shared-market rows in `logs/a36_shared_market_times.csv` |
| A37 | splits and folds by connected case group | 59 groups; 35 train / 31 test cases |
| A38 | twins by question type, never a placebo type or the same subject | |
| A39 | no twins for the tweet-count case; withheld names scrubbed in every string column | 1 outcome label scrubbed in `fills` |
| A40 | known-answer tests | Maduro 436,759.61 Yes shares for 32,538.34 USDC; AlphaRaccoon 10,650.04 USDC: both exact |
| A41 | `ftx-sbf` keeps only its named markets | 11 market rows and their 55 placebo markets out |
| A42 | claim timing and alleged-side outcome | see section 6 |
| A43 | all-NULL columns dropped; lifetime share in [0, 1] | |
| A44 | duplicate_of, event_occurred/market_deadline split, minute-token note, T2 control dedup | |
| A45 | rebuild everything | done twice in the finishing session (see A47, note to A48) |
| A46 | twins from the full Polymarket-v1 catalog | 2,486 twins for 464 case markets (A38-restricted: 1,485 for 317; before A38: 596 case markets) |
| A47 | fresh-disk rebuild; data CSVs are inputs | case fills byte-identical to run 11 |
| A48 | `claim_positions` completeness audit | 10 claims gain 28 rows; one shared market's cut moves (note to A48) |
| A49 | `claims.claim_day_contains_resolution` | flags same-day "ex-ante" claims |

## 3. Twin coverage (A46)
A38 had fallen from 596 to 317 case markets because only already-downloaded markets were eligible. A46 restores A22's full Polymarket-v1 catalog pool, with every A38/A39 condition kept, and pulls the new twins' fills with a fresh `hf_pass_v9.py` pass over the pinned tape.

| | Before A38 | A38 (run 11 audit) | A46 |
|---|---|---|---|
| Case markets with twins | 596 | 317 | **464** |
| Twins | n/a | 1,485 | **2,486** |
| Cases | n/a | 25 | 34 |

Unmatched rows:
- 203 market rows have no catalog category. These are Data-API-era markets (World Cup, Nvidia, most of Ballon d'Or and Survivor). The Gamma catalog does not carry A22's `category_refined`, so they remain a gap.
- 268 have too few eligible twins.
- 132 are the tweet-count case (A39).

Checks: no twin is a case or placebo market, none has a placebo question type, every twin's slug type equals its case market's type, the tweet-count case has no twins, and each twin is used once. With the new twins, twin look-alike losers (A21) rise from 1,651 to 2,877 and twin directional positions to 975,519 (precise).

## 4. A35: alleged positions (precise cut; standard control design, whose suspected side is the same in every design)
- **Alleged share.** Of 527 suspected-side pre-news positions (labelled wallets in their own cases), **143 are alleged**. The other 384 are `labelled_other_position`.
- **Losing positions.** All **39** of them (`won_post = false`) are labelled-other positions; **no alleged position lost**. Day cut: 98 of 414 alleged; all 34 losing positions are labelled-other.
- **Label sets on alleged positions:**
  - `label_strict`: 21 positions, 16 wallets, 6 cases (from 55 positions, 19 wallets, 7 cases).
  - `label_standard`: 140 positions, 79 wallets, 8 cases (from 501 positions, 111 wallets, 11 cases).
  - `label_broad`: 143 positions, 82 wallets, 11 cases (from 527 positions, 117 wallets, 17 cases).
- **Dropouts.** 35 wallets drop out (`logs/a35_dropouts.csv`):
  - 30 because no linked or cluster claim names a market or side: kpmg-earnings-2025-26 (22), world-cup-2026-06 (3, all strict), biden-pardons (2), draftkings, fed-chair and super-bowl-halftime-2026 (1 each).
  - 5 because they held no alleged market and side before the cut: maduro-2026-01 (3) and us-iran-strike-2026-02-28 (2).
  - Cases leaving strict: world-cup-2026-06. Leaving standard: also biden-pardons and kpmg-earnings-2025-26. Leaving broad: also draftkings-pm-launch, fed-chair-nomination-2026 and super-bowl-halftime-2026.
- **A48 audit.** 50 alleging claims had no row. 10 gained 28 rows (CL0018, CL0019, CL0020, CL0030, CL0031, CL0035, CL0036, CL0054, CL0118, CL0119); 40 have none, each with a logged reason. The 150 old rows are unchanged. No labelled wallet's alleged positions changed (143 before and after).
- **Knock-on effect through A36.** CL0031 now names "US x Iran ceasefire by March 31?", so that shared market's cut moved from 2026-02-28 06:15 to its own case's time, 2026-03-24 00:00 (note to A48). That changed 15 placebo and 15 twin `t_ref` values and added 28 coordinated-candidate rows. It also added 4 suspected-side positions (labelled-other, not alleged).
- **Usable folds under the A37 connected-component splits** (headline tasks, precise):
  - `label_strict`: **3** (bubblemaps-military-cluster group, maduro-2026-01, zachxbt-axiom-2026-02).
  - `label_standard` and `label_broad`: 4 (adding nobel-peace-2025).
  - **Strict has fewer than 4 usable folds.** The card says so in the benchmark section.
- **Time split.** It has **no alleged positive in its test groups** for any label set: all 142 reliable alleged positions are in train groups, so the time split is empty. The wallet-level secondary version still has 6 folds and a time split.

## 5. A34: economic view after the rebuild
Directional pre-news positions that exist only in the economic view (precise):

| Market set | Share |
|---|---|
| Case markets | 34.3% |
| Twins | 40.5% (40.2% with the A38 twins) |
| Placebos | 51.2% |

Econ-only positions are least common in case markets, so the re-reading is market mechanics, not a case-market signal. Market makers: 18.1% / 17.3% / 13.8% (case / twin / placebo). The market-maker check (`logs/market_maker_check.csv`) is unchanged.

## 6. Claim timing (A42, A49)
- **Ex-ante claims.** 9 claims were published before their alleged market resolved; the alleged side won in **8 of 9 (89%)**.
- **Same-day claims.** 7 of the 9 are dated on the resolution day (`claim_day_contains_resolution = true`), so they likely describe the event after the fact. Only CL0011 and CL0031 are dated a full day earlier, and the alleged side won in 1 of those 2.
- **CL0011** (Google Year in Search) postdates the published ranking.
- **CL0031**, the March 31 ceasefire flag (2026-03-24), is the one clearly pre-news flag, and **its market resolved No**.
- Ex-post claims: 19, of which 14 won, 1 lost and 4 have an unresolved mapped market.

## 7. Counts
- Cases: 66 (E1 4, E2 3, E3 10, E4 13, E5 28, E6 8). Investigation outcome: unresolved 44, under investigation 10, sanctioned 4, charged 3, cleared (analyst) 2, disputed 2, cleared (official) 1.
- Claims: 124 (E1 17, E2 5, E3 14, E4 25, E5 54, E6 9); 109 verified, 15 pending.
- Markets: 1,107 case-market rows (1,009 distinct). Cut methods: case time 733, deadline rule 284, scheduled start 90. 355 rows are unreliable (A29.2), and these cases are removed entirely: ballon-dor-2026, biden-pardons, draftkings-pm-launch, fed-chair-nomination-2026, ftx-sbf, mstr-btc-sale, openai-browser-2025-10, romania-2024, spotify-wrapped-2025, trump-pardon-cz-2025, tweet-count-self-2026-03. Documented wallets with a reliable pre-news position: strict 19 of 19, standard 109 of 111, broad 112 of 117.
- Placebo markets: 4,172; twins 2,486; hard negatives 11,302; fills 65.6 M legs; positions 14,981,178; episodes 59,611; controls 55,879; minute rows 1,765,726.

| Case | Grade | strict | standard | broad | alleged positions (precise) | alleged wallets |
|---|---|---|---|---|---|---|
| us-iran-strike-2026-02-28 | E4 | 0 | 52 | 52 | 97 | 49 |
| kpmg-earnings-2025-26 | E4 | 0 | 22 | 22 | 0 | 0 |
| zachxbt-axiom-2026-02 | E4 | 9 | 10 | 10 | 10 | 10 |
| nobel-peace-2025 | E3 | 0 | 8 | 8 | 8 | 8 |
| maduro-2026-01 | E2 | 1 | 7 | 7 | 5 | 4 |
| us-iran-ceasefire-2026-04-07 | E3 | 3 | 4 | 4 | 11 | 4 |
| world-cup-2026-06 | E4 | 3 | 3 | 3 | 0 | 0 |
| biden-pardons | E4 | 0 | 2 | 2 | 0 | 0 |
| bubblemaps-military-cluster | E4 | 1 | 2 | 2 | 6 | 2 |
| google-yis-2025 | E2 | 1 | 1 | 1 | 1 | 1 |
| israel-rising-lion-2025-06 | E2 | 1 | 1 | 1 | 2 | 1 |
| trump-pardon-cz-2025, taylor-swift-engagement, walz-vp-2024 | E5 | 0 | 0 | 1 each | 1 each | 1 each |
| draftkings-pm-launch, mstr-btc-sale, fed-chair-nomination-2026, super-bowl-halftime-2026 | E5 | 0 | 0 | 1 each | 0 | 0 |
| **Total** | | **19** | **112** | **119** | **143** | **82** |

## 8. Benchmarks (A23, A27, A32, A33, A35, A37; seed 192; alleged positions as positives; precise cuts; reliable markets only)
Every cell is a range of fold values, because every label set has fewer than 6 folds (A32). The time split is empty (section 4). Training uses `label_standard`; `label_strict` is evaluation only. Day-version results are in `baselines.json` (no gradient-boosting tuning).

#### label_standard (precise; folds min-max (n))

| Task | prevalence | gate1_rule | account_age_heuristic | logistic_regression | gradient_boosting_tuned |
|---|---|---|---|---|---|
| T1s | 0.020-0.148 (4) | 0.216-0.844 (4) | 0.088-0.696 (4) | 0.312-0.729 (4) | 0.128-0.975 (4) |
| T2s | 0.500-0.500 (4) | 0.706-0.994 (4) | 0.566-0.645 (4) | 0.552-1.000 (4) | 0.552-1.000 (4) |
| T2w | 0.500-0.500 (4) | 0.716-1.000 (4) | 0.464-0.700 (4) | 0.450-1.000 (4) | 0.583-1.000 (4) |
| T2open | 0.500-0.500 (4) | 0.821-0.972 (4) | 0.783-0.977 (4) | 0.655-0.963 (4) | 0.792-0.995 (4) |
| T1 | 0.001-0.005 (4) | 0.052-0.830 (4) | 0.002-0.058 (4) | 0.180-0.908 (4) |  |
| T2 | 0.500-0.500 (4) | 0.835-0.990 (4) | 0.788-0.980 (4) | 0.686-0.969 (4) |  |
| T3 | 0.500-0.500 (3) | 0.333-1.000 (3) |  | 1.000-1.000 (3) | 0.500-1.000 (3) |
| T3b | 0.500-0.500 (4) | 0.200-1.000 (4) |  | 0.900-1.000 (4) | 0.950-1.000 (4) |

#### label_strict (precise; folds min-max (n))

| Task | prevalence | gate1_rule | account_age_heuristic | logistic_regression | gradient_boosting_tuned |
|---|---|---|---|---|---|
| T1s | 0.004-0.059 (3) | 0.090-1.000 (3) | 0.043-0.333 (3) | 0.144-1.000 (3) | 0.073-1.000 (3) |
| T2s | 0.500-0.500 (3) | 0.744-1.000 (3) | 0.100-0.566 (3) | 0.774-1.000 (3) | 0.920-1.000 (3) |
| T2w | 0.500-0.500 (3) | 0.752-1.000 (3) | 0.000-0.459 (3) | 0.809-1.000 (3) | 0.885-1.000 (3) |
| T2open | 0.500-0.500 (3) | 0.849-1.000 (3) | 0.766-1.000 (3) | 0.834-1.000 (3) | 0.827-1.000 (3) |
| T1 | 0.000-0.003 (3) | 0.005-0.500 (3) | 0.000-0.032 (3) | 0.071-1.000 (3) |  |
| T2 | 0.500-0.500 (3) | 0.855-1.000 (3) | 0.783-1.000 (3) | 0.839-1.000 (3) |  |
| T3 | 0.500-0.500 (2) | 0.200-0.975 (2) |  | 1.000-1.000 (2) | 0.500-1.000 (2) |
| T3b | 0.500-0.500 (3) | 0.200-1.000 (3) |  | 1.000-1.000 (3) | 0.971-1.000 (3) |

#### label_broad (precise; folds min-max (n))

| Task | prevalence | gate1_rule | account_age_heuristic | logistic_regression | gradient_boosting_tuned |
|---|---|---|---|---|---|
| T1s | 0.020-0.148 (4) | 0.216-0.844 (4) | 0.088-0.696 (4) | 0.319-0.725 (4) | 0.137-0.925 (4) |
| T2s | 0.500-0.500 (4) | 0.706-0.994 (4) | 0.566-0.645 (4) | 0.521-1.000 (4) | 0.406-1.000 (4) |
| T2w | 0.500-0.500 (4) | 0.716-1.000 (4) | 0.464-0.700 (4) | 0.442-1.000 (4) | 0.375-1.000 (4) |
| T2open | 0.500-0.500 (4) | 0.821-0.972 (4) | 0.783-0.977 (4) | 0.655-0.967 (4) | 0.841-1.000 (4) |
| T1 | 0.001-0.005 (4) | 0.052-0.830 (4) | 0.002-0.058 (4) | 0.185-0.853 (4) |  |
| T2 | 0.500-0.500 (4) | 0.835-0.990 (4) | 0.788-0.980 (4) | 0.689-0.969 (4) |  |
| T3 | 0.500-0.500 (3) | 0.333-1.000 (3) |  | 0.833-1.000 (3) | 0.500-1.000 (3) |
| T3b | 0.500-0.500 (4) | 0.200-1.000 (4) |  | 0.900-1.000 (4) | 0.962-1.000 (4) |

#### label_strict per fold (precise, logistic regression / Gate 1 / tuned GB)

| Task | loco:bubblemaps-military-cluster | loco:maduro-2026-01 | loco:zachxbt-axiom-2026-02 |
|---|---|---|---|
| T1s | 0.144 / 0.090 / 0.073 (n+=8) | 1.000 / 1.000 / 1.000 (n+=1) | 0.440 / 0.308 / 0.203 (n+=9) |
| T2s | 0.774 / 0.871 / 0.920 (n+=8) | 1.000 / 1.000 / 1.000 (n+=1) | 0.862 / 0.744 / 0.970 (n+=9) |
| T2w | 0.809 / 0.889 / 0.885 (n+=8) | 1.000 / 1.000 / 1.000 (n+=1) | 0.852 / 0.752 / 0.941 (n+=9) |
| T2open | 0.834 / 0.849 / 0.827 (n+=8) | 1.000 / 1.000 / 1.000 (n+=1) | 0.853 / 0.863 / 0.934 (n+=9) |

#### wallet-level secondary (precise, logistic regression)

- label_standard T1s: 0.227-0.942 (6), time split 0.840
- label_standard T2s: 0.494-0.932 (6), time split 0.847
- label_strict T1s: 0.067-0.804 (4), time split 0.917
- label_strict T2s: 0.494-0.777 (4), time split 0.796

#### day version, label_standard, logistic regression

- T1s: 0.237-0.575 (3)
- T2s: 0.913-1.000 (4)
- T2w: 0.914-1.000 (4)
- T2open: 0.894-1.000 (4)

### What the benchmarks show
- **Strict is anecdotal.** In the Maduro fold, every model, Gate 1 included, ranks the single positive first (1.000). The other two strict folds disagree by up to 0.3 AP in T1s (bubblemaps 0.144, Axiom 0.440 for logistic regression).
- **The Gate 1 rule is the steadiest detector on the selection-controlled tasks.** T2s for label_standard: Gate 1 0.706-0.994 against 0.552-1.000 for logistic regression and tuned gradient boosting; T2w: 0.716-1.000 against 0.450-1.000 and 0.583-1.000. On broad, tuned gradient boosting falls to 0.406 (T2s) and 0.375 (T2w) in one fold.
- **Age matching still removes the account-age shortcut** (T2s heuristic 0.566-0.645). It returns when Orca/Inca wallets may be controls (T2-open 0.783-0.977), as in run 10.
- **Alleged positives change T2's construction.** In T2s only 44 of 140 alleged episodes have a same-side control (39 in T2w, where 131 control rows needed the adjacent band). Every alleged episode and every same-side control won; every other-side control lost. Price features therefore separate the classes partly by construction: `first_price_usdc` has univariate AUC 0.85 in T2s and 0.88 in T2w. `prior_net_long_win_rate` falls from 0.90 (T2s) to 0.83 (T2w) when matched on its band. *Read T2 results as "alleged winner vs other-side buyer" for most episodes.*
- **T1s.** `gate1_score` has univariate AUC 0.92 and lifetime market count 0.87: sources flag fresh, concentrated wallets.
- **T3 (case vs twins, all matched case markets).** 443 case markets against 2,089 twins over 6 folds: logistic regression 0.583-1.000, Gate 1 rate 0.474-0.956. The per-label-set T3 has only 3 folds (strict 2). T3b stays market-type sensitive (gradient boosting at least 0.95 in every set).
- **Wallet-level secondary** (any position of a labelled wallet; logistic regression): label_standard T1s 0.227-0.942 over 6 folds, time split 0.840; T2s 0.494-0.932, time split 0.847.

## The 10 biggest remaining weaknesses (ranked), each with its fix
1. **Strict evaluation is anecdotal.** `label_strict` has **3 usable leave-one-group-out folds** (fewer than 4), one of which (Maduro) holds a single positive that every model ranks first, and the time split is empty. Standard and broad have 4 folds. *Fix:* more official cases with published addresses (dockets, CFTC and Kalshi orders); until then report strict per fold only, never as a headline.
2. **Positives are concentrated and won by construction.** 97 of 140 `label_standard` alleged positions are in one case (`us-iran-strike-2026-02-28`); no alleged position lost (all 39 losing suspected-side positions are labelled-other positions). Sources describe winning bets, so a model can learn "this bet won" through any outcome-correlated feature. *Fix:* cases found without looking at outcomes (platform referrals, regulator data), and per-case reporting as the default.
3. **Whole cases drop out of the alleged positives.** `kpmg-earnings-2025-26` (22 standard wallets) and `world-cup-2026-06` (3 strict wallets) have no claim that names a market or side, so 30 wallets have no alleged position. *Fix:* read the KPMG and World Cup sources again for named markets (new claims, never edits), or report wallet-level results for those cases.
4. **Coarse dates still remove a third of the case markets.** 355 of 1,107 market rows are `t_news_reliable = false` (11 cases; Ballon d'Or, Spotify, tweet-count and the pardon cases entirely or mostly). *Fix:* sourced first-report times for those cases (A10), searched case by case as in `logs/exact_time_search_run11.md`.
5. **Data-API-era case markets get no twins** (203 market rows: World Cup, Nvidia, most of Ballon d'Or and Survivor): A22 matches on the Polymarket-v1 `category_refined`, which Gamma lacks, so T3 covers only pre-May-2026 cases. *Fix:* an amendment that defines categories from Gamma tags for post-2026-04-28 markets and pulls their twins' fills from the Data API.
6. **The claim mapping rests on one AI extractor.** The A48 audit found 10 claims that the run-11 spec had missed (CL0031 among them), so the mapping error rate is unknown. *Fix:* the human second extractor maps the 36-row blind sample (`logs/blind_check_sample.csv`, section 2) and the 18-claim sample (section 1); report agreement.
7. **Claim timing says little about ex-ante validity.** Of 9 claims dated before their market resolved, 7 are dated on the resolution day; only CL0011 and CL0031 are a full day earlier, and CL0011 still postdates the published result. The one clearly pre-news flag (CL0031, ceasefire by March 31) lost. *Fix:* collect timestamped pre-resolution flags (analyst posts with minute times) as a separate claim type.
8. **Cluster links are unchecked.** 87 of 112 `label_standard` wallets are cluster members linked by money flows that this dataset cannot verify (no archive Polygon RPC; A8 not run). *Fix:* an archive RPC or explorer key to run the money graph.
9. **Prior win rate remains a selection shortcut** (sources find wallets that won before); T2w controls for its band, but the feature still carries the sources' search rule. *Fix:* T2w as the main T2 task and features that do not use past outcomes.
10. **Small reproducibility gaps.** The rebuild is byte-identical for case fills, but `prior_net_long_win_rate` differs by at most 0.0065 in 143 control rows (most likely the non-deterministic `any_value()` over outcome labels in the catalog join), Data API pulls are not guaranteed stable, and Kalshi has no trades. *Fix:* a deterministic aggregate (`min()`) in `episodes.py`, snapshots of API pulls with the release, Kalshi trade data.

## Decisions needed
1. **Owner placeholders** (unchanged): contact e-mail, `<hf-user>/pmitc`, `<kaggle-username>/...`, extractor model name in EXTRACTION.md.
2. **A48 and A36 together:** accept that the audit moved the cut of "US x Iran ceasefire by March 31?" to its own case (2026-03-24), or freeze A36's source-case choice to the pre-audit mapping.
3. **Daily markets in event claims (A35.1):** CL0079 names the Oct 1 2024 strike and a Yes side, but its only same-event market is the daily "today?" market, which A35.1 excludes. Keep the exclusion, or allow a daily market when it is the event's only market?
4. **Determinism fix:** amend `episodes.py` to use a deterministic outcome-label aggregate (changes `prior_net_long_win_rate` and the T2w bands slightly).
5. **Twins for post-April-2026 markets** (weakness 5): Gamma-tag categories, yes or no.
6. **Strict as a reported column** (weakness 1): keep the strict column with per-fold values, or drop it from the card until it has 4 or more folds.
7. **Human blind check:** who extracts sections 1 and 2.
