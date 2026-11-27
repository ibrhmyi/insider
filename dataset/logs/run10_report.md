# Run 10 report (2026-11-27): PMITC v1.2.0, final fixes and freeze

Nothing was uploaded. Every rule change was committed as a dated PROTOCOL amendment before the tables it governs were computed. No claim was edited. One new claim (CL0124, a context claim recording the World Cup re-read) was added. Branch `claude/pmitc-v1`.

## Amendments
| Id | Rule | Committed |
|---|---|---|
| A25 | Per-market news times: Gamma scheduled start (rule 1), else a market deadline inside a coarse case date (rule 2), else the case time (rule 3). Case-level columns kept. | before any run-10 table |
| A25.1 | A structural time never moves a cut later than a sourced exact case time | after a first draft, before any table used it |
| A25.2 | A deadline-form question ("by <date>", "before <month/year>") never takes a scheduled-start cut | after the first per-market tables, **before** the release tables and benchmarks; all time-dependent tables rebuilt again |
| A26 | `label_strict` also needs a pre-news buy under the precise cut; `strict_no_prenews` flag; `label_standard` is the training label, `label_strict` evaluation-only | before computing |
| A27 | Selection-controlled headline tasks T1s, T2s, T2-open; `control_design` in `episodes`/`controls` keys | before any run-10 benchmark |
| A28 | `label_family = multi_account` for shared-ownership / multi-accounting allegations without an informed-trading claim; excluded from label sets | before computing |

**Why A25.2 was needed.** The first gate run (`test_market_cut_not_after_sourced_case_time`) showed one market whose cut was five months after its case date. The market is "MicroStrategy sells any Bitcoin by May 31, 2026?". Its Gamma `gameStartTime` (2026-06-01) is the deadline, not an event, and the case date is December 2025. Under rule 1, trades after the news counted as pre-news. A25.2 moves 2 markets: mstr-btc-sale goes to `case_time`, and uma-ukraine-minerals-2025 goes to `case_time` (3 minutes later than its scheduled start, inside the case day). Their placebo and twin `t_ref` (10 rows) were updated too. Everything time-dependent was rebuilt after it.

## 1. Per-market news times (A25)
| Method | Markets |
|---|---|
| `case_time` | 743 |
| `market_deadline` | 285 |
| `scheduled_start` | 90 |

| Case | case_time | deadline | scheduled start | median shift vs case precise time |
|---|---|---|---|---|
| tweet-count-self-2026-03 (range) | 0 | 132 | 0 | +689 h |
| ballon-dor-2026 (year) | 1 | 89 | 0 | +7,180 h |
| world-cup-2026-06 (month) | 0 | 0 | 51 | +358 h |
| kpmg-earnings-2025-26 (month) | 0 | 0 | 39 | +782 h (range -251 to +3,301 h) |
| spotify-wrapped-2025 (month) | 0 | 36 | 0 | +720 h |
| biden-pardons (month) | 0 | 13 | 0 | +468 h |
| ftx-sbf (year) | 12 | 6 | 0 | +5,424 h |
| romania-2024 (month) | 0 | 6 | 0 | +180 h |
| mstr-btc-sale, openai-browser-2025-10, draftkings-pm-launch (month) | 4 / 0 / 0 | 1 / 1 / 1 | 0 | +720 to +732 h |

- The case-level `t_news_utc` / `t_news_precise_utc` are unchanged. The new columns are `markets.t_news_market_utc`, `t_news_market_day_utc` and `t_news_market_method`.
- Rebuilt with the per-market cut:
  - the coordinated-buyer rule (16,997 candidate rows);
  - episodes and controls for 3 designs × 2 versions;
  - positions (11.74 M rows) and minute paths (2.22 M);
  - label sets, hard negatives and amount checks;
  - placebo and twin `t_ref` (placebo: 1,421 day and 1,721 precise rows changed; twin: 550 day and 630 precise).
- This also fixes stale precise `t_ref` values for the Maduro and Railgun-Venezuela placebos and twins left by run 9. Run 9 set their exact case time after the references were computed.
- Documented episodes: 580 in the precise version, 461 in the day version.

