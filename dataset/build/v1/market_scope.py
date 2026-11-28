"""PROTOCOL A41: ftx-sbf keeps only the markets its claims name (pardon of SBF, FTX payouts, SBF sentence); the other Biden-pardon ladder
markets leave ftx-sbf (they stay under biden-pardons). Removes those (case, market) rows from data/markets.csv, data/placebo_markets.csv and
data/twin_markets.csv; writes logs/market_scope_removed.csv. Idempotent. Usage: python3 build/v1/market_scope.py"""
import os
import pandas as pd

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
rd = lambda f: pd.read_csv(os.path.join(D, "data", f), dtype=str, keep_default_na=False)
mk = rd("markets.csv")
drop = mk[(mk.case_id == "ftx-sbf") & mk.question.str.match(r"^Will Biden pardon ") & ~mk.question.str.contains(r"\bSBF\b")]
keys = set(zip(drop.case_id, drop.condition_id.str.lower()))
prev = os.path.join(D, "logs", "market_scope_removed.csv")
old = pd.read_csv(prev, dtype=str) if os.path.exists(prev) else pd.DataFrame(columns=["case_id", "condition_id", "question", "rule"])
pd.concat([old, drop[["case_id", "condition_id", "question"]].assign(rule="A41")]).drop_duplicates(["case_id", "condition_id"]).to_csv(prev, index=False)
mk[~mk.index.isin(drop.index)].to_csv(os.path.join(D, "data", "markets.csv"), index=False)
for f in ["placebo_markets.csv", "twin_markets.csv"]:
    t = rd(f); k = [(a, b.lower()) in keys for a, b in zip(t.case_id, t.case_condition_id)]
    t[[not x for x in k]].to_csv(os.path.join(D, "data", f), index=False); print(f, "rows removed", sum(k))
print("markets removed", len(drop), sorted(drop.question.str[:40]))

# counts per case for the current market scope (same query as build/v1/fills.py; the release gate reconciles against it)
import csv, duckdb
c = duckdb.connect(); cur = rd("markets.csv")
c.register("m", pd.DataFrame({"case_id": cur.case_id, "condition_id": cur.condition_id.str.lower()}))
res = c.sql(f"""SELECT m.case_id, l.source, count(*) legs, count(DISTINCT l.fill_id) fills, count(DISTINCT l.wallet) wallets, round(sum(l.usdc)/2) usdc
               FROM m JOIN '{D}/out/v1/fills/fills_case.parquet' l USING (condition_id) GROUP BY ALL ORDER BY 1, 2""").fetchall()
with open(os.path.join(D, "logs", "fills_counts_by_case.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["case_id", "source", "legs", "fills", "wallets", "usdc_half_of_legs"]); w.writerows(res)
print("fills_counts_by_case.csv rewritten", len(res))
