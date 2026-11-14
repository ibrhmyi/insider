# HANDOFF: Detecting Potential Insider Trading on Polymarket (CP191 Nano Capstone)

Written 2026-11-14 for agents taking over. Read this first, then `README.md`, `rules/frozen_v1.md`, `data/results/v1_summary.md`, and `log/process_log.md`.

## Non-negotiable rules for anyone continuing
1. **Wording:** never call a wallet an insider. Only "consistent with informed trading" or "unusual activity for review". Every card or figure that shows a wallet carries: *"Unusual activity for review — this does not identify an owner or prove insider trading."*
2. **Freeze before validate:** thresholds live in `rules/frozen_v1.md` (committed in `f39e644` before any v1 feature existed). Do not change them after seeing results. A change means a new version (`frozen_v2.md`), committed before it is run, with a dated log entry explaining why.
3. **Labels come only from public reporting** (`data/labels/documented_wallets.csv`: source URL, claim, alleged/charged). Never add a wallet because our screen flagged it.
4. **F7 (won) and F8 (dormant) are post-hoc** and must never enter the score.
5. **Report nulls and negatives plainly; state n everywhere.** This is a 3-market pilot, not a validated model.
6. **Log every problem and decision** as a dated entry in `log/process_log.md`.
7. Do not publish full wallet addresses in prose or figures except those already published by the cited sources (full addresses exist in the data CSVs, which is fine).

## What has been done
### v0 (2026-11-09): ripple after large trades. Result: null (Finding #1)
- Markets: Iran strike (Jun 2025, development), Maduro out by Jan 31 2026, Machado Nobel 2025; BTC controls (Jun 17, Jan 5, Oct 14 Up/Down). Metadata: `data/markets.csv`, news times `data/news_events.csv`, matching `data/control_match_table.md`.
- Seed = trade above the rolling 99th pct of size; ripple = same-direction wallets in 30 min minus a matched no-seed baseline. Tuned on controls only, frozen in `rules/frozen_v0.md`.
- Result: insider-possible +1.98 vs controls +1.58 extra wallets (n = 147 vs 50 seeds, p = 0.72). Maduro blind validation: 1 pre-news alert (96 h early, wrong direction), and the final pre-news hours were unscorable.
- Figures 1-3; results in `data/results/comparison_summary.md`, `maduro_blind_validation.md`.

### v1 (2026-11-11): wallet-market suspicion screen + follow-on test
- **Layer 1** (unit = wallet x market, pre-news buyers): flags F1 freshness <= 7 d, F2 focus >= 0.8 or <= 2 markets, F3 longshot <= 0.35, F4 size >= $2,500, F5 conviction >= 0.8, F6 timing <= 72 h; score = flags, high = >= 4.
  - Timestamp-permutation null (1,000 per market): only **Nobel** exceeds the null (137 vs ~88, p = 0.001); Iran p = 0.81, Maduro p = 0.83.
  - **Validation:** all 7 documented wallets (8 labels) score >= 4. The CFTC-charged wallet ("Burdensome-Mix" = Lookonchain's 0x31a5) ranks #1/2,608, crossing the threshold 30 h before news. Caveat: circular, because journalists used similar cues.
  - Precision unproven: 271 high-score wallet-markets (213 under $1k). F7 is confounded (all markets resolved to the longshot). Dormancy separates larger winners (47-73% vs 8-13%) but partly mechanically.
  - Price impact per $ (last-fill proxy): no difference vs similarly sized wallets.
- **Layer 2:** high-score buys (A) vs size- and time-matched established-wallet buys (B). Pooled, A draws *fewer* followers (-1.9 at 30 min, n = 273; -9.7 at 120 min, n = 224); no whale/bot difference at 30 min. **Nobel is the exception** (+8.9 / +18.5).
- Figures 4-7; full numbers in `data/results/v1_summary.md`.

## Known weaknesses (fix candidates, each needs a new frozen version)
- F6 fires for 100% of Iran buyers (market lived ~49 h); F5 fires for 71-73% in Iran/Maduro. Both are weak discriminators.
- Layer 2 B seeds are not matched on local activity (only size +-30% and time +-6 h).
- F2 uses the single market, not the event cluster (sibling Maduro markets ignored).
- Composite-key dedup with maker rows removed 199/420/14 rows; some may be real fills (no log index in the API).
- Maduro feed completeness: maker+taker notional / Gamma volume = 0.885.

## Open tasks (priority order)
1. **Add 2-3 more insider-possible markets** (military, award, appointment) using `rules/labeling_rule.md` and the *frozen v1* rules unchanged; this is the main path to statistical power.
2. **Layer 2 activity matching**: match B seeds on prior-hour trade count as well (new version, frozen first).
3. **On-chain funding** for high-score wallets (first incoming USDC on Polygon; group shared sources as "possible links", never common ownership). Needs Polygonscan/Dune/Bitquery access and probably an API key; not reachable from the original session.
4. **Verify thresholds** against Bock & Guenthoer (2026, MIF research paper) and the ACDC report; these PDFs could not be opened from the original session.
5. Event-cluster F2 via `/v2/activity?user=...&event_id=...`.
6. 5-minute video for the course: v0 null -> why the method changed -> Fig 4 -> Fig 6 -> Fig 7 -> limitations.

## Environment requirements
- Python 3.13 with `requirements.txt` (pandas, numpy, matplotlib, requests, tabulate, scipy).
- Network: `gamma-api.polymarket.com`, `data-api.polymarket.com`, `clob.polymarket.com`, `docs.polymarket.com`.
- Raw API pages are committed under `data/raw/` (about 71 MB), so the pipeline re-runs from cache without network for v0/v1 trades; wallet profiles are in `data/clean/v1_wallet_*.csv`.
- Reproduce: `./run_all.sh` (v0 then v1). `src/04_run_frozen.py` refuses to run if `src/measures.py` differs from the frozen hash.

## API facts learned the hard way (see log for details)
- Data API **v1 retired 2026-11-02** (HTTP 410). Use `/v2/...`: cursor pagination (`next_cursor`), `condition=` not `market=`, snake_case fields, `offset` is a 400.
- `/v2/trades?condition=` ignores start/end (fixed 3-year window); filter time locally. Newest-first. `taker_only` defaults to true.
- Gamma hides closed markets unless `closed=true`; `limit` silently capped at 100; offset > ~2,000 returns 422.
- Price history for 2025/early-2026 is only 12-hour grain; rebuild fine prices from fills.
- `/v2/user-stats` gives `join_date`, distinct markets (`trades`), lifetime volume (inside `all_time_pnl`); `/v2/user-volume?start&end` is day-floored.

## Repository map
| Path | Contents |
|---|---|
| `rules/` | labeling rule, frozen v0 and v1 definitions |
| `src/00-05*.py` | v0 pipeline; `src/v1_0*.py` v1 pipeline; `common.py` HTTP helper; `measures.py` frozen v0 measures |
| `data/markets.csv`, `news_events.csv` | market metadata and public-news timestamps with sources |
| `data/labels/` | documented wallets (public reporting) and their matched addresses |
| `data/clean/` | deduplicated trades/fills and wallet profiles |
| `data/audit/` | v0 field audits and tuning grids |
| `data/results/` | all v0/v1 result tables, `v1_summary.md` |
| `data/raw/` | cached API responses and docs (OpenAPI specs) |
| `figures/` | fig1-fig7 |
| `log/process_log.md` | dated decisions, problems, data gaps |
