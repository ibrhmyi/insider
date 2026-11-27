"""PMITC v1.1 benchmark tasks (PROTOCOL A15, A23). Runs on the released files only (../data).
  python3 pmitc_bench.py [--data ../data] [--out baselines.json] [--quick]
Folds: leave-one-case-out over cases with >= 3 label_standard wallets in the task's rows, plus the A15 time split (splits.csv).
Label sets: label_strict, label_standard, label_broad (A20). Documented wallets outside the set are dropped from that run.
Baselines: prevalence, Gate 1 rule, account-age heuristic, logistic regression; gradient boosting with case-grouped tuning (precise only).
Seed 192.
"""
import argparse, itertools, json, os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
SEED = 192
SETS = ["label_strict", "label_standard", "label_broad"]
GRID = [dict(max_depth=d, learning_rate=lr, max_iter=it, l2_regularization=l2) for d, lr, it, l2 in itertools.product([3, None], [0.05, 0.1], [100, 300], [0.0, 1.0])]
T1_FEATURES = ["log_buy_usdc_pre", "vwap_price_usdc_pre", "first_buy_price_usdc", "max_buy_price_usdc", "log_n_buy_fills_pre", "taker_share_pre",
               "log_account_age_days", "log_market_usdc_pre", "f2_share", "log_n_lifetime_markets", "f5_conviction_ratio", "f6_hours_median_buy_to_tnews",
               "gate1_score", "gate2a_int", "sell_share_pre", "hours_first_buy_to_cut", "hours_last_buy_to_cut"]
T2_FEATURES = ["account_age_days_at_first_buy", "n_prior_markets", "prior_net_long_win_rate", "first_price_usdc", "vwap_price_usdc", "max_price_paid_usdc",
               "n_buy_fills", "median_fill_usdc", "fill_size_cv_ratio", "taker_share", "hour_of_day_first_buy", "pre_buy_usdc", "signal_a_rebuy_1_5x",
               "size_price_slope_usdc", "hours_last_buy_to_tnews", "ladder_rank", "hours_first_buy_to_tnews"]
T3_FEATURES = ["log_usdc_48h", "log_usdc_24h", "log_usdc_1h", "usdc_share_last_6h", "log_n_wallets_48h", "new_wallet_share_48h", "price_change_24h",
               "price_change_6h", "price_change_1h", "abs_max_minute_move_24h", "taker_buy_share_24h", "log_n_buyers", "top10_buy_share",
               "fresh_buyer_share", "gate1_rate", "longshot_buy_share"]
LEAKAGE = dict(
    T1=["is_documented", "doc_grade", "label_*", "hard_negative*", "coordinated_rule_fired", "triggering_suspect", "placebo_rate", "is_control", "is_placebo_market",
        "is_twin_market", "gate1 (a label)", "gate2b and is_shortest_sufficient (use the resolution)", "every _post column", "ids", "absolute times (t_cut_unix,"
        " first_buy_unix, last_buy_unix) except as differences to the cut", "source_pre", "vol_to_day_usdc (includes the rest of the cut's day)"],
    T2=["share_on_this_ladder_market (construction artifact: controls are drawn one market at a time, so it is 1 for them; AUC 0.97 alone)", "role", "episode_id",
        "control_of", "wallet", "label_*", "case_share_of_lifetime_volume (lifetime denominator)", "is_shortest_sufficient",
        "n_follower_wallets_60m / follower_buy_usdc_60m (window can pass t_news)", "every _post column", "the empty funding columns"],
    T3=["market_set / is_placebo_market / is_twin_market (the label)", "any minute at or after the cut", "_post columns", "placebo_category, category_refined",
        "resolution, outcome and volume fields (total volume includes post-cut trading)", "question / slug text"])
SHORTCUTS = {
    "T2.share_on_this_ladder_market": "controls are sampled one market at a time, so the value is always 1 for a control (excluded)",
    "T2.hours_first_buy_to_tnews": "controls are matched on first-buy time within 24-72 h, so this cannot separate classes much (kept; check its univariate AUC)",
    "T3b.*": "placebo markets are crypto-price and weather markets: volume shape, price path and buyer mix differ by market type, not by informed trading",
    "T3.log_usdc_*": "twins are matched on total volume decile, so total volume is controlled only coarsely; pre-cut volume can still differ by market age",
}


