"""v1 Layer 2: do others follow suspicious wallets more than equally large trades by established wallets? (rules/frozen_v1.md)
Outputs: data/results/v1_layer2_seeds.csv, data/results/v1_layer2.json
"""
import numpy as np
import pandas as pd

from common import CLEAN, DATA, dump, iso

RES = DATA / "results"
MARKETS = ["iran", "maduro", "nobel"]
NEWS = pd.read_csv(DATA / "news_events.csv")
T_NEWS = {k: int(NEWS[NEWS.market_key == k].news_epoch.min()) for k in MARKETS}
S = pd.read_csv(RES / "v1_wallet_scores.csv")
ST = pd.read_csv(CLEAN / "v1_wallet_stats.csv").set_index("wallet")
WINDOWS = [30, 120]
EXCL = 15 * 60
rng = np.random.default_rng(7)

# follower types (frozen): whale = top 1% lifetime volume_usdc among all wallets in the 3 markets; bot = >= 50 trades/day since join
whale_cut = ST.life_volume_usdc.quantile(0.99)
days = (ST.pnl_obs_ts - ST.join_date) / 86400
bot = (ST.life_trade_count / days.clip(lower=1)) >= 50
TYPE = pd.Series("other", index=ST.index)
TYPE[bot.fillna(False)] = "bot"
TYPE[ST.life_volume_usdc >= whale_cut] = "whale"  # whale takes precedence if both


def load(m):
    f = pd.read_csv(CLEAN / f"v1_fills_{m}.csv").sort_values("timestamp", kind="stable").reset_index(drop=True)
    yes = f.outcome_index == 0
    f["dir"] = np.where(yes == (f.side == "BUY"), 1, -1)
    f["yes_price"] = np.where(yes, f.price, 1 - f.price)
    f["usd"] = f["size"] * f["price"]
    return f


def seeds_for(f, wallets, T):
    b = f[(f.side == "BUY") & (f.timestamp < T) & f.proxy_wallet.isin(wallets)].sort_values("timestamp")
    out = []
    for w, g in b.groupby("proxy_wallet"):
        cur = None
        for _, r in g.iterrows():
            if cur and r.timestamp - cur["t"] <= 1800:
                cur["usd"] += r.usd; cur["dirusd"] += r.dir * r.usd; cur["n_fills"] += 1
            else:
                if cur: out.append(cur)
                cur = dict(wallet=w, t=int(r.timestamp), usd=r.usd, dirusd=r.dir * r.usd, n_fills=1)
        out.append(cur)
    d = pd.DataFrame(out)
    if len(d):
        d["dir"] = np.sign(d.dirusd).astype(int).replace(0, 1)
    return d


def outcomes(f, taker, at, seed, H):
    t0, d, w = seed["t"], seed["dir"], seed["wallet"]
    win = taker[(taker.timestamp > t0) & (taker.timestamp <= t0 + H * 60) & (taker.dir == d) & (taker.proxy_wallet != w)]
    ws = win.proxy_wallet.unique()
    ty = TYPE.reindex(ws).fillna("other")
    return dict(wallets=len(ws), usd=float(win.usd.sum()),
                price_move=float(d * (at(t0 + H * 60) - at(t0))),
                whales=int((ty == "whale").sum()), bots=int((ty == "bot").sum()), others=int((ty == "other").sum()))


def signflip(d, n=10000):
    d = np.asarray(d, float)
    if len(d) == 0:
        return np.nan
    obs = abs(d.mean())
    flips = rng.choice([-1, 1], size=(n, len(d)))
    return float((1 + (np.abs((flips * d).mean(1)) >= obs).sum()) / (n + 1))