## 2. World Cup 2026 source re-read (A28)
- **What the source alleges:** the source (a Lookonchain post, reported by crypto.news) says "a suspected insider made $24.25M from #WorldCup betting" through three accounts (5/5, 2/2 and 6/9 winning bets). It gives one fact as evidence that one person controls the accounts: the same Binance deposit address. The wallets then stopped trading and withdrew. crypto.news adds that the claim "remains based on wallet links and public trading data".
- **Classification:** the allegation is informed trading. Shared control is the evidence that links the accounts, not the allegation itself. So A28 is not triggered, and the case stays `informed_trading`. The reading is recorded as context claim CL0124 (verified, stance context).
- **Amount check:** the three wallets' net payout in the case markets is $23.38 M, 2.0% from the claimed $24.25 M. That is within tolerance, so there is no contradiction.
- **Side effect:** `claim_wallet_links` gained 6 rows linking CL0124 to the three wallets, by handle and source URL. They change no label (strict 19 before and after). A context claim arguably should not create links; see decision 3.

## 3. Strict needs a pre-news buy (A26)
- All 19 `label_strict` wallets (7 cases) bought before their market's precise cut, so `strict_no_prenews` is empty (0 wallets).
- Label counts are unchanged: strict 19, standard 112, broad 119.
- `label_standard` is the main training label. `label_strict` is evaluation-only: models are trained on `label_standard` and scored on strict positives. The card, the benchmark README and `baselines.json` (`training_label`) say so.

## 4. Selection-controlled benchmarks (A27; precise times; seed 192; case-weighted leave-one-case-out mean ± SD (folds) / time split)
Episode counts (precise): 580 suspected episodes in each design. Other-side controls: 5,727 standard, 5,121 age-matched, 5,727 open. With age matching, 145 of 580 episodes have no same-side control (38 under the standard design), because bands are never relaxed.

### Headline
| Task | Model | label_standard (train = eval) | label_strict (eval only) | label_broad |
|---|---|---|---|---|
| T1s AP | prevalence | 0.134 ± 0.192 (7) / 0.166 | 0.161 ± 0.246 (4) / 0.199 | 0.134 ± 0.192 (7) / 0.166 |
| | Gate 1 rule | 0.423 ± 0.208 / 0.406 | 0.518 ± 0.372 / 0.277 | 0.423 ± 0.208 / 0.406 |
| | account age | 0.425 ± 0.227 / 0.326 | 0.545 ± 0.375 / 0.283 | 0.425 ± 0.227 / 0.326 |
| | logistic regression | **0.514** ± 0.238 / 0.458 | 0.457 ± 0.267 / 0.329 | 0.515 ± 0.236 / 0.453 |
| | tuned GB | 0.476 ± 0.240 / 0.438 | 0.551 ± 0.381 / 0.316 | 0.488 ± 0.253 / 0.394 |
| T2s AUC | account age | **0.568** ± 0.101 / 0.532 | 0.495 ± 0.116 / 0.582 | 0.568 ± 0.101 / 0.532 |
| | Gate 1 rule | 0.755 ± 0.123 / 0.772 | **0.840** ± 0.149 / 0.803 | 0.755 ± 0.123 / 0.772 |
| | logistic regression | 0.703 ± 0.150 / 0.788 | 0.490 ± 0.180 / 0.797 | 0.753 ± 0.127 / 0.795 |
| | tuned GB | 0.715 ± 0.098 / 0.760 | 0.684 ± 0.136 / 0.682 | 0.763 ± 0.101 / 0.746 |
| T2-open AUC | account age | 0.795 ± 0.146 / 0.676 | 0.771 ± 0.190 / 0.709 | 0.795 ± 0.146 / 0.676 |
| | Gate 1 rule | 0.724 ± 0.126 / 0.662 | 0.754 ± 0.181 / 0.636 | 0.724 ± 0.126 / 0.662 |
| | logistic regression | 0.733 ± 0.155 / 0.824 | 0.629 ± 0.120 / 0.834 | 0.768 ± 0.098 / 0.837 |
| | tuned GB | 0.847 ± 0.095 / 0.760 | 0.818 ± 0.138 / 0.744 | 0.847 ± 0.098 / 0.720 |

