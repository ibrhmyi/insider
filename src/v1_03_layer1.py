"""v1 Layer 1: wallet x market suspicion screen, permutation null, validation, precision proxy, price impact.
Implements rules/frozen_v1.md exactly (thresholds read from the FLAGS dict below, copied from the frozen file).
Outputs: data/results/v1_wallet_scores.csv, data/results/v1_layer1.json, data/results/v1_validation.csv
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from common import CLEAN, DATA, dump, iso

RES = DATA / "results"
MARKETS = ["iran", "maduro", "nobel"]
MK = pd.read_csv(DATA / "markets.csv").set_index("market_key")
NEWS = pd.read_csv(DATA / "news_events.csv")
T_NEWS = {k: int(NEWS[NEWS.market_key == k].news_epoch.min()) for k in MARKETS}
WIN_IDX = {k: (0 if MK.loc[k, "resolution"] == MK.loc[k, "outcome_0"] else 1) for k in MARKETS}
FLAGS = dict(F1_days=7, F2_share=0.8, F2_markets=2, F3_price=0.35, F4_usd=2500, F5_conv=0.8, F6_hours=72, HIGH=4)
N_PERM = 1000
ST = pd.read_csv(CLEAN / "v1_wallet_stats.csv").set_index("wallet")
WN = pd.read_csv(CLEAN / "v1_wallet_windows.csv").set_index(["market_key", "wallet"])


def load(m):
    f = pd.read_csv(CLEAN / f"v1_fills_{m}.csv").sort_values("timestamp", kind="stable").reset_index(drop=True)
    yes = f.outcome_index == 0
    f["dir"] = np.where(yes == (f.side == "BUY"), 1, -1)
    f["yes_price"] = np.where(yes, f.price, 1 - f.price)
    f["usd"] = f["size"] * f["price"]
    return f


def price_path(f):
    t = f.timestamp.values
    p = f.yes_price.values
    def at(x, strict=False):
        i = np.searchsorted(t, x, side="left" if strict else "right") - 1
        return np.where(i >= 0, p[np.clip(i, 0, None)], np.nan)
    return at


def wmedian_time(t, w):
    o = np.argsort(t)
    c = np.cumsum(w[o])
    return t[o][np.searchsorted(c, c[-1] / 2)]


def features(m, f, upto=None):
    """Per-wallet features from pre-news fills (optionally only fills <= upto[wallet])."""
    T = T_NEWS[m]
    pre = f[(f.timestamp < T) & (~f.after_resolution)]
    buyers = set(pre[pre.side == "BUY"].proxy_wallet)
    pre = pre[pre.proxy_wallet.isin(buyers)]
    rows = []
    for w, g in pre.groupby("proxy_wallet", sort=False):
        if upto is not None:
            g = g[g.timestamp <= upto[w]]
        b = g[g.side == "BUY"]
        if not len(b):
            continue
        by_tok = b.groupby("outcome_index").usd.sum()
        main = int(by_tok.idxmax())
        bm = b[b.outcome_index == main]
        st = ST.loc[w] if w in ST.index else None
        wn = WN.loc[(m, w)] if (m, w) in WN.index else None
        join = st["join_date"] if st is not None else np.nan
        first_m = g.timestamp.min()
        if pd.isna(join):
            cand = [first_m] + ([wn["first_activity_ts"]] if wn is not None and pd.notna(wn["first_activity_ts"]) else [])
            acct = min(cand)
            acct_src = "first_activity" if len(cand) > 1 and acct < first_m else "first_fill_in_market"
        else:
            acct, acct_src = join, "join_date"
        f1 = max(first_m - acct, 0) / 86400
        denom = wn["vol_to_tnews_usdc"] if wn is not None else np.nan
        share = min(g.usd.sum() / denom, 1.0) if pd.notna(denom) and denom > 0 else np.nan
        nmk = st["n_markets"] if st is not None else np.nan
        vwap = bm.usd.sum() / bm["size"].sum()
        buy_usd = b.usd.sum()
        conv = abs((g.dir * g.usd).sum()) / g.usd.sum()
        tmed = wmedian_time(bm.timestamp.values, bm.usd.values)
        hrs = (T - tmed) / 3600
        fl = dict(F1=f1 <= FLAGS["F1_days"],
                  F2=(pd.notna(share) and share >= FLAGS["F2_share"]) or (pd.notna(nmk) and nmk <= FLAGS["F2_markets"]),
                  F3=vwap <= FLAGS["F3_price"], F4=buy_usd >= FLAGS["F4_usd"], F5=conv >= FLAGS["F5_conv"],
                  F6=hrs <= FLAGS["F6_hours"])
        rows.append(dict(market_key=m, wallet=w, main_outcome=bm.outcome.iloc[0], main_outcome_index=main,
                         n_pre_fills=len(g), n_pre_buys=len(b), first_fill_utc=iso(first_m),
                         account_start_utc=iso(acct), account_start_source=acct_src,
                         F1_days=round(f1, 3), F2_share=share, F2_n_markets=nmk, F3_vwap=round(vwap, 4),
                         F4_buy_usd=round(buy_usd, 2), F5_conviction=round(conv, 4), F6_hours_before_news=round(hrs, 2),
                         **{f"flag_{k}": bool(v) for k, v in fl.items()}, score=int(sum(fl.values())),
                         flags_fired=",".join(k for k, v in fl.items() if v)))
    return pd.DataFrame(rows)


def post_hoc(m, S):
    S["F7_correct"] = S.main_outcome_index == WIN_IDX[m]
    pc = [WN.loc[(m, w), "post30_trade_count"] if (m, w) in WN.index else np.nan for w in S.wallet]
    S["F8_post30_trades"] = pc
    S["F8_dormant"] = pd.Series([np.nan if pd.isna(x) else float(x == 0) for x in pc], dtype=float).values
    return S


def price_impact(m, f, S):
    at = price_path(f)
    T = T_NEWS[m]
    b = f[(f.side == "BUY") & (f.role == "taker") & (f.timestamp < T)].copy()
    b["dsgn"] = np.where(b.outcome_index == 0, 1, -1)
    p0 = at(b.timestamp.values, strict=True)
    for h, lab in [(300, "5m"), (3600, "60m")]:
        ok = b.timestamp.values + h <= T  # window must end before news
        ph = at(b.timestamp.values + h)
        b[f"imp_{lab}"] = np.where(ok, b.dsgn * (ph - p0) / b.usd * 1000, np.nan)
    agg = b.groupby("proxy_wallet")[["imp_5m", "imp_60m"]].median()
    S = S.merge(agg.rename(columns=dict(imp_5m="impact_5m_per_1k", imp_60m="impact_60m_per_1k")),
                left_on="wallet", right_index=True, how="left")
    return S


def permutation(m, f, S, rng):
    """Timestamp permutation null (frozen v1): redraw each pre-news BUY fill time from the market's pre-news fill-time distribution."""
    T = T_NEWS[m]
    at = price_path(f)
    pre = f[(f.timestamp < T) & (~f.after_resolution)]
    pool_t = pre.timestamp.values
    pool_yes = at(pool_t)
    S = S.set_index("wallet")
    b = pre[(pre.side == "BUY") & pre.proxy_wallet.isin(S.index)].copy()
    b = b[b.outcome_index.values == S.loc[b.proxy_wallet, "main_outcome_index"].values]  # main-side buys (F3, F6)
    allb = pre[(pre.side == "BUY") & pre.proxy_wallet.isin(S.index)]
    wid = {w: i for i, w in enumerate(S.index)}
    bw = b.proxy_wallet.map(wid).values
    aw = allb.proxy_wallet.map(wid).values
    shares, usd, yes_tok = b["size"].values, b.usd.values, (b.outcome_index.values == 0)
    nW = len(S)
    acct = np.array([pd.Timestamp(x).timestamp() for x in S.account_start_utc])
    sells = pre[(pre.side == "SELL") & pre.proxy_wallet.isin(S.index)]
    sell_first = np.full(nW, np.inf)
    np.minimum.at(sell_first, sells.proxy_wallet.map(wid).values, sells.timestamp.values.astype(float))
    fixed = (S.flag_F2.values.astype(int) + S.flag_F4.values.astype(int) + S.flag_F5.values.astype(int))
    null = np.empty(N_PERM, dtype=int)
    for k in range(N_PERM):
        ia = rng.integers(0, len(pool_t), len(allb))
        first = sell_first.copy()  # sells keep their real times; buys are redrawn
        np.minimum.at(first, aw, pool_t[ia].astype(float))
        f1 = (np.maximum(first - acct, 0) / 86400) <= FLAGS["F1_days"]
        ib = rng.integers(0, len(pool_t), len(b))
        tb = pool_t[ib]
        pr = np.where(yes_tok, pool_yes[ib], 1 - pool_yes[ib])
        num = np.bincount(bw, shares * pr, nW)
        den = np.bincount(bw, shares, nW)
        f3 = np.divide(num, den, out=np.ones(nW), where=den > 0) <= FLAGS["F3_price"]
        # USD-weighted median time per wallet
        o = np.lexsort((tb, bw))
        w_s, t_s, u_s = bw[o], tb[o], usd[o]
        cs = np.cumsum(u_s)
        start = np.searchsorted(w_s, np.arange(nW), "left")
        end = np.searchsorted(w_s, np.arange(nW), "right")
        base = np.where(start > 0, cs[np.maximum(start - 1, 0)], 0.0)
        tot = np.where(end > start, cs[np.maximum(end - 1, 0)] - base, 0.0)
        tmed = np.full(nW, -np.inf)
        for i in np.nonzero(end > start)[0]:
            j = start[i] + np.searchsorted(cs[start[i]:end[i]] - base[i], tot[i] / 2)
            tmed[i] = t_s[min(j, end[i] - 1)]
        f6 = ((T - tmed) / 3600) <= FLAGS["F6_hours"]
        score = fixed + f1 + f3 + f6
        null[k] = int((score >= FLAGS["HIGH"]).sum())
    return null


