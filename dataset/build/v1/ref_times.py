"""PROTOCOL A25: recompute placebo and twin cut times (t_ref_day_utc, t_ref_precise_utc and the case-position ratios) from the
per-market case cut (t_news_market_day_utc / t_news_market_utc), without changing which markets were selected. Usage: python3 build/v1/ref_times.py"""
import os
import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
ts = lambda s: pd.to_datetime(s.replace("", None), utc=True, errors="coerce", format="mixed")
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
mk["condition_id"] = mk.condition_id.str.lower()
mk["created"] = ts(mk.created_utc); mk["end"] = ts(mk.resolved_utc).fillna(ts(mk.deadline_utc))
mk["cut_day"], mk["cut_precise"] = ts(mk.t_news_market_day_utc), ts(mk.t_news_market_utc)
M = mk.set_index(["case_id", "condition_id"])
for fname, opens, end, fcol in [("placebo_markets.csv", "placebo_opens_utc", "placebo_end_utc", "case_tnews_fraction"),
                                ("twin_markets.csv", "twin_opens_utc", "twin_end_utc", "case_tnews_fraction")]:
    p = os.path.join(D, "data", fname); T = pd.read_csv(p, dtype=str, keep_default_na=False)
    o, e = ts(T[opens]), ts(T[end])
    for v in ["day", "precise"]:
        fr, ref = [], []
        for i, r in enumerate(T.itertuples()):
            key = (r.case_id, r.case_condition_id)
            if not getattr(r, opens) or key not in M.index:
                fr.append(""); ref.append(""); continue
            m = M.loc[key]
            m = m.iloc[0] if isinstance(m, pd.DataFrame) else m
            span = (m.end - m.created).total_seconds()
            f = min(1.0, max(0.0, (m[f"cut_{v}"] - m.created).total_seconds() / span)) if span > 0 else 1.0
            fr.append(str(round(f, 6))); ref.append((o[i] + (e[i] - o[i]) * f).strftime("%Y-%m-%dT%H:%M:%SZ"))
        old = ts(T[f"t_ref_{v}_utc"]); new = ts(pd.Series(ref))
        keep = (old.notna() & new.notna() & ((new - old).dt.total_seconds().abs() <= 2)).values  # rounding only: keep the earlier value
        T[f"{fcol}_{v}"] = [T[f"{fcol}_{v}"].iloc[i] if keep[i] else fr[i] for i in range(len(T))]
        T[f"t_ref_{v}_utc"] = [T[f"t_ref_{v}_utc"].iloc[i] if keep[i] else ref[i] for i in range(len(T))]
        print(fname, v, "rows changed", int((~keep & new.notna().values).sum()))
    T.to_csv(p, index=False); print(fname, "updated")