def boot_ci(d, n=5000):
    d = np.asarray(d, float)
    if len(d) < 2:
        return [np.nan, np.nan]
    m = rng.choice(d, size=(n, len(d))).mean(1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def main():
    rows, excluded = [], []
    for m in MARKETS:
        f = load(m)
        T = T_NEWS[m]
        t_arr, p_arr = f.timestamp.values, f.yes_price.values
        at = lambda x: p_arr[max(np.searchsorted(t_arr, x, "right") - 1, 0)]
        taker = f[f.role == "taker"]
        Sm = S[S.market_key == m]
        A = seeds_for(f, set(Sm[Sm.is_high].wallet), T)
        est = Sm[(Sm.score <= 1)].wallet
        est = [w for w in est if w in ST.index and pd.notna(ST.loc[w, "n_markets"]) and ST.loc[w, "n_markets"] >= 10]
        B = seeds_for(f, set(est), T)
        for _, a in A.iterrows():
            cand = B[(B.usd >= 0.7 * a.usd) & (B.usd <= 1.3 * a.usd) & ((B.t - a.t).abs() <= 6 * 3600)] if len(B) else B
            for H in WINDOWS:
                if a.t + H * 60 >= T - EXCL:
                    excluded.append(dict(market_key=m, kind="A", wallet=a.wallet, seed_utc=iso(a.t), H=H, usd=a.usd))
                    continue
                oa = outcomes(f, taker, at, a, H)
                bo = []
                for _, b in cand.iterrows():
                    if b.t + H * 60 >= T - EXCL:
                        excluded.append(dict(market_key=m, kind="B", wallet=b.wallet, seed_utc=iso(b.t), H=H, usd=b.usd))
                        continue
                    bo.append(outcomes(f, taker, at, b, H))
                rows.append(dict(market_key=m, A_wallet=a.wallet, seed_utc=iso(a.t), t=a.t, H=H, usd=a.usd, dir=a.dir,
                                 hours_before_news=(T - a.t) / 3600, n_B=len(bo),
                                 **{f"A_{k}": v for k, v in oa.items()},
                                 **{f"B_{k}": (np.mean([x[k] for x in bo]) if bo else np.nan) for k in oa}))
    R = pd.DataFrame(rows)
    R.to_csv(RES / "v1_layer2_seeds.csv", index=False)
    E = pd.DataFrame(excluded)
    E.to_csv(RES / "v1_layer2_excluded_windows.csv", index=False)
    res = dict(whale_cut_usd=float(whale_cut), n_whales=int((TYPE == "whale").sum()), n_bots=int((TYPE == "bot").sum()),
               n_A_seeds_total=int(R[R.H == 30].shape[0]), excluded_counts=E.groupby(["kind", "H"]).size().rename("n").reset_index().to_dict("records") if len(E) else [],
               tests=[])
    for H in WINDOWS:
        P = R[(R.H == H) & (R.n_B > 0)]
        for k in ["wallets", "usd", "price_move", "whales", "bots", "others"]:
            for scope, Q in [("pooled", P)] + [(m, P[P.market_key == m]) for m in MARKETS]:
                d = (Q[f"A_{k}"] - Q[f"B_{k}"]).values
                dw = (Q.assign(d=Q[f"A_{k}"] - Q[f"B_{k}"]).groupby("A_wallet").d.mean().values) if len(Q) else []
                res["tests"].append(dict(H=H, outcome=k, scope=scope, n_A_seeds=len(Q), n_A_wallets=int(Q.A_wallet.nunique()),
                                         mean_A=float(Q[f"A_{k}"].mean()) if len(Q) else None,
                                         mean_B=float(Q[f"B_{k}"].mean()) if len(Q) else None,
                                         mean_diff=float(d.mean()) if len(d) else None, ci95=boot_ci(d), p_signflip=signflip(d),
                                         wallet_clustered_mean_diff=float(np.mean(dw)) if len(dw) else None,
                                         wallet_clustered_p=signflip(dw)))
        res[f"A_seeds_without_B_H{H}"] = int(((R.H == H) & (R.n_B == 0)).sum())
    dump(res, RES / "v1_layer2.json")
    T_ = pd.DataFrame(res["tests"])
    print(T_[T_.scope == "pooled"].round(3).to_string())
    print(T_[(T_.outcome == "wallets")].round(3).to_string())
    print({k: v for k, v in res.items() if k != "tests"})


if __name__ == "__main__":
    main()
