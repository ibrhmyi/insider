# Run 3 report (2026-11-26)

Run 3 turned the casebook into a trade-level dataset. It attached markets to cases, pulled every fill in those markets and every fill of labelled wallets, checked the claimed wallets against their trades, rebuilt the ACDC and Inca rule labels from the whole Polymarket-v1 tape, and drew matched controls with pre-news episode features. Rules: PROTOCOL A6 to A8, each written and committed before the data it governs. Branch `claude/pmitc-v1`; one commit per phase.

## Amendments written this run

| Amendment | Written | What |
|---|---|---|
| A6 | before any run-3 data | `verified` and `run` columns; partial dates; rules for markets, t_news, fills, wallet checks, money graph, rule labels, controls, features |
| A7 | after `markets.csv`, before anything that uses t_news | t_news anchors on day-precision event dates; claim dates can only move it earlier |
| A8 | before any Polygon transfer data | Money-graph window, funder/cash-out, hub test, one-hop rule |

**A7 reason.** A6.6 put t_news on the first day of a month-only claim date, two days before the Maduro operation. A first draft of A7 was tried and rejected: where the event date is coarse, it moved t_news years after the event (ftx-sbf, romania-2024 and biden-pardons to 2026; kpmg-earnings to 2026-11). The adopted A7 changed t_news for 6 cases, all to the event day:

| Case | Before (A6.6) | After (A7) |
|---|---|---|
| maduro-2026-01 | 2026-01-01 (month) | 2026-01-03 (day) |
| us-iran-ceasefire-2026-04-07 | 2026-04-01 (month) | 2026-04-07 (day) |
| us-iran-strike-2025-06 | 2025-06-01 (month) | 2025-06-21 (day) |
| super-bowl-halftime-2025 | 2025-02-01 (month) | 2025-02-09 (day) |
| walz-vp-2024 | 2024-08-01 (month) | 2024-08-06 (day) |
| arbitrum-airdrop-2023 | 2023-03-01 (month) | 2023-03-16 (day) |

## Network used

- Hugging Face (Polymarket-v1), Polymarket Gamma and Data API v2, and docs.polymarket.com, added to the environment with your approval.
- Polygon RPCs:
  - publicnode serves recent blocks only;
  - dRPC's free plan allows 100-block ranges;
  - 1RPC's free plan allows 50-block ranges and was already over its usage limit.
- The Data API v1 is retired (HTTP 410). v2 floors `user` queries to three years back unless `start=1`; no stored history was cut by this (checked), and the puller now always sends `start=1`.

## Phase 0: housekeeping

- `claims.csv` gains `run` (84 rows run 1, 8 rows run 2) and `verified` (84 `true`, 8 `pending`: CL0085 to CL0092).
- `build_cases.py` parses partial dates (helpers in `build/dates.py`). `cases.csv` gains `*_earliest` and `*_precision`.
  - Formats found besides YYYY, YYYY-MM, YYYY-MM-DD and A/B: `YYYY-YYYY`, `YYYY-YYYY-MM-DD` (read as ranges) and `YYYY-Qn` (quarter).
- `logs/needs_page_read.csv` (14 entries) and `data/contradictions.csv` created.

## Phase 1: wallet checks (`logs/handle_checks.csv`)

| Check | Result |
|---|---|
| Elonfax89678 → profile `ElonfaX89678` 0x1fa1be3e… | **Accepted (A6.7).** Bought Yes in "US x Iran ceasefire by April 7?": 49 fills, $10,092.93, 2026-03-26 to 04-07 19:40 UTC, before the event day ended |
| Bama124 → profile `bama124` 0xe5c80262… | **Accepted.** Bought Walz Yes: 540 fills, $206,970.59, 2024-07-29 to 08-06 00:11 UTC. Profile created 2024-07-22 (claim: "joined July 2024") |
| romanticpaul on "Taylor Swift and Travis Kelce engaged in 2025?" | **Traded, consistent with the claim.** Yes $2,068.10 (35 fills), No hedge $58.22, redeemed $5,180.42 (about $3.1k profit); $1,285.59 of the Yes buys in the 24 h before the last Yes fill |
| Maduro: 0x31a56e9e… vs the CFTC complaint | **Match.** 436,759.61 Yes shares in "Maduro out by January 31, 2026?" for $32,538.34 (average 0.0745); profile created 2025-12-26 06:32 UTC. Its pseudonym is "Burdensome-Mix", the handle the press uses (recorded; not a name match under the lookup rule) |

Suspected wallets: 110 of 123 traded a market of their case. **13 flagged, not deleted:**
- 5 Maduro cluster members whose trades fall outside the attached `maduro-out-in-2025` event;
- 8 Feb-28 Iran cluster members;
- 2 of the 13 have no Data API activity at all.

All 13 come from repo cluster lists linked by money flows, not by trades.

## Phase 2: markets (`data/markets.csv`)

