#!/usr/bin/env bash
# Reproduce the pilot end to end. Needs network access to gamma-api / data-api.polymarket.com.
set -euo pipefail
cd "$(dirname "$0")/src"
python3 00_match_controls.py                       # rank control candidates (writes data/raw/control_match_candidates.json)
python3 00b_screen_controls.py 620852 621677 621695 623433 621697 551260 1058617 620793 619920 627476 627507 632731 626182
python3 01_select_markets.py                        # data/markets.csv, news_events.csv, control_match_table.md
python3 02_extract_trades.py iran ctrl_btc110k_jun17 ctrl_btc94k_jan5 ctrl_btcupdown_oct14 maduro nobel
python3 03_tune_controls.py                         # controls only -> data/audit/tuning_*.  (rules/frozen_v0.* are NOT overwritten)
python3 04_run_frozen.py                            # aborts if src/measures.py differs from the frozen hash
python3 05_figures.py
# --- v1 ---
python3 v1_01_fetch.py trades
python3 v1_01_fetch.py wallets
python3 v1_02_match_labels.py
python3 v1_03_layer1.py
python3 v1_04_layer2.py
python3 v1_05_figures.py
python3 v1_06_summary.py
# --- web app data (reads frozen outputs only; no re-analysis) ---
python3 export_web.py                               # web/public/data/*.json, web/tests/fixtures/flags_20.json
