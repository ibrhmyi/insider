"""Run-11 report, PROTOCOL A35 (A35.1, A48): alleged positions among the suspected-side episodes, how the losing ones split, label-set
counts on alleged positions, and the wallets and cases that drop out, with the reason. Reads the release tables and data/claim_positions.csv
(via alleged.py). Standard control design (the suspected side is identical in every design, A27). Writes logs/a35_report.json and
logs/a35_dropouts.csv. Usage: python3 build/v1/a35_report.py"""
import json, os, sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from alleged import alleged_positions  # noqa

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R = os.path.join(D, "release", "data")
SETS = ["label_strict", "label_standard", "label_broad"]
A = alleged_positions(D)
has_rows = set(zip(A.case_id, A.wallet))
W = pd.read_parquet(os.path.join(R, "wallets.parquet"))
out, drops = {}, []
for v in ["precise", "day"]:
    e = pd.read_parquet(os.path.join(R, "episodes.parquet"), filters=[("control_design", "==", "standard"), ("t_news_version", "==", v)])
    s = e[e.role.isin(["suspected", "labelled_other_position"])]
    lost = s[s.won_post == False]  # noqa: E712
    r = dict(suspected_side_positions=int(len(s)), alleged_positions=int(s.is_alleged_position.sum()),
             labelled_other_positions=int((s.role == "labelled_other_position").sum()),
             losing_positions=int(len(lost)), losing_by_role=lost.role.value_counts().to_dict(), won_post_null=int(s.won_post.isna().sum()),
             reliable_alleged_positions=int((s.is_alleged_position & s.t_news_reliable).sum()), label_sets={})
    key = set(zip(s.case_id, s.wallet))
    for L in SETS:
        b, a = s[s[L]], s[s[L] & s.is_alleged_position]
        wl = W[W[L]]
        r["label_sets"][L] = dict(positions=int(len(b)), alleged_positions=int(len(a)), wallets_with_position=int(b.wallet.nunique()),
                                  wallets_with_alleged_position=int(a.wallet.nunique()), cases_with_position=int(b.case_id.nunique()),
                                  cases_with_alleged_position=int(a.case_id.nunique()), wallets_in_set=int(len(wl)),
                                  wallets_without_prenews_position=int(sum((c, w) not in key for c, w in zip(wl.case_id, wl.wallet))),
                                  cases_dropping_out=sorted(set(b.case_id) - set(a.case_id)))
    g = s.groupby(["case_id", "wallet"]).agg(n_positions=("row_id", "size"), n_alleged=("is_alleged_position", "sum"),
                                             label_strict=("label_strict", "max"), label_standard=("label_standard", "max"),
                                             label_broad=("label_broad", "max")).reset_index()
    d = g[g.n_alleged == 0].copy()
    d["reason"] = ["alleged_market_or_side_not_held_before_cut" if (c, w) in has_rows else "no_linked_or_cluster_claim_names_market_or_side"
                   for c, w in zip(d.case_id, d.wallet)]
    r["dropouts"] = dict(wallets=int(len(d)), by_reason=d.reason.value_counts().to_dict(),
                         by_case={c: dict(wallets=int(len(x)), reason=";".join(sorted(set(x.reason))), strict=int(x.label_strict.sum()),
                                          standard=int(x.label_standard.sum())) for c, x in d.groupby("case_id")})
    out[v] = r
    drops.append(d.assign(t_news_version=v))
json.dump(out, open(os.path.join(D, "logs", "a35_report.json"), "w"), indent=1)
pd.concat(drops).to_csv(os.path.join(D, "logs", "a35_dropouts.csv"), index=False)
print(json.dumps(out["precise"], indent=1))