### Secondary (unchanged definitions)
| Task | Best model, label_standard | account age | Gate 1 |
|---|---|---|---|
| T1 AP | LR 0.363 ± 0.228 / 0.352 | 0.051 | 0.233 |
| T2 AUC | account age 0.800 ± 0.147 / 0.677 | 0.800 | 0.731 |
| T3 AUC | LR 0.883 ± 0.087 / 0.915 | n/a | 0.754 |
| T3b AUC | GB 0.958 ± 0.042 / 0.924 (market-type sensitive) | n/a | 0.529 |

The day version is in `baselines.json`; it has no GB tuning. Day results for label_standard: T1s LR 0.371; T2s account age 0.585 and LR 0.815; T2-open account age 0.787 and LR 0.839.

### What the selection-controlled tasks show
- **Age matching removes the account-age shortcut.** The account-age heuristic falls from 0.800 (T2) to 0.568 (T2s), and the feature's univariate AUC falls from 0.82 to 0.50. Gate 1 (0.755) and the models (0.70-0.72) now beat it. In T2, "new wallet" alone was the best detector.
- **The past-performance shortcut is selection, not construction.** Allowing Orca/Inca-flagged wallets as controls (T2-open) changes almost nothing: `prior_net_long_win_rate` has univariate AUC 0.877 in T2-open against 0.880 in T2, and the account-age heuristic stays at 0.795. The A6.10 exclusion removed few relevant wallets: the pool excludes 1,763 addresses instead of 12,337, yet the control counts hardly move. So the run-9 explanation, "partly construction", was mostly wrong. Documented wallets win more often in their *prior* markets than matched controls do, under every design (T2s univariate 0.879).
- **The size band removes the size shortcut but not account age.** In T1s, size features fall to univariate AUC 0.67 (0.93-0.98 in T1), and prevalence rises from 0.004 to 0.134. Account age (0.79) and lifetime market count (0.86) still separate positives within the band: sources flag fresh wallets.
- **Strict is fragile.** Strict T2s has 4 folds. The Maduro fold holds 1 positive, Iran-ceasefire 14, World Cup 12 and Axiom 18. LR scores 0.490 leave-one-case-out but 0.797 on the time split. Report strict results as fold ranges, never as one number.
- **Outcome does not separate episodes.** In T2s, matched same-side controls won 83.1% of the time and documented episodes 83.8%.

## 5. Issue templates
`release/.github/ISSUE_TEMPLATE/{submit_case,correct_row,request_removal}.md` are copied to the repository root `.github/ISSUE_TEMPLATE/`. The contact e-mail (`<owner contact e-mail ...>`) and the upload ids (`<hf-user>/pmitc`, `<kaggle-username>/...`) remain placeholders for the owner.

## 6. Version, docs and quality gates
- **Version and docs:** v1.2.0 in the CHANGELOG, CITATION.cff, DATASHEET, EXTRACTION (run 10 row), dataset card, `dataset/README.md` (run-10 build order) and benchmark README. The notebooks are regenerated and executed without errors; 03 re-runs T2s and reproduces the stored values. Kaggle metadata (59 resources), CODEBOOK, both MANIFESTs, `release_safe` and the upload copies are all regenerated.
- **New gates (85 in total):**
  - A25 and A25.2: cut bounds and no deadline-form scheduled starts;
  - positions use the market's own cut;
  - A26: every strict wallet has a pre-news buy, and `strict_no_prenews` is disjoint from strict;
  - A27: three designs with identical suspected episodes;
  - A19/A28: only `informed_trading` wallets carry label sets.
  - The A25.2 test cannot check withheld-title markets (no question text in the release).

| Copy | Result |
|---|---|
| `release/` | 85 passed |
| `release_safe/` | 84 passed, 1 skipped (boundary dedup; Data API rows withheld) |
| `upload/hf/` | 85 passed |
| `upload/kaggle/` (flat; tested through a folder view of symlinks) | 84 passed, 1 expected failure: `dataset-metadata.json` is rewritten with the flat resource names by design, so its hash differs from the manifest; every other file matches |
| `upload/zenodo/pmitc-v1.2.0.zip` (2.77 GB; SHA-256 verified, unpacked to scratch) | 85 passed |

