"""v1.0 table 11, market_minutes (PROTOCOL A9.3 with A10.2 and A14): one row per (market_set, case_id, condition_id, t_news_version,
UTC minute) with fills, from 48 h before the cut (t_news / t_news_precise; placebo t_ref) to 24 h after, for the Yes token (or the
first outcome). HF minutes count fills from taker legs and carry aggressor volume; Data API minutes count legs (n_legs_api).
n_new_wallets: wallets whose first Polymarket-v1 fill was within the previous 7 days (out/v1/wallet_history.parquet).
Usage: python3 build/v1/minutes.py <tmp_dir>
"""
import os, sys
import duckdb, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
F = os.path.join(D, "out", "v1", "fills")
c = duckdb.connect(); c.sql(f"SET memory_limit='5GB'; SET enable_progress_bar=false; SET temp_directory='{sys.argv[1]}'")
ep = lambda s: (pd.to_datetime(s.replace("", None), utc=True, errors="coerce", format="mixed") - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().round().astype("Int64")
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False); mk["condition_id"] = mk.condition_id.str.lower()
yes = lambda s: "Yes" if "Yes" in s.split(";") else (s.split(";")[0] if s else "")
pl = pd.read_csv(os.path.join(D, "data", "placebo_markets.csv"), dtype=str, keep_default_na=False); pl = pl[pl.placebo_condition_id != ""]
rows = [mk.assign(market_set="case", t_news_version=v, t_cut=ep(mk[col]), yes_label=mk.outcomes.map(yes))[["market_set", "case_id", "condition_id", "t_news_version", "t_cut", "yes_label"]]
        for v, col in [("day", "t_news_utc"), ("precise", "t_news_precise_utc")]]
rows += [pl.assign(market_set="placebo", condition_id=pl.placebo_condition_id, t_news_version=v, t_cut=ep(pl[f"t_ref_{v}_utc"]), yes_label=pl.placebo_outcomes.map(yes))[
         ["market_set", "case_id", "condition_id", "t_news_version", "t_cut", "yes_label"]] for v in ["day", "precise"]]
tw = pd.read_csv(os.path.join(D, "data", "twin_markets.csv"), dtype=str, keep_default_na=False); tw = tw[tw.twin_condition_id != ""]
rows += [tw.assign(market_set="twin", condition_id=tw.twin_condition_id, t_news_version=v, t_cut=ep(tw[f"t_ref_{v}_utc"]), yes_label=tw.twin_outcomes.map(yes))[
         ["market_set", "case_id", "condition_id", "t_news_version", "t_cut", "yes_label"]] for v in ["day", "precise"]]
c.register("mk_df", pd.concat(rows)); c.sql("CREATE TABLE mk AS SELECT * FROM mk_df")
c.sql(f"CREATE TABLE ff AS SELECT wallet, first_fill_v1_ts ffts FROM '{D}/out/v1/wallet_history.parquet'")
c.sql(f"""COPY (
  WITH l AS (
    SELECT m.market_set, m.case_id, l.condition_id, m.t_news_version, m.t_cut, l.source, l.wallet, l.wallet_role, l.aggressor_side, l.ts, l.price, l.usdc,
           (l.ts // 60) * 60 AS minute_ts
    FROM read_parquet(['{F}/fills_case.parquet', '{F}/fills_placebo.parquet', '{F}/fills_twin.parquet']) l JOIN mk m ON m.condition_id = l.condition_id AND m.market_set = l.market_set
    WHERE l.outcome_label = m.yes_label AND l.ts >= m.t_cut - 48 * 3600 AND l.ts < m.t_cut + 24 * 3600)
  SELECT market_set, case_id, condition_id, t_news_version, minute_ts, to_timestamp(minute_ts) minute_utc,
         ((minute_ts - any_value(t_cut)) / 60)::INTEGER AS minutes_from_cut, string_agg(DISTINCT source, ';') source,
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
  FROM l LEFT JOIN ff USING (wallet)
  GROUP BY market_set, case_id, condition_id, t_news_version, minute_ts
  ORDER BY market_set, case_id, condition_id, t_news_version, minute_ts) TO '{D}/out/v1/market_minutes.parquet' (FORMAT parquet, COMPRESSION zstd)""")
print(c.sql(f"SELECT market_set, t_news_version, count(*), count(DISTINCT condition_id) FROM '{D}/out/v1/market_minutes.parquet' GROUP BY ALL").fetchall())
