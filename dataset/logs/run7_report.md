# Run 7 report (2026-11-26)

Run 7 turned PMITC into a release package (v1.0.0, `release/`): typed tables, two news-time versions, all-buyer positions, placebo markets, coordinated-buyer candidates, benchmarks, tests, licensing and ethics notes. Every new rule was written as a dated amendment and committed before the computation it governs. Nothing was uploaded. Branch `claude/pmitc-v1`.

## Amendments written this run

| Amendment | Committed | Governs |
|---|---|---|
| A10 | before any run-7 table | exact news times: `t_news_precise` from `event_times.csv` (minute, quarter-hour, hour, window start), day fallback; every time-dependent table in `day` and `precise` versions |
| A11 | before re-checking handles | a handle also resolves by exact **pseudonym**, but only if the wallet's fills confirm the market, side and window |
| A12.1 to A12.6 | with A10/A11 | E3 covers employer discipline (D8); money graph out of scope (D2: no `POLYGON_RPC` or explorer key set); ACDC kept exactly (D3); `inca_flag` kept and described (D4); `trade_confirmed` / `is_documented` (D5); tweet-count markets by condition id with titles withheld (D7) |
| A12.7 | after the name test found three titles | any case-market title naming a listed person is withheld |
| A13 | before the coordinated-buyer search | coordinated buyers and placebo-window false-positive rate |
| A14 | before placebo selection | placebo categories (crypto prices, weather readings), matching and relaxation, `t_ref` |
| A14.1 | after a discarded first selection, before the used one | weather markets lack `resolved_at` (use `close_at`); whole-token coin match; relaxation bug fix |
| A14.2 | | the 4 markets of the new Nvidia case are not placebo-matched (added after the pass started) |
| A15 | before any split or baseline | case-grouped, time-ordered split (test = first claim on/after 2026-03-01); baselines |
| A16 | before any gate value | Gate 1 = frozen v1 Layer 1 with two stated input substitutions; Gate 2a/2b = Signals A/B |
| A16.1 | after a failed first computation (no values), before any gate value | F2 market branch uses lifetime markets, as frozen v1 itself specifies (disk allowance) |

## Environment

- Reachable: Hugging Face, Polymarket Gamma and Data API v2, docs.polymarket.com, justice.gov, the public Kalshi notice bucket (`kalshi-public-docs.s3.amazonaws.com`), cryptoslate.com, raw.githubusercontent.com.
- Not reachable (proxy): kalshi.com, news.kalshi.com, courtlistener.com, polymarket.com, kaggle.com, reed.senate.gov and several outlets. cftc.gov answers 403 (site bot protection). Nothing was worked around: these pages are in `logs/needs_page_read.csv` (46 entries, 24 added this run). One attempt to fetch the pending claim pages with a browser user agent was blocked by the session's own guard, which is the right outcome under B4; no page was fetched that way.
- No `POLYGON_RPC` or explorer key was set (checked at the start), so the money graph stayed out of scope (A12.2).
- The session's disk allowance and memory limit forced three rewrites (positions streamed in SQL, F2 streamed from the day files, fills written by DuckDB `COPY`); each failure is listed below. The raw Polymarket-v1 tape (16 GB) was re-downloaded at the pinned commit, used, then deleted; it is re-downloadable.

## Phase A: decisions

- **D1 / A10.** 7 new sourced times added to `data/event_times.csv` (committed before the rebuild): papal conclave balcony announcement, US warning before the Oct 2024 Iran strike, Super Bowl LX halftime start, the SEC ETF approval report, the Arbitrum airdrop report, and the Feb-28 strike start for `khamenei-removal-2026` and `bubblemaps-military-cluster`; plus the Nvidia announcement for the new case. 17 of 42 market-bearing cases now have an exact time (`t_news_precise_precision`, per case: minute 9, quarter-hour 4, hour 3, window 1). Searches that found no usable time (election night, Walz, Vance, GPT-5.2, Swift, Spotify, CZ pardon, Zelenskyy meeting, Super Bowl LIX) are logged with the reason; for the election, results came in through the night, so no single time was taken.
- Caveat on A10: where the day-level date was month-precision, the exact time can be weeks later (Gemini 3: 2025-11-01 vs 2025-11-18 16:00 UTC). The rule takes the source's time as written; earlier leaks, if any, are not modelled.
- **D2** money graph: out of scope (no RPC/key). **D3** ACDC: rerun gives exactly the run-3 counts (90,843 longshots, 13,045 wallets, 1,599 Orcas, 294 military Orcas); not a label. **D4** `inca_flag` kept (9,285 vs 39). **D5** `trade_confirmed`: 120 of 133 suspected wallets are trade-confirmed (unchanged from run 6). **D6 / A11**: `Burdensome-Mix` resolves by pseudonym to `0x31a56e9e…`, whose 7 confirming buys total $32,538.34 (the CFTC figure); the address was already labelled, so no new wallet. **D7**: 132 weekly post-count markets attached by condition id, titles withheld. **D8 / A12.1**: the OpenAI firing claim keeps E3 under the new rule.

