"""PMITC v1.2.1 benchmark tasks (PROTOCOL A15, A23, A26, A27, A29, A32, A33, A34).
A34-A34.2: positions are in the economic view, net of full sets; T1 candidates are directional pre-news positions. Runs on the released files only (../data).
  python3 pmitc_bench.py [--data ../data] [--out baselines.json] [--quick]
Folds: leave-one-case-out over cases with >= 3 label_standard wallets in the task's rows, plus the A15 time split (splits.csv).
Label sets: label_strict, label_standard, label_broad (A20). A26: models train on label_standard (label_broad for the broad run); label_strict is
evaluation-only. Documented wallets outside the evaluated set are dropped from evaluation (and outside the training set from training).
Headline tasks (A27, A33): T1s (rank within the positives' size band), T2s (controls also matched on account-age band), T2w (account-age and
prior win-rate bands), T2-open (Orca/Inca wallets may be controls). A29: every task uses only rows with t_news_reliable = true.
A32: a task / label set with fewer than 6 leave-one-case-out folds is reported per fold with min and max only (no mean, SD or headline number).
Secondary: T1, T2 (logistic regression and baselines only), T3 (case vs twin), T3b (case vs placebo; market-type sensitive).
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
    'T1.log_buy_usdc_pre / log_market_usdc_pre / log_n_buy_fills_pre': 'selection by the sources, not construction: sources flag large bets, so pre-cut size alone ranks positives highly (univariate AUC 0.93-0.98). A detector that learns size learns what the press notices.',
    'T2.prior_net_long_win_rate / n_prior_markets': 'selection, not construction (run 10): allowing Orca/Inca wallets as controls (T2-open) leaves it at univariate AUC 0.88; sources find wallets that won before. T2w matches controls on its band.',
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


def fit_gb(tr, feats, params):
    """drops features that are entirely missing in this training set (HistGradientBoosting cannot bin them)"""
    use = [f for f in feats if tr[f].notna().any()]
    m = HistGradientBoostingClassifier(random_state=SEED, **params).fit(tr[use], tr.y)
    m.used_features_ = use
    return m


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
                try:
                    m = fit_gb(tr, feats, g)
                    s.append(score_fn(te.assign(score=m.predict_proba(te[m.used_features_])[:, 1])))
                except ValueError:
                    s.append(np.nan)
            res.append((np.nanmean(s) if s else -1, g))
        res = [(x if x == x else -1, g) for x, g in res]
        best = max(res, key=lambda x: x[0])[1]
    tr = subsample(train, n_neg, rng)
    return fit_gb(tr, feats, best), best


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


def t1_ap(df):
    return market_ap(df)["ap"]


def auc_cw(df):
    """case-weighted AUC: per case with both classes, then mean."""
    v = [roc_auc_score(g.y, g.score) for _, g in df.groupby("case_id") if g.y.nunique() == 2]
    return float(np.mean(v)) if v else np.nan


def folds_for(df, std_counts):
    """A37: leave-one-group-out over connected groups (splits.csv group_id) with >= 3 label_standard wallets."""
    grp = df.drop_duplicates("case_id").set_index("case_id").group_id
    gc = {}
    for c, n in std_counts.items():
        if c in grp.index:
            gc[grp[c]] = gc.get(grp[c], 0) + n
    loco = sorted([g for g, n in gc.items() if n >= 3])
    f = [("loco:" + g, df.group_id != g, df.group_id == g) for g in loco]
    f.append(("time_split", df.split == "train", df.split == "test"))
    return f


MIN_FOLDS = 6  # A32
ALLEGED = True  # A35: alleged positions are the positives; False = the wallet-level secondary version


def summarise(per_fold):
    out = {}
    for model in sorted({m for f in per_fold.values() for m in f}):
        vals = {f: r[model] for f, r in per_fold.items() if model in r}
        loco = [v["primary"] for f, v in vals.items() if f.startswith("loco:") and not np.isnan(v["primary"])]
        out[model] = dict(loco_mean=round(float(np.mean(loco)), 4) if loco else None, loco_sd=round(float(np.std(loco)), 4) if loco else None,
                          loco_min=round(float(np.min(loco)), 4) if loco else None, loco_max=round(float(np.max(loco)), 4) if loco else None,
                          n_loco_folds=len(loco), time_split=round(vals["time_split"]["primary"], 4) if "time_split" in vals and not np.isnan(vals["time_split"]["primary"]) else None)
        if len(loco) < MIN_FOLDS:  # A32: per-fold values with min and max only
            out[model].pop("loco_mean"); out[model].pop("loco_sd")
            out[model]["fold_values"] = {f: round(float(v["primary"]), 4) for f, v in vals.items() if not np.isnan(v["primary"])}
            out[model]["reporting"] = "per_fold_only_A32"
    return out


def run_task(df, feats, metric, std_counts, rule_col, age_col, tune, n_neg, rng, task, extra=None):
    per_fold = {}
    for name, trm, tem in folds_for(df, std_counts):
        train = df[trm & df.use_tr].assign(y=lambda d: d.y_tr)
        test = df[tem & df.use_ev]
        if test.y.sum() == 0 or train.y.sum() == 0 or test.y.nunique() < 2:
            continue
        r = {}
        base = test.assign(score=0.0); r["prevalence"] = dict(primary=metric(base))
        if rule_col is not None:
            r["gate1_rule"] = dict(primary=metric(test.assign(score=test[rule_col].fillna(-1) + 1e-9 * test.get("tie", 0))))
        if age_col is not None:
            r["account_age_heuristic"] = dict(primary=metric(test.assign(score=-test[age_col].fillna(test[age_col].median()).fillna(0.0))))  # a test case with no known ages ranks as ties
        tr = subsample(train, n_neg, rng)
        m = lr_model().fit(tr[feats], tr.y); r["logistic_regression"] = dict(primary=metric(test.assign(score=m.predict_proba(test[feats])[:, 1])))
        if tune:
            try:
                gb, best = tuned_gb(train, feats, metric, rng, n_neg)
                r["gradient_boosting_tuned"] = dict(primary=metric(test.assign(score=gb.predict_proba(test[gb.used_features_])[:, 1])), params=best)
            except ValueError as ex:
                r["gradient_boosting_tuned"] = dict(primary=np.nan, error=str(ex)[:80])
        per_fold[name] = {k: dict(v, primary=float(v["primary"]) if v["primary"] == v["primary"] else np.nan) for k, v in r.items()}
        if extra is not None:  # T1: P@10, R@10, R@100 for logistic regression and the rule, recomputed on the same scores
            per_fold[name]["logistic_regression"]["extra"] = {k: round(x, 4) for k, x in extra(test.assign(score=m.predict_proba(test[feats])[:, 1])).items()}
        per_fold[name]["_n"] = dict(primary=float(test.y.sum()))
    clean = {f: {m: v for m, v in r.items() if m != "_n"} for f, r in per_fold.items()}
    s = summarise(clean)
    if "gradient_boosting_tuned" in s and "prevalence" in s and s["gradient_boosting_tuned"].get("loco_mean") is not None and s["prevalence"].get("loco_mean") is not None:
        s["gradient_boosting_tuned"]["below_prevalence"] = s["gradient_boosting_tuned"]["loco_mean"] < s["prevalence"]["loco_mean"]
    return dict(summary=s, folds={f: {m: {k: (round(x, 4) if isinstance(x, float) else x) for k, x in v.items()} for m, v in r.items() if m != "_n"} | {"n_test_positives": int(r["_n"]["primary"])} for f, r in per_fold.items()})


def univariate(df, feats):
    out = {}
    for f in feats:
        x = df[f].astype(float); m = x.notna()
        if m.sum() > 10 and df.y[m].nunique() == 2:
            a = roc_auc_score(df.y[m], x[m]); out[f] = round(max(a, 1 - a), 4)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def train_set(lset):
    """A26: label_standard is the training label; label_broad trains on itself; label_strict is evaluation-only."""
    return "label_broad" if lset == "label_broad" else "label_standard"


def t1(data, splits, version, lset, tune, quick, size_band=False):
    """T1 (secondary) or T1s (A27 headline, size_band=True: candidates within [0.5 x min, 2 x max] of the market's positives' pre-cut BUY)."""
    p = pd.read_parquet(os.path.join(data, "positions.parquet"), filters=[("market_set", "==", "case"), ("t_news_version", "==", version), ("is_directional_position", "==", True), ("t_news_reliable", "==", True)])  # A34.2
    p = prep_t1(p).merge(splits, on="case_id")
    tr = train_set(lset)
    al = p.is_alleged_position if ALLEGED else True  # A35: positives are alleged positions; other positions of labelled wallets are dropped
    p["y"] = (p[lset] & al).astype(int); p["y_tr"] = (p[tr] & al).astype(int); p["tie"] = p.buy_usdc_pre
    p["use_ev"] = ~(p.is_documented & ~(p[lset] & al)); p["use_tr"] = ~(p.is_documented & ~(p[tr] & al))
    k = ["case_id", "condition_id"]
    if size_band:
        for lab, use in [("y", "use_ev"), ("y_tr", "use_tr")]:
            b = p[p[lab] == 1].groupby(k).buy_usdc_pre.agg(["min", "max"])
            lo = p.set_index(k).index.map(lambda x: b["min"].get(x, np.nan) * 0.5).values
            hi = p.set_index(k).index.map(lambda x: b["max"].get(x, np.nan) * 2).values
            p[use] = p[use] & (p.buy_usdc_pre >= lo) & (p.buy_usdc_pre <= hi)
    p = p[(p.groupby(k).y.transform("max") > 0) | (p.groupby(k).y_tr.transform("max") > 0)].reset_index(drop=True)
    std = p[p.label_standard].groupby("case_id").wallet.nunique().to_dict()
    res = run_task(p, T1_FEATURES, t1_ap, std, "gate1_score", "account_age_days_at_first_buy", tune, 20000 if quick else 60000, np.random.default_rng(SEED), "T1s" if size_band else "T1", extra=market_ap)
    ev = p[p.use_ev]
    res.update(n_rows_eval=int(len(ev)), n_pos_eval=int(ev.y.sum()), n_cases_with_pos=int(ev[ev.y == 1].case_id.nunique()), train_label=tr,
               univariate_auc=univariate(ev, T1_FEATURES))
    return res


def t2(data, splits, version, lset, tune, quick, design="standard"):
    """T2 (standard controls), T2s (A27: age_matched), T2w (A33: winrate_matched) or T2-open (A27: open)."""
    e = pd.read_parquet(os.path.join(data, "episodes.parquet"), filters=[("t_news_version", "==", version), ("control_design", "==", design), ("t_news_reliable", "==", True)]).merge(splits, on="case_id")
    tr = train_set(lset)
    if not ALLEGED:  # wallet-level (secondary): every position of a labelled wallet counts as suspected
        e.loc[e.role == "labelled_other_position", "role"] = "suspected"
    e = e[e.role != "labelled_other_position"]  # A35: positives are alleged positions only
    ep_tr = set(e[(e.role == "suspected") & e[tr]].episode_id); ep_ev = set(e[(e.role == "suspected") & e[lset]].episode_id)
    owner = np.where(e.role == "suspected", e.episode_id, e.control_of)
    e["use_tr"] = pd.Series(owner).isin(ep_tr).values; e["use_ev"] = pd.Series(owner).isin(ep_ev).values
    e = e[e.use_tr | e.use_ev]
    # A44: a control (case, market, token, wallet) matched to several episodes counts once
    k = ["case_id", "condition_id", "asset_id", "wallet"]; ctl = e[e.role != "suspected"]
    fl = ctl.groupby(k)[["use_tr", "use_ev"]].transform("max")
    ctl = ctl.assign(use_tr=fl.use_tr.values, use_ev=fl.use_ev.values).drop_duplicates(k)
    e = pd.concat([e[e.role == "suspected"], ctl]).reset_index(drop=True)
    pos = pd.read_parquet(os.path.join(data, "positions.parquet"), columns=["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version", "gate1_score"],
                          filters=[("market_set", "==", "case"), ("t_news_version", "==", version)])
    e = e.merge(pos.drop(columns=["market_set", "t_news_version"]), on=["case_id", "condition_id", "asset_id", "wallet"], how="left")
    e["y"] = (e.role == "suspected").astype(int); e["y_tr"] = e.y; e["tie"] = e.pre_buy_usdc
    W = pd.read_parquet(os.path.join(data, "wallets.parquet"), columns=["wallet", "case_id", "label_standard"])
    std = {c: n for c, n in W[W.label_standard].groupby("case_id").wallet.nunique().items() if c in set(e.case_id)}
    res = run_task(e, T2_FEATURES, auc_cw, std, "gate1_score", "account_age_days_at_first_buy", tune, 10**9, np.random.default_rng(SEED), "T2")
    ev = e[e.use_ev]
    sus = e[e.role == "suspected"]; ctl = e[e.role != "suspected"]
    cov = dict(n_episodes=int(sus.episode_id.nunique()), n_episodes_with_same_side=int(e[e.role == "control_same_side"].control_of.nunique()),
               n_control_rows=int(len(ctl)), n_relaxed_band_control_rows=int(ctl.relaxed_band.sum()) if "relaxed_band" in ctl else 0,
               n_episodes_relaxed_band=int(ctl[ctl.relaxed_band == True].control_of.nunique()) if "relaxed_band" in ctl else 0)  # noqa: E712
    res.update(control_design=design, train_label=tr, coverage=cov, n_rows_eval=int(len(ev)), n_pos_eval=int(ev.y.sum()),
               won_post_rate_by_role={k: round(float(v), 4) for k, v in ev.groupby("role").won_post.mean().items()},
               base_result="matched same-side controls win about as often as documented episodes: outcome alone does not separate them",
               univariate_auc=univariate(ev, T2_FEATURES + ["share_on_this_ladder_market"]))
    return res


def market_features(data, version, sets):
    mm = pd.read_parquet(os.path.join(data, "market_minutes.parquet"), filters=[("t_news_version", "==", version), ("t_news_reliable", "==", True)])
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
    p = pd.read_parquet(os.path.join(data, "positions.parquet"), columns=k + ["t_news_version", "wallet", "buy_usdc_pre", "account_age_days_at_first_buy", "gate1", "vwap_price_usdc_pre", "is_alleged_position"] + sets,
                        filters=[("t_news_version", "==", version), ("t_news_reliable", "==", True), ("is_directional_position", "==", True)])  # A34.2
    def pagg(g):
        tot = g.buy_usdc_pre.sum(); w = g.groupby("wallet").buy_usdc_pre.sum().sort_values(ascending=False)
        d = dict(log_n_buyers=np.log1p(g.wallet.nunique()), top10_buy_share=w.head(10).sum() / tot if tot else np.nan,
                 fresh_buyer_share=(g.account_age_days_at_first_buy <= 7).mean(), gate1_rate=g.gate1.astype(float).mean(),
                 longshot_buy_share=g.loc[g.vwap_price_usdc_pre <= 0.35, "buy_usdc_pre"].sum() / tot if tot else np.nan)
        d.update({f"has_{s}": bool((g[s] & g.is_alleged_position).any()) for s in sets})  # A35
        return pd.Series(d)
    q = p.groupby(k).apply(pagg, include_groups=False).reset_index()
    return f.merge(q, on=k, how="outer")


def excluded_unreliable(data):
    """A29/A29.1: what the per-market t_news_reliable filter removes (markets, cases fully or partly removed, positives, suspected episodes)."""
    m = pd.read_parquet(os.path.join(data, "markets.parquet"), columns=["case_id", "condition_id", "t_news_reliable"])
    by = m.groupby("case_id").t_news_reliable.agg(["sum", "size"])
    p = pd.read_parquet(os.path.join(data, "positions.parquet"), columns=["case_id", "wallet", "t_news_reliable"] + SETS,
                        filters=[("market_set", "==", "case"), ("t_news_version", "==", "precise"), ("is_directional_position", "==", True)])
    pos = {}
    for s in SETS:
        q = p[p[s]].groupby(["case_id", "wallet"]).t_news_reliable.any()
        pos[s] = dict(with_prenews_position=int(len(q)), kept=int(q.sum()), removed=int((~q).sum()),
                      removed_by_case={k: int(v) for k, v in (~q).groupby(level=0).sum().items() if v})
    e = pd.read_parquet(os.path.join(data, "episodes.parquet"), columns=["t_news_version", "t_news_reliable"],
                        filters=[("control_design", "==", "standard"), ("role", "==", "suspected")])
    return dict(rule="A29.1: per market; false only for deadline-rule cuts", n_markets=int((~m.t_news_reliable).sum()), n_markets_total=int(len(m)),
                cases_fully_removed=sorted(by[by["sum"] == 0].index), cases_partly_removed=sorted(by[(by["sum"] > 0) & (by["sum"] < by["size"])].index),
                markets_by_case={c: dict(reliable=int(r["sum"]), unreliable=int(r["size"] - r["sum"])) for c, r in by[by["sum"] < by["size"]].iterrows()},
                positives=pos, suspected_episodes_removed={v: int((~g.t_news_reliable).sum()) for v, g in e.groupby("t_news_version")})


def t3(data, splits, version, comp, lset, tune, feats_cache):
    key = (version,)
    if key not in feats_cache:
        feats_cache[key] = market_features(data, version, SETS)
    f = feats_cache[key]
    ref = pd.read_csv(os.path.join(data, "twin_markets.csv" if comp == "twin" else "placebo_markets.csv"))
    cid_col = "twin_condition_id" if comp == "twin" else "placebo_condition_id"
    ref = ref[ref[cid_col].notna()]
    case = f[f.market_set == "case"].merge(ref[["case_id", "case_condition_id"]].drop_duplicates(), left_on=["case_id", "condition_id"], right_on=["case_id", "case_condition_id"])
    if lset == "all":
        case["use_ev"] = True; case["use_tr"] = True
    else:
        case["use_ev"] = case[f"has_{lset}"] == True; case["use_tr"] = case[f"has_{train_set(lset)}"] == True  # noqa: E712
        case = case[case.use_ev | case.use_tr]
    other = f[f.market_set == comp].merge(ref[["case_id", "case_condition_id", cid_col]], left_on=["case_id", "condition_id"], right_on=["case_id", cid_col])
    other = other.merge(case[["case_condition_id", "use_ev", "use_tr"]].drop_duplicates("case_condition_id"), on="case_condition_id")
    d = pd.concat([case.assign(y=1), other.assign(y=0)], ignore_index=True).merge(splits, on="case_id")
    d["tie"] = 0; d["y_tr"] = d.y
    W = pd.read_parquet(os.path.join(data, "wallets.parquet"), columns=["wallet", "case_id", "label_standard"])
    std = {c: n for c, n in W[W.label_standard].groupby("case_id").wallet.nunique().items() if c in set(d.case_id)}
    res = run_task(d, T3_FEATURES, auc_cw, std, "gate1_rate", None, tune, 10**9, np.random.default_rng(SEED), "T3")
    ev = d[d.use_ev]
    res.update(n_case_markets=int(ev.y.sum()), n_comparison_markets=int((ev.y == 0).sum()), univariate_auc=univariate(ev, T3_FEATURES))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--data", default=os.path.join(here, "..", "data")); ap.add_argument("--out", default=os.path.join(here, "baselines.json"))
    ap.add_argument("--quick", action="store_true", help="no gradient-boosting tuning, smaller negative samples (for the notebook)")
    a = ap.parse_args()
    splits = pd.read_csv(os.path.join(here, "splits.csv"))[["case_id", "split", "group_id"]]
    out = dict(seed=SEED, protocol="A15, A23, A26, A27, A29, A32, A33, A34, A35, A37, A44", positives="alleged positions (A35); wallet_level = secondary", label_sets=SETS, training_label="label_standard (label_broad for the broad run); label_strict evaluation-only (A26)",
               headline_tasks=["T1s", "T2s", "T2w", "T2open"], secondary_tasks=["T1", "T2", "T3", "T3b"], leakage=LEAKAGE, known_shortcuts=SHORTCUTS,
               features=dict(T1=T1_FEATURES, T2=T2_FEATURES, T3=T3_FEATURES), gb_grid=GRID, min_folds_for_summary=MIN_FOLDS,
               excluded_unreliable=excluded_unreliable(a.data))
    cache = {}
    for v in ["precise", "day"]:
        tune = (v == "precise") and not a.quick
        out[v] = {}
        for s_ in SETS:
            out[v][s_] = dict(T1s=t1(a.data, splits, v, s_, tune, a.quick, size_band=True), T2s=t2(a.data, splits, v, s_, tune, a.quick, "age_matched"),
                              T2w=t2(a.data, splits, v, s_, tune, a.quick, "winrate_matched"),
                              T2open=t2(a.data, splits, v, s_, tune, a.quick, "open"), T1=t1(a.data, splits, v, s_, False, a.quick),
                              T2=t2(a.data, splits, v, s_, False, a.quick, "standard"), T3=t3(a.data, splits, v, "twin", s_, tune, cache),
                              T3b=t3(a.data, splits, v, "placebo", s_, tune, cache))
            ALLEGED = False  # A35 secondary: wallet-level positives (any position of a labelled wallet), no gradient boosting
            out[v][s_]["wallet_level"] = dict(T1s=t1(a.data, splits, v, s_, False, a.quick, size_band=True), T2s=t2(a.data, splits, v, s_, False, a.quick, "age_matched"))
            ALLEGED = True
            print(v, s_, "done", flush=True)
        out[v]["all_case_markets"] = dict(T3=t3(a.data, splits, v, "twin", "all", tune, cache), T3b=t3(a.data, splits, v, "placebo", "all", tune, cache))
    json.dump(out, open(a.out, "w"), indent=1, default=lambda x: None if (isinstance(x, float) and np.isnan(x)) else (bool(x) if isinstance(x, np.bool_) else float(x)))
    for s_ in SETS:
        for t in ["T1s", "T2s", "T2w", "T2open", "T1", "T2", "T3", "T3b"]:
            print("precise", s_, t, {m: (r.get("loco_mean"), r.get("loco_min"), r.get("loco_max"), r["time_split"]) for m, r in out["precise"][s_][t]["summary"].items()})