- **Attached:** 870 rows, 761 distinct markets, 38 cases. Each row records `found_via` (Gamma search, claimed wallets, FFIC prefix, HF slug), a reason taken from the claims, and its Gamma-event ladder.
- **Not attached:** 22 cases (`logs/markets_not_found.csv`): 7 aggregates, 6 Kalshi cases (no public account or trade data), and 9 whose claims name no specific market or where the market is ambiguous. One is held for a decision (below).
- **Lookups:** no failures after retrying Gamma with `closed=true`.
- **ForesightFlow t_news:** none of the attached markets is in its tier 1 or 3 subsets; 54 rows have a tier-2 proxy, which is stored, not used (A6.6). So t_news is `claim_min` everywhere, at day precision or coarser.

## Phase 3: fills

- **Source:** Polymarket-v1 at commit `6d1bcd52…`, 2,105 day files (16.8 GB; list in `logs/hf_files_used.tsv`), **746,110,412 fills** read in one pass. After 2026-04-28 11:00:40 UTC: Data API v2.
- **Labelled wallets:** 115,886 legs. 107,272 from HF (223 wallets) and 8,614 from the API (60 wallets).
- **Case markets:** 20,622,245 legs. Counts per case are in `logs/fills_counts_by_case.csv`. Largest:

  | Case | Legs |
  |---|---|
  | election-2024 | 9.9 M |
  | bubblemaps-military-cluster | 3.6 M |
  | us-iran-strike-2026-02-28 | 2.4 M |
  | ballon-dor-2026 (API) | 1.05 M |
  | us-iran-ceasefire-2026-03 and -04-07 (same ladder) | 0.97 M |

- **Zero-fill markets:** 127 markets returned no trades from the API. All are unused placeholders with zero Gamma volume, e.g. "Will [Placeholder BE] win the 2026 Ballon d'Or?".
- **Limits:**
  - API legs have no maker/taker role.
  - HF shares are usdc / price.
  - The cleaned HF layers carry no transaction hash.

## Phase 4: money graph: **blocked**

- **What exists:** `build/money_graph.py` is written. Windows for 121 of 123 suspected wallets are computed (`logs/money_graph/windows.json`; 2 have no activity).
- **Why it can't run:** no reachable RPC serves historical `eth_getLogs` at a usable range (see "Network used").
- **Consequences:** no `edges_expanded.csv`, no `wallet_labels_expanded.csv`, no candidates; funding features in `episodes.parquet` are empty.
- **Needed:** an archive Polygon RPC (set `POLYGON_RPC`) or an explorer API key. See "Decisions needed".

## Phase 5: rule labels (`out/weak_labels.parquet`, `logs/acdc_reconstruction.json`)

2,651,672 wallets in Polymarket-v1.

| ACDC count | Published (to 2026-05-05) | Ours (to 2026-04-28) | Gap |
|---|---|---|---|
| Longshot bets | 78,496 | 90,843 | +15.7% |
| Longshot wallets | 12,355 | 13,045 | +5.6% |
| Orcas | 556 | 1,599 | +187.6% |
| Military Orcas | 152 | 294 | +93.4% |

- **ACDC:** the gap exceeds 5%, so under A6.9 the reconstruction is published but **not used as a label**. Our data also end 7 days earlier than ACDC's.
- **Probable causes, not tested:**
  - A6.9 sets no minimum number of longshots for an Orca, so one winning longshot qualifies.
  - Clock hours stand in for ACDC's window.
  - `category_refined` stands in for ACDC's market types.
- **Inca:** 9,285 wallets meet "≤10 markets and ≥$30,000 realised PnL", against Inca's published 39. The published list must use a narrower scope or extra conditions.
- **Not computed:** splits, merges and redemptions are ignored in PnL (A6.9). Gate 1/2 columns from PIPELINE step 5 were not asked for in this run.

## Phases 6 and 7: controls and episodes (`out/controls.parquet`, `out/episodes.parquet`, `logs/controls_summary.json`)

- **Episodes:** 408 suspected episodes (case, wallet, market, token with a pre-news buy) in 15 cases:

  | Case | Episodes |
  |---|---|
  | us-iran-strike-2026-02-28 | 311 |
  | google-yis-2025 | 19 |
  | us-iran-ceasefire-2026-04-07 | 18 |
  | bubblemaps-military-cluster | 15 |
  | walz-vp-2024 | 12 |
  | maduro-2026-01 | 8 |
  | biden-pardons | 6 |
  | zachxbt-axiom-2026-02 | 6 |
  | israel-rising-lion-2025-06 | 3 |
  | kpmg-earnings-2025-26 | 2 |
  | spotify-wrapped-2025 | 2 |
  | taylor-swift-engagement | 2 |
  | nobel-peace-2025 | 2 |
  | trump-pardon-cz-2025 | 1 |
  | draftkings-pm-launch | 1 |

