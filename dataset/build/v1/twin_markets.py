"""Run 9, PROTOCOL A22, A38, A39: same-category, same-question-type comparison ("twin") markets, never a placebo category or the same subject.
Run 11 (A38): twins are chosen from the markets whose fills are already in the release pass (out/v1/fills/fills_twin.parquet). Writes data/twin_markets.csv.
Usage: python3 build/v1/twin_markets.py"""
import os, sys
import duckdb, numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
D = os.path.join(os.path.dirname(__file__), "..", "..")
SEED = 192
BANDS = [(0, 1, "<1d"), (1, 7, "1-7d"), (7, 30, "7-30d"), (30, 90, "30-90d"), (90, 365, "90-365d"), (365, 1e9, ">365d")]
BN = [b[2] for b in BANDS]
band = lambda d: None if pd.isna(d) else next((n for lo, hi, n in BANDS if lo <= d < hi), BN[0] if d < 0 else None)
c = duckdb.connect(); c.sql("SET memory_limit='6GB'")
cat = c.sql(f"""SELECT lower(condition_id) condition_id, count(*) n_tok, string_agg(asset_id, ';' ORDER BY outcome_seq) token_ids,
                       string_agg(outcome_label, ';' ORDER BY outcome_seq) outcomes, any_value(winning_outcome_label) outcome, any_value(market_slug) slug,
                       any_value(category_refined) category_refined, any_value(neg_risk_market_id) neg_risk_market_id, min(opens_at) opens_at,
                       max(close_at) close_at, max(resolved_at) resolved_at, sum(usdc_volume) volume, any_value(resolution_status) status
                FROM '{D}/out/hf_market_catalog.parquet' GROUP BY 1""").df()
res2 = cat[(cat.status == "resolved") & cat.outcome.notna() & (cat.n_tok == 2)].copy()
edges = np.quantile(res2.volume, np.linspace(0, 1, 11)[1:-1])  # same deciles as A14 (resolved two-token catalog)
dec = lambda v: int(np.searchsorted(edges, v, side="right")) + 1
for X in (cat, res2):
    X["end_at"] = X.resolved_at.fillna(X.close_at)
    X["duration_band"] = ((X.end_at - X.opens_at).dt.total_seconds() / 86400).map(band)
    X["year"] = X.end_at.dt.year
res2["volume_decile"] = res2.volume.map(dec)
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False); mk["condition_id"] = mk.condition_id.str.lower()
pl = pd.read_csv(os.path.join(D, "data", "placebo_markets.csv"), dtype=str, keep_default_na=False)
case_cids = set(mk.condition_id); plc = set(pl.placebo_condition_id) - {""}
case_events = set(cat[cat.condition_id.isin(case_cids)].neg_risk_market_id.dropna()) - {""}
ev_slugs = {s for s in mk.event_slug if s}
pool = res2[~res2.condition_id.isin(case_cids) & ~res2.condition_id.isin(plc) & ~res2.neg_risk_market_id.fillna("~").isin(case_events)
            & res2.duration_band.notna() & res2.category_refined.notna()].copy()
