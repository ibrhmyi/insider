# Datasheet: Prediction-Market Informed-Trading Casebook (PMITC), v1.2.1

Headings follow Gebru et al. (2021), *Datasheets for Datasets*. Collection rules: `PROTOCOL.md` v1.0 with amendments A1 to A24. Columns: `CODEBOOK.md`. Run history: `dataset/logs/run2_report.md` to `run7_report.md` in the repository.

## Motivation
- **Purpose.** A citable, source-traced register of publicly documented suspected informed trading on prediction markets, joined to the trades, with honest negatives (matched controls, all other buyers, placebo markets) for analysis and machine learning.
- **Gap filled.** Public "insider wallet" lists lack sources, evidence grades, market links, exact news times and comparison groups.
- **Creator.** I. Yildiz, with an AI extractor (Claude); see `extractor` in `claims`. The second-extractor check (A4) is pending.
- **Funding.** None.

## Composition
- **Instances:** claims, cases, wallet labels, case markets, placebo markets, fills (wallet legs), all-buyer positions, episodes, controls, rule labels, minute paths, contradictions, money links. Counts are in `README.md` and `MANIFEST.json`.
- **Label sets (A20):** `label_strict` (linked to an E1-E3 claim or named in an E4 claim), `label_standard` (case grade E1-E4, includes cluster members), `label_broad` (E1-E5). Counts in the dataset card.
- **Hard negatives (A21) and twin markets (A22):** look-alike negatives and same-category comparison markets that appear in no claim.
- **Labelled positives:** 119 wallets that a source flags as suspected, whose own fills confirm they traded the case's markets, in informed-trading cases (`is_documented`, A19), in 18 cases. 74 of them come from two cases (52 Feb-28 Iran strike, 22 KPMG), and 87 are cluster members linked by money flows, not flagged one by one. 13 more suspected wallets are not trade-confirmed and one is in a public-data-leak case (kept, not positive). The A13 coordinated-buyer rule is a rule output in `positions` and `weak_labels` (`coordinated_rule_fired`): about 1/3 expected by chance, may include copy-traders, not an allegation.
- **Sample, not population.** The collection holds what was publicly noticed (PROTOCOL 8). Do not estimate prevalence from it.
- **Labels:** evidence grades E1 to E6 per claim (a case takes its strongest); wallet polarity; rule labels (E6) kept separately; benchmark split. A label is an allegation, not a finding.
- **Missing information:** money graph (no archive RPC; A12.2); Kalshi trades and accounts (not public); 24 cases without a market (aggregates, Kalshi, no identifiable market); 16 claims pending page reads.
- **Confidentiality:** no personal names in data fields; titles that name listed people are withheld (A12.6, A12.7); raw profiles of A13 lookups are not published.
- **Errors and redundancy:** Data API legs have no maker/taker role; HF shares are usdc / price; mint-matched trades appear as the recorded leg side (A6.4); a market can belong to more than one case, so case-level sums can double count across cases.

## Collection process
- **Claims:** web, press, official, research and code searches (every query in `search_log.csv`; A1, A5 for X); Kalshi notices from its public notice bucket (run 7).
- **Markets:** Gamma events named by the claims or traded by the claimed wallets, FFIC prefixes, Polymarket-v1 slugs (A6.5); placebo markets by rule A14.
- **Fills:** Polymarket-v1 (`TimeSeventeen/Polymarket-v1` @ 6d1bcd52, cleaned layers, 746,110,412 fills to 2026-04-28 11:00:40 UTC), then the Polymarket Data API v2.
- **News times:** day-level (A6.6, A7) and exact (A10) from `event_times.csv`, compiled from sources before any episode under them was computed.
- **Timeframe:** claims dated 2023 to 2026-11; collected 2026-11-26 in runs 1 to 7.

## Preprocessing, cleaning, labelling
- Partial dates by earliest possible day (A6.3); taker = aggressor (A6.4); handle resolution by exact name or pseudonym plus confirming fills (A6.7, A11).
- `trade_confirmed` from fills (A12.5); coordinated buyers (A13) with placebo-window false-positive rate; placebo matching (A14, A14.1); Gate 1/2 (A16, A16.1).
- ACDC reconstruction misses its 5% bar (Orcas +188%) and is not a label; the Inca rule flags 9,285 wallets against Inca's 39.
- Every table is rebuilt by the scripts in `dataset/build/` and `dataset/build/v1/` (order in the repository README).

## Uses
- **Intended:** benchmark detection methods (T1 to T3); study pre-news trading around documented events; audit public allegations against fills.
- **Not intended (see also `DATA_PROTECTION.md`):** identifying people; estimating prevalence; training a detector only on these cases; treating E2 to E6 as findings.
- **Freeze rule:** report results on cases added after your method's freeze date separately.

## Distribution
- CC-BY-4.0 for PMITC tables; third-party licences in `LICENSES_UPSTREAM.md`. Data API v2 rows are in separate files pending a terms check.
- Prepared for Kaggle (`dataset-metadata.json`); not uploaded.

## Maintenance
- Maintained in `ibrhmyi/insider` (`dataset/`). Corrections and removals: open an issue with the row id.
- New runs append claims (stable ids), log every query, and add protocol amendments before seeing the data they govern; contradictions go to `contradictions`, claims are never edited.
