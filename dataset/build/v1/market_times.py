"""PROTOCOL A25 (A25.1, A25.2, A29, A30): per-market news times. Adds t_news_market_utc, t_news_market_day_utc, t_news_market_method to data/markets.csv
from Gamma market fields cached in logs/gamma_raw/events/ (gameStartTime, eventStartTime, endDate). Idempotent.
Usage: python3 build/v1/market_times.py"""
import glob, json, os
import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
G = {}
for f in glob.glob(os.path.join(D, "logs", "gamma_raw", "events", "*.json")):
    d = json.load(open(f))
    items = d if isinstance(d, list) else [d]
    for e in items:
        if not isinstance(e, dict):
            continue
        for m in (e.get("markets") or ([e] if e.get("conditionId") else [])):
            cid = (m.get("conditionId") or "").lower()
            if cid:
                g = G.setdefault(cid, {})
                for k in ("gameStartTime", "eventStartTime", "endDate", "closedTime"):
                    if m.get(k) and not g.get(k):
                        g[k] = m[k]
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
mk = mk.drop(columns=[c for c in mk.columns if c.startswith("t_news_market") or c in ("t_news_reliable", "t_news_deadline_rule_utc")])  # includes t_news_market_source_case
ts = lambda x: pd.to_datetime(x, utc=True, errors="coerce", format="mixed") if x else pd.NaT


def coarse_end(t0, prec, ev):
    if prec == "month": return t0 + pd.offsets.MonthBegin(1)
    if prec == "quarter": return t0 + pd.offsets.QuarterBegin(1, startingMonth=1)
    if prec == "year": return t0 + pd.offsets.YearBegin(1)
    if prec == "range" and "/" in ev:
        b = ev.split("/")[1]
        t = pd.Timestamp(b if len(b) > 7 else b + ("-01" if len(b) == 7 else "-01-01"), tz="UTC")
        return t + (pd.Timedelta(days=1) if len(b) == 10 else (pd.offsets.MonthBegin(1) if len(b) == 7 else pd.offsets.YearBegin(1)))
    return None


import re
DEADLINE_Q = re.compile(r"\b(?:by|before)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|end of|\d{4}|q[1-4])", re.I)  # A25.2
cases = pd.read_csv(os.path.join(D, "data", "cases.csv"), dtype=str, keep_default_na=False).set_index("case_id")
out, chk = [], []
for r in mk.itertuples():
    g = G.get(r.condition_id.lower(), {})
    sched = ts(g.get("gameStartTime") or g.get("eventStartTime") or "")
    t0 = ts(r.t_news_utc)
    use_sched = pd.notna(sched) and not DEADLINE_Q.search(r.question or "")
    if use_sched:  # A30: the start must be strictly before the market's close
        close, csrc = ts(g.get("closedTime") or ""), "gamma_closedTime"
        if pd.isna(close):
            close, csrc = ts(r.resolved_utc), "markets.resolved_utc"
        if pd.isna(close):
            csrc = "none"
        ok = pd.notna(close) and sched < close
        chk.append(dict(case_id=r.case_id, condition_id=r.condition_id, scheduled_start_utc=sched.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        close_utc=close.strftime("%Y-%m-%dT%H:%M:%SZ") if pd.notna(close) else "", close_source=csrc,
                        hours_start_to_close=round((close - sched).total_seconds() / 3600, 2) if pd.notna(close) else "",
                        decision="scheduled_start" if ok else "fallback_case_time", disagreement=not ok))
        use_sched = ok
    dl_rule = pd.NaT
    if use_sched:
        t, meth = sched, "scheduled_start"
    else:
        t, meth = ts(r.t_news_precise_utc), "case_time"
        if r.t_news_precision in ("month", "quarter", "year", "range") and not (pd.notna(sched) and not DEADLINE_Q.search(r.question or "")):
            end = coarse_end(t0, r.t_news_precision, cases.loc[r.case_id, "event_date"] if r.case_id in cases.index else "")
            dl = sched if pd.notna(sched) else ts(g.get("endDate") or r.deadline_utc)  # A25.2: a deadline-form start is the deadline
            if end is not None and pd.notna(dl) and t0 <= dl < end:
                t, meth, dl_rule = dl, "market_deadline", dl
    if meth != "case_time" and r.t_news_precise_precision != "day_fallback":  # A25.1
        tc = ts(r.t_news_precise_utc)
        if pd.notna(tc) and tc < t:
            t, meth, dl_rule = tc, "case_time", pd.NaT
    day = t.floor("D") if meth != "case_time" else t0
    coarse_fallback = meth == "case_time" and r.t_news_precision in ("month", "quarter", "year", "range") and r.t_news_precise_precision == "day_fallback"
    reliable = meth != "market_deadline" and not coarse_fallback  # A29.1 (per market) and A29.2 (coarse case-date fallbacks)
    out.append((t.strftime("%Y-%m-%dT%H:%M:%SZ"), day.strftime("%Y-%m-%dT%H:%M:%SZ"), meth, "true" if reliable else "false",
                dl_rule.strftime("%Y-%m-%dT%H:%M:%SZ") if pd.notna(dl_rule) else ""))