def prep_t1(p):
    p = p.copy()
    p["log_buy_usdc_pre"] = np.log1p(p.buy_usdc_pre); p["log_n_buy_fills_pre"] = np.log1p(p.n_buy_fills_pre)
    p["log_account_age_days"] = np.log1p(p.account_age_days_at_first_buy.clip(lower=0)); p["log_market_usdc_pre"] = np.log1p(p.market_usdc_pre)
    p["log_n_lifetime_markets"] = np.log1p(p.n_lifetime_markets_v1); p["gate2a_int"] = p.gate2a.astype(float)
    p["sell_share_pre"] = p.sell_shares_pre / p.buy_shares_pre
    p["hours_first_buy_to_cut"] = (p.t_cut_unix - p.first_buy_unix) / 3600; p["hours_last_buy_to_cut"] = (p.t_cut_unix - p.last_buy_unix) / 3600
    return p


def lr_model():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=1.0, max_iter=2000, random_state=SEED))


def subsample(df, n_neg, rng):
    neg = df.index[df.y == 0]
    keep = neg if len(neg) <= n_neg else rng.choice(neg, n_neg, replace=False)
    return df.loc[df.index[df.y == 1].union(pd.Index(keep))]


def tuned_gb(train, feats, score_fn, rng, n_neg):
    """Inner leave-cases-out (3 groups) over GRID; returns the model refit on all training cases with the best parameters."""
    cases = train.case_id.unique()
    if len(cases) < 3:
        best = GRID[0]
    else:
        res = []
        for g in GRID:
            s = []
            for a, b in GroupKFold(3).split(train, train.y, train.case_id):
                tr = subsample(train.iloc[a], n_neg, rng); te = train.iloc[b]
                if te.y.nunique() < 2:
                    continue
                m = HistGradientBoostingClassifier(random_state=SEED, **g).fit(tr[feats], tr.y)
                s.append(score_fn(te.assign(score=m.predict_proba(te[feats])[:, 1])))
            res.append((np.nanmean(s) if s else -1, g))
        best = max(res, key=lambda x: x[0])[1]
    tr = subsample(train, n_neg, rng)
    return HistGradientBoostingClassifier(random_state=SEED, **best).fit(tr[feats], tr.y), best


def market_ap(df):
    """T1 metric for one test set: per-market AP / P@10 / R@10 / R@100, averaged per case, then over cases (case-weighted)."""
    out = []
    for (case, cid), g in df.groupby(["case_id", "condition_id"]):
        y = g.y.values
        if y.sum() == 0:
            continue
        o = np.argsort(-g.score.values, kind="stable"); ys = y[o]
        out.append(dict(case_id=case, ap=average_precision_score(y, g.score.values), p10=ys[:10].sum() / min(10, len(y)), r10=ys[:10].sum() / y.sum(), r100=ys[:100].sum() / y.sum()))
    if not out:
        return dict(ap=np.nan)
    m = pd.DataFrame(out).groupby("case_id").mean(numeric_only=True)
    return {k: float(v) for k, v in m.mean().items()}


def auc_cw(df):
    """case-weighted AUC: per case with both classes, then mean."""
    v = [roc_auc_score(g.y, g.score) for _, g in df.groupby("case_id") if g.y.nunique() == 2]
    return float(np.mean(v)) if v else np.nan


def folds_for(df, std_counts):
    loco = sorted([c for c, n in std_counts.items() if n >= 3])
    f = [("loco:" + c, df.case_id != c, df.case_id == c) for c in loco]
    f.append(("time_split", df.split == "train", df.split == "test"))
    return f


