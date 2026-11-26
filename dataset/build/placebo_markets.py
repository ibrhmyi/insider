"""Run 7, PROTOCOL A14: placebo markets matched to case markets. Writes data/placebo_markets.csv.
Usage: python3 build/placebo_markets.py
"""
import os, re
import duckdb, numpy as np, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..")
SEED = 192
COIN = r"(?:^|-)(?:bitcoin|btc|ethereum|eth|solana|sol|xrp|doge|dogecoin|bnb|cardano|ada|avax|link|ltc|litecoin|hype|sui)(?:-|$)"
PRICE = r"(?:up-or-down|updown|-above-|-below-|less-than|greater-than|price-of|-reach-|-dip-to-|-hit-|-between-)"
CRYPTO_EXCL = r"(?:etf|airdrop|launch|listing|list-on|fdv|market-cap|marketcap|token-sale|exploit|hack|hacked|reserve|treasury|approve|sec-|halving|fork|unlock|staking)"
WEATHER = r"(?:highest-temperature|lowest-temperature|precipitation|inches-of-rain|inches-of-snow|snowfall|hottest-day|temperature-in)"
WEATHER_EXCL = r"(?:hurricane|storm|landfall|named-storm|tornado|earthquake|wildfire)"
BANDS = [(0, 1, "<1d"), (1, 7, "1-7d"), (7, 30, "7-30d"), (30, 90, "30-90d"), (90, 365, "90-365d"), (365, 1e9, ">365d")]
BAND_NAMES = [b[2] for b in BANDS]


def band(days):
    if pd.isna(days):
        return None
    for lo, hi, n in BANDS:
        if lo <= days < hi:
            return n
    return BANDS[0][2] if days < 0 else None


c = duckdb.connect(); c.sql("SET memory_limit='8GB'")
cat = c.sql(f"""SELECT lower(condition_id) condition_id, count(*) n_tok, string_agg(asset_id, ';' ORDER BY outcome_seq) token_ids,
                       string_agg(outcome_label, ';' ORDER BY outcome_seq) outcomes, any_value(winning_outcome_label) outcome,
                       any_value(market_slug) slug, any_value(category_refined) category_refined, min(opens_at) opens_at,
                       max(close_at) close_at, max(resolved_at) resolved_at, sum(usdc_volume) volume
                FROM '{D}/out/hf_market_catalog.parquet' WHERE resolution_status = 'resolved' AND winning_outcome_label IS NOT NULL
                GROUP BY 1 HAVING count(*) = 2""").df()
print("resolved two-token markets", len(cat))
edges = np.quantile(cat.volume, np.linspace(0, 1, 11)[1:-1])
dec = lambda v: int(np.searchsorted(edges, v, side="right")) + 1  # 1..10
cat["volume_decile"] = [dec(v) for v in cat.volume]
cat["end_at"] = cat.resolved_at.fillna(cat.close_at)  # A14.1
cat["duration_days"] = (cat.end_at - cat.opens_at).dt.total_seconds() / 86400
cat["duration_band"] = cat.duration_days.map(band)
cat["resolution_month"] = cat.end_at.dt.strftime("%Y-%m")
s = cat.slug.fillna("").str.lower()
crypto = s.str.contains(COIN) & s.str.contains(PRICE) & ~s.str.contains(CRYPTO_EXCL)
weather = s.str.contains(WEATHER) & ~s.str.contains(WEATHER_EXCL)
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
case_cids = set(mk.condition_id.str.lower())
cat["placebo_category"] = np.where(crypto, "crypto_price", np.where(weather, "weather_reading", None))
pool = cat[cat.placebo_category.notna() & ~cat.condition_id.isin(case_cids) & cat.duration_band.notna()].copy()
pool["mi"] = pool.end_at.dt.year * 12 + pool.end_at.dt.month - 1
print("placebo pool", pool.placebo_category.value_counts().to_dict())