- **Controls:** 7,669 (seed 192). Same-side controls exist for 392 of 408 episodes; 16 episodes have none. Relaxation used: base 299, window 72 h 16, price ±0.10 9, size 0.25×–4× 68. Excluded from control pools: 10,855 addresses (labelled, or flagged Orca/Inca).
- **Episode rows:** 8,077 (408 suspected, 3,637 same-side controls, 4,032 large other-side buyers).
- **Win rates:** won_post is 84.3% for suspected episodes, 84.1% for same-side controls and 15.4% for other-side buyers. Matched same-side buyers won as often as the suspected wallets.

## Phase 8: package

- `DATASHEET.md` (Gebru et al. headings) and `CODEBOOK.md`; `build/package.py` fails if any column lacks a description.
- `out/MANIFEST.json`: 20 tables with row counts and SHA-256. Three files over 50 MB are out of git: `case_market_legs`, `hf_market_catalog`, `weak_labels`.
- `logs/blind_check_sample.csv`: 18 claims (20% of 92, seed 192), claim_id and url only, left blank for a second extractor (A4).
- README updated: counts, build order, known gaps.

## Counts by grade

- Claims by grade are unchanged; run 3 added no claims.
- Cases: E1 = 4, E2 = 3, E3 = 8, E4 = 13, E5 = 24, E6 = 8.
- Wallet labels: 250 (2 new suspected wallets from the accepted handles).

## Failed lookups

**Handles**, all logged in `data/handles_to_resolve.csv`:

| Handle | Result |
|---|---|
| ricosuave666 | Exact match rejected: zero activity; the trader is the seed's 0x0afc7ce5… |
| rundeep | Only `Rundeep` (case differs) = 0x0afc7ce5…, already in the seed |
| AlphaRaccoon | No exact match (renamed); the address was settled from fills in run 2 |
| Burdensome-Mix | No name match; it is the pseudonym of 0x31a56e9e… |
| OnlyBibi2026 | No profiles |

**Other:**
- No Gamma profile for 12 addresses (mostly without activity).
- 2 suspected wallets (0x8c33013f…, 0x82be522b…) have no Data API activity even with full history.
- All Polygon archive log requests failed (phase 4).

## needs_page_read entries (`logs/needs_page_read.csv`)

- **CL0085 to CL0092:** read the quoting page and recover the X post URL. Also: CL0089, confirm the page reports BlueHorseshoe86; CL0091, get the exact post date.
- **Leads:**
  - Polymarket-run account's 25 insider-signal posts (Barron's, needs date);
  - ZachXBT $70k deposit;
  - ceasefire handles Fernandoinfante and NOTHINGEVERFRICKINHAPPENS;
  - Lookonchain "clear case" Maduro post;
  - the Andrey_10gwei post behind CL0006.

## Contradictions with earlier claims (`data/contradictions.csv`)

- **CX001, CL0040 (walz-vp-2024):** the claim says $617,380 profit. The bama124 proxy's net over all `democratic-vp-nominee` markets is **$592,848.09** (−4.0%): sells $643,284 + redemptions $1,156,844 − buys $1,207,280. The claim may count another period or unrealised value.

**Confirmed, not contradicted:**
- AlphaRaccoon d4vd buy ($10,650.04 vs CL0011's $10,647);
- the Maduro complaint figures;
- romanticpaul's profit and hedge.

## Decisions needed

1. **tweet-count-self-2026-03.** The markets are titled with the name of the person the claim says controls the accounts, so attaching them would link a named person to wallets (PROTOCOL 9). No market is attached and no fills are pulled. Decide whether case markets may carry the subject's name when the subject is the alleged trader.
2. **Sub-day t_news.** With day-start t_news, trades made on the event day before the news count as post-news. All 8 Nobel 2025 wallets bought between 00:44 and 03:29 UTC on 2025-10-10, before the announcement, so only 2 Nobel episodes exist. world-cup-2026-06 has a month-only date, so t_news is 2026-06-01 and it has 0 episodes. An hour-precision source (announcement time with URL) would need a new amendment.
3. **Phase 4 access.** Provide an archive Polygon RPC or explorer key, or accept the money graph as out of scope for v0.3.
4. **ACDC Orca definition.** Whether to add a minimum longshot count, or another ACDC detail, as a new amendment and rerun. Any such change is made after seeing this gap and must be reported as such.
5. **Inca scope.** The published 39 cannot be reproduced from the published rule alone; decide whether `inca_flag` stays as a broad screen.
6. **Flagged cluster wallets.** 13 suspected wallets never traded their case's markets. Keep them as suspected (the source's money-flow claim) or downgrade them in a later run.
7. **Burdensome-Mix.** It is the pseudonym, not the name, of 0x31a56e9e…. The lookup rule covers names only; decide whether pseudonym matches with confirming fills may resolve handles.
