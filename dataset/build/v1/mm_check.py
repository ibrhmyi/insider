"""Run-11 report check (A34.1, A34.2): for the 5 market makers (A34.1 rule) with the most case-market legs, directional shares (A34.2, precise cut)
against their gross pre-cut volume, per (case, market) at the same cut. Writes logs/market_maker_check.csv. Usage: python3 build/v1/mm_check.py"""
import os, sys
import duckdb
sys.path.insert(0, os.path.dirname(__file__))
from cuts import build_cuts  # noqa
from econ_view import legs_sql  # noqa
D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
F = f"{D}/out/v1/fills/fills_case.parquet"
M, _ = build_cuts(D)
c = duckdb.connect(); c.sql("SET memory_limit='4GB'")
c.register("M", M[(M.market_set == "case") & (M.t_news_version == "precise")][["case_id", "condition_id", "t_cut_ts"]])
top = [r[0] for r in c.sql(f"""SELECT f.wallet FROM '{F}' f JOIN '{D}/out/v1/market_makers.parquet' m USING (wallet) WHERE m.is_market_maker
                               GROUP BY 1 ORDER BY count(*) DESC LIMIT 5""").fetchall()]
c.sql(f"CREATE TABLE L AS SELECT * FROM {legs_sql(F)} WHERE wallet IN ({','.join(repr(w) for w in top)})")
r = c.sql(f"""WITH g AS (SELECT l.wallet, m.case_id, lower(l.condition_id) condition_id, sum(l.shares) gross_all,
                                sum(l.shares) FILTER (WHERE l.wallet_side = 'BUY') gross_buy
                         FROM L l JOIN M m ON m.condition_id = lower(l.condition_id) WHERE l.ts < m.t_cut_ts GROUP BY ALL)
  SELECT g.wallet, count(*) case_markets, count(DISTINCT g.condition_id) markets, round(sum(g.gross_all)) gross_pre_cut_shares,
         round(sum(g.gross_buy)) gross_econ_buy_shares, round(sum(d.full_sets_pre_shares)) full_sets_pre_shares,
         round(sum(d.directional_shares_pre)) directional_shares_pre, round(sum(d.directional_shares_pre) / sum(g.gross_all), 4) directional_share_of_gross
  FROM g LEFT JOIN '{D}/out/v1/directional.parquet' d ON d.market_set = 'case' AND d.t_news_version = 'precise' AND d.wallet = g.wallet
       AND d.case_id = g.case_id AND d.condition_id = g.condition_id GROUP BY 1 ORDER BY 1""").df()
r.to_csv(f"{D}/logs/market_maker_check.csv", index=False); print(r.to_string())
