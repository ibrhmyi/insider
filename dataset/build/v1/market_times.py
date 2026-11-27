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
mk = mk.drop(columns=[c for c in mk.columns if c.startswith("t_news_market") or c in ("t_news_reliable", "t_news_deadline_rule_utc")])
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
    reliable = not (r.t_news_precision in ("month", "year") and r.t_news_precise_precision == "day_fallback")  # A29
    out.append((t.strftime("%Y-%m-%dT%H:%M:%SZ"), day.strftime("%Y-%m-%dT%H:%M:%SZ"), meth, "true" if reliable else "false",
                dl_rule.strftime("%Y-%m-%dT%H:%M:%SZ") if pd.notna(dl_rule) else ""))
mk["t_news_market_utc"], mk["t_news_market_day_utc"], mk["t_news_market_method"], mk["t_news_reliable"], mk["t_news_deadline_rule_utc"] = zip(*out)
pd.DataFrame(chk).sort_values(["case_id", "condition_id"]).to_csv(os.path.join(D, "logs", "scheduled_start_check.csv"), index=False)
mk.to_csv(os.path.join(D, "data", "markets.csv"), index=False)
s = mk.groupby(["case_id", "t_news_market_method"]).size().unstack(fill_value=0)
print(s[s.drop(columns=["case_time"], errors="ignore").sum(axis=1) > 0].to_string())
print(mk.t_news_market_method.value_counts().to_dict())
ck = pd.DataFrame(chk); print("A30 checked", len(ck), "disagreements", int(ck.disagreement.sum()), ck.close_source.value_counts().to_dict())
print("A29 unreliable markets", int((mk.t_news_reliable == 'false').sum()), sorted(mk[mk.t_news_reliable == 'false'].case_id.unique()))
