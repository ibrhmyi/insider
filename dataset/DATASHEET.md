# Datasheet: Prediction-Market Informed-Trading Casebook (PMITC), v0.3

Headings follow Gebru et al. (2021), *Datasheets for Datasets*. Collection rules: [PROTOCOL.md](PROTOCOL.md) v1.0 with amendments A1 to A8. Column meanings: [CODEBOOK.md](CODEBOOK.md). Run history: `logs/run2_report.md`, `logs/run3_report.md`.

## Motivation

- **Purpose.** A citable, source-traced register of publicly documented suspected informed trading on prediction markets, joined to the trades. Each documented case is linked to its markets, the fills in those markets, the claimed wallets' fills, matched control wallets, and pre-news episode features. Researchers can then test detection methods against documented cases without rebuilding the joins.
- **Gap filled.** Public lists of "insider" wallets lack sources, grades, market links and comparison groups.
- **Creator.** Built by I. Yildiz with an AI extractor (Claude); see `extractor` in `claims.csv`. The second-extractor check (A4) has not been done.
- **Funding.** None.

## Composition

- **Instances.**
  - claims: one source statement each;
  - cases: underlying events;
  - wallet labels: an address in a case;
  - markets: Polymarket markets attached to cases, with deadline ladders and t_news;
  - fills: wallet legs of every fill in every case market, plus all fills of labelled wallets;
  - rule labels: ACDC and Inca reconstructions for every Polymarket-v1 wallet;
  - controls and episodes.
- **Counts.** See `out/MANIFEST.json`: 92 claims, 60 cases, 250 labelled addresses, 870 case-market rows (761 markets, 38 cases), 20.6 million case-market legs, 115,886 labelled-wallet legs, 2.65 million wallets with rule labels, 408 suspected episodes with 7,669 controls.
- **Sample, not population.** The collection holds what was publicly noticed. It over-represents large, fresh-wallet, long-shot wins on viral and geopolitical markets (PROTOCOL 8). Do not estimate prevalence from it.
- **Labels.**
  - Evidence grades E1 to E6 per claim. A case takes its strongest claim.
  - Wallet polarity: suspected, ambiguous, negative_control, manipulation, context, candidate.
  - Rule labels (E6) are stored separately and never merged with claims.
  - A label is an allegation, not a finding. Only E1 is adjudicated.
- **Missing information.**
  - The money graph (A6.8, A8) could not be built: no archive-capable Polygon RPC was reachable. Funding features are therefore empty, and no `L4_graph_expanded` candidates exist.
  - 8 run-2 claims are `verified=pending`.
  - 22 cases have no market (see `logs/markets_not_found.csv`).
- **Confidentiality.** No personal names in data tables. Official records are referenced by URL. Public market questions can name public figures; one case where the market names the person a claim accuses is held back (see run 3 report, "Decisions needed").
- **Errors and redundancy.**
  - Data API legs have no maker/taker role.
  - HF shares are derived as usdc / price.
  - The same market can belong to more than one case (for example the US-strikes-Iran ladder), so case-level sums can double count across cases.

## Collection process

- **Claims.** Web, press, official, research and code searches; every query is in `logs/search_log.csv` (A1, A5 for X).
- **Markets.** Gamma public search, FFIC prefixes, the markets the claimed wallets traded, and a slug catalog built from Polymarket-v1 (A6.5).
- **Fills.** Polymarket-v1 on Hugging Face (`TimeSeventeen/Polymarket-v1` at commit `6d1bcd5279cbbd8e833feaeba9a56a0aee139144`, cleaned layers `daily_aligned/` and `daily_aligned_multi/`, 746,110,412 fills from 2022-11-21 to 2026-04-28 11:00:40 UTC; file list in `logs/hf_files_used.tsv`). After that: the Polymarket Data API v2 (`/v2/activity`, `/v2/trades?condition=..&taker_only=false`). Raw API responses are in `logs/gamma_raw/`.
- **Timeframe.** Claims dated 2023 to 2026-11. Collected on 2026-11-26 in runs 1 to 3.
- **Ethics.** No attempt to identify people behind wallets (PROTOCOL 9).

## Preprocessing, cleaning, labelling

- Partial dates are parsed by their earliest possible day (A6.3).
- t_news per A6.6 and A7: day-precision event dates first; ForesightFlow tier 1 or 3 when available (none matched).
- Side convention: the taker is the aggressor (A6.4).
- **ACDC reconstruction** (A6.9) misses its 5% validation bar:

  | Count | Gap vs published |
  |---|---|
  | Longshot bets | +15.7% |
  | Longshot wallets | +5.6% |
  | Orcas | +188% |
  | Military Orcas | +93% |

  It is published but must not be used as a label.
- **Inca rule** flags 9,285 wallets, against 39 in the published Inca list.
- **Raw data.** Raw HF day files are not stored; they are re-downloadable at the pinned commit. Raw API responses are stored.
- **Code.** Every table is rebuilt by the scripts in `build/` (order in README).

## Uses

- **Intended:**
  - benchmark detection methods against documented cases, with the matched controls;
  - study pre-news trading around documented events;
  - audit public allegations against fills.
- **Not intended:**
  - identifying people;
  - estimating prevalence;
  - training a detector only on these cases (selection bias);
  - treating E2 to E6 as findings.
- **Freeze rule.** Report results on cases added after your method's freeze date separately (README rule 4).

## Distribution

- Tables written for PMITC: CC-BY-4.0.
- Polymarket-v1-derived tables inherit its CC-BY-4.0. Third-party sources keep their own licenses (README).
- Files over 50 MB are not in git; they are listed with SHA-256 in `out/MANIFEST.json` and rebuild from the scripts.
- Not uploaded anywhere yet.

## Maintenance

- Maintained in `ibrhmyi/insider` (`dataset/`).
- Corrections and removals: open an issue with the row ID.
- New runs append claims (stable IDs), log every query, and add protocol amendments before seeing the data they govern.
- Contradictions with recorded claims go to `data/contradictions.csv`; claims are never edited.