mk["t_news_market_utc"], mk["t_news_market_day_utc"], mk["t_news_market_method"], mk["t_news_reliable"], mk["t_news_deadline_rule_utc"] = zip(*out)
# A36: one news time per market. A market in several cases takes the time of the case whose claim_positions row names it (its resolving
# event); if none or several do, the earliest per-market time (never later than any case's). Method, reliability and deadline-rule time follow.
_cp = pd.read_csv(os.path.join(D, "data", "claim_positions.csv"), dtype=str)
_named = _cp.groupby("condition_id").case_id.agg(lambda s: sorted(set(s))).to_dict()
mk["_cid"] = mk.condition_id.str.lower(); a36 = []; mk["t_news_market_source_case"] = mk.case_id
for cid, g in mk.groupby("_cid"):
    if g.t_news_market_utc.nunique() == 1 and g.t_news_market_day_utc.nunique() == 1:
        continue
    nm = [k for k in _named.get(cid, []) if k in set(g.case_id)]
    src = g[g.case_id == nm[0]].iloc[0] if len(nm) == 1 else g.sort_values(["t_news_market_utc", "t_news_market_day_utc"]).iloc[0]
    for i in g.index:
        a36.append(dict(condition_id=cid, case_id=mk.at[i, "case_id"], old_utc=mk.at[i, "t_news_market_utc"], new_utc=src.t_news_market_utc,
                        source_case=src.case_id, basis="claim_positions" if len(nm) == 1 else "earliest"))
        for col in ["t_news_market_utc", "t_news_market_day_utc", "t_news_market_method", "t_news_reliable", "t_news_deadline_rule_utc"]:
            mk.at[i, col] = src[col]
        mk.at[i, "t_news_market_source_case"] = src.case_id  # A36.1
mk = mk.drop(columns="_cid")
pd.DataFrame(a36, columns=["condition_id", "case_id", "old_utc", "new_utc", "source_case", "basis"]).to_csv(os.path.join(D, "logs", "a36_shared_market_times.csv"), index=False)
print("A36 shared markets harmonised:", len({r["condition_id"] for r in a36}), "rows", len(a36), "changed", sum(r["old_utc"] != r["new_utc"] for r in a36))
pd.DataFrame(chk).sort_values(["case_id", "condition_id"]).to_csv(os.path.join(D, "logs", "scheduled_start_check.csv"), index=False)
mk.to_csv(os.path.join(D, "data", "markets.csv"), index=False)
s = mk.groupby(["case_id", "t_news_market_method"]).size().unstack(fill_value=0)
print(s[s.drop(columns=["case_time"], errors="ignore").sum(axis=1) > 0].to_string())
print(mk.t_news_market_method.value_counts().to_dict())
ck = pd.DataFrame(chk); print("A30 checked", len(ck), "disagreements", int(ck.disagreement.sum()), ck.close_source.value_counts().to_dict())
print("A29.1 unreliable markets", int((mk.t_news_reliable == 'false').sum()), sorted(mk[mk.t_news_reliable == 'false'].case_id.unique()))
