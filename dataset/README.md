# Prediction-Market Informed-Trading Casebook (PMITC)

An open, source-traced register of every publicly documented case of suspected informed trading on prediction markets: court and regulator actions, platform sanctions, analyst investigations, press reports, and rule-based screens. Each claim keeps its own source and evidence grade, so a researcher can choose how strict to be.

**Version:** 0.3 (2026-11-26, run 3: trades, markets, controls). Collected under [PROTOCOL.md](PROTOCOL.md) v1.0 and amendments A1 to A8. Every column is described in [CODEBOOK.md](CODEBOOK.md); the datasheet is [DATASHEET.md](DATASHEET.md).

## Contents

| File | Rows | One row is |
|---|---|---|
| `data/claims.csv` | 107 | One claim by one source: subject, paraphrase, evidence grade, amount, dates, URL |
| `data/cases.csv` | 65 | One underlying event, derived from its claims: strongest grade, number of sources, whether amounts disagree |
| `data/wallet_labels.csv` | 260 | One wallet address in one case, with role, label tier, polarity, source, and whether it traded its case market |
| `data/wallet_edges.csv` | 416 | One money link between addresses (funding, Relay handoff, Safe owner, cash-out, transfer) |
| `data/handles_to_resolve.csv` | 19 | A public username, its Gamma lookup result (`resolved_address`, `status`, `notes`) |
| `data/markets.csv` | 982 | One Polymarket market attached to one case (873 markets, 40 cases), with its Gamma-event deadline ladder, outcome and t_news |
| `data/event_times.csv` | 13 | A timestamped public moment for a case (official post, first report, scheduled release), with source; not yet used for t_news |
| `data/contradictions.csv` | 3 | A place where the trades disagree with a recorded claim (the claim itself is never edited) |
| `out/fills/case_market_legs.parquet` | 22,588,620 | One wallet's leg of one fill in a case market (not in git; size in `out/MANIFEST.json`) |
| `out/fills/label_wallet_legs.parquet` | 116,787 | One leg of a fill by a labelled wallet, all time |
| `out/weak_labels.parquet` | 2,651,672 | One Polymarket-v1 wallet with ACDC and Inca rule labels (E6; not in git) |
| `out/acdc_longshots.parquet` | 90,843 | One ACDC longshot bet (reconstruction) |
| `out/controls.parquet` | 7,898 | One matched control for a suspected episode |
| `out/episodes.parquet` | 8,323 | One (wallet, market, token) episode with pre-news features: 425 suspected, the rest controls |
| `out/market_minutes.parquet` | 216,552 | One case market per minute, t_news - 48 h to + 24 h (A9.3) |
| `out/hf_market_catalog.parquet` | 1,538,514 | One Polymarket-v1 market token (not in git) |
| `logs/search_log.csv` | 115 | Every search query run, its source class, and what it produced |
| `logs/repos.csv` | 12 | Every code repository used, with the exact commit |
| `build/*.py` | | Scripts that rebuild every table from the cloned sources and public APIs |

### Build order

`build_seed.py <repos>` → `claims.py` → `build_cases.py` → `pull_activity.py` / `pull_profiles.py` → `hf_catalog.py <hf>` → `build_markets.py <ForesightFlow clone>` → `wallet_checks.py` → `hf_pass.py <hf> <work>` → `pull_market_trades.py` → `assemble_fills.py` → `weak_labels.py` → `money_graph.py` (needs an archive Polygon RPC in `POLYGON_RPC`) → `controls_episodes.py` → `market_minutes.py` → `package.py`.

### Coverage (v0.3)

