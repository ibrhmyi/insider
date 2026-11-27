"""PROTOCOL A34.2: direction net of full sets. For each (market_set, case_id, condition_id, t_news_version, wallet), from the econ legs
(A34, A34.1) before the cut: H per token = econ BUY shares - econ SELL shares (>= 0); full_sets_pre_shares = min(H_yes, H_no);
directional token = larger H; directional_shares_pre = |H_yes - H_no|; directional_cost_usdc_pre = FIFO cost of the excess shares
(sells consume the oldest lots, full sets pair with the oldest remaining lots, the excess is the newest remaining lots).
For FIFO without overselling, the remaining lots are the buys beyond cumulative bought = total sold, so the excess is the last
directional_shares shares bought. Writes out/v1/directional.parquet. Usage: python3 build/v1/directional.py <tmp_dir>"""
import os, sys
import duckdb

sys.path.insert(0, os.path.dirname(__file__))
from cuts import build_cuts  # noqa
from econ_view import legs_sql  # noqa

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
F = os.path.join(D, "out", "v1", "fills"); OUT = os.path.join(D, "out", "v1")
NB = 8
c = duckdb.connect(); c.sql(f"SET memory_limit='5GB'; SET enable_progress_bar=false; SET temp_directory='{sys.argv[1]}'; SET preserve_insertion_order=false; SET threads=3")
M, _ = build_cuts(D)
c.register("M_df", M[["market_set", "case_id", "condition_id", "t_news_version", "t_cut_ts"]]); c.sql("CREATE TABLE M AS SELECT * FROM M_df")
c.sql(f"CREATE VIEW legs AS SELECT * FROM {legs_sql([f'{F}/fills_case.parquet', f'{F}/fills_placebo.parquet', f'{F}/fills_twin.parquet'])} WHERE wallet IS NOT NULL AND wallet <> ''")
K = "market_set, case_id, condition_id, t_news_version, wallet"
parts = []
for b in range(NB):
    c.sql(f"""CREATE OR REPLACE TABLE LB AS SELECT l.market_set, m.case_id, lower(l.condition_id) condition_id, m.t_news_version, l.wallet, l.asset_id,
                     l.wallet_side, l.shares, l.price, l.ts, l.leg_id
              FROM legs l JOIN M m ON m.condition_id = lower(l.condition_id) AND m.market_set = l.market_set
              WHERE l.ts < m.t_cut_ts AND hash(lower(l.condition_id)) % {NB} = {b}""")
    out = os.path.join(sys.argv[1], f"directional_{b}.parquet")
    c.sql(f"""COPY (
        WITH T AS (SELECT {K}, asset_id, coalesce(sum(shares) FILTER (WHERE wallet_side = 'BUY'), 0) B,
                          greatest(coalesce(sum(shares) FILTER (WHERE wallet_side = 'BUY'), 0) - coalesce(sum(shares) FILTER (WHERE wallet_side = 'SELL'), 0), 0) H
                   FROM LB GROUP BY ALL),
             W AS (SELECT {K}, arg_max(asset_id, H) directional_asset_id, max(H) hmax, CASE WHEN count(*) >= 2 THEN min(H) ELSE 0 END hmin FROM T GROUP BY ALL),
             X AS (SELECT W.*, W.hmax - W.hmin dshares, T.B btot FROM W JOIN T USING ({K}) WHERE T.asset_id = W.directional_asset_id),
             LOTS AS (SELECT LB.market_set, LB.case_id, LB.condition_id, LB.t_news_version, LB.wallet, LB.price, LB.shares,
                             sum(LB.shares) OVER (PARTITION BY LB.market_set, LB.case_id, LB.condition_id, LB.t_news_version, LB.wallet ORDER BY LB.ts, LB.leg_id
                                                  ROWS UNBOUNDED PRECEDING) cum, X.btot, X.dshares
                      FROM LB JOIN X USING ({K}) WHERE LB.asset_id = X.directional_asset_id AND LB.wallet_side = 'BUY' AND X.dshares > 1e-6),
             C AS (SELECT {K}, sum(price * greatest(least(cum, btot) - greatest(cum - shares, btot - dshares), 0)) cost FROM LOTS GROUP BY ALL)
        SELECT X.market_set, X.case_id, X.condition_id, X.t_news_version, X.wallet, X.directional_asset_id,
               X.dshares directional_shares_pre, X.hmin full_sets_pre_shares, coalesce(C.cost, 0) directional_cost_usdc_pre
        FROM X LEFT JOIN C USING ({K})) TO '{out}' (FORMAT parquet, COMPRESSION zstd)""")
    parts.append(out); print("bucket", b, flush=True)
c.sql(f"COPY (SELECT * FROM read_parquet({parts})) TO '{OUT}/directional.parquet' (FORMAT parquet, COMPRESSION zstd)")
for p in parts:
    os.remove(p)
print(c.sql(f"""SELECT market_set, t_news_version, count(*) n, sum((directional_shares_pre > 1e-6)::INT) directional, sum((full_sets_pre_shares > 1e-6)::INT) with_full_sets
                FROM '{OUT}/directional.parquet' GROUP BY ALL ORDER BY 1, 2""").df().to_string())