def summarise(per_fold):
    out = {}
    for model in sorted({m for f in per_fold.values() for m in f}):
        vals = {f: r[model] for f, r in per_fold.items() if model in r}
        loco = [v["primary"] for f, v in vals.items() if f.startswith("loco:") and not np.isnan(v["primary"])]
        out[model] = dict(loco_mean=round(float(np.mean(loco)), 4) if loco else None, loco_sd=round(float(np.std(loco)), 4) if loco else None,
                          loco_min=round(float(np.min(loco)), 4) if loco else None, loco_max=round(float(np.max(loco)), 4) if loco else None,
                          n_loco_folds=len(loco), time_split=round(vals["time_split"]["primary"], 4) if "time_split" in vals and not np.isnan(vals["time_split"]["primary"]) else None)
    return out


def run_task(df, feats, metric, std_counts, rule_col, age_col, tune, n_neg, rng, task):
    per_fold = {}
    for name, trm, tem in folds_for(df, std_counts):
        train, test = df[trm], df[tem]
        if test.y.sum() == 0 or train.y.sum() == 0 or test.y.nunique() < 2:
            continue
        r = {}
        base = test.assign(score=0.0); r["prevalence"] = dict(primary=metric(base))
        if rule_col is not None:
            r["gate1_rule"] = dict(primary=metric(test.assign(score=test[rule_col].fillna(-1) + 1e-9 * test.get("tie", 0))))
        if age_col is not None:
            r["account_age_heuristic"] = dict(primary=metric(test.assign(score=-test[age_col].fillna(test[age_col].median()))))
        tr = subsample(train, n_neg, rng)
        m = lr_model().fit(tr[feats], tr.y); r["logistic_regression"] = dict(primary=metric(test.assign(score=m.predict_proba(test[feats])[:, 1])))
        if tune:
            gb, best = tuned_gb(train, feats, metric, rng, n_neg)
            r["gradient_boosting_tuned"] = dict(primary=metric(test.assign(score=gb.predict_proba(test[feats])[:, 1])), params=best)
        per_fold[name] = {k: dict(v, primary=float(v["primary"]) if v["primary"] == v["primary"] else np.nan) for k, v in r.items()}
        per_fold[name]["_n"] = dict(primary=float(test.y.sum()))
    clean = {f: {m: v for m, v in r.items() if m != "_n"} for f, r in per_fold.items()}
    s = summarise(clean)
    if "gradient_boosting_tuned" in s and "prevalence" in s and s["gradient_boosting_tuned"]["loco_mean"] is not None and s["prevalence"]["loco_mean"] is not None:
        s["gradient_boosting_tuned"]["below_prevalence"] = s["gradient_boosting_tuned"]["loco_mean"] < s["prevalence"]["loco_mean"]
    return dict(summary=s, folds={f: {m: {k: (round(x, 4) if isinstance(x, float) else x) for k, x in v.items()} for m, v in r.items()} for f, r in per_fold.items()})


def univariate(df, feats):
    out = {}
    for f in feats:
        x = df[f].astype(float); m = x.notna()
        if m.sum() > 10 and df.y[m].nunique() == 2:
            a = roc_auc_score(df.y[m], x[m]); out[f] = round(max(a, 1 - a), 4)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def t1(data, splits, version, lset, tune, quick):
    p = pd.read_parquet(os.path.join(data, "positions.parquet"), filters=[("market_set", "==", "case"), ("t_news_version", "==", version), ("is_main_side", "==", True)])
    p = prep_t1(p).merge(splits, on="case_id")
    p = p[~(p.is_documented & ~p[lset])]  # documented wallets outside the set are dropped
    p["y"] = p[lset].astype(int); p["tie"] = p.buy_usdc_pre
    p = p[p.groupby(["case_id", "condition_id"]).y.transform("max") > 0].reset_index(drop=True)
    std = p.assign(s=p.label_standard).groupby("case_id").apply(lambda g: g.loc[g.s, "wallet"].nunique(), include_groups=False).to_dict()
    res = run_task(p, T1_FEATURES, market_ap if True else None, std, "gate1_score", "account_age_days_at_first_buy", tune, 20000 if quick else 60000, np.random.default_rng(SEED), "T1")
    res.update(n_rows=int(len(p)), n_pos=int(p.y.sum()), n_cases_with_pos=int(p[p.y == 1].case_id.nunique()), univariate_auc=univariate(p, T1_FEATURES))
    return res