- **Platforms:** Polymarket (most cases), Kalshi (official enforcement), both (pre-taped TV).
- **Families:** informed trading; manipulation by the outcome maker or odds support; oracle and resolution attacks; public-data leaks; pre-taped show leaks; negative controls; rule-based screens.
- **Topics:** military and geopolitical (Venezuela, the June 2025 and February 2026 Iran strikes, Khamenei, ceasefires), elections (US 2024 VP picks, 2026 midterms, Israel 2026), executive decisions (pardons, tariffs, a Trump–Zelenskyy meeting), awards (Nobel, Ballon d'Or, papal conclave), technology (Google, Gemini, OpenAI), corporate (earnings, MicroStrategy, DraftKings, Spotify), crypto (Arbitrum airdrop, the ZachXBT exposé), culture (Taylor Swift, Super Bowl halftime, Survivor, MrBeast), and speech mention markets.
- **Case grades:** E1 = 4, E2 = 3, E3 = 10, E4 = 13, E5 = 27, E6 = 8 (after run 5; see `logs/run5_report.md`).
- **Investigation outcome (A9.2):** sanctioned 4, charged 3, cleared (official) 1, cleared (analyst) 2, disputed 2, under investigation 10, unresolved 43.
- **Trades:** Polymarket-v1 (746 million fills, to 2026-04-28) and the Data API v2 after that.

## Evidence grades (per claim; a case takes its strongest)

| Grade | Meaning |
|---|---|
| E1 | Adjudicated or final sanction (conviction, settlement order, final platform discipline) |
| E2 | Charged (indictment or complaint) |
| E3 | Official inquiry or referral reported |
| E4 | Analyst with transaction-level evidence (funding paths, transfers, fills) |
| E5 | Pattern claim (timing, account age, win rate) without transaction-level links |
| E6 | Rule-based flag from a published screen |

Wallet label tiers (`L2` to `L4`, `A`, `NC`, `M`) are explained in `build/build_seed.py`.

## Rules for use

1. **A label is an allegation, not a finding.** Only E1 is a final outcome, and E1 is mostly platform discipline on Kalshi.
2. **One case is one event.** A cohort of 38 wallets on one market is one observation.
3. **The collection is biased toward what was noticed.** Almost every case is a fresh wallet making a big, cheap, well-timed bet on a viral market. Do not estimate prevalence from it, and do not train a detector only on it.
4. **Freeze before you test.** These cases were public before you built your method. Report results on cases added after your freeze date separately.
5. **No identity work.** The tables contain no personal names. Official records are referenced by URL. Do not use the data to identify people behind wallets.

## Known gaps

- X was not searched directly (protocol amendment A1). Run 2 swept X through search engines (A5), but the engine returned pages quoting the posts, not the posts: the 8 run-2 claims carry the quoting page as `url`, were taken from search-result text, and need their post URLs and page text checked (see `notes`).
- The 20% blind re-extraction is not done yet (A4); the sample is drawn in `logs/blind_check_sample.csv` for a second extractor.
- The money graph (A6.8, A8) is not built: no archive-capable Polygon RPC was reachable, so funding features are empty and there are no graph-expanded candidates.
- 22 cases have no market attached (`logs/markets_not_found.csv`): aggregates, Kalshi cases, and cases whose claims name no market.
- t_news is day-precision at best. Where trades happened on the event day before the news (e.g. Nobel 2025), they count as post-news; see run 3 "Decisions needed".
- The ACDC reconstruction misses its 5% bar (Orcas +188%) and is not used as a label.
- 13 of 123 suspected wallets have no fill in their case's markets (flagged in `wallet_labels.csv`).
- Several large lists exist but are private: the ~100 Polymarket referrals, the ~34,000 Polysights flags, the NYT's 80+ accounts, ACDC's 556 Orcas, Inca Digital's 39. Rule-based lists can be rebuilt from trades (see `build/PIPELINE.md`).
- AlphaRaccoon conflict settled in run 2: `0xafEe` is the current display name of proxy `0xee50…`, whose d4vd Yes buys ($10,650.04) match the press figure.

## How to cite

Yildiz, I. (2026). *Prediction-Market Informed-Trading Casebook (PMITC)*, version 0.3. Collected under protocol v1.0. https://github.com/ibrhmyi/insider (dataset folder).

## License

Tables written for this dataset: CC-BY-4.0. Third-party sources keep their own licenses: searadacunha's research text is CC BY-NC-ND 4.0, and ForesightFlow is CC-BY-4.0. Only public blockchain facts and short paraphrases are copied, with links. To correct or remove a row, open an issue with the row ID and the reason.
