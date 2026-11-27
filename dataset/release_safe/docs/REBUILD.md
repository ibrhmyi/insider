# Rebuilding PMITC from scratch

All tables are rebuilt by the scripts in the repository (`dataset/build/` and `dataset/build/v1/`); the order is in `dataset/README.md`. Package versions: `requirements.txt` (pinned; Python 3.13).

## Compute and disk (measured in run 9)
| Step | Time | Peak disk |
|---|---|---|
| Download Polymarket-v1 cleaned layers (pinned commit 6d1bcd52, 2,105 day files) | ~4 min | 16 GB |
| Full tape pass, case + placebo markets, labelled wallets, rule-label inputs (`hf_pass_v7.py`, 4 processes) | ~15 min | +8 GB (pass outputs) |
| Twin-market pass (`hf_pass_v9.py`) | ~3 min | +0.5 GB |
| Data API v2 pulls (267 case markets; two pullers) | ~2 h | 0.2 GB |
| Gamma profile look-ups (coordinated-buyer rule, hard negatives; ~13,000 addresses) | ~1 h | small |
| Rule labels (`weak_labels.py`) | ~40 min | |
| Positions (9.7 M rows), episodes, minute paths | ~45 min | spills to temp |
| Release tables and fill parts | ~15 min | 2.6 GB |
| Benchmarks with tuned gradient boosting (`pmitc_bench.py`) | ~1.5 h | |
| Total | ~7 h wall clock | ~30 GB peak (the tape can be deleted after the passes) |

Machine used: 4 CPUs, 15 GB RAM. DuckDB memory limits are set to 3-6 GB per step so that the build fits in 15 GB. The Data API keeps returning new rows, so a rebuild of `source = data_api_v2` fills will not match the SHA-256 in `MANIFEST.json`; the Polymarket-v1 parts and every table derived only from them do (`tests/`, manifest check).