def t2(data, splits, version, lset, tune, quick):
    e = pd.read_parquet(os.path.join(data, "episodes.parquet"), filters=[("t_news_version", "==", version)]).merge(splits, on="case_id")
    keep_ep = set(e[(e.role == "suspected") & e[lset]].row_id)
    e = e[((e.role == "suspected") & e[lset]) | ((e.role != "suspected") & e.control_of.isin(keep_ep))].reset_index(drop=True)
    pos = pd.read_parquet(os.path.join(data, "positions.parquet"), columns=["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version", "gate1_score"],
                          filters=[("market_set", "==", "case"), ("t_news_version", "==", version)])
    e = e.merge(pos.drop(columns=["market_set", "t_news_version"]), on=["case_id", "condition_id", "asset_id", "wallet"], how="left")
    e["y"] = (e.role == "suspected").astype(int); e["tie"] = e.pre_buy_usdc
    W = pd.read_parquet(os.path.join(data, "wallets.parquet"), columns=["wallet", "case_id", "label_standard"])
    std = W[W.label_standard].groupby("case_id").wallet.nunique().to_dict()
    std = {c: n for c, n in std.items() if c in set(e.case_id)}
    res = run_task(e, T2_FEATURES, auc_cw, std, "gate1_score", "account_age_days_at_first_buy", tune, 10**9, np.random.default_rng(SEED), "T2")
    res.update(n_rows=int(len(e)), n_pos=int(e.y.sum()), won_post_rate_by_role={k: round(float(v), 4) for k, v in e.groupby("role").won_post.mean().items()},
               base_result="matched same-side controls win about as often as documented episodes: outcome alone does not separate them",
               univariate_auc=univariate(e, T2_FEATURES + ["share_on_this_ladder_market"]))
    return res


def market_features(data, version, sets):
    mm = pd.read_parquet(os.path.join(data, "market_minutes.parquet"), filters=[("t_news_version", "==", version)])
    mm = mm[mm.minutes_from_cut < 0]
    k = ["market_set", "case_id", "condition_id"]
    def agg(g):
        g = g.sort_values("minute_unix"); last = lambda h: g[g.minutes_from_cut >= -60 * h]
        def chg(h):
            a = g[g.minutes_from_cut < -60 * h]
            return (g.last_price_usdc.iloc[-1] - a.last_price_usdc.iloc[-1]) if len(a) else np.nan
        tb, ts_ = last(24).taker_buy_usdc.sum(), last(24).taker_sell_usdc.sum()
        return pd.Series(dict(log_usdc_48h=np.log1p(g.usdc.sum()), log_usdc_24h=np.log1p(last(24).usdc.sum()), log_usdc_1h=np.log1p(last(1).usdc.sum()),
            usdc_share_last_6h=last(6).usdc.sum() / g.usdc.sum() if g.usdc.sum() else np.nan, log_n_wallets_48h=np.log1p(g.n_wallets.sum()),
            new_wallet_share_48h=g.n_new_wallets.sum() / g.n_wallets.sum() if g.n_wallets.sum() else np.nan,
            price_change_24h=chg(24), price_change_6h=chg(6), price_change_1h=chg(1), abs_max_minute_move_24h=last(24).last_price_usdc.diff().abs().max(),
            taker_buy_share_24h=tb / (tb + ts_) if (tb + ts_) else np.nan))
    f = mm.groupby(k).apply(agg, include_groups=False).reset_index()
    p = pd.read_parquet(os.path.join(data, "positions.parquet"), columns=k + ["t_news_version", "wallet", "buy_usdc_pre", "account_age_days_at_first_buy", "gate1", "vwap_price_usdc_pre"] + sets,
                        filters=[("t_news_version", "==", version)])
    def pagg(g):
        tot = g.buy_usdc_pre.sum(); w = g.groupby("wallet").buy_usdc_pre.sum().sort_values(ascending=False)
        d = dict(log_n_buyers=np.log1p(g.wallet.nunique()), top10_buy_share=w.head(10).sum() / tot if tot else np.nan,
                 fresh_buyer_share=(g.account_age_days_at_first_buy <= 7).mean(), gate1_rate=g.gate1.astype(float).mean(),
                 longshot_buy_share=g.loc[g.vwap_price_usdc_pre <= 0.35, "buy_usdc_pre"].sum() / tot if tot else np.nan)
        d.update({f"has_{s}": bool(g[s].any()) for s in sets})
        return pd.Series(d)
    q = p.groupby(k).apply(pagg, include_groups=False).reset_index()
    return f.merge(q, on=k, how="outer")


