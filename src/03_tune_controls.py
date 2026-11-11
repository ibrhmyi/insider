"""Task 4: tune v0 parameters on CONTROL markets only (insider-possible markets are never loaded here).

Placebo calibration: pseudo-seeds = random ordinary (non-seed) trades. If the matched no-seed
baseline is fair, the pseudo-seeds' excess ripple should be ~0. We grid over anchor mode, k and
min_prior_trades and pick the combination whose pooled placebo mean excess (distinct wallets) is
closest to 0 (tie-break: smaller SD). Seed counts at 95/99/99.5 are reported for the chosen setting.
"""
import itertools
import json

import numpy as np
import pandas as pd

import measures as M
from common import AUDIT, DATA, RULES, dump

CONTROLS = ["ctrl_btc110k_jun17", "ctrl_btc94k_jan5", "ctrl_btcupdown_oct14"]
BASE = dict(seed_quantile=0.99, seed_lookback_h=24, ripple_window_min=30, news_buffer_min=30,
            carry_cutoff=0.98, anchor_step_min=5, anchor_min_prior_hour_trades=1, max_anchors=3000)
FEATURE_SETS = {"brief": ["price", "log_cnt_1h"],
                "brief+burst": ["price", "log_cnt_1h", "log_cnt_5m"],
                "brief+burst+expiry": ["price", "log_cnt_1h", "log_cnt_5m", "log_h_to_ref"]}
# Iterations 1-3 (grid/trade x k x min_prior x feature set) are logged in log/process_log.md;
# trade-anchored, brief+burst+expiry, min_prior 20 was best. Iteration 4 adds the time caliper.
GRID = dict(anchor_mode=["trade"], k_matches=[10, 20], min_prior_trades=[20],
            feature_set=["brief+burst+expiry"], time_caliper_h=[0, 12, 6, 2])
N_PLACEBO = 150


def placebo(key, p, rng):
    mk = pd.read_csv(DATA / "markets.csv").set_index("market_key").loc[key]
    df = M.load_trades(key)
    news = M.load_news(key)
    first_news = min(news)
    end_ts = first_news - p["news_buffer_min"] * 60
    seeds = M.find_seeds(df, p)
    start = df["timestamp"].min()
    pool = df[(df["timestamp"] >= start) & (df["timestamp"] <= end_ts - 1800) & (~df.index.isin(seeds.index))]
    pool = pool[pool["timestamp"].diff().fillna(1) >= 0]
    ps = pool.sample(min(N_PLACEBO, len(pool)), random_state=rng).copy()
    ps["threshold_usd"] = np.nan
    # placebo trades are removed from the anchor pool too (cannot match themselves)
    # placebo trades are removed from the anchor pool (cannot match themselves) but, unlike real
    # seeds, do not blank out +-window around them (bug found in iteration 2, fixed in iteration 3)
    anchors = M.candidate_anchors(df, seeds, p, news, end_ts, exclude_idx=set(ps.index))
    rt = M.ripple_table(df, ps, anchors, p, news, first_news)
    if not len(rt):
        return pd.DataFrame(columns=["excess_wallets"]), len(seeds)
    return rt[~rt["news_overlap_excluded"]], len(seeds)


def main():
    res = []
    for combo in itertools.product(*GRID.values()):
        p = dict(BASE, **dict(zip(GRID.keys(), combo)))
        p["match_features"] = FEATURE_SETS[p["feature_set"]]
        ex = []
        for key in CONTROLS:
            rt, ns = placebo(key, p, rng=7)
            ex.append(rt[["excess_wallets", "log_ratio_wallets"]].dropna() if len(rt) else pd.DataFrame(columns=["excess_wallets", "log_ratio_wallets"]))
        E = pd.concat(ex); e = E["excess_wallets"]
        res.append(dict(**dict(zip(GRID.keys(), combo)), placebo_n=len(e), placebo_mean_excess_wallets=round(e.mean(), 3),
                        placebo_sd=round(e.std(), 3), placebo_median=round(e.median(), 3),
                        placebo_mean_log_ratio=round(E["log_ratio_wallets"].mean(), 3)))
        print({k: (round(float(v), 2) if isinstance(v, (float, np.floating)) else v) for k, v in res[-1].items()}, flush=True)
    tab = pd.DataFrame(res)
    tab["abs_mean"] = tab["placebo_mean_excess_wallets"].abs()
    best = tab.sort_values(["abs_mean", "placebo_sd"]).iloc[0]
    tab.drop(columns="abs_mean").to_csv(AUDIT / "tuning_grid_controls.csv", index=False)
    chosen = dict(BASE, anchor_mode=best["anchor_mode"], k_matches=int(best["k_matches"]),
                  min_prior_trades=int(best["min_prior_trades"]), feature_set=best["feature_set"],
                  time_caliper_h=int(best["time_caliper_h"]),
                  match_features=FEATURE_SETS[best["feature_set"]])

    # seed counts + real-seed ripple on controls at 95 / 99 / 99.5 (chosen params)
    rows, ctrl_rt = [], []
    for q in [0.95, 0.99, 0.995]:
        for key in CONTROLS:
            news = M.load_news(key)
            df, seeds, anchors, rt = M.run_market(key, chosen, min(news) - 1800, first_news=min(news), q=q)
            kept = rt[(~rt["news_overlap_excluded"]) & (rt["phase"] == "pre-news")] if len(rt) else rt
            rows.append(dict(quantile=q, market_key=key, n_trades=len(df), n_seeds=len(seeds),
                             n_news_excluded=int(rt["news_overlap_excluded"].sum()) if len(rt) else 0,
                             n_used=len(kept), n_anchors=len(anchors),
                             mean_obs_wallets=round(kept["obs_wallets"].mean(), 2) if len(kept) else np.nan,
                             mean_exp_wallets=round(kept["exp_wallets"].mean(), 2) if len(kept) else np.nan,
                             mean_excess_wallets=round(kept["excess_wallets"].mean(), 2) if len(kept) else np.nan))
            if q == chosen["seed_quantile"]:
                ctrl_rt.append(kept)
    seedtab = pd.DataFrame(rows)
    seedtab.to_csv(AUDIT / "tuning_seed_counts_controls.csv", index=False)
    print(seedtab.to_string())
    c = pd.concat(ctrl_rt)
    chosen["alert_threshold_excess_wallets"] = float(np.nanpercentile(c["excess_wallets"], 95))
    chosen["alert_threshold_basis"] = f"95th percentile of control excess_wallets at q={chosen['seed_quantile']} (n={c['excess_wallets'].notna().sum()} control seeds)"
    dump(dict(chosen=chosen, best_row=best.to_dict()), AUDIT / "tuning_result.json")
    print("CHOSEN", chosen)


if __name__ == "__main__":
    main()
