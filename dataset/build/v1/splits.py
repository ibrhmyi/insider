"""PROTOCOL A15, A37: benchmark splits by connected component. Cases sharing any condition_id or Gamma event_id are one group; a group is
'test' if its earliest first-claim date is on or after 2026-03-01, else 'train'. group_id = the alphabetically first case of the group.
Writes release/benchmarks/splits.csv (case_id, group_id, split, first_claim_date_earliest, group_first_claim_date). Usage: python3 build/v1/splits.py"""
import os
import pandas as pd

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CUT = "2026-03-01"
cases = pd.read_csv(os.path.join(D, "data", "cases.csv"), dtype=str, keep_default_na=False)
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
parent = {c: c for c in cases.case_id}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[max(ra, rb)] = min(ra, rb)
for key in ["condition_id", "event_id"]:
    for _, g in mk[mk[key] != ""].assign(k=lambda d: d[key].str.lower()).groupby("k"):
        cs = sorted(set(g.case_id) & set(parent))
        for a in cs[1:]:
            union(cs[0], a)
cases["group_id"] = cases.case_id.map(find)
fc = cases.first_claim_date_earliest.where(cases.first_claim_date_earliest != "", cases.first_claim_date)
cases["first_claim_date_earliest"] = fc
cases["group_first_claim_date"] = cases.groupby("group_id").first_claim_date_earliest.transform("min")
cases["split"] = (cases.group_first_claim_date >= CUT).map({True: "test", False: "train"})
out = cases[["case_id", "group_id", "split", "first_claim_date_earliest", "group_first_claim_date"]].sort_values(["split", "group_id", "case_id"])
out.to_csv(os.path.join(D, "release", "benchmarks", "splits.csv"), index=False)
multi = out.groupby("group_id").case_id.apply(list); multi = multi[multi.map(len) > 1]
print(out.split.value_counts().to_dict(), "groups", out.group_id.nunique()); print(multi.to_dict())
