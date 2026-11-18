"""v2 step 5: select 10 open markets per prereg/forward_test.md and score them with the FROZEN model at one snapshot time.
Writes prereg/forward_test_locked.csv and data/v2/forward_detail.csv."""
import json, re, time, datetime as dt
import numpy as np, pandas as pd
from common import *
from v2_features import FEATS, K_SHRINK
FZ = json.load(open(RULES / "frozen_v2.json"))
src = open(Path(__file__).parent / "v2_01_markets.py").read()
exec(src[src.index("EXCL = "):src.index('df["closed_ts"]')])      # reuse the exact EXCL/INCL/cat() text screen
logit = lambda p: np.log(p / (1 - p)); sig = lambda z: 1 / (1 + np.exp(-z))
SNAP = int(time.time()); N = FZ["N_hours"]
# ---- open candidate markets
rows = []
for off in range(0, 2000, 100):
    r = get_json(GAMMA + "/markets", params=dict(closed="false", limit=100, offset=off, order="volumeNum", ascending="false",
                 end_date_min="2026-11-19", end_date_max="2026-12-10"))
    rows += r
    if len(r) < 100 or float(r[-1].get("volumeNum") or 0) < 50000: break
M = pd.DataFrame(rows).drop_duplicates("conditionId"); n0 = len(M)
M["event_title"] = M.events.map(lambda e: (e or [{}])[0].get("title", "") if isinstance(e, list) else "")
M["text"] = M.question.fillna("") + " | " + M.event_title.fillna("")
excl = []
def ok(r):
    if float(r.volumeNum or 0) < 50000: return "volume<50k"
    if r.get("closed") or not r.get("acceptingOrders", True): return "not open"
    try: oc = json.loads(r.outcomes)
    except Exception: return "bad outcomes"
    if oc != ["Yes", "No"]: return "not_Yes/No"
    c, why = cat(r.text)
    return why if c is None else ""
M["why"] = [ok(r) for _, r in M.iterrows()]
C = M[M.why == ""].sort_values("volumeNum", ascending=False).copy()
C["ek"] = C.event_title.where(C.event_title != "", C.question); C = C.drop_duplicates("ek")
print("open markets pulled", n0, "pass screen (1 per event)", len(C), flush=True)
# ---- dataset for track record / share
P = pd.read_csv(DATA / "v2" / "positions.csv.gz"); MI = pd.read_csv(DATA / "v2" / "market_info.csv")[["conditionId", "res_ts"]]
D = P[(P.net_shares_dec > 1e-6) & (P.usd_bought_dec > 0)].merge(MI, on="conditionId")
D["excess"] = D.won - D.vwap_dec.clip(0.01, 0.99)
BW = pd.read_csv(DATA / "v2" / "buys.csv.gz"); BW = BW[BW.pre].groupby("proxy_wallet").usd.sum()
WS = pd.read_csv(DATA / "v2" / "wallet_stats.csv").set_index("wallet")
Dg = {w: (g.res_ts.values, g.excess.values) for w, g in D.groupby("proxy_wallet")}
def stats(w):
    if w in WS.index and WS.loc[w, "known"] == True: return WS.loc[w, "join_date"]
    try:
        d = get_json(f"{DATA_API}/user-stats", params=dict(user=w), max_tries=3, timeout=40).get("data")
        return d.get("join_date") if d else None
    except Exception: return None
def fetch_fills(cid):
    rows, cur, pg = [], None, 0
    while True:
        pg += 1
        if pg > 400: return None
        p = dict(condition=cid, cursor=cur, taker_only="false") if cur else dict(condition=cid, limit=1000, taker_only="false")
        js = get_json(f"{DATA_API}/trades", params=p)
        rows += [(x["transaction_hash"], x["proxy_wallet"], x["token_id"], x["timestamp"], x["size"], x["price"], x["side"]) for x in js.get("data") or []]
        pgn = js.get("pagination") or {}; cur = pgn.get("next_cursor")
        if not pgn.get("has_more") or not cur: break
    d = pd.DataFrame(rows, columns=["transaction_hash", "proxy_wallet", "token_id", "timestamp", "size", "price", "side"])
    return d.drop_duplicates(subset=["transaction_hash", "proxy_wallet", "token_id", "timestamp", "size", "price"])
