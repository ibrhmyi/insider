"""Shared feature code for v2 (used for training/validation and, unchanged, for the forward test).
All features are computed from information available at the time of the unit's (wallet x market x side) trades:
account age (join date fixed at signup), size, conviction, time to scheduled end, track record from markets resolved before the first buy."""
import numpy as np, pandas as pd

K_SHRINK = 5.0   # prior excess win rate is multiplied by n/(n+K): n=0 -> 0, n=5 -> half weight, n=45 -> 90% weight
FEATS = ["log_age", "share_event", "log_usd", "log_rel_size", "conviction", "log_hours_to_end", "log_prior_markets", "prior_excess"]

def prior_track(units):
    """units: DataFrame with proxy_wallet, conditionId, res_ts, t_first, excess (won - price paid). Returns n_prior and shrunk prior excess,
    using only the wallet's units in OTHER markets with res_ts < this unit's first buy time."""
    n = np.zeros(len(units)); s = np.zeros(len(units))
    u = units.reset_index(drop=True)
    for w, idx in u.groupby("proxy_wallet").indices.items():
        if len(idx) == 1: continue
        r = u.res_ts.values[idx]; t = u.t_first.values[idx]; ex = u.excess.values[idx]
        order = np.argsort(r); rs = r[order]; cs = np.concatenate([[0], np.cumsum(ex[order])])
        k = np.searchsorted(rs, t, side="left")           # number of markets resolved strictly before first buy
        n[idx] = k; s[idx] = cs[k]
    mean = np.divide(s, n, out=np.zeros_like(s), where=n > 0)
    return n, mean * n / (n + K_SHRINK)

def share_event(buys, units):
    """Share of the wallet's cumulative buy USD (in the dataset, up to the unit's last pre-decision buy) that went into this event's markets."""
    out = np.full(len(units), np.nan)
    ev = units.event_key.values; wl = units.proxy_wallet.values; tl = units.t_last.values; cid = units.conditionId.values
    b = buys.sort_values(["proxy_wallet", "timestamp"])
    grp = b.groupby("proxy_wallet").indices
    bw = b.proxy_wallet.values
    ts = b.timestamp.values; usd = b.usd.values; bev = b.event_key.values
    for i in range(len(units)):
        ix = grp.get(wl[i])
        if ix is None: continue
        m = ts[ix] <= tl[i]
        tot = usd[ix][m].sum()
        out[i] = usd[ix][m & (bev[ix] == ev[i])].sum() / tot if tot > 0 else np.nan
    return out
