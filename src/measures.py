"""Version-0 measures: seed trades, ripple, matched no-seed baseline, news exclusion.

Pure functions; all parameters come in through a `params` dict so the frozen
definition (rules/frozen_v0.json) is the single source of truth for the final run.
"""
import numpy as np
import pandas as pd

from common import CLEAN, DATA

HOUR = 3600


def load_trades(key):
    df = pd.read_csv(CLEAN / f"trades_{key}.csv", dtype={"token_id": str})
    # direction in YES-exposure terms: BUY Yes / SELL No = +1 ; SELL Yes / BUY No = -1
    yes_tok = df["outcome_index"] == 0
    buy = df["side"] == "BUY"
    df["direction"] = np.where(yes_tok == buy, 1, -1)
    df["yes_price"] = np.where(yes_tok, df["price"], 1 - df["price"])
    df["notional"] = df["size"] * df["price"]
    return df.sort_values("timestamp", kind="stable").reset_index(drop=True)


def load_news(key):
    n = pd.read_csv(DATA / "news_events.csv")
    return n.loc[n["market_key"] == key, "news_epoch"].astype(int).tolist()


def rolling_threshold(df, q, lookback_s, min_prior):
    """Per trade: q-quantile of notional over trades in [t - lookback, t) (strictly prior).
    NaN when fewer than min_prior prior trades."""
    t = df["timestamp"].values
    x = df["notional"].values
    lo = np.searchsorted(t, t - lookback_s, side="left")
    hi = np.searchsorted(t, t, side="left")  # strictly before t (same-second trades excluded)
    thr = np.full(len(df), np.nan)
    for i in range(len(df)):
        if hi[i] - lo[i] >= min_prior:
            thr[i] = np.quantile(x[lo[i]:hi[i]], q)
    return thr


def window_stats(df, t0, direction, win_s, exclude_wallet=None):
    """Same-direction activity in (t0, t0+win]: distinct wallets, trade count, USD volume."""
    t = df["timestamp"].values
    a = np.searchsorted(t, t0, side="right")
    b = np.searchsorted(t, t0 + win_s, side="right")
    w = df.iloc[a:b]
    w = w[w["direction"] == direction]
    if exclude_wallet is not None:
        w = w[w["proxy_wallet"] != exclude_wallet]
    return w["proxy_wallet"].nunique(), len(w), float(w["notional"].sum())


def pre_features(df, t0, ref_ts):
    """Matching features observable at t0 (nothing after t0 is used):
    price      last YES price at or before t0
    log_cnt_1h log(1 + trades in previous hour)        (trading intensity, per the brief)
    log_cnt_5m log(1 + trades in previous 5 minutes)   (added in tuning iteration 2: burstiness)
    log_h_to_ref log(1 + hours until the reference/news time) (added in iteration 2: expiry ramp)"""
    t = df["timestamp"].values
    b = np.searchsorted(t, t0, side="right")
    a1 = np.searchsorted(t, t0 - HOUR, side="left")
    a5 = np.searchsorted(t, t0 - 300, side="left")
    return dict(price=df["yes_price"].values[b - 1] if b > 0 else np.nan,
                cnt_1h=int(b - a1),
                log_cnt_1h=np.log1p(b - a1), log_cnt_5m=np.log1p(b - a5),
                log_h_to_ref=np.log1p(max(ref_ts - t0, 0) / HOUR))


def overlaps_news(t0, win_s, news, buf_s):
    return any((t0 <= n + buf_s) and (t0 + win_s >= n - buf_s) for n in news)


def find_seeds(df, p, q=None):
    q = p["seed_quantile"] if q is None else q
    thr = rolling_threshold(df, q, p["seed_lookback_h"] * HOUR, p["min_prior_trades"])
    ok = (~np.isnan(thr)) & (df["notional"].values > thr) & (~df["after_resolution"].values)
    # exclude "carry" trades: betting on the side the market already prices above carry_cutoff
    yp, d = df["yes_price"].values, df["direction"].values
    carry = ((d == 1) & (yp > p["carry_cutoff"])) | ((d == -1) & (yp < 1 - p["carry_cutoff"]))
    ok &= ~carry
    s = df.loc[ok].copy()
    s["threshold_usd"] = thr[ok]
    # collapse: one seed per (wallet, direction) within the ripple window (split orders)
    s = s.sort_values("timestamp")
    keep, last = [], {}
    for i, r in s.iterrows():
        k = (r["proxy_wallet"], r["direction"])
        if k in last and r["timestamp"] - last[k] <= p["ripple_window_min"] * 60:
            continue
        last[k] = r["timestamp"]
        keep.append(i)
    return s.loc[keep]