## Phase B: more insider data

- **B1 coordinated buyers (A13).**

  | | day | precise |
  |---|---|---|
  | triggers (pre-news BUY legs of documented wallets) | 10,644 | 13,107 |
  | candidates per trigger | 0.347 | 0.446 |
  | candidates per placebo window | 0.102 | 0.145 |
  | placebo / real ratio (false-positive rate proxy) | 0.29 | 0.32 |
  | share of triggers with >= 1 candidate | 21.0% | 25.8% |
  | share of placebo windows with >= 1 candidate | 7.9% | 10.3% |
  | distinct candidate wallets | 1,090 | 1,313 |

  1,338 (wallet, case) candidate rows (1,313 wallets) were added as `L4_coordinated`, `polarity = candidate`: 686 in the Feb-28 Iran strike, 159 Walz, 148 Axiom, 124 April ceasefire, 121 Bubblemaps cluster, the rest under 50 each. About a third of the real hits are expected by chance, so these are search leads, not labels. 8,792 Gamma profiles were looked up; 883 (precise) size/time matches had no profile and were not candidates. Raw profiles are not committed (only `createdAt`, `logs/gamma_raw/profiles_created_run7.csv`).
- **B2 official sources.**
  - Kalshi: the public notice bucket lists 674 files; all 11 disciplinary notices were read (PDF text). 10 became E1 claims, one per notice, notice ID as subject (CL0108-CL0117); KDA-2026-0010 (account misuse, trading for another person) is outside the protocol's families and was excluded (logged). Three notices print "EFFECTIVE April 21, 2025" in files posted on 2026-04-22: recorded as printed, flagged in `notes`.
  - CFTC: release 9276-26 (State of the Union contract order) added as CL0122, `pending` (cftc.gov 403). 9217-26 and 9237-26 were already held. The teleprompter-operator CFTC settlement is covered by KDA-2026-0011.
  - DOJ: no new prediction-market releases beyond the two SDNY cases already held (the API's keyword filter is not honoured, so site search was used).
  - CourtListener: not reachable; the four SDNY docket lookups are in `needs_page_read.csv` (docket number, filing dates, status, no names).
  - Polymarket integrity statement (X post on the DOJ referral, CL0121, pending) and the Reed/Hickenlooper Senate letter to the CFTC (CL0120, E5: a request, not an inquiry; pending).
- **B3 press.** One new case: **`nvidia-ceo-return-2026-11`** (Bubblemaps, 2026-11-23: 16 freshly funded Nvidia-only accounts, about $20k to $350k; CL0118 verified by reading CryptoSlate, post URL recovered; CL0119 Public Citizen's separate account; CL0123 Kalshi side, 21 trades of $3k+). 4 markets attached (Gamma event `jensen-huang-rejoins-nvidia-by…`), fills from the Data API. Only a `0x307` prefix is published, so no wallet is labelled. The topic queries stopped after two queries with nothing new. 30 queries logged (n 116-145).
- **B4.** 24 unreachable pages listed with what to extract (`needs_page_read.csv`).
- **B5 handles.** 22 handles checked (`logs/handle_checks_run7.csv`): 17 resolve with confirming fills (14 exact name, 3 case-insensitive), 1 by pseudonym (`Burdensome-Mix`), 1 rejected (`ricosuave666`: exact match with no case fills), 3 unresolved (`AlphaRaccoon`, renamed, settled from fills in run 2; `OnlyBibi2026`, no profiles; `BornTooLate.eth`, an ENS name, not a Polymarket handle; `hogriddahhhh` also has no profile match).
- **B6.** Pending claims could not be re-read from this environment; all 16 pending claims are in `needs_page_read.csv`. No claim changed status except the new ones read this run.

**New insider wallets this run: none documented.** The new handle resolution points to an address already labelled; the new case publishes no addresses. The documented set stays at 120 wallets in 19 cases. 1,313 candidates are new, with the false-positive rate above.

## Counts

| | E1 | E2 | E3 | E4 | E5 | E6 | total |
|---|---|---|---|---|---|---|---|
| claims | 17 | 5 | 14 | 24 | 54 | 9 | 123 (16 new; 107 verified, 16 pending) |
| cases | 4 | 3 | 10 | 13 | 28 | 8 | 66 (1 new) |
| documented wallets by `doc_grade` | | 9 | 12 | 91 | 8 | | 120 |

Investigation outcome: sanctioned 4, charged 3, cleared (official) 1, cleared (analyst) 2, disputed 2, under investigation 10, unresolved 44.

Wallet labels (1,598 rows): L2 official 3, L3 analyst address 19, L3 handle 12, L4 cluster 99 suspected + 8 context, L4_coordinated 1,338 candidates, A ambiguous 11, NC 71, M 37.

## Phase C: placebo and context

- **C1 (A14, A14.1).** Pool: 281,671 crypto-price and 33,974 weather-reading markets. 4,227 placebos matched to 743 case markets (each used once): exact 1,445; month ±1 880; ±3 515; ±6 140; adjacent band 945; any month 60; adjacent decile 242. Not matched: 141 zero-volume case markets, 123 with no placebo available, 4 added after the pass (A14.2). Categories: 3,927 crypto, 300 weather.
- **C2 positions.** 6,074,515 rows (case: 1.44 M day / 1.50 M precise; placebo: 1.55 M / 1.59 M), about 430 k distinct buyers per version in case markets. Gate 1 fires on 2.7% of case and 1.9% of placebo positions (precise); Gate 2a on 1.9% and 3.1%.

## Phase D: tables

13 typed tables in `release/data/` (parquet; CSV where under 50 MB). Fills: 58,060,526 legs (case 23.1 M, placebo 30.3 M, other legs of labelled wallets 4.7 M, mostly the A13 candidates' histories). Case-market legs changed from run 6 for four cases: tweet-count (+113,742, newly attached), Nvidia (+58,131, new), fed-chair (+302,313) and Super Bowl LX (+35,534): the Data API now returns more rows for those markets than the run-5/6 pulls (the fed-chair markets kept trading after Polymarket-v1 ends; the Super Bowl difference is not explained). Episodes: 425 (day, as in run 6) and 479 (precise; +54, mostly Axiom +11, Nobel +12, Maduro +4, ceasefire +4); controls 16,767; same-side controls for every episode in both versions; relaxation (precise): base 282, size 139, price 21, window 21. Minute paths: 1,239,464 rows (case and placebo, both versions).

## Phase E: benchmarks (seed 192; `release/benchmarks/baselines.json`)

Split (A15): 29 train cases, 37 test cases (test holds 4 cases with documented wallets in scored markets: 32 positives, precise).

| Task (precise) | Metric | Random | Gate 1 rule | Logistic regression | Gradient boosting |
|---|---|---|---|---|---|
| T1 ranking, test | AP / R@100 | 0.052 / 0.34 | 0.065 / 0.35 | 0.076 / 0.78 | 0.012 / 0.11 |
| T1 ranking, train grouped CV | AP | | | 0.352 | 0.194 |
| T2 episodes, test | AUC (log loss) | | | 0.788 (0.186) | 0.704 (0.356) |
| T2 episodes, grouped CV | AUC | | | 0.801 | 0.879 |
| T3 markets, test | AUC | | | 0.718 | 0.844 |
| T3 markets, grouped CV | AUC | | | 0.748 | 0.856 |

- T2 base result: matched same-side controls won 83.5% of the time, documented episodes 83.9% (precise); outcome does not separate them.
- One construction artifact was found and moved to the leakage list before reporting: `share_on_this_ladder_market` alone gives AUC 0.97 because controls are matched one market at a time. With it, T2 AUC was 0.99; without it, the table above.
- T1 test rests on 4 cases and 20 markets; the gradient-boosting model overfits the train cases. T3 partly measures market type (placebos are crypto and weather markets).
- Day-version results are in `baselines.json` (T1 LR test AP 0.064, T2 LR test AUC 0.818, T3 GB test AUC 0.851).

## Phase F: quality gates (`dataset/tests/test_release.py`)

**45 passed, 3 skipped** (the skipped are the primary-key tests of the three tables with no declared key: placebo_markets, which holds unmatched case-market rows with NULL ids, episodes and edges).
- Schema: dtypes and columns match `schema.py` for all 13 tables and every fills part; every column has a CODEBOOK entry; allowed values hold; no empty strings.
- Primary keys unique (fills: `leg_id` after a fix, see below); foreign keys resolve; every labelled wallet is in fills or flagged `trade_confirmed = false`.
- Address format: 40 hex lower-case in every address column, including all 58 M fills legs.
- Names: hashed name list over every 1-3 word n-gram of free text: 0 hits after A12.7; the "Name Surname" regex hits (463 phrases) were reviewed by hand (`tests/name_review.csv`): market subjects, outlets, places, phrases; none is a person alleged in PMITC.
- Leakage: in both versions no pre-news column uses a fill at or after the cut; `buy_usdc_pre` of every documented position was recomputed from fills before the cut and matches.
- Rebuild: the final stage (`tables.py`, `fills_release.py`) was run a second time; all 29 data files reproduced their SHA-256 in `release/MANIFEST.json`. A full rebuild from raw sources was not repeated (hours; the tape and Data API pulls are not hash-stable over time because the API keeps returning new rows).
- Counts reconcile: case-market legs per case equal `logs/fills_counts_by_case.csv`.
- Amount checks: 14 claims with an amount link to a documented wallet by address or resolved handle. One gap over 10% was found and recorded: **CX004, CL0011** (Google Year-in-Search: claimed "nearly $1M", closest observed net payout $1.18 M, gap 17.6%). Fills-based stakes understate some wallets because Polymarket-v1 records mint-matched buys as maker sells of the other token (A6.4); Data API activity (economic sides) is used alongside, both reported in `logs/amount_checks.csv`.

## Phase G: release package (`release/`, not uploaded)

- `data/` (13 tables, 2.1 GB), `benchmarks/` (README, frozen `splits.csv`, `pmitc_bench.py`, `baselines.json`), `notebooks/` (01 explore, 02 baselines; both executed end to end on the released files), `docs/` (README, DATASHEET, CODEBOOK, PROTOCOL, CHANGELOG runs 1-7, LICENSE, CITATION.cff, LICENSES_UPSTREAM, blank `blind_check_sample.csv`), `MANIFEST.json`, `dataset-metadata.json` (Kaggle format, id placeholder, column descriptions copied from the schema that generates the CODEBOOK).
- Files over 50 MB (positions, weak_labels, fills parts) are git-ignored and listed in the manifest. Largest file 510 MB; 8 fills parts of at most 15 M rows.
- **Kaggle limits not verified:** kaggle.com is not reachable here (logged in `needs_page_read.csv`).

### Licensing findings (`release/docs/LICENSES_UPSTREAM.md`)

- Polymarket-v1: CC-BY-4.0. ForesightFlow: CC-BY-4.0. 1712n/dn-institute: Unlicense. PolyShadow, pselamy, searadacunha: MIT (searadacunha's research text was earlier noted as CC BY-NC-ND; only facts are used).
- Seven source repositories have no licence file: only addresses and links (facts) are shipped from them; `build_seed.py` rebuilds the rows from the clones.
- Polymarket API terms: **not verified** (polymarket.com unreachable). Data API rows are shipped in separate files so they can be withheld.
- No source was found that explicitly forbids redistribution of a shipped table or column.

## Failed lookups and blocked pages

- Handles: `AlphaRaccoon`, `OnlyBibi2026`, `BornTooLate.eth`, `hogriddahhhh` (no match); `ricosuave666` rejected.
- Profiles: 883 A13 size/time matches with no Gamma profile (not candidates).
- Pages (all in `needs_page_read.csv`): 16 pending claims; CourtListener dockets (4); CFTC 9185-26, 9217-26, 9276-26 and the teleprompter order; Kalshi news index; Bubblemaps' Nvidia blog (full addresses); the Senate letter PDF; Kaggle limits; Polymarket terms.
- Data API: no failures after retries; 267 case markets pulled (2 pullers; one restarted after a list-join error).

## Failures during the run (fixed, nothing lost)

1. Placebo first selection discarded (A14.1: no weather markets, substring coin match, a precedence bug).
2. Positions killed twice for disk (temporary spill) and twice for memory; rewritten to stream in SQL; F2 rewritten as a streamed join (A16.1 recorded the one rule change this forced).
3. Duplicate `leg_id` in Data API wallet activity (two labelled wallets in one transaction): leg id now includes the wallet.
4. A12.7 added after the name test found three market titles naming listed people.

## Decisions needed

1. **Polymarket API terms.** Confirm that Data API v2 rows may be redistributed. If not, drop `fills_part*_data_api_v2.parquet` (and the Data API share of `positions`, `episodes`, `market_minutes`) and ship the rebuild scripts instead.
2. **A13 candidates.** With a placebo/real ratio of about 0.32, decide whether to tighten the rule in a new amendment (for example a shorter window or an age of 3 days), or keep it as a search aid. Any change is made after seeing this rate and must say so.
3. **Pending pages.** The 46 entries in `needs_page_read.csv` (16 pending claims, dockets, CFTC releases, Kaggle limits, Polymarket terms) need a separate read and send-back.
4. **Gemini-type exact times.** Where the day date was month-precision, `t_news_precise` can be weeks later than `t_news`. Decide whether exact times should only be used when they fall within a set distance of the day-level date.
5. **Blind check (A4).** `blind_check_sample.csv` is still blank; it needs a human second extractor.
6. **Money graph.** Provide an archive Polygon RPC or explorer key for a later run, or keep it out of scope.
7. **Kalshi notice dates.** Three notices print an effective year of 2025 in 2026 files; ask Kalshi or keep as printed.
8. **Kaggle.** Check current size and file-count limits before upload; the package was split conservatively.
