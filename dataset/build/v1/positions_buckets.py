"""Runs positions.py in event-hash buckets (disk allowance) and merges them into out/v1/positions.parquet and out/v1/wallet_history.parquet.
Usage: python3 build/v1/positions_buckets.py <hf_pass_work_dir> <tmp_dir> [n_buckets]"""
import glob, os, shutil, subprocess, sys
import duckdb

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); OUT = os.path.join(D, "out", "v1")
WORK, TMP = sys.argv[1:3]; NB = int(sys.argv[3]) if len(sys.argv) > 3 else 6
for f in glob.glob(os.path.join(OUT, "positions_bucket*.parquet")) + glob.glob(os.path.join(OUT, "wallet_history_bucket*.parquet")):
    os.remove(f)
for b in range(NB):
    shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "positions.py"), WORK, TMP], check=True, env=dict(os.environ, PMITC_POS_BUCKET=f"{b}/{NB}"))
c = duckdb.connect(); c.sql(f"SET memory_limit='4GB'; SET temp_directory='{TMP}'; SET preserve_insertion_order=false")
c.sql(f"""COPY (SELECT * FROM '{OUT}/positions_bucket*.parquet' ORDER BY market_set, case_id, condition_id, t_news_version, wallet, asset_id)
          TO '{OUT}/positions.parquet' (FORMAT parquet, COMPRESSION zstd)""")
c.sql(f"""COPY (SELECT wallet, any_value(first_fill_polymarket_v1_utc) first_fill_polymarket_v1_utc, any_value(first_fill_v1_ts) first_fill_v1_ts
                FROM '{OUT}/wallet_history_bucket*.parquet' GROUP BY 1 ORDER BY 1) TO '{OUT}/wallet_history.parquet' (FORMAT parquet)""")
for f in glob.glob(os.path.join(OUT, "positions_bucket*.parquet")) + glob.glob(os.path.join(OUT, "wallet_history_bucket*.parquet")):
    os.remove(f)
print(c.sql(f"SELECT market_set, t_news_version, count(*), sum(is_directional_position::INT) FROM '{OUT}/positions.parquet' GROUP BY ALL ORDER BY 1, 2").fetchall())
