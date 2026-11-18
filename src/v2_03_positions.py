"""v2 step 1d: wallet x market x side positions from cached fills. Cutoff = resolution time (Gamma closedTime) - 1 hour.
Outputs (data/v2/): positions.csv.gz (units), buys.csv.gz (every buy before cutoff, compact, for the market-level step),
market_info.csv (price at cutoff, last fill, counts), data_log.json"""
import json
import numpy as np, pandas as pd
from common import *
cand = pd.read_csv(DATA / "v2" / "markets_ranked.csv", dtype={"yes_token": str, "no_token": str}).set_index("conditionId")
log = fetch = pd.read_csv(DATA / "v2" / "fetch_log.csv")
ok = fetch[fetch.status.isin(["ok", "cached"])].conditionId.tolist()
pos_all, buys_all, minfo = [], [], []
gaps = dict(markets_no_pre_cutoff_fills=[], neg_or_zero_net_units=0, zero_usd_units=0, fills_after_cutoff=0)
for cid in ok:
    m = cand.loc[cid]; f = RAW / "v2_fills" / f"{cid}.csv.gz"
    d = pd.read_csv(f, dtype={"token_id": str})
    cutoff = int(m.res_ts) - 3600
    gaps["fills_after_cutoff"] += int((d.timestamp > cutoff).sum())
    d = d[d.timestamp <= cutoff].copy()
    if d.empty: gaps["markets_no_pre_cutoff_fills"].append(cid); continue
    d["side_name"] = np.where(d.token_id == m.yes_token, "Yes", np.where(d.token_id == m.no_token, "No", "?"))
    d = d[d.side_name != "?"]
    d["usd"] = d["size"] * d["price"]
    d["sgn"] = np.where(d.side == "BUY", 1.0, -1.0)
    d["net_sh"] = d.sgn * d["size"]
    d = d.sort_values("timestamp", kind="stable")
    d["yes_px"] = np.where(d.side_name == "Yes", d.price, 1 - d.price)
    # decision time T_dec: after this fill the rolling-median (11 fills) Yes price stays outside (0.05, 0.95) until the cutoff
    med = d.yes_px.rolling(11, center=False, min_periods=3).median().values
    mid = np.where((med > 0.05) & (med < 0.95))[0]
    t_dec = int(d.timestamp.iloc[min(mid[-1] + 1, len(d) - 1)]) if len(mid) else int(d.timestamp.iloc[0])
    t_dec = min(t_dec, cutoff)
    d["pre"] = d.timestamp <= t_dec
    buys = d[d.side == "BUY"]
    def agg(dd, bb, sfx):
        g = bb.groupby(["proxy_wallet", "side_name"]).agg(usd_bought=("usd", "sum"), shares_bought=("size", "sum"),
                    first_buy_ts=("timestamp", "min"), last_buy_ts=("timestamp", "max"), n_buys=("usd", "size"))
        g = g.join(dd.groupby(["proxy_wallet", "side_name"]).net_sh.sum().rename("net_shares")).reset_index()
        g["vwap"] = g.usd_bought / g.shares_bought
        return g.add_suffix(sfx).rename(columns={"proxy_wallet" + sfx: "proxy_wallet", "side_name" + sfx: "side_name"})
    gc = agg(d, buys, "_cut")
    gd = agg(d[d.pre], buys[buys.pre], "_dec")
    g = gc.merge(gd, on=["proxy_wallet", "side_name"], how="left")
    gaps["neg_or_zero_net_units"] += int((g.net_shares_cut <= 1e-6).sum())
    g = g[g.net_shares_cut > 1e-6].copy()
    g["won"] = np.where(g.side_name == "Yes", m.yes_won, 1 - m.yes_won).astype(int)
    g["conditionId"] = cid; g["t_dec"] = t_dec
    pos_all.append(g)
    b = buys[["proxy_wallet", "side_name", "timestamp", "usd", "pre"]].copy(); b["conditionId"] = cid; buys_all.append(b)
    minfo.append(dict(conditionId=cid, cutoff_ts=cutoff, n_fills=len(d), n_wallets=d.proxy_wallet.nunique(), first_fill_ts=int(d.timestamp.min()),
                      last_fill_ts=int(d.timestamp.max()), yes_px_at_cutoff=float(d.yes_px.iloc[-20:].median()), t_dec=t_dec, yes_px_at_dec=float(d[d.pre].yes_px.iloc[-20:].median()) if d.pre.any() else None, total_buy_usd=float(buys.usd.sum())))
pos = pd.concat(pos_all, ignore_index=True)
pos.to_csv(DATA / "v2" / "positions.csv.gz", index=False, compression="gzip")
pd.concat(buys_all, ignore_index=True).to_csv(DATA / "v2" / "buys.csv.gz", index=False, compression="gzip")
mi = pd.DataFrame(minfo).merge(cand.reset_index()[["conditionId","slug","question","category","res_ts","volumeNum","yes_won","event_title"]], on="conditionId")
mi.to_csv(DATA / "v2" / "market_info.csv", index=False)
gaps.update(markets=len(mi), units=len(pos), wallets=int(pos.proxy_wallet.nunique()), units_ge_100usd=int((pos.usd_bought_cut >= 100).sum()),
            wallets_ge_100usd=int(pos[pos.usd_bought_cut >= 100].proxy_wallet.nunique()))
dump(gaps, DATA / "v2" / "data_log.json"); print(json.dumps(gaps, indent=1, default=str)[:1200])