def t3(data, splits, version, comp, lset, tune, feats_cache):
    key = (version,)
    if key not in feats_cache:
        feats_cache[key] = market_features(data, version, SETS)
    f = feats_cache[key]
    ref = pd.read_csv(os.path.join(data, "twin_markets.csv" if comp == "twin" else "placebo_markets.csv"))
    cid_col = "twin_condition_id" if comp == "twin" else "placebo_condition_id"
    ref = ref[ref[cid_col].notna()]
    case = f[f.market_set == "case"].merge(ref[["case_id", "case_condition_id"]].drop_duplicates(), left_on=["case_id", "condition_id"], right_on=["case_id", "case_condition_id"])
    if lset != "all":
        case = case[case[f"has_{lset}"] == True]  # noqa: E712
    other = f[f.market_set == comp].merge(ref[["case_id", "case_condition_id", cid_col]], left_on=["case_id", "condition_id"], right_on=["case_id", cid_col])
    other = other[other.case_condition_id.isin(set(case.case_condition_id))]
    d = pd.concat([case.assign(y=1), other.assign(y=0)], ignore_index=True).merge(splits, on="case_id")
    d["tie"] = 0
    W = pd.read_parquet(os.path.join(data, "wallets.parquet"), columns=["wallet", "case_id", "label_standard"])
    std = {c: n for c, n in W[W.label_standard].groupby("case_id").wallet.nunique().items() if c in set(d.case_id)}
    res = run_task(d, T3_FEATURES, auc_cw, std, "gate1_rate", None, tune, 10**9, np.random.default_rng(SEED), "T3")
    res.update(n_case_markets=int(d.y.sum()), n_comparison_markets=int((d.y == 0).sum()), univariate_auc=univariate(d, T3_FEATURES))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--data", default=os.path.join(here, "..", "data")); ap.add_argument("--out", default=os.path.join(here, "baselines.json"))
    ap.add_argument("--quick", action="store_true", help="no gradient-boosting tuning, smaller negative samples (for the notebook)")
    a = ap.parse_args()
    splits = pd.read_csv(os.path.join(here, "splits.csv"))[["case_id", "split"]]
    out = dict(seed=SEED, protocol="A15, A23", label_sets=SETS, leakage=LEAKAGE, known_shortcuts=SHORTCUTS,
               features=dict(T1=T1_FEATURES, T2=T2_FEATURES, T3=T3_FEATURES), gb_grid=GRID)
    cache = {}
    for v in ["precise", "day"]:
        tune = (v == "precise") and not a.quick
        out[v] = {}
        for s in SETS:
            out[v][s] = dict(T1=t1(a.data, splits, v, s, tune, a.quick), T2=t2(a.data, splits, v, s, tune, a.quick),
                             T3=t3(a.data, splits, v, "twin", s, tune, cache), T3b=t3(a.data, splits, v, "placebo", s, tune, cache))
            print(v, s, "done", flush=True)
        out[v]["all_case_markets"] = dict(T3=t3(a.data, splits, v, "twin", "all", tune, cache), T3b=t3(a.data, splits, v, "placebo", "all", tune, cache))
    json.dump(out, open(a.out, "w"), indent=1, default=lambda x: None if (isinstance(x, float) and np.isnan(x)) else (bool(x) if isinstance(x, np.bool_) else float(x)))
    for v in ["precise"]:
        for s in SETS:
            for t in ["T1", "T2", "T3", "T3b"]:
                print(v, s, t, {m: (r["loco_mean"], r["loco_sd"], r["time_split"]) for m, r in out[v][s][t]["summary"].items()})
