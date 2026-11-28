# How the claims were extracted

## Extractor
- The claims, cases, wallet labels, event times and protocol amendments were extracted and written by an **AI model (Anthropic Claude)** working under `PROTOCOL.md`, run by the dataset owner. Model and version: `<to be filled in by the owner from the session records>`. The `extractor` column of `claims` records the extractor per row.
- No human has yet re-extracted any claim. The blind check (PROTOCOL A4) is **pending**: `blind_check_sample.csv` (18 claims, 20% of the first 92, seed 192) is blank, waiting for a second extractor who did not see the first pass.

| Blind check (A4) | Result |
|---|---|
| Sample | 18 claims |
| Re-extracted | 0 (pending) |
| Agreement on grade / subject / amount | pending |

## Runs (prompt summaries)
| Run | Instruction in short | Main output |
|---|---|---|
| 1 | Systematic search under PROTOCOL v1.0 (official, research, press, X via citations, code); grade every claim | 84 claims |
| 2 | X sweep through search engines (A5); resolve handles through Gamma | 8 claims (pending), handle resolutions |
| 3 | Build trade-level tables: markets, fills, wallet checks, rule labels, controls, episodes (A6-A8) | first trade tables |
| 4 | Deeper data search; event times; modelling backlog | 5 claims, `event_times.csv` |
| 5 | Handle hunt; stance and investigation outcome (A9) | 9 claims |
| 6 | Read the claim source pages; recover addresses and post URLs | 9 confirmed wallets, 1 claim |
| 7 | Kaggle-ready release: exact times, placebo markets, positions, coordinated-buyer rule, benchmarks, tests (A10-A16) | 16 claims, v1.0 |
| 8 | Release fixes: rule output vs labels, label family, exact-time range, two packages (A17-A19) | v1.0.1 |
| 9 | Public release: label sets, hard negatives, twin markets, leave-one-case-out benchmarks, data protection, dataset card (A20-A24) | v1.1 |
| 10 | Final fixes: per-market news times, strict label needs a pre-news buy, selection-controlled benchmarks, multi-account family (A25-A28) | v1.2 |
| 11 | Last fixes: reliability flag for coarse-dated cases, scheduled starts checked against close, links only from allegations, fold-level strict reporting, T2w and adjacent-band relaxation (A29-A33) | v1.2.1 |

## Verification status per claim
`claims.verified`: `true` (the extractor read the page and it supports every part of the claim), `pending` (search-result text only, or the page was blocked; listed in `dataset/logs/needs_page_read.csv`), `false` (read and not supported). The counts are in the dataset card. Pages blocked by site protection were never worked around.
