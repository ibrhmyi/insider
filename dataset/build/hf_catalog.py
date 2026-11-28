"""Market catalog from Polymarket-v1 (HF) cleaned layers: one row per (condition_id, outcome token).

Usage: python3 build/hf_catalog.py <hf_dir>   (hf_dir holds daily_aligned/ and daily_aligned_multi/)
Writes out/hf_market_catalog.parquet. Used to find case markets by slug (A6.5) and as market metadata.
"""
import os, sys, duckdb
HF = sys.argv[1]
OUT = os.path.join(os.path.dirname(__file__), "..", "out", "hf_market_catalog.parquet")
c = duckdb.connect(); c.sql("SET memory_limit='10GB'; SET threads=4")
c.sql(f"""
COPY (
  SELECT condition_id, asset_id, any_value(outcome_seq) outcome_seq, any_value(outcome_label) outcome_label,
         any_value(market_slug) market_slug, any_value(category) category, any_value(category_refined) category_refined,
         any_value(neg_risk) neg_risk, any_value(neg_risk_market_id) neg_risk_market_id,
         any_value(winning_outcome_label) winning_outcome_label, any_value(resolution_status) resolution_status,
         any_value(opens_at) opens_at, any_value(close_at) close_at, any_value(resolved_at) resolved_at,
         min(block_timestamp) first_fill_ts, max(block_timestamp) last_fill_ts, count(*) n_fills, sum(usdc_amount) usdc_volume
  FROM read_parquet(['{HF}/daily_aligned/*.parquet', '{HF}/daily_aligned_multi/*.parquet'], union_by_name=true)
  GROUP BY condition_id, asset_id
) TO '{OUT}' (FORMAT parquet, COMPRESSION zstd)""")
print(c.sql(f"select count(*), count(distinct condition_id) from '{OUT}'"))