def hours_early(m, f, S, wallets):
    """First own buy time at which the wallet's cumulative features reach score >= 4 (retrospective; F6 uses T_news)."""
    T = T_NEWS[m]
    pre = f[(f.timestamp < T) & (~f.after_resolution)]
    out = {}
    for w in wallets:
        times = sorted(set(pre[(pre.proxy_wallet == w) & (pre.side == "BUY")].timestamp))
        hit = None
        for t in times:
            r = features(m, pre[pre.proxy_wallet == w], upto={w: t})
            if len(r) and r.score.iloc[0] >= FLAGS["HIGH"]:
                hit = t
                break
        out[w] = (T - hit) / 3600 if hit is not None else np.nan
    return out


def main():
    rng = np.random.default_rng(20261111)
    allS, perm_rows = [], []
    for m in MARKETS:
        f = load(m)
        S = features(m, f)
        S = post_hoc(m, S)
        S = price_impact(m, f, S)
        null = permutation(m, f, S, rng)
        obs = int((S.score >= FLAGS["HIGH"]).sum())
        perm_rows.append(dict(market_key=m, n_wallets=len(S), observed_high=obs, null_mean=float(null.mean()),
                              null_p95=float(np.percentile(null, 95)), null_min=int(null.min()), null_max=int(null.max()),
                              p_value=float((1 + (null >= obs).sum()) / (1 + N_PERM)),
                              pre_news_buy_fills=int(((f.timestamp < T_NEWS[m]) & (f.side == "BUY")).sum()),
                              pre_news_buy_fills_last6h=int(((f.timestamp < T_NEWS[m]) & (f.timestamp >= T_NEWS[m] - 6 * 3600) & (f.side == "BUY")).sum())))
        np.save(RES / f"v1_perm_null_{m}.npy", null)
        print(perm_rows[-1], flush=True)
        allS.append(S)
    S = pd.concat(allS, ignore_index=True)

    # sensitivity on F4 threshold
    sens = []
    for thr in [1000, 2500, 10000]:
        sc = S.score - S.flag_F4.astype(int) + (S.F4_buy_usd >= thr).astype(int)
        sens.append(dict(F4_threshold=thr, **{m: int((sc[S.market_key == m] >= FLAGS["HIGH"]).sum()) for m in MARKETS}))
        S[f"score_F4_{thr}"] = sc

    # ranks
    S = S.sort_values(["market_key", "score", "F4_buy_usd"], ascending=[True, False, False])
    S["rank_in_market"] = S.groupby("market_key").cumcount() + 1
    S["n_in_market"] = S.groupby("market_key").wallet.transform("size")
    S["is_high"] = S.score >= FLAGS["HIGH"]

    # validation
    L = pd.read_csv(DATA / "labels" / "documented_wallets_matched.csv")
    val = []
    early_cache = {}
    for _, r in L.iterrows():
        row = S[(S.market_key == r.market_key) & (S.wallet == r.matched_wallet)]
        if not len(row):
            val.append(dict(label_id=r.label_id, identifier=r.identifier, confidence=r.confidence, market_key=r.market_key,
                            wallet=r.matched_wallet, in_population=False))
            continue
        x = row.iloc[0]
        key = (r.market_key, r.matched_wallet)
        if key not in early_cache:
            early_cache[key] = hours_early(r.market_key, load(r.market_key), S, [r.matched_wallet])[r.matched_wallet]
        val.append(dict(label_id=r.label_id, identifier=r.identifier, confidence=r.confidence, market_key=r.market_key,
                        wallet=r.matched_wallet, in_population=True, score=int(x.score), flags_fired=x.flags_fired,
                        rank=int(x.rank_in_market), n_in_market=int(x.n_in_market),
                        percentile_rank=round(100 * (1 - (x.rank_in_market - 1) / x.n_in_market), 2),
                        high=bool(x.is_high), hours_before_news_first_high=early_cache[key],
                        F4_buy_usd=x.F4_buy_usd, F3_vwap=x.F3_vwap, F6_hours=x.F6_hours_before_news,
                        F1_days=x.F1_days, F2_share=x.F2_share, F2_markets=x.F2_n_markets, F5_conv=x.F5_conviction,
                        F7_correct=bool(x.F7_correct), F8_dormant=x.F8_dormant,
                        **{f"score_F4_{t}": int(x[f"score_F4_{t}"]) for t in [1000, 2500, 10000]}))
    V = pd.DataFrame(val)
    V.to_csv(RES / "v1_validation.csv", index=False)
    # hours-early for every high-score wallet (for timelines)
    he = []
    for m in MARKETS:
        hw = S[(S.market_key == m) & S.is_high].wallet.tolist()
        hm = hours_early(m, load(m), S, hw) if hw else {}
        he += [dict(market_key=m, wallet=w, hours_before_news_first_high=v) for w, v in hm.items()]
    S = S.merge(pd.DataFrame(he, columns=["market_key", "wallet", "hours_before_news_first_high"]), how="left", on=["market_key", "wallet"])
    S.to_csv(RES / "v1_wallet_scores.csv", index=False)

    # precision proxy: F7 / F8 by high vs other within F4 size bands
    bands = pd.cut(S.F4_buy_usd, [0, 1000, 2500, 10000, np.inf], right=False, labels=["<1k", "1k-2.5k", "2.5k-10k", ">=10k"])
    S["size_band"] = bands
    prec = (S.groupby(["size_band", "is_high"], observed=True)
              .agg(n=("wallet", "size"), win_rate=("F7_correct", "mean"),
                   dormant_rate=("F8_dormant", lambda s: pd.to_numeric(s, errors="coerce").mean()),
                   n_dormant_known=("F8_dormant", lambda s: pd.to_numeric(s, errors="coerce").notna().sum()))
              .round(3).reset_index())
    # price impact comparison
    imp = {}
    for col in ["impact_5m_per_1k", "impact_60m_per_1k"]:
        a = S.loc[S.is_high, col].dropna(); o = S.loc[~S.is_high, col].dropna()
        # size-matched comparison: others with F4 >= $2,500 (high-score wallets mostly pass F4)
        o2 = S.loc[(~S.is_high) & (S.F4_buy_usd >= 2500), col].dropna()
        imp[col] = dict(high_n=len(a), high_median=float(a.median()) if len(a) else None,
                        other_n=len(o), other_median=float(o.median()) if len(o) else None,
                        p_mwu=float(mannwhitneyu(a, o).pvalue) if len(a) and len(o) else None,
                        other_ge2500_n=len(o2), other_ge2500_median=float(o2.median()) if len(o2) else None,
                        p_mwu_vs_ge2500=float(mannwhitneyu(a, o2).pvalue) if len(a) and len(o2) else None)
    dump(dict(flags=FLAGS, permutation=perm_rows, sensitivity=sens, precision=prec.to_dict("records"),
              impact=imp, score_dist={m: S[S.market_key == m].score.value_counts().sort_index().to_dict() for m in MARKETS}),
         RES / "v1_layer1.json")
    print(pd.DataFrame(perm_rows).to_string()); print(pd.DataFrame(sens).to_string())
    print(V.to_string()); print(prec.to_string()); print(json.dumps(imp, indent=1))


if __name__ == "__main__":
    main()