def candidate_anchors(df, seeds, p, news, end_ts, rng_seed=0, exclude_idx=None):
    """No-seed baseline anchors.
    mode 'grid' : regular clock grid.
    mode 'trade': ordinary (non-seed) trades; the anchoring trade's wallet is excluded from its window,
                  mirroring how the seed wallet is excluded from the seed window."""
    win = p["ripple_window_min"] * 60
    start = df["timestamp"].min()  # threshold itself needs min_prior_trades of history
    if p["anchor_mode"] == "grid":
        cand = [(a, None) for a in np.arange(start, end_ts - win, p["anchor_step_min"] * 60)]
    else:
        seed_idx = set(seeds.index)
        pool = df[(df["timestamp"] >= start) & (df["timestamp"] <= end_ts - win) & (~df["after_resolution"])]
        pool = pool[~pool.index.isin(seed_idx)]
        if exclude_idx is not None:  # placebo trades: removed as anchors, but do not blank out windows
            pool = pool[~pool.index.isin(exclude_idx)]
        if len(pool) > p["max_anchors"]:
            pool = pool.sample(p["max_anchors"], random_state=rng_seed)
        cand = list(zip(pool["timestamp"].values, pool["proxy_wallet"].values))
    st = np.sort(seeds["timestamp"].values) if len(seeds) else np.array([])
    out = []
    for a, w in cand:
        if len(st):
            j = np.searchsorted(st, a - win)
            if j < len(st) and st[j] <= a + win:
                continue  # a seed within +-window: not a no-seed window
        if overlaps_news(a, win, news, p["news_buffer_min"] * 60):
            continue
        f = pre_features(df, a - 1, min(news))
        if np.isnan(f["price"]) or f["cnt_1h"] < p["anchor_min_prior_hour_trades"]:
            continue
        out.append(dict(t=int(a), wallet=w, **f))
    return pd.DataFrame(out, columns=["t", "wallet", "price", "cnt_1h", "log_cnt_1h", "log_cnt_5m", "log_h_to_ref"])


def ripple_table(df, seeds, anchors, p, news, first_news=None):
    """Observed vs expected ripple for each seed."""
    win = p["ripple_window_min"] * 60
    rows = []
    feats = p["match_features"]
    if len(anchors):
        A = anchors[feats].values.astype(float)
        sd = np.maximum(A.std(axis=0), 1e-3)
    for _, s in seeds.iterrows():
        t0, d = int(s["timestamp"]), int(s["direction"])
        obs_w, obs_n, obs_v = window_stats(df, t0, d, win, exclude_wallet=s["proxy_wallet"])
        f = pre_features(df, t0 - 1, min(news))
        price, cnt = f["price"], f["cnt_1h"]
        exp_w = exp_n = exp_v = np.nan
        n_match = 0
        if len(anchors):
            x = np.array([f[k] for k in feats], dtype=float)
            dist = np.sqrt((((A - x) / sd) ** 2).sum(axis=1))
            if p.get("time_caliper_h"):  # local baseline: only anchors within +-caliper of the seed
                dist = np.where(np.abs(anchors["t"].values - t0) <= p["time_caliper_h"] * HOUR, dist, np.inf)
            idx = [i for i in np.argsort(dist)[: p["k_matches"]] if np.isfinite(dist[i])]
            m = [window_stats(df, int(anchors["t"].values[i]), d, win, exclude_wallet=anchors["wallet"].values[i])
                 for i in idx]
            if m:
                exp_w, exp_n, exp_v = (float(np.mean([x[j] for x in m])) for j in range(3))
            n_match = len(idx)
        excl = overlaps_news(t0, win, news, p["news_buffer_min"] * 60)
        phase = "pre-news"
        if first_news is not None and t0 > first_news - p["news_buffer_min"] * 60:
            phase = "post-news"
        rows.append(dict(timestamp=t0, wallet=s["proxy_wallet"], direction=d, notional=s["notional"],
                         threshold_usd=s["threshold_usd"], yes_price=s["yes_price"], outcome=s["outcome"],
                         side=s["side"], pre_hour_trades=cnt, pre_price=price,
                         obs_wallets=obs_w, obs_trades=obs_n, obs_volume=obs_v,
                         exp_wallets=exp_w, exp_trades=exp_n, exp_volume=exp_v, n_matches=n_match,
                         excess_wallets=obs_w - exp_w, log_ratio_wallets=np.log1p(obs_w) - np.log1p(exp_w), excess_trades=obs_n - exp_n, excess_volume=obs_v - exp_v,
                         news_overlap_excluded=excl, phase=phase))
    return pd.DataFrame(rows)


def run_market(key, p, end_ts, first_news=None, q=None):
    df = load_trades(key)
    news = load_news(key)
    seeds = find_seeds(df, p, q)
    anchors = candidate_anchors(df, seeds, p, news, end_ts)
    rt = ripple_table(df, seeds, anchors, p, news, first_news)
    if len(rt):
        rt.insert(0, "market_key", key)
    return df, seeds, anchors, rt