## Operational notes
- **Benchmark crash:** the first full benchmark run crashed. In T2s, a test case with no known account ages made the account-age baseline NaN. The fix: such a case ranks as ties (AUC 0.5), committed separately.
- **Memory:** running tests next to the benchmark was killed for lack of memory (one 15 GB limit). Gates were run afterwards, one copy at a time.
- **Raw Gamma profiles:** the rebuild wrote raw Gamma profile JSON files. They are now git-ignored (`logs/gamma_raw/profile_*.json`); only `createdAt` is kept, in `profiles_created_run7.csv` (+581 rows for the new age-matched candidates).

## The 10 biggest remaining weaknesses (ranked) and what would fix each
1. **Strict evaluation rests on 4 folds, one of them with a single positive** (Maduro). The strict numbers swing by 0.3 AUC between leave-one-case-out and the time split. *Fix:* more official cases with published addresses (court dockets, CFTC/Kalshi orders), a second extractor, and fold-level reporting as the only form.
2. **Prior-market win rate is a selection shortcut that no control design removes** (univariate AUC 0.88 in T2, T2s and T2-open). Sources find wallets *because* they won before, so the features that look most predictive are partly the sources' own search rule. *Fix:* cases found without looking at past wins (platform referrals, regulator data), and a T2 variant matched on prior win-rate band.
3. **Coarse case dates make per-market cuts very late.** With a year- or month-level case date, rule 2 sets the cut at each market's deadline. Ballon d'Or cuts fall about 7,180 h after the case time, FTX up to 8,736 h. This is correct only if the news is the resolution; for a leak that came earlier, post-leak trades count as pre-news. *Fix:* sourced exact times for those 11 cases, or an amendment that caps rule 2 at a fixed window before the deadline.
4. **Rule 1 trusts Gamma's `gameStartTime`/`eventStartTime`.** A25.2 catches deadline-form questions only by a regular expression, and withheld-title markets cannot be checked. KPMG cuts span -251 h to +3,301 h around the case month. *Fix:* check each scheduled start against the market's `closedTime`/resolution time, and hand-check the 90 scheduled-start markets.
5. **Age matching costs coverage.** 145 of 580 episodes have no same-side control under the age-matched design, against 38 under the standard design. T2s is therefore biased towards episodes in well-populated age bands. *Fix:* a larger control pool (all buyers in the token, not only the matched time window), or adjacent-band relaxation recorded as a flag.
6. **87 of 112 standard positives are cluster members** linked by money flows we cannot check (no money graph). Training on `label_standard` inherits that unchecked linkage. *Fix:* an archive Polygon RPC or explorer key to run A8 and verify the links.
7. **Labels are allegations; none is adjudicated.** The only E2 links are Maduro, Google and Israel (charged or official), none decided. *Fix:* follow the dockets (CourtListener blocked here) and record outcomes as new claims.
8. **Context claims create wallet links.** CL0124 added 6 `claim_wallet_links` rows. The run-10 counts are unaffected, but a reading note can raise a wallet's link count. *Fix:* restrict links to claims whose stance is `alleges` or `confirms` (an amendment); decision 3.
9. **Kalshi remains a blind spot** (10 E1 notices, no trades) and **T3b mostly measures market type** (GB 0.958 on crypto/weather placebos). *Fix:* Kalshi public market-trade data for minute paths; Gamma-based twins with finer tags for post-April 2026 markets.
10. **Reproducibility of API data.** Data API pulls are not hash-stable. Polymarket-v1 records some economic buys as maker sells of the other token (A6.4), which distorts stakes. The second-extractor check (A4) is still pending. *Fix:* snapshot API pulls with the release, add the CTF mint/merge layer, and have a person re-extract the 18-claim sample.

## Decisions needed
1. **Rule 2 cap (weakness 3):** keep deadline cuts for coarse-dated cases, or cap them (for example 7 days before the deadline) in an amendment?
2. **Scheduled-start audit (weakness 4):** accept Gamma's times as structural, or require a `closedTime` check before a scheduled start is used?
3. **Context-claim links (weakness 8):** amend so only `alleges` or `confirms` claims create `claim_wallet_links` rows?
4. **Headline metric for strict:** keep reporting strict as an evaluation column, or report only fold ranges until it has at least 6 folds?
5. **Owner placeholders before upload:** contact e-mail, `<hf-user>/pmitc`, `<kaggle-username>/pmitc-prediction-market-informed-trading`, extractor model name in DATASHEET.
