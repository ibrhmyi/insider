"""Release table 6 (fills) in parts: release/data/fills_partNNN_<market_set>_<source>.parquet, at most PART_ROWS rows each,
streamed by DuckDB COPY (types per build/v1/schema.py; ts_utc is timestamp with time zone UTC). Usage: python3 build/v1/fills_release.py <tmp_dir>"""
import glob, os, sys
import duckdb

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V1, OUT = os.path.join(D, "out", "v1", "fills"), os.path.join(D, "release", "data")
PART_ROWS = 15_000_000
c = duckdb.connect(); c.sql(f"SET memory_limit='3GB'; SET threads=2; SET enable_progress_bar=false; SET temp_directory='{sys.argv[1]}'; SET preserve_insertion_order=true")
for f in glob.glob(os.path.join(OUT, "fills_part*")):
    os.remove(f)
n_part = total = 0
for ms in ["case", "placebo", "twin", "label_other"]:
    for src in ["hf_polymarket_v1", "data_api_v2"]:
        q = f"(SELECT * FROM '{V1}/fills_{ms}.parquet' WHERE source = '{src}')"
        if not os.path.exists(f"{V1}/fills_{ms}.parquet"):
            continue
        n = c.sql(f"SELECT count(*) FROM {q}").fetchall()[0][0]
        for off in range(0, n, PART_ROWS):
            n_part += 1
            out = os.path.join(OUT, f"fills_part{n_part:03d}_{ms}_{src}.parquet")
            c.sql(f"""COPY (SELECT market_set, leg_id, source, fill_id, tx_hash, ts::BIGINT ts_unix, to_timestamp(ts) ts_utc, condition_id, asset_id, outcome_label,
                         outcome_seq::BIGINT outcome_seq, price::DOUBLE price_usdc, usdc::DOUBLE usdc, shares::DOUBLE shares,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE fee_usdc::DOUBLE END fee_usdc, wallet,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE wallet_role END wallet_role,
                         (source = 'hf_polymarket_v1') role_fields_available, wallet_side,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE aggressor_side END aggressor_side,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE maker END maker, CASE WHEN source = 'data_api_v2' THEN NULL ELSE taker END taker,
                         market_slug, econ_side, econ_asset_id, econ_outcome_label, econ_price_usdc::DOUBLE econ_price_usdc,
                         econ_size_usdc::DOUBLE econ_size_usdc, econ_inferred FROM {q} LIMIT {PART_ROWS} OFFSET {off})
                      TO '{out}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)""")
            total += min(PART_ROWS, n - off)
print("fills", total, "rows in", n_part, "parts")