pool = pool[~pool.slug.fillna("").map(lambda s: any(e and s.startswith(e) for e in ev_slugs))]
from question_type import qtype, PLACEBO_TYPES  # A38
import duckdb as _dd, re as _re
_fetched = {r[0] for r in _dd.sql(f"SELECT DISTINCT lower(condition_id) FROM '{D}/out/v1/fills/fills_twin.parquet'").fetchall()}
pool = pool[pool.condition_id.isin(_fetched)].copy()
pool["qt"] = pool.slug.fillna("").str.replace("-", " ").map(qtype)
pool = pool[~pool.qt.isin(PLACEBO_TYPES)]
pool["slug_words"] = pool.slug.fillna("").str.lower().str.split("-").map(set)
MONTHS = set("january february march april may june july august september october november december will".split())
subject = lambda q: {w.lower() for w in _re.findall(r"(?<!^)(?<![.?!] )\b[A-Z][A-Za-z.'’]{2,}", q or "")} - MONTHS  # proper nouns of the case question
print("twin pool", len(pool), pool.qt.value_counts().to_dict())
ci = cat.set_index("condition_id")
ts = lambda x: pd.to_datetime(x.replace("", None), utc=True, errors="coerce", format="mixed")
mk["created"] = ts(mk.created_utc); mk["end"] = ts(mk.resolved_utc).fillna(ts(mk.deadline_utc))
mk["vol"] = pd.to_numeric(mk.volume_hf_usdc.replace("", None), errors="coerce")
mk = mk.sort_values(["case_id", "condition_id"]).reset_index(drop=True)
rng = np.random.default_rng(SEED); used = set(); out = []; n = 0
for r in mk.itertuples():
    base = dict(case_id=r.case_id, case_condition_id=r.condition_id)
    if r.condition_id not in ci.index or pd.isna(ci.loc[r.condition_id, "category_refined"]):
        out.append(dict(base, relaxation="not_matched_no_category")); continue
    if pd.isna(r.vol) or r.vol <= 0 or pd.isna(r.created) or pd.isna(r.end):
        out.append(dict(base, relaxation="not_matched_zero_volume_or_dates")); continue
    if r.case_id == "tweet-count-self-2026-03":  # A39: same-subject markets are not twins
        out.append(dict(base, relaxation="not_matched_same_subject_case_A39")); continue
    catg = ci.loc[r.condition_id, "category_refined"]; d = dec(r.vol)
    qt = qtype(r.question); subj = subject(r.question)
    b = band((r.end - r.created).total_seconds() / 86400) or BN[0]; bi = BN.index(b); y = r.end.year
    adj = [BN[j] for j in (bi - 1, bi, bi + 1) if 0 <= j < len(BN)]
    av = pool[(pool.category_refined == catg) & (pool.qt == qt) & ~pool.condition_id.isin(used)]  # A38: same question type
    if subj:
        av = av[~av.slug_words.map(lambda w: bool(w & subj)).astype(bool).values] if len(av) else av  # A38: never the same subject
    steps = [("exact", av[(av.volume_decile == d) & (av.duration_band == b) & (av.year == y)]),
             ("year_pm1", av[(av.volume_decile == d) & (av.duration_band == b) & ((av.year - y).abs() <= 1)]),
             ("adjacent_band_year_pm1", av[(av.volume_decile == d) & av.duration_band.isin(adj) & ((av.year - y).abs() <= 1)]),
             ("adjacent_decile_year_pm1", av[((av.volume_decile - d).abs() <= 1) & av.duration_band.isin(adj) & ((av.year - y).abs() <= 1)]),
             ("any_year", av[(av.volume_decile == d) & (av.duration_band == b)])]
    name, q = next(((nm, q) for nm, q in steps if len(q) >= 5), steps[-1])
    q = q.sort_values("condition_id")
    if not len(q):
        out.append(dict(base, relaxation="not_matched_none_available", category_refined=catg, question_type=qt)); continue
    pick = q.iloc[np.sort(rng.choice(len(q), min(5, len(q)), replace=False))]
    span = (r.end - r.created).total_seconds()
    for p in pick.itertuples():
        used.add(p.condition_id); n += 1
        row = dict(base, twin_id=f"TW{n:05d}", twin_condition_id=p.condition_id, category_refined=catg, question_type=qt, twin_slug=p.slug, twin_token_ids=p.token_ids,
                   twin_outcomes=p.outcomes, twin_outcome=p.outcome, twin_opens_utc=p.opens_at, twin_end_utc=p.end_at, twin_volume_usdc=round(p.volume, 2),
                   volume_decile=d, duration_band=b, resolution_year=y, twin_duration_band=p.duration_band, twin_year=p.year, relaxation=name, n_eligible=len(q))
        for v, col in [("day", "t_news_utc"), ("precise", "t_news_precise_utc")]:
            t = ts(pd.Series([getattr(r, col)]))[0]
            f = min(1.0, max(0.0, (t - r.created).total_seconds() / span)) if span > 0 else 1.0
            row[f"case_tnews_fraction_{v}"] = round(f, 6); row[f"t_ref_{v}_utc"] = p.opens_at + (p.end_at - p.opens_at) * f
        out.append(row)
T = pd.DataFrame(out)
for col in [x for x in T.columns if x.endswith("_utc")]:
    T[col] = pd.to_datetime(T[col], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
T.to_csv(os.path.join(D, "data", "twin_markets.csv"), index=False)
m = T[T.twin_id.notna()]
print("twins", len(m), "case markets matched", m.case_condition_id.nunique(), T.relaxation.value_counts().to_dict())
print(m.category_refined.value_counts().head(10).to_dict())