out, detail, skipped = [], [], []
for _, m in C.iterrows():
    if len(out) >= 10: break
    cid = m.conditionId; yt, nt = json.loads(m.clobTokenIds)
    f = fetch_fills(cid)
    if f is None or len(f) < 30: skipped.append((m.question, "over 400 pages" if f is None else "fewer than 30 fills")); continue
    f = f[f.timestamp <= SNAP].sort_values("timestamp", kind="stable")
    ypx = np.where(f.token_id == yt, f.price, 1 - f.price); pm = float(np.median(ypx[-10:]))
    if not (0.03 <= pm <= 0.97): skipped.append((m.question, f"price {pm:.3f} outside 0.03-0.97")); continue
    f["side_name"] = np.where(f.token_id == yt, "Yes", "No"); f["usd"] = f["size"] * f["price"]; f["net"] = np.where(f.side == "BUY", 1, -1) * f["size"]
    bu = f[f.side == "BUY"]
    g = bu.groupby(["proxy_wallet", "side_name"]).agg(usd=("usd", "sum"), sh=("size", "sum"), t_first=("timestamp", "min"), t_last=("timestamp", "max"))
    g = g.join(f.groupby(["proxy_wallet", "side_name"]).net.sum().rename("net")).reset_index()
    g = g[g.net > 1e-6]; med = g.usd.median()
    end_ts = parse_ts(m.endDate); win = bu[bu.timestamp > SNAP - N * 3600]
    wdrive = set(); num = den = 0.0; cand_units = g[g.usd >= FZ["min_unit_usd"]]
    wins = win.groupby(["proxy_wallet", "side_name"]).usd.sum()
    scores = {}
    for _, u in cand_units.iterrows():
        if (u.proxy_wallet, u.side_name) not in wins.index: continue
        jd = stats(u.proxy_wallet)
        if jd is None or pd.isna(jd): continue
        rs, ex = Dg.get(u.proxy_wallet, (np.array([]), np.array([]))); k = int((rs < u.t_first).sum()); pe = (ex[rs < u.t_first].mean() * k / (k + K_SHRINK)) if k else 0.0
        x = dict(log_age=np.log1p(max(0, (u.t_first - float(jd)) / 86400)), share_event=u.usd / (u.usd + BW.get(u.proxy_wallet, 0.0)), log_usd=np.log(u.usd),
                 log_rel_size=np.log(u.usd / med), conviction=min(1.0, u.net / u.sh), log_hours_to_end=np.log1p(min(max((end_ts - u.t_first) / 3600, 0), 8760)),
                 log_prior_markets=np.log1p(k), prior_excess=pe)
        scores[(u.proxy_wallet, u.side_name)] = sum(FZ["coef"][a] * (x[a] - FZ["feat_mean"][a]) / FZ["feat_sd"][a] for a in FEATS)
    for (w, s), usd in wins.items():
        den += usd; sc = scores.get((w, s), 0.0); num += (1 if s == "Yes" else -1) * usd * sc
        if (w, s) in scores: wdrive.add(w)
    Zv = num / den if den > 0 else 0.0; pmod = float(sig(logit(pm) + FZ["gamma"] * Zv))
    diff = (pmod - pm) * 100
    out.append(dict(snapshot_utc=iso(SNAP), question=m.question, slug=m.slug, condition_id=cid, end_date=m.endDate, market_price_yes=round(pm, 4), model_prob_yes=round(pmod, 4),
                    diff_points=round(diff, 2), direction="model above market" if diff > 0.005 else ("model below market" if diff < -0.005 else "same"),
                    wallets_driving=len(wdrive), buy_wallets_last_24h=int(win.proxy_wallet.nunique()), buy_usd_last_24h=round(float(win.usd.sum()), 0), Z=round(Zv, 5)))
    print(len(out), m.question[:80], pm, round(pmod, 4), len(wdrive), flush=True)
L = pd.DataFrame(out); L.to_csv(ROOT / "prereg" / "forward_test_locked.csv", index=False)
dump(dict(snapshot=SNAP, pulled=n0, passed_screen=len(C), skipped=skipped, excl_counts=M.why.value_counts().to_dict()), DATA / "v2" / "forward_selection_log.json")
print(L[["question", "market_price_yes", "model_prob_yes", "diff_points", "wallets_driving"]].to_string()); print("skipped", skipped)
