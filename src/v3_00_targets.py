"""v3 step 0: build the fill-fetch target list and market metadata (BLIND: no outcome fields kept).

Targets:
  v2_165       the 165 markets v2 fetched (re-pull; cache was not committed)
  mil_rest     military/government markets in v2's 4,192 ranked list not fetched by v2
  mil_over12m  military/government markets over $12M excluded by Amendment B (no page cap)
  v1           Maduro, Nobel, Iran (v1 markets)
  ffic         markets in the FFIC inventory (ForesightFlow/datasets, ffic-inventory v1) matched on Polymarket
Gamma is read through a whitelist: outcomePrices, umaResolutionStatus and every other outcome field are dropped
as soon as the JSON is parsed. Event id = Gamma event id; series id = Gamma series of that event (if any).
Outputs: data/v3/targets.csv, data/v3/ffic_match.csv, data/v3/gamma_meta_log.json"""
import json, re, sys, time
import pandas as pd
from common import *

OUT = DATA / "v3"; OUT.mkdir(exist_ok=True)
FFIC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "foresightflow" / "datasets" / "ffic-inventory" / "ffic-v1.csv"
MKEEP = ["conditionId", "question", "slug", "startDate", "endDate", "closedTime", "volumeNum", "clobTokenIds", "outcomes", "negRisk"]
N_REQ = 0

def g(url, params=None):
    global N_REQ; N_REQ += 1; return get_json(url, params=params)

def blind_market(m):
    out = {k: m.get(k) for k in MKEEP}
    ev = m.get("events") or []
    out["event_id"] = str(ev[0]["id"]) if ev else None
    out["event_title"] = ev[0].get("title") if ev else None
    return out

def gamma_by_cids(cids):
    res = {}
    for i in range(0, len(cids), 20):
        chunk = cids[i:i + 20]
        for closed in ("true", "false"):
            todo = [c for c in chunk if c not in res]
            if not todo: break
            js = g(f"{GAMMA}/markets", [("condition_ids", c) for c in todo] + [("closed", closed), ("limit", 100)])
            for m in js: res[m["conditionId"]] = blind_market(m)
    return res

cand = pd.read_csv(DATA / "v2" / "markets_candidates.csv", usecols=lambda c: c not in ("yes_won",), dtype={"yes_token": str, "no_token": str})
rank = set(pd.read_csv(DATA / "v2" / "markets_ranked.csv", usecols=["conditionId"]).conditionId)
v2 = set(pd.read_csv(DATA / "v2" / "fetch_log.csv").conditionId)
T = []
for r in cand.itertuples():
    if r.conditionId in v2: T.append((r.conditionId, "v2_165", 400))
    elif r.conditionId in rank and r.category == "military_gov": T.append((r.conditionId, "mil_rest", 400))
    elif r.category == "military_gov" and r.volumeNum > 12e6: T.append((r.conditionId, "mil_over12m", None))
v1 = pd.read_csv(DATA / "markets.csv", usecols=["market_key", "condition_id"])
for r in v1[v1.market_key.isin(["iran", "maduro", "nobel"])].itertuples(): T.append((r.condition_id, "v1", None))

# ---- FFIC: prefixes -> full condition ids (outcome columns dropped at load; parenthetical label notes stripped)
ff = pd.read_csv(FFIC, usecols=["case_id", "case_title", "category", "market_id_prefix", "market_label", "volume_total_usdc_approx"])
ff["query"] = ff.market_label.str.replace(r"\s*\(.*\)\s*$", "", regex=True)
known = {c: c for c in cand.conditionId}
fm = []
for r in ff.itertuples():
    pre = r.market_id_prefix.lower(); hit = next((c for c in known if c.lower().startswith(pre)), None); how = "v2 candidate list" if hit else None
    if not hit:
        for q in (r.query, re.sub(r"\b(by|on|in)\b.*$", "", r.query).strip(), r.case_title, re.sub(r"[^\w\s]", "", r.case_title)):
            js = g(f"{GAMMA}/public-search", dict(q=q, limit_per_type=50, events_status="all", keep_closed_markets=1))
            for e in js.get("events") or []:
                for m in e.get("markets") or []:
                    if str(m.get("conditionId", "")).lower().startswith(pre): hit = m["conditionId"]; how = f"gamma public-search '{q}'"
                if hit: break
            if hit: break
    fm.append(dict(case_id=r.case_id, case_title=r.case_title, ffic_category=r.category, prefix=pre, label=r.query, conditionId=hit, matched_by=how))
    if hit: T.append((hit, "ffic", None))
fm = pd.DataFrame(fm); fm.to_csv(OUT / "ffic_match.csv", index=False)
print("FFIC matched", fm.conditionId.notna().sum(), "of", len(fm))

t = pd.DataFrame(T, columns=["conditionId", "source", "max_pages"])
t = t.groupby("conditionId", as_index=False).agg(source=("source", lambda s: "+".join(sorted(set(s)))), max_pages=("max_pages", lambda s: None if s.isna().any() else int(s.max())))

# ---- Gamma metadata (blind) incl. event id, then series id per event
meta = gamma_by_cids(t.conditionId.tolist())
t["in_gamma"] = t.conditionId.isin(meta)
for k in ["question", "slug", "startDate", "endDate", "closedTime", "volumeNum", "negRisk", "event_id", "event_title"]:
    t[k] = t.conditionId.map(lambda c: meta.get(c, {}).get(k))
def toks(c):
    m = meta.get(c)
    if not m: return (None, None)
    ids, outs = json.loads(m["clobTokenIds"] or "[]"), json.loads(m["outcomes"] or "[]")
    d = dict(zip(outs, ids)); return (d.get("Yes"), d.get("No")) if "Yes" in d else (ids[0] if ids else None, ids[1] if len(ids) > 1 else None)
t["yes_token"], t["no_token"] = zip(*t.conditionId.map(toks))
series = {}
for eid in sorted(set(t.event_id.dropna())):
    e = g(f"{GAMMA}/events/{eid}")
    s = e.get("series") or []
    series[eid] = (str(s[0]["id"]), s[0].get("title")) if s else (None, None)
t["series_id"] = t.event_id.map(lambda e: series.get(e, (None,))[0])
t["series_title"] = t.event_id.map(lambda e: series.get(e, (None, None))[1])
c2 = cand.set_index("conditionId")
t["category"] = t.conditionId.map(c2.category)
t["res_ts"] = t.conditionId.map(c2.res_ts)
t.loc[t.source.str.contains("v1") & t.conditionId.str.startswith("0x14a3"), "category"] = "award_committee"
t.loc[t.source.str.contains("v1") & t.category.isna(), "category"] = "military_gov"
nores = t.res_ts.isna()
t.loc[nores, "res_ts"] = t.loc[nores, "closedTime"].map(parse_ts)  # Gamma closedTime (a date, not an outcome) where v2 had none
t.to_csv(OUT / "targets.csv", index=False)
json.dump(dict(gamma_requests=N_REQ, http_events=HTTP_EVENTS, n_targets=len(t), by_source=t.source.value_counts().to_dict(),
               not_in_gamma=t[~t.in_gamma].conditionId.tolist()), open(OUT / "gamma_meta_log.json", "w"), indent=1)
print(t.source.value_counts().to_string()); print("not in gamma", (~t.in_gamma).sum(), "requests", N_REQ, "http events", len(HTTP_EVENTS))
