# Detecting Potential Insider Trading on Polymarket: pilot (CP191 Nano Capstone)

**Status: preliminary pilot, not a validated model.** 3 insider-possible markets, 3 controls (2 usable).
Any flagged pattern is **"unusual activity for review"**. It is never a claim that a wallet is an insider.

## Question
After a large "seed" trade, is follow-on same-direction trading (the "ripple") larger in *insider-possible*
markets (outcome known early to a small group) than in matched *insider-impossible* controls (outcome set by a
public price at a fixed time), once windows that cross public-news times are excluded?

## Reproduce
```bash
pip install -r requirements.txt
./run_all.sh          # ~10 min; needs gamma-api.polymarket.com and data-api.polymarket.com
```
Raw API pages are cached in `data/raw/trades/<market>/page_*.json`, so re-runs reuse them.

## Pipeline (`src/`)
| Step | Script | Output |
|---|---|---|
| Control candidates | `00_match_controls.py`, `00b_screen_controls.py` | `data/raw/control_match_candidates.json`, `data/raw/control_screen_*.json` |
| Market selection (task 2) | `01_select_markets.py` | `data/markets.csv`, `data/news_events.csv`, `data/control_match_table.md` |
| Trade extraction + audit (task 3) | `02_extract_trades.py` | `data/clean/trades_*.csv`, `data/audit/audit_*.md`, `data/raw/trades/*/batch_log.csv` |
| Tuning on controls (task 4) | `03_tune_controls.py` | `data/audit/tuning_*` |
| Frozen run (tasks 5-6) | `04_run_frozen.py` | `data/results/*` |
| Figures (task 5) | `05_figures.py` | `figures/fig1..3*.png` |
| Shared code | `common.py` (HTTP/retry), `measures.py` (frozen v0 measures) | |

## Rules (fixed before use)
- `rules/labeling_rule.md`: insider-possible / impossible label from resolution mechanics only (16:11:20Z).
- `rules/frozen_v0.md` + `rules/frozen_v0.json`: seed, ripple, baseline, news exclusion, alert threshold (16:31:34Z), with `measures.py` sha256.

## Data sources
| Data | Source |
|---|---|
| Market metadata | Polymarket Gamma API `/markets/{id}` |
| Trades (all markets) | Polymarket Data API **v2** `/v2/trades?condition=` (taker rows; v1 retired 2026-11-02) |
| Resolutions | Data API v2 `/v2/resolutions` |
| Price history (control matching only) | Data API v2 `/v2/prices-history` (12 h grain for these dates) |
| News timestamps | Press reports; URLs in `data/news_events.csv` |
Not used: Dome API (shut down April 2026); on-chain/Dune (no API key in this session).

## Key results (q = 0.99, pre-news seeds with a matched baseline)
- Insider-possible mean excess ripple **+1.98** distinct wallets (n = 147 seeds, 3 markets) vs controls **+1.58** (n = 50, 2 markets); permutation p = 0.72. No detectable difference.
- Placebo bias of the baseline on controls: **+2.45** wallets on average.
- Maduro blind validation: 1 pre-news alert (96 h before news, toward NO); none in the final 24 h; the last pre-news hours were not scorable.
- Full logs: `log/process_log.md`; results: `data/results/comparison_summary.md`, `data/results/maduro_blind_validation.md`.

## v1 (2026-11-11): wallet-market suspicion screen + follow-on test
Rules frozen first: `rules/frozen_v1.md` (git commit `f39e644`). Labels from public reporting: `data/labels/documented_wallets.csv`.
| Step | Script | Output |
|---|---|---|
| Fills (maker+taker) and wallet profiles | `src/v1_01_fetch.py trades` / `wallets` | `data/clean/v1_fills_*.csv`, `v1_wallet_stats.csv`, `v1_wallet_windows.csv` |
| Match labels (frozen rule) | `src/v1_02_match_labels.py` | `data/labels/documented_wallets_matched.csv` |
| Layer 1 screen, permutation null, validation, price impact | `src/v1_03_layer1.py` | `data/results/v1_wallet_scores.csv`, `v1_validation.csv`, `v1_layer1.json` |
| Layer 2 follow-on (A vs B) | `src/v1_04_layer2.py` | `data/results/v1_layer2*.{csv,json}` |
| Figures 4-7 | `src/v1_05_figures.py` | `figures/fig4..fig7*.png` |
| Summary | `src/v1_06_summary.py` | `data/results/v1_summary.md` |

## Web app: Insider Signal (2026-11-14)
`web/` presents the frozen v1 screen as a product: overview, market view, wallet alert cards, a live scan, a method page and a keyboard-driven story mode for the video. It reads only frozen outputs, exported by `src/export_web.py` (last step of `run_all.sh`).
```bash
cd web && npm install && npm run dev     # http://localhost:3000
python3 src/export_web.py               # regenerate web/public/data from the frozen results (repo root)
cd web && npm test                      # TypeScript flag port vs the Python scores for 20 wallets
```
Deploy: import the repository in Vercel with Root Directory `web` (details in `web/README.md`). UI review: `web/REVIEW.md`. Screenshots: `figures/app_*.png`.
