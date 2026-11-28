# Run 4 report (2026-11-26)

A deeper search for useful data, after a critiqued backlog of modelling ideas (`build/IDEAS.md`). No rule changed. Everything taken from search-result text is `verified=pending`. No timestamp in `data/event_times.csv` is used for t_news yet: that would change A7 and needs a new amendment.

## Added

**Claims.** 5 new claims (CL0093–CL0097, run 4, pending) and 2 new cases:

| Case or claim | What |
|---|---|
| nyt-siena-polls-2026 (new case) | Bets placed before NYT/Siena Senate poll releases, flagged by university researchers via the NYT, E5, plus The Block's on-chain counter-claim |
| kalshi-q2q3-2026-aggregate (new case) | 50+ Kalshi law-enforcement referrals in Q2–Q3 2026, E3 |
| kalshi-teleprompter-2026 | CFTC-ordered halt of Trump speech markets, 2026-11-17, E3 |
| polymarket-referrals-aggregate | Dozens of military-market accounts referred to the DOJ (CNN, 2026-08-21), E3 |

**`data/event_times.csv`.** 13 timestamps for 11 cases, each with its basis (official post, first report, operation start, scheduled release) and a source URL. Minute or near-minute precision for:
- maduro-2026-01
- us-iran-strike-2026-02-28
- us-iran-strike-2025-06
- the June 2025 Israel strike cases
- nobel-peace-2025
- zachxbt-axiom-2026-02
- us-iran-ceasefire-2026-04-07 (as a 30-minute window)
- gemini3-release-2025

Day only for google-yis-2025, walz-vp-2024 and taylor-swift-engagement.

**`logs/source_candidates.csv`.** External datasets and methods worth using later:
- per-user features and PnL for all Polymarket users;
- Kalshi trades;
- the Polymarket-v1 CTF layer, for exact PnL and redemptions;
- the Gómez-Cram et al. skilled-trader test;
- Bitquery, as an alternative to the archive RPC.

**Queries:** 28 (n 76–103 in `logs/search_log.csv`).

## Not found / stopped

- No public GitHub, Dune, Kaggle or Hugging Face dataset with labelled insider wallets beyond the sources already ingested.
- The ACDC, Polysights, Polymarket-referral and Gómez-Cram lists are not public.
- No minute-level time found for the Walz pick, the Swift engagement or Google's Year in Search release.

## needs_page_read additions

The NYT/Siena trader's address and the poll release times; the Kalshi Q2–Q3 counts; a House letter to Kalshi; a Fortune piece on Truth Social insider bets; the address used in the on-chain review; and the Polymarket Money "HD2" handle.

## Next (see `build/IDEAS.md`)

1. An amendment to allow sub-day t_news from `event_times.csv`.
2. Placebo markets from the HF data already processed.
3. `episodes_master`, with labels kept in separate columns.
