"""v3 step 2: per-market info from the fill cache + the committed manifest (BLIND).

T_dec = the v2 rule (src/v2_03_positions.py): after this fill the rolling median (11 fills) of the Yes price stays
outside (0.05, 0.95) up to the cutoff (resolution time - 1 h). For the v1 markets the first news time is used, as in
the v1 work and the first Gate 1 report. No price level after T_dec is stored or printed (it would reveal the outcome).
Exclusion: T_dec within 24 h of the first fill -> 'no usable pre-decision period'.
Outputs: data/v3/market_info.csv, data/v2/fills_manifest.csv (committed; rebuild the cache with
`python src/v3_01_fetch.py --manifest`)."""
import json
import numpy as np, pandas as pd
from common import *

OUT = DATA / "v3"; FD = RAW / "v2_fills"
tg = pd.read_csv(OUT / "targets.csv", dtype={"yes_token": str, "no_token": str, "event_id": str, "series_id": str})
fl = pd.read_csv(OUT / "fetch_log.csv").drop_duplicates("conditionId", keep="last").set_index("conditionId")
v1 = pd.read_csv(DATA / "markets.csv", usecols=["condition_id", "first_news_utc"]).set_index("condition_id").first_news_utc.map(parse_ts)
rows = []
for r in tg.itertuples():
    st = fl.status.get(r.conditionId, "not_fetched")
    info = dict(conditionId=r.conditionId, source=r.source, category=r.category if isinstance(r.category, str) else "ffic_other", event_id=r.event_id, series_id=r.series_id,
                question=r.question, start_ts=parse_ts(r.startDate), end_ts=parse_ts(r.endDate), res_ts=r.res_ts, max_pages=r.max_pages, status=st,
                pages=fl.pages.get(r.conditionId), rows=None, first_fill_ts=None, last_fill_ts=None, t_dec=None, t_dec_basis=None, max_gap_pre_dec_h=None)
    f = FD / f"{r.conditionId}.csv.gz"
    if st == "ok" and f.exists():
        d = pd.read_csv(f, usecols=["token_id", "timestamp", "price"], dtype={"token_id": str})
        info.update(rows=len(d), first_fill_ts=int(d.timestamp.min()), last_fill_ts=int(d.timestamp.max()))
        cutoff = int(r.res_ts) - 3600
        d = d[(d.timestamp <= cutoff) & d.token_id.isin([r.yes_token, r.no_token])].sort_values("timestamp", kind="stable")
        if r.conditionId in v1.index:
            t_dec, basis = int(v1[r.conditionId]), "first news (v1)"
        elif len(d):
            yes = np.where(d.token_id == r.yes_token, d.price, 1 - d.price)
            med = pd.Series(yes).rolling(11, min_periods=3).median().values
            mid = np.where((med > 0.05) & (med < 0.95))[0]
            t_dec = int(d.timestamp.iloc[min(mid[-1] + 1, len(d) - 1)]) if len(mid) else int(d.timestamp.iloc[0])
            t_dec, basis = min(t_dec, cutoff), "price path (v2 rule)"
        else:
            t_dec, basis = None, "no fills before cutoff"
        info.update(t_dec=t_dec, t_dec_basis=basis)
        if t_dec is not None:
            pre = np.unique(d.timestamp[d.timestamp < t_dec].values)
            info["max_gap_pre_dec_h"] = float(np.diff(pre).max() / 3600) if len(pre) > 1 else None
    rows.append(info)
m = pd.DataFrame(rows)
def why(r):
    if r.status != "ok": return f"fetch status {r.status}"
    if pd.isna(r.t_dec): return "no fills before cutoff"
    if r.t_dec - r.first_fill_ts < 86400: return "no usable pre-decision period (T_dec within 24 h of first fill)"
    return ""
m["exclude_reason"] = m.apply(why, axis=1); m["excluded"] = m.exclude_reason != ""
m.to_csv(OUT / "market_info.csv", index=False)
man = m[["conditionId", "source", "event_id", "series_id", "category", "max_pages", "status", "pages", "rows", "first_fill_ts", "last_fill_ts", "excluded", "exclude_reason"]]
man.to_csv(DATA / "v2" / "fills_manifest.csv", index=False)
print(m.status.value_counts().to_string()); print(m.exclude_reason.value_counts().to_string())