ts = lambda x: pd.to_datetime(x.replace("", None), utc=True, errors="coerce", format="mixed")
mk["created"] = ts(mk.created_utc); mk["end"] = ts(mk.resolved_utc).fillna(ts(mk.deadline_utc))
mk["vol"] = pd.to_numeric(mk.volume_hf_usdc.replace("", None), errors="coerce")
mk["volume_basis"] = np.where(mk.in_hf == "True", "hf", "gamma")
mk.loc[mk.in_hf != "True", "vol"] = pd.to_numeric(mk.volume_gamma.replace("", None), errors="coerce")
mk = mk.sort_values(["case_id", "condition_id"]).reset_index(drop=True)
rng = np.random.default_rng(SEED)
used = set(); out = []; pid = 0
for r in mk.itertuples():
    base = dict(case_id=r.case_id, case_condition_id=r.condition_id.lower(), case_volume=r.vol, case_volume_basis=r.volume_basis)
    if pd.isna(r.vol) or r.vol <= 0 or pd.isna(r.created) or pd.isna(r.end):
        out.append(dict(base, relaxation="not_matched_zero_volume" if (pd.isna(r.vol) or r.vol <= 0) else "not_matched_no_dates")); continue
    d = dec(r.vol); b = band((r.end - r.created).total_seconds() / 86400) or BAND_NAMES[0]; mi = r.end.year * 12 + r.end.month - 1
    bi = BAND_NAMES.index(b)
    avail = pool[~pool.condition_id.isin(used)]
    steps = [("exact", avail[(avail.volume_decile == d) & (avail.duration_band == b) & (avail.mi == mi)])]
    for k, name in [(1, "month_pm1"), (3, "month_pm3"), (6, "month_pm6")]:
        steps.append((name, avail[(avail.volume_decile == d) & (avail.duration_band == b) & ((avail.mi - mi).abs() <= k)]))
    adj = [BAND_NAMES[j] for j in (bi - 1, bi, bi + 1) if 0 <= j < len(BAND_NAMES)]
    steps.append(("adjacent_band_month_pm6", avail[(avail.volume_decile == d) & avail.duration_band.isin(adj) & ((avail.mi - mi).abs() <= 6)]))
    steps.append(("any_month", avail[(avail.volume_decile == d) & (avail.duration_band == b)]))
    steps.append(("adjacent_decile_any_month", avail[((avail.volume_decile - d).abs() <= 1) & avail.duration_band.isin(adj)]))
    name, q = next(((n, q) for n, q in steps if len(q) >= 5), steps[-1])
    q = q.sort_values("condition_id")
    pick = q.iloc[np.sort(rng.choice(len(q), min(5, len(q)), replace=False))] if len(q) else q
    if not len(pick):
        out.append(dict(base, relaxation="not_matched_none_available")); continue
    f_day = None
    for p in pick.itertuples():
        used.add(p.condition_id); pid += 1
        row = dict(base, placebo_id=f"PL{pid:05d}", placebo_condition_id=p.condition_id, placebo_category=p.placebo_category,
                   placebo_slug=p.slug, placebo_token_ids=p.token_ids, placebo_outcomes=p.outcomes, placebo_outcome=p.outcome,
                   placebo_opens_utc=p.opens_at, placebo_close_utc=p.close_at, placebo_resolved_utc=p.resolved_at, placebo_end_utc=p.end_at, placebo_volume=round(p.volume, 2),
                   volume_decile=d, duration_band=b, resolution_month=r.end.strftime("%Y-%m"), placebo_duration_band=p.duration_band,
                   placebo_resolution_month=p.resolution_month, relaxation=name, n_eligible=len(q))
        span = (r.end - r.created).total_seconds()
        for v, col in [("day", "t_news_utc"), ("precise", "t_news_precise_utc")]:
            t = ts(pd.Series([getattr(r, col)]))[0]
            frac = min(1.0, max(0.0, (t - r.created).total_seconds() / span)) if span > 0 else 1.0
            row[f"case_tnews_fraction_{v}"] = round(frac, 6)
            row[f"t_ref_{v}_utc"] = p.opens_at + (p.end_at - p.opens_at) * frac
        out.append(row)
P = pd.DataFrame(out)
for col in [x for x in P.columns if x.endswith("_utc")]:
    P[col] = pd.to_datetime(P[col], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
P.to_csv(os.path.join(D, "data", "placebo_markets.csv"), index=False)
m = P[P.placebo_id.notna()]
print("case-market rows", len(mk), "matched rows", m.case_condition_id.nunique(), "placebos", len(m))
print(P.relaxation.value_counts().to_dict()); print(m.placebo_category.value_counts().to_dict())
