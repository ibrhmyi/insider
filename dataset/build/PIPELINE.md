# Build pipeline (run on a machine with network access)

The seed tables in `data/` were built from public sources by `build_seed.py`. Everything below needs Polymarket, Polygon and Hugging Face access. Do the steps in order. Write each output under `dataset/out/`. Keep anything over 50 MB out of git and list it in `dataset/out/MANIFEST.json` with a SHA-256.

Rules for every step:
- Never invent an address. A row gets an address only from a source, an API lookup, or a chain transfer. Log every failed lookup.
- New wallets found by graph expansion get `polarity=candidate`, never `suspected`.
- Do not change anything under `rules/frozen_*.md` or `web/`.

## 1. Resolve handles and conflicts
- For each row in `handles_to_resolve.csv`: call Gamma `public-search?q=<handle>&search_profiles=true`. Accept only an exact, unique name match. Write `resolved_address` and `resolved_via`.
- AlphaRaccoon: the seed has `0xee50a31c…` (from a repo list), but the press cites the prefix `0xafEe`. Check both proxies' trades on the Year-in-Search markets and the Gemini 3 market. Keep the address whose fills match the reported trades (a d4vd Yes buy of about $10.6k), and record the evidence.
- Maduro: check whether `0x31a56e9e…` is the account the CFTC complaint describes (436k Yes shares at about $0.074 average). Record match or no match. Do not write a person's name anywhere.

## 2. Markets and news times → `markets.parquet`
- For every case in `cases.csv`, find its condition IDs: use FFIC (`ffic-v1.jsonl`) where it has them, otherwise Gamma search by question text and date.
- Add the full deadline ladder: every market in the same Gamma series or event.
- Columns: condition_id, case_id, question, slug, event_id, series_id, deadline_utc, created_utc, resolved_utc, outcome, volume, ladder_rank.
- T_news: take it from ForesightFlow `polymarket-tnews-tevent-recovery` when the market is there (keep its tier). Otherwise use the earliest timestamped public report in the case sources, and mark it `manual`.

## 3. Fills → `fills/`
- Up to 2026-04-28: Polymarket-v1 on Hugging Face (`TimeSeventeen/Polymarket-v1`), read with DuckDB over `hf://` and filtered at the source. Keep its true aggressor side.
- After that: Data API `/trades` (cursor paging) for the same filters.
- Pull (a) every fill, all-time, of every address in `wallet_labels.csv` plus the resolved handles; and (b) every fill by anyone in every market in `markets.parquet`.
- Columns: tx_hash, log_index, ts_utc, condition_id, outcome_index, side, price, size, usdc, maker, taker, aggressor, wallet_role.

## 4. Money graph → append to `wallet_edges.csv` as `edges_expanded.csv`
- For each labelled address, get Polygon USDC and USDC.e Transfer logs in and out (Etherscan V2 API or Polygon RPC `eth_getLogs` on the two token contracts, filtered by address topic).
- Tag each counterparty as exchange, bridge, Relay, privacy pool, or Polymarket contract when it is a known address. Tag any address with more than 500 distinct counterparties as `hub`, and do not expand through it.
- One hop out: find other Polymarket proxies that share a non-hub funder or cash-out address with a labelled wallet. Add them to `wallet_labels_expanded.csv` with `label_tier=L4_graph_expanded`, `polarity=candidate`, and the edge that links them.

## 5. Platform-wide rule labels → `weak_labels.parquet`
Run on all of Polymarket-v1 (and the Data API after it), one row per wallet:
- **ACDC:** longshot = a buy of $2,500 or more at 35¢ or less on a resolved market. Classify wallets the way the ACDC report does (Orca, Whale, Bot, Small Fish), using its definitions. Check the reconstruction before trusting it: on data up to 2026-05-05 it should give about 78,496 longshot bets, 12,355 wallets and 556 Orcas. Report the gap.
- **Inca Digital:** 10 or fewer markets and $30,000 or more of realised PnL.
- **Our gates:** Gate 1 alert episodes; Gate 2 Signals A and B, using the frozen rules exactly as written.
- Columns: address, n_markets, n_longshots, longshot_win_rate, realised_pnl, acdc_class, inca_flag, gate1_n, gate2a_n, gate2b_n.

## 6. Matched controls → `controls.parquet`
For each labelled episode (wallet, market, side, first buy time), sample up to 10 controls from the same market:
- same side; first buy within 24 hours of the labelled first buy; first-buy price within ±0.05; size within 0.5× to 2×;
- not in any label table, expanded table, or ACDC Orca list.
Also add up to 10 large buyers of the other side in the same window. Use a fixed seed (192). Record which conditions had to be relaxed.

## 7. Episode features → `episodes.parquet`
One row per (wallet, condition_id, side), for labelled, expanded and control wallets. Compute with data available before T_news only, unless the column name ends in `_post`:
- wallet: account age at first fill, prior markets, prior win rate, share of lifetime volume in this case
- entry: first price, VWAP, max price paid, number of fills, median fill size, fill-size dispersion, taker share, hour of day
- price insensitivity: bought again at ≥1.5× the first price (Signal A); slope of size against price
- holding: share sold before resolution; time from last buy to T_news
- deadline choice: ladder rank bought, share on the shortest sufficient deadline (Signal B)
- timing: hours from first buy to T_news; hours from funding to first trade
- funding: source type (exchange, bridge, Relay, privacy), funder shared with another labelled wallet
- followers: buys in the same direction by other wallets within 60 minutes after each fill
- outcome (`_post`): won, PnL, redemption delay

## 8. Package
- Write `DATASHEET.md` (Gebru et al. 2021 headings) and `MANIFEST.json` with row counts and SHA-256 for every file.
- Prepare a Hugging Face dataset folder (parquet plus the CSVs and README). **Do not upload.** Stop and report the counts, the ACDC reconstruction gap, and every failed lookup.
