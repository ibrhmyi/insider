"""PROTOCOL A9.3: minute-level paths of every case market, t_news - 48 h to t_news + 24 h, for the Yes token
(or the first outcome where no Yes exists).

HF (Polymarket-v1) minutes count fills once, from taker legs, and carry aggressor buy/sell volume.
Data API minutes count legs (the API gives maker and taker rows without saying which), so n_fills and the
aggressor columns are empty there and n_legs is filled instead.
n_new_wallets: wallets whose first Polymarket-v1 fill was within the previous 7 days (out/weak_labels.parquet);
wallets absent from Polymarket-v1 (Data API era) are counted in n_wallets_age_unknown.
Usage: python3 build/market_minutes.py <tmp_dir>
"""
import os, sys
import duckdb, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(D, "out")
c = duckdb.connect(); c.sql(f"SET memory_limit='6GB'; SET enable_progress_bar=false; SET temp_directory='{sys.argv[1]}'")
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str)
mk["t_news"] = ((pd.to_datetime(mk["t_news_utc"], utc=True, errors="coerce", format="mixed") - EPOCH).dt.total_seconds()).round().astype("Int64")
mk["yes_label"] = mk["outcomes"].fillna("").map(lambda s: "Yes" if "Yes" in s.split(";") else (s.split(";")[0] if s else ""))
c.register("mk_df", mk[["case_id", "condition_id", "t_news", "yes_label", "t_news_precision"]]); c.sql("CREATE TABLE mk AS SELECT * FROM mk_df")
c.sql(f"CREATE TABLE ff AS SELECT address, epoch(first_fill_utc)::BIGINT ffts FROM '{OUT}/weak_labels.parquet'")
c.sql(f"""COPY (
  WITH l AS (
    SELECT m.case_id, l.condition_id, m.t_news, m.t_news_precision, l.source, l.wallet, l.wallet_role, l.aggressor_side, l.ts, l.price, l.usdc,
           (l.ts // 60) * 60 AS minute_ts
    FROM '{OUT}/fills/case_market_legs.parquet' l JOIN mk m USING (condition_id)
    WHERE l.outcome_label = m.yes_label AND l.ts >= m.t_news - 48 * 3600 AND l.ts < m.t_news + 24 * 3600)
  SELECT case_id, condition_id, minute_ts, to_timestamp(minute_ts) minute_utc, (minute_ts - any_value(t_news)) / 60 AS minutes_from_tnews,
         any_value(t_news_precision) t_news_precision, string_agg(DISTINCT source, ';') source,
         count(*) FILTER (WHERE source = 'hf_polymarket_v1' AND wallet_role = 'taker') n_fills_hf,
         count(*) FILTER (WHERE source = 'data_api_v2') n_legs_api,
         sum(usdc) FILTER (WHERE source = 'data_api_v2' OR wallet_role = 'taker') usdc,
         sum(usdc) FILTER (WHERE source = 'data_api_v2' OR wallet_role = 'taker')
           / nullif(sum(usdc / nullif(price, 0)) FILTER (WHERE source = 'data_api_v2' OR wallet_role = 'taker'), 0) vwap,
         arg_max(price, ts) last_price,
         sum(usdc) FILTER (WHERE wallet_role = 'taker' AND aggressor_side = 'BUY') taker_buy_usdc,
         sum(usdc) FILTER (WHERE wallet_role = 'taker' AND aggressor_side = 'SELL') taker_sell_usdc,
         count(DISTINCT wallet) n_wallets,
         count(DISTINCT wallet) FILTER (WHERE ff.ffts IS NOT NULL AND ff.ffts >= minute_ts - 7 * 86400) n_new_wallets,
         count(DISTINCT wallet) FILTER (WHERE ff.ffts IS NULL) n_wallets_age_unknown
  FROM l LEFT JOIN ff ON ff.address = l.wallet
  GROUP BY case_id, condition_id, minute_ts
  ORDER BY case_id, condition_id, minute_ts) TO '{OUT}/market_minutes.parquet' (FORMAT parquet, COMPRESSION zstd)""")
print(c.sql(f"SELECT count(*), count(DISTINCT case_id), count(DISTINCT condition_id) FROM '{OUT}/market_minutes.parquet'").fetchall())
