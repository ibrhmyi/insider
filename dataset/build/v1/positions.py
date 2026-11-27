"""v1.0 table 7, positions (PROTOCOL C2, A10.2, A14, A16): one row per (market_set, case_id, condition_id, outcome token, wallet,
t_news_version) for every wallet with at least one BUY on that token before the cut time (case: t_news / t_news_precise;
placebo: t_ref_day / t_ref_precise). Pre-cut features only, plus Gate 1 (frozen v1 Layer 1, with the A16 substitutions) and
Gate 2a/2b; *_post columns use fills at or after the cut and are outcome columns.
Inputs: out/v1/fills/fills_{case,placebo}.parquet, data/markets.csv, data/placebo_markets.csv, <hf_pass_work>/P (day files).
Output: out/v1/positions.parquet, out/v1/wallet_history.parquet (account start from Polymarket-v1).
Usage: python3 build/v1/positions.py <hf_pass_work_dir> <tmp_dir>
"""
import os, sys
import duckdb, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from econ_view import legs_sql  # A34: economic view by default

D = os.path.join(os.path.dirname(__file__), "..", "..")
WORK, TMPD = sys.argv[1:3]
F = os.path.join(D, "out", "v1", "fills"); OUT = os.path.join(D, "out", "v1")
c = duckdb.connect(); c.sql(f"SET memory_limit='5GB'; SET temp_directory='{TMPD}'; SET enable_progress_bar=false; SET preserve_insertion_order=false; SET threads=3")
ts = lambda s: pd.to_datetime(s.replace("", None), utc=True, errors="coerce", format="mixed")
ep = lambda s: (ts(s) - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().round().astype("Int64")
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
mk["condition_id"] = mk.condition_id.str.lower()
# Yes token = outcome 'Yes', else the first listed outcome (frozen v1 YES-direction convention)
mk["yes_label"] = mk.outcomes.map(lambda s: "Yes" if "Yes" in s.split(";") else (s.split(";")[0] if s else ""))
lad = mk.copy(); lad["lr"] = pd.to_numeric(lad.ladder_rank, errors="coerce")
yes_res = lad[lad.outcome.str.lower().eq("yes") & lad.lr.notna()]
short = set(map(tuple, yes_res.loc[yes_res.groupby(["case_id", "event_id"]).lr.idxmin(), ["case_id", "condition_id"]].values))
rows = []
for r in mk.itertuples():
    for v, col in [("day", "t_news_market_day_utc"), ("precise", "t_news_market_utc")]:
        rows.append(dict(market_set="case", case_id=r.case_id, condition_id=r.condition_id, t_news_version=v, t_cut=getattr(r, col),
                         event_id=r.event_id, yes_label=r.yes_label, is_shortest_sufficient=(r.case_id, r.condition_id) in short,
                         winning_outcome=r.outcome or None, resolved_utc=r.resolved_utc))
pl = pd.read_csv(os.path.join(D, "data", "placebo_markets.csv"), dtype=str, keep_default_na=False)
pl = pl[pl.placebo_condition_id != ""]
for r in pl.itertuples():
    outs = r.placebo_outcomes.split(";")
    for v in ["day", "precise"]:
        rows.append(dict(market_set="placebo", case_id=r.case_id, condition_id=r.placebo_condition_id, t_news_version=v,
                         t_cut=getattr(r, f"t_ref_{v}_utc"), event_id=None, yes_label="Yes" if "Yes" in outs else outs[0],
                         is_shortest_sufficient=False, winning_outcome=r.placebo_outcome, resolved_utc=r.placebo_end_utc))
tw = pd.read_csv(os.path.join(D, "data", "twin_markets.csv"), dtype=str, keep_default_na=False)
tw = tw[tw.twin_condition_id != ""]
for r in tw.itertuples():  # A22: twin markets, cut at t_ref
    outs = r.twin_outcomes.split(";")
    for v in ["day", "precise"]:
        rows.append(dict(market_set="twin", case_id=r.case_id, condition_id=r.twin_condition_id, t_news_version=v,
                         t_cut=getattr(r, f"t_ref_{v}_utc"), event_id=None, yes_label="Yes" if "Yes" in outs else outs[0],
                         is_shortest_sufficient=False, winning_outcome=r.twin_outcome, resolved_utc=r.twin_end_utc))
M = pd.DataFrame(rows); M["t_cut_ts"] = ep(M.t_cut); M["resolved_ts"] = ep(M.resolved_utc)
c.register("M_df", M.drop(columns=["t_cut", "resolved_utc"])); c.sql("CREATE TABLE M AS SELECT * FROM M_df")
LSRC = legs_sql([f"{F}/fills_case.parquet", f"{F}/fills_placebo.parquet", f"{F}/fills_twin.parquet"])
c.sql(f"""CREATE VIEW legs AS SELECT market_set, condition_id, asset_id, outcome_label, ts, price, usdc, shares, wallet, wallet_role, wallet_side, source, econ_inferred
          FROM {LSRC} WHERE wallet IS NOT NULL AND wallet <> ''""")
c.sql("""CREATE VIEW L AS SELECT m.market_set, m.case_id, m.condition_id, m.t_news_version, m.t_cut_ts, m.yes_label, m.event_id,
                 m.is_shortest_sufficient, m.winning_outcome, l.asset_id, l.outcome_label, l.ts, l.price, l.usdc, l.shares, l.wallet,
                 l.wallet_role, l.wallet_side, l.source, l.econ_inferred,
                 CASE WHEN (l.outcome_label = m.yes_label) = (l.wallet_side = 'BUY') THEN 1 ELSE -1 END yes_dir
          FROM legs l JOIN M m ON m.condition_id = l.condition_id AND m.market_set = l.market_set""")
print("legs view ready", flush=True)
K = "market_set, case_id, condition_id, t_news_version, wallet"
# --- token-level positions (population: >= 1 BUY before the cut)
c.sql(f"""CREATE TABLE P AS SELECT {K}, asset_id, any_value(outcome_label) outcome_label, any_value(t_cut_ts) t_cut_ts,
   any_value(winning_outcome) winning_outcome, any_value(event_id) event_id, any_value(is_shortest_sufficient) is_shortest_sufficient,
   any_value(yes_label) yes_label,
   count(*) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) n_buy_fills_pre,
   sum(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) buy_usdc_pre,
   sum(shares) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) buy_shares_pre,
   min(ts) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) first_buy_ts,
   max(ts) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) last_buy_ts,
   arg_min(price, ts) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) first_buy_price,
   max(price) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) max_buy_price,
   median(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) median_buy_fill_usdc,
   coalesce(sum(usdc) FILTER (WHERE wallet_side='SELL' AND ts < t_cut_ts), 0) sell_usdc_pre,
   coalesce(sum(shares) FILTER (WHERE wallet_side='SELL' AND ts < t_cut_ts), 0) sell_shares_pre,
   avg((wallet_role='taker')::INT) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts AND wallet_role <> 'unknown') taker_share_pre,
   string_agg(DISTINCT source, ';') FILTER (WHERE ts < t_cut_ts) source_pre,
   coalesce(sum(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts AND econ_inferred), 0) econ_inferred_buy_usdc_pre,
   count(*) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts AND NOT econ_inferred) > 0 raw_view_prenews_buy,
   coalesce(sum(usdc) FILTER (WHERE wallet_side='BUY' AND ts >= t_cut_ts), 0) buy_usdc_post,
   coalesce(sum(shares) FILTER (WHERE wallet_side='BUY' AND ts >= t_cut_ts), 0) buy_shares_post,
   coalesce(sum(usdc) FILTER (WHERE wallet_side='SELL' AND ts >= t_cut_ts), 0) sell_usdc_post,
   coalesce(sum(shares) FILTER (WHERE wallet_side='SELL' AND ts >= t_cut_ts), 0) sell_shares_post
  FROM L GROUP BY {K}, asset_id HAVING count(*) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) > 0""")
print("positions", c.sql("SELECT count(*) FROM P").fetchall(), flush=True)
# Signal A (gate 2a): a later pre-cut BUY at >= 1.5x the first pre-cut price
c.sql(f"""CREATE TABLE SA AS SELECT {K}, l.asset_id, bool_or(l.price >= 1.5 * p.first_buy_price) gate2a
          FROM L l JOIN P p USING ({K}, asset_id) WHERE l.wallet_side='BUY' AND l.ts < l.t_cut_ts AND l.ts > p.first_buy_ts GROUP BY ALL""")
# --- wallet x market level (frozen v1 unit): F3-F6 inputs and the F2 numerator
c.sql(f"""CREATE TABLE WM AS SELECT {K}, any_value(t_cut_ts) t_cut_ts,
   min(ts) FILTER (WHERE ts < t_cut_ts) first_fill_in_market_ts,
   sum(usdc) FILTER (WHERE ts < t_cut_ts) market_usdc_pre,
   sum(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) market_buy_usdc_pre,
   abs(sum(yes_dir * usdc) FILTER (WHERE ts < t_cut_ts)) / nullif(sum(usdc) FILTER (WHERE ts < t_cut_ts), 0) f5_conviction
  FROM L GROUP BY {K} HAVING count(*) FILTER (WHERE wallet_side='BUY' AND ts < t_cut_ts) > 0""")
c.sql(f"""CREATE TABLE MAIN AS SELECT {K}, arg_max(asset_id, buy_usdc_pre) main_asset, max(buy_usdc_pre) main_buy_usdc FROM P GROUP BY {K}""")
c.sql(f"""CREATE TABLE MEDT AS WITH b AS (
    SELECT l.market_set, l.case_id, l.condition_id, l.t_news_version, l.wallet, l.ts, l.usdc,
           sum(l.usdc) OVER (PARTITION BY l.market_set, l.case_id, l.condition_id, l.t_news_version, l.wallet ORDER BY l.ts ROWS UNBOUNDED PRECEDING) cum,
           sum(l.usdc) OVER (PARTITION BY l.market_set, l.case_id, l.condition_id, l.t_news_version, l.wallet) tot
    FROM L l JOIN MAIN m ON m.market_set=l.market_set AND m.case_id=l.case_id AND m.condition_id=l.condition_id AND m.t_news_version=l.t_news_version
         AND m.wallet=l.wallet AND m.main_asset=l.asset_id
    WHERE l.wallet_side='BUY' AND l.ts < l.t_cut_ts)
  SELECT market_set, case_id, condition_id, t_news_version, wallet, min(ts) FILTER (WHERE cum >= tot / 2) weighted_median_buy_ts FROM b GROUP BY ALL""")
c.sql("DROP VIEW L")
# --- wallet history from the Polymarket-v1 day files (A16 F1 / F2 substitutions)
c.sql(f"""CREATE TABLE WH AS SELECT address wallet, epoch(first_fill_utc)::BIGINT first_fill_v1_ts, n_markets lifetime_markets_v1
          FROM '{D}/out/weak_labels.parquet' WHERE address IN (SELECT DISTINCT wallet FROM WM)""")
c.sql(f"COPY (SELECT wallet, to_timestamp(first_fill_v1_ts) first_fill_polymarket_v1_utc, first_fill_v1_ts FROM WH ORDER BY 1) TO '{OUT}/wallet_history.parquet' (FORMAT parquet)")
c.sql("""CREATE TABLE WMD AS SELECT DISTINCT wallet, (to_timestamp(t_cut_ts) AT TIME ZONE 'UTC')::DATE dcut FROM WM""")
# A16 F2 denominator: Polymarket-v1 volume (all markets) up to the end of the cut's UTC day, streamed from the day files (A16.1)
c.sql(f"""CREATE TABLE F2 AS SELECT k.wallet, k.dcut, sum(p.buy_usdc + p.sell_usdc) vol_to_day
          FROM read_parquet('{WORK}/P/*.parquet', filename=true) p JOIN WMD k ON k.wallet = p.wallet
          WHERE strptime(regexp_extract(p.filename, '(\\d{{4}}_\\d{{2}}_\\d{{2}})', 1), '%Y_%m_%d')::DATE <= k.dcut GROUP BY 1, 2""")
print("wallet history done", flush=True)
c.sql(f"""CREATE TABLE G1 AS SELECT w.*, m.main_asset, h.first_fill_v1_ts, f.vol_to_day, h.lifetime_markets_v1, t.weighted_median_buy_ts,
     (w.first_fill_in_market_ts - h.first_fill_v1_ts) / 86400.0 f1_days_account_to_first_fill,
     w.market_usdc_pre / nullif(f.vol_to_day, 0) f2_share,
     (t.weighted_median_buy_ts IS NOT NULL) has_main
  FROM WM w JOIN MAIN m USING ({K}) LEFT JOIN WH h USING (wallet)
  LEFT JOIN F2 f ON f.wallet = w.wallet AND f.dcut = (to_timestamp(w.t_cut_ts) AT TIME ZONE 'UTC')::DATE
  LEFT JOIN MEDT t USING ({K})""")
# --- final assembly in SQL (streams to parquet; pandas would not fit the memory limit)
c.sql(f"""CREATE TABLE HFM AS SELECT market_set, condition_id, bool_or(coalesce(source_pre, '') LIKE '%hf_polymarket_v1%') hf_market FROM P GROUP BY 1, 2""")
c.sql(f"""CREATE TABLE MV AS SELECT p.market_set, p.case_id, p.condition_id, p.t_news_version, p.wallet, p.buy_usdc_pre / nullif(p.buy_shares_pre, 0) f3_main_vwap
          FROM P p JOIN MAIN m ON m.market_set = p.market_set AND m.case_id = p.case_id AND m.condition_id = p.condition_id
               AND m.t_news_version = p.t_news_version AND m.wallet = p.wallet AND m.main_asset = p.asset_id""")
c.sql(f"""CREATE TABLE BIG AS SELECT * FROM (
            SELECT market_set, case_id, condition_id, asset_id, t_news_version, wallet, is_shortest_sufficient, outcome_label = yes_label is_yes,
                   row_number() OVER (PARTITION BY market_set, case_id, event_id, t_news_version, wallet ORDER BY buy_usdc_pre DESC, condition_id, asset_id) rn
            FROM P WHERE event_id IS NOT NULL AND event_id <> '') WHERE rn = 1 AND is_shortest_sufficient AND is_yes""")
FLAGS = ["flag_f1", "flag_f2", "flag_f3", "flag_f4", "flag_f5", "flag_f6"]
c.sql(f"""CREATE VIEW X0 AS SELECT p.*, coalesce(sa.gate2a, false) gate2a, g.first_fill_in_market_ts, g.market_usdc_pre, g.market_buy_usdc_pre,
     g.f5_conviction, g.main_asset, g.first_fill_v1_ts, g.vol_to_day, g.lifetime_markets_v1, g.f1_days_account_to_first_fill, g.f2_share,
     mv.f3_main_vwap, (p.t_cut_ts - g.weighted_median_buy_ts) / 3600.0 f6_hours_median_buy_to_tnews, h.hf_market,
     (b.wallet IS NOT NULL) gate2b
  FROM P p LEFT JOIN SA sa USING ({K}, asset_id) LEFT JOIN G1 g USING ({K}) LEFT JOIN MV mv USING ({K})
  LEFT JOIN HFM h ON h.market_set = p.market_set AND h.condition_id = p.condition_id
  LEFT JOIN BIG b ON b.market_set = p.market_set AND b.case_id = p.case_id AND b.condition_id = p.condition_id AND b.asset_id = p.asset_id
       AND b.t_news_version = p.t_news_version AND b.wallet = p.wallet""")
c.sql("""CREATE VIEW X1 AS SELECT *,
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN f1_days_account_to_first_fill <= 7 END flag_f1,
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN coalesce(f2_share >= 0.8, false) OR coalesce(lifetime_markets_v1 <= 2, false) END flag_f2,
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN f3_main_vwap <= 0.35 END flag_f3,
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN market_buy_usdc_pre >= 2500 END flag_f4,
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN f5_conviction >= 0.8 END flag_f5,
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN f6_hours_median_buy_to_tnews <= 72 END flag_f6 FROM X0""")
score = " + ".join(f"coalesce({f}, false)::INT" for f in FLAGS)
c.sql(f"""COPY (SELECT market_set, case_id, condition_id, asset_id, wallet, t_news_version, outcome_label, t_cut_ts, is_shortest_sufficient,
     n_buy_fills_pre, buy_usdc_pre, buy_shares_pre, first_buy_ts, last_buy_ts, first_buy_price, max_buy_price, median_buy_fill_usdc,
     sell_usdc_pre, sell_shares_pre, taker_share_pre, source_pre, econ_inferred_buy_usdc_pre, raw_view_prenews_buy, buy_usdc_pre / nullif(buy_shares_pre, 0) vwap_pre, asset_id = main_asset is_main_side,
     (first_buy_ts - first_fill_v1_ts) / 86400.0 account_age_days_at_first_buy, first_fill_in_market_ts, market_usdc_pre, market_buy_usdc_pre,
     f5_conviction, vol_to_day, lifetime_markets_v1, f1_days_account_to_first_fill, f2_share, f3_main_vwap, f6_hours_median_buy_to_tnews,
     {", ".join(FLAGS)},
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN {score} END gate1_score,
     CASE WHEN hf_market AND first_fill_v1_ts IS NOT NULL THEN ({score}) >= 4 END gate1, gate2a, gate2b,
     buy_usdc_post, buy_shares_post, sell_usdc_post, sell_shares_post,
     CASE WHEN winning_outcome IS NOT NULL THEN lower(coalesce(outcome_label, '')) = lower(winning_outcome) END won_post,
     CASE WHEN winning_outcome IS NOT NULL THEN sell_usdc_pre + sell_usdc_post - buy_usdc_pre - buy_usdc_post
          + CASE WHEN lower(coalesce(outcome_label, '')) = lower(winning_outcome)
                 THEN greatest(buy_shares_pre + buy_shares_post - sell_shares_pre - sell_shares_post, 0) ELSE 0 END END pnl_post
  FROM X1 ORDER BY market_set, case_id, condition_id, t_news_version, wallet, asset_id) TO '{OUT}/positions.parquet' (FORMAT parquet, COMPRESSION zstd)""")
print(c.sql(f"SELECT market_set, t_news_version, count(*), sum(gate1::INT), sum(gate2a::INT), sum(gate2b::INT) FROM '{OUT}/positions.parquet' GROUP BY ALL").fetchall())
