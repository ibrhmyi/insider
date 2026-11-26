"""Phase 5: platform-wide rule labels (E6) from the HF pass (PROTOCOL A6.9). Never merged with documented claims.

Inputs: <work>/C/*.parquet (longshot candidates), <work>/P/*.parquet (positions), out/hf_market_catalog.parquet.
Outputs: out/weak_labels.parquet (one row per wallet seen in Polymarket-v1), out/acdc_longshots.parquet,
         logs/acdc_reconstruction.json (our counts vs the published ACDC counts, gap, used_as_label).
Usage: python3 build/weak_labels.py <work_dir>
"""
import json, os, sys
import duckdb

D = os.path.join(os.path.dirname(__file__), "..")
WORK = sys.argv[1]
OUT = os.path.join(D, "out")
MIL = r"strike|military|attack|invade|invasion|ceasefire|missile|troops|war|bomb|airstrike|nuclear|drone|army|navy|forces|khamenei|regime"
PUBLISHED = dict(longshot_bets=78496, wallets=12355, orcas=556, military_orcas=152)  # ACDC, data to 2026-05-05
c = duckdb.connect(); c.sql(f"SET memory_limit='10GB'; SET threads=4; SET enable_progress_bar=false; SET temp_directory='{WORK}/tmp'")

# ACDC longshots (clock-hour buckets, >= $2,500, VWAP <= 0.35, resolved market)
c.sql(f"""CREATE TABLE ls AS SELECT wallet, asset_id, condition_id, hour, usdc, shares, usdc / shares vwap, n_fills,
          outcome_label, winning_outcome_label, (outcome_label = winning_outcome_label) won, category_refined, market_slug,
          regexp_matches(lower(market_slug), '{MIL}') military_market
          FROM read_parquet('{WORK}/C/*.parquet')""")
c.sql(f"COPY ls TO '{OUT}/acdc_longshots.parquet' (FORMAT parquet, COMPRESSION zstd)")
c.sql("""CREATE TABLE acdc AS SELECT wallet, count(*) n_longshots, avg(won::INT) longshot_win_rate,
          count(DISTINCT category_refined) n_longshot_types, avg(military_market::INT) military_share
          FROM ls GROUP BY wallet""")
c.sql("""ALTER TABLE acdc ADD COLUMN orca BOOLEAN; UPDATE acdc SET orca = n_longshot_types BETWEEN 1 AND 2 AND longshot_win_rate >= 0.75""")
c.sql("ALTER TABLE acdc ADD COLUMN military_orca BOOLEAN; UPDATE acdc SET military_orca = orca AND military_share >= 0.5")

# Inca: <= 10 markets and realised PnL >= $30,000 (resolved markets only; splits, merges, redemptions, fees ignored)
c.sql(f"""CREATE TABLE res AS SELECT asset_id, condition_id, any_value(outcome_label) outcome_label, any_value(winning_outcome_label) winning,
          any_value(resolution_status) status FROM '{OUT}/hf_market_catalog.parquet' GROUP BY 1, 2""")
c.sql(f"""CREATE TABLE pos AS SELECT wallet, condition_id, asset_id, sum(buy_usdc) buy_usdc, sum(buy_shares) buy_shares,
          sum(sell_usdc) sell_usdc, sum(sell_shares) sell_shares, sum(n_fills) n_fills, min(first_ts) first_ts, max(last_ts) last_ts
          FROM read_parquet('{WORK}/P/*.parquet') GROUP BY 1, 2, 3""")
c.sql("""CREATE TABLE inca AS SELECT p.wallet, count(DISTINCT p.condition_id) n_markets, sum(p.n_fills) n_fills,
          sum(p.buy_usdc) buy_usdc, sum(p.sell_usdc) sell_usdc, min(p.first_ts) first_ts, max(p.last_ts) last_ts,
          sum(CASE WHEN r.status = 'resolved' AND r.winning IS NOT NULL THEN
                p.sell_usdc - p.buy_usdc + CASE WHEN r.outcome_label = r.winning THEN greatest(p.buy_shares - p.sell_shares, 0) ELSE 0 END
              ELSE 0 END) realised_pnl
          FROM pos p LEFT JOIN res r USING (asset_id, condition_id) GROUP BY p.wallet""")
c.sql("ALTER TABLE inca ADD COLUMN inca_flag BOOLEAN; UPDATE inca SET inca_flag = n_markets <= 10 AND realised_pnl >= 30000")

c.sql(f"""COPY (SELECT i.wallet address, i.n_markets, i.n_fills, round(i.buy_usdc, 2) buy_usdc, round(i.sell_usdc, 2) sell_usdc,
          to_timestamp(i.first_ts) first_fill_utc, to_timestamp(i.last_ts) last_fill_utc,
          coalesce(a.n_longshots, 0) n_longshots, a.longshot_win_rate, a.n_longshot_types, a.military_share military_longshot_share,
          CASE WHEN a.orca THEN 'Orca' WHEN a.n_longshots > 0 THEN 'longshot_wallet' ELSE '' END acdc_class,
          coalesce(a.military_orca, false) acdc_military_orca, round(i.realised_pnl, 2) realised_pnl, i.inca_flag,
          'E6' evidence_grade, 'hf_polymarket_v1 to 2026-04-28' data_scope
          FROM inca i LEFT JOIN acdc a USING (wallet)) TO '{OUT}/weak_labels.parquet' (FORMAT parquet, COMPRESSION zstd)""")

ours = dict(longshot_bets=c.sql("SELECT count(*) FROM ls").fetchall()[0][0],
            wallets=c.sql("SELECT count(*) FROM acdc").fetchall()[0][0],
            orcas=c.sql("SELECT count(*) FROM acdc WHERE orca").fetchall()[0][0],
            military_orcas=c.sql("SELECT count(*) FROM acdc WHERE military_orca").fetchall()[0][0])
gap = {k: round(100 * (ours[k] / PUBLISHED[k] - 1), 1) for k in PUBLISHED}
used = all(abs(v) <= 5 for v in gap.values())
inca_n = c.sql("SELECT count(*) FROM inca WHERE inca_flag").fetchall()[0][0]
rep = dict(published=PUBLISHED, published_data_end="2026-05-05", ours=ours, our_data_end="2026-04-28T11:00:40Z", gap_percent=gap,
           used_as_label=used, rule="PROTOCOL A6.9", inca_flagged_wallets=inca_n, inca_published_wallets=39,
           wallets_total=c.sql("SELECT count(*) FROM inca").fetchall()[0][0])
json.dump(rep, open(os.path.join(D, "logs", "acdc_reconstruction.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
