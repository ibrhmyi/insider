"""PROTOCOL A34.1 market-maker rule (reporting only): >= 20 active (market, UTC minute) pairs over case, twin and placebo markets
(raw fills) and legs on both tokens of the market in > 50% of them. Writes out/v1/market_makers.parquet. Usage: python3 build/v1/market_makers.py <tmp>"""
import os, sys
import duckdb

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
F = os.path.join(D, "out", "v1", "fills")
c = duckdb.connect(); c.sql(f"SET memory_limit='5GB'; SET enable_progress_bar=false; SET temp_directory='{sys.argv[1]}'; SET preserve_insertion_order=false")
src = [f"{F}/fills_{s}.parquet" for s in ["case", "twin", "placebo"]]
c.sql(f"""COPY (SELECT wallet, count(*) n_active_minutes, avg((nt >= 2)::INT) both_token_share,
                       count(*) >= 20 AND avg((nt >= 2)::INT) > 0.5 is_market_maker
                FROM (SELECT wallet, condition_id, ts // 60 m, count(DISTINCT asset_id) nt FROM read_parquet({src})
                      WHERE wallet IS NOT NULL AND wallet <> '' GROUP BY 1, 2, 3) GROUP BY 1)
          TO '{D}/out/v1/market_makers.parquet' (FORMAT parquet)""")
print(c.sql(f"SELECT count(*), sum(is_market_maker::INT) FROM '{D}/out/v1/market_makers.parquet'").fetchall())
