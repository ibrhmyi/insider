"""PMITC v1.0 benchmark tasks T1-T3 (PROTOCOL A15). Runs on the released files only (../data).
  python3 pmitc_bench.py [--data ../data] [--out baselines.json]
Splits: benchmarks/splits.csv (frozen; grouped by case; test = cases first claimed on/after 2026-03-01).
Baselines: logistic regression (standardised, L2, C=1) and HistGradientBoosting (defaults), seed 192.
"""
import argparse, json, os
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

SEED = 192
T1_FEATURES = ["log_buy_usdc_pre", "vwap_pre", "first_buy_price", "max_buy_price", "log_n_buy_fills_pre", "taker_share_pre", "log_account_age_days",
               "log_market_usdc_pre", "f2_share", "log_lifetime_markets", "f5_conviction", "f6_hours_median_buy_to_tnews", "gate1_score", "gate2a_int",
               "sell_share_pre", "hours_first_buy_to_cut", "hours_last_buy_to_cut"]
T1_LEAKAGE = ["is_documented", "doc_grade", "is_candidate_coordinated", "is_control", "is_placebo_market", "gate1", "gate2b", "is_shortest_sufficient",
              "won_post", "pnl_post", "buy_usdc_post", "buy_shares_post", "sell_usdc_post", "sell_shares_post", "wallet", "case_id", "condition_id",
              "asset_id", "t_cut_ts (absolute time)", "first_buy_ts / last_buy_ts (absolute time)", "source_pre", "vol_to_day (includes the rest of the cut's day)"]
T2_FEATURES = ["account_age_days_at_first_buy", "prior_markets", "prior_net_long_win_rate", "first_price", "vwap", "max_price_paid", "n_buy_fills",
               "median_fill_usdc", "fill_size_cv", "taker_share", "hour_of_day_first_buy", "pre_buy_usdc", "signal_a_rebuy_1_5x", "size_price_slope",
               "hours_last_buy_to_tnews", "ladder_rank", "hours_first_buy_to_tnews"]
T2_LEAKAGE = ["share_on_this_ladder_market (construction artifact: controls are drawn one market at a time, so their share is 1; AUC 0.97 alone)", "role", "episode_id", "control_of", "wallet", "case_share_of_lifetime_volume (lifetime denominator)", "is_shortest_sufficient",
              "follower_wallets_60m / follower_buy_usdc_60m (window can pass t_news)", "share_sold_before_resolution_post", "won_post", "pnl_post",
              "redemption_delay_hours_post", "hours_funding_to_first_trade / funding_source_type / funder_shared_with_labelled (empty)"]
T3_FEATURES = ["log_usdc_48h", "log_usdc_24h", "log_usdc_1h", "usdc_share_last_6h", "log_n_wallets_48h", "new_wallet_share_48h", "price_change_24h",
               "price_change_6h", "price_change_1h", "abs_max_minute_move_24h", "taker_buy_share_24h", "log_n_buyers", "top10_buy_share",
               "fresh_buyer_share", "gate1_rate", "longshot_buy_share"]
T3_LEAKAGE = ["market_set / is_placebo_market (the label)", "any minute with minutes_from_cut >= 0", "_post columns", "placebo_category",
              "resolution, outcome and volume_decile fields (volume is total, includes post-cut)", "question / slug text"]


def per_market_rank_metrics(df, score, ks=(10, 100)):
    out = []
    for (case, cid), g in df.groupby(["case_id", "condition_id"]):
        y = g.y.values
        if y.sum() == 0:
            continue
        o = np.argsort(-g[score].values, kind="stable"); ys = y[o]
        r = dict(case_id=case, condition_id=cid, n=len(y), n_pos=int(y.sum()), ap=average_precision_score(y, g[score].values))
        for k in ks:
            r[f"p@{k}"] = ys[:k].sum() / min(k, len(y)); r[f"r@{k}"] = ys[:k].sum() / y.sum()
        out.append(r)
    m = pd.DataFrame(out)
    if not len(m):
        return {}
    byc = m.groupby("case_id")[[c for c in m.columns if c[:2] in ("ap", "p@", "r@")]].mean()
    res = {k: round(float(v), 4) for k, v in byc.mean().items()}
    res.update(n_cases=int(len(byc)), n_markets=int(len(m)), per_case={c: {k: round(float(v), 4) for k, v in r.items()} for c, r in byc.iterrows()})
    return res


def models():
    lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=1.0, max_iter=2000, random_state=SEED))
    gb = HistGradientBoostingClassifier(random_state=SEED)
    return {"logistic_regression": lr, "gradient_boosting": gb}


def t1(data, splits, version):
    p = pd.read_parquet(os.path.join(data, "positions.parquet"), filters=[("market_set", "==", "case"), ("t_news_version", "==", version), ("is_main_side", "==", True)])
    p = p.merge(splits, on="case_id")
    p["y"] = p.is_documented.astype(int)
    p["log_buy_usdc_pre"] = np.log1p(p.buy_usdc_pre); p["log_n_buy_fills_pre"] = np.log1p(p.n_buy_fills_pre)
    p["log_account_age_days"] = np.log1p(p.account_age_days_at_first_buy.clip(lower=0)); p["log_market_usdc_pre"] = np.log1p(p.market_usdc_pre)
    p["log_lifetime_markets"] = np.log1p(p.lifetime_markets_v1); p["gate2a_int"] = p.gate2a.astype(float)
    p["sell_share_pre"] = p.sell_shares_pre / p.buy_shares_pre
    p["hours_first_buy_to_cut"] = (p.t_cut_ts - p.first_buy_ts) / 3600; p["hours_last_buy_to_cut"] = (p.t_cut_ts - p.last_buy_ts) / 3600
    X = p[T1_FEATURES].astype(float)
    # keep markets that contain at least one documented wallet
    has = p.groupby(["case_id", "condition_id"]).y.transform("max") > 0
    p, X = p[has], X[has]
    tr, te = p.split == "train", p.split == "test"
    rng = np.random.default_rng(SEED)
    keep = tr & ((p.y == 1) | (rng.random(len(p)) < min(1.0, 200000 / max(1, (tr & (p.y == 0)).sum()))))  # negative subsample for training
    res = {"n_rows": int(len(p)), "n_pos": int(p.y.sum()), "n_pos_train": int(p[tr].y.sum()), "n_pos_test": int(p[te].y.sum())}
    p = p.copy(); p["random"] = rng.random(len(p)); p["gate1_score_rule"] = p.gate1_score.fillna(-1) + 1e-9 * p.buy_usdc_pre
    res["rule_gate1_score_test"] = per_market_rank_metrics(p[te], "gate1_score_rule")
    res["random_test"] = per_market_rank_metrics(p[te], "random")
    for name, m in models().items():
        m.fit(X[keep], p.y[keep]); p[name] = m.predict_proba(X)[:, 1]
        res[f"{name}_test"] = per_market_rank_metrics(p[te], name)
        # case-grouped CV inside train
        cv = np.full(tr.sum(), np.nan); pt = p[tr]; Xt = X[tr]
        for a, b in GroupKFold(5).split(Xt, pt.y, pt.case_id):
            kk = np.zeros(len(pt), bool); kk[a] = True; kk &= ((pt.y == 1) | (rng.random(len(pt)) < 0.5)).values
            m.fit(Xt[kk], pt.y[kk]); cv[b] = m.predict_proba(Xt.iloc[b])[:, 1]
        pt = pt.assign(cv=cv); res[f"{name}_train_cv"] = per_market_rank_metrics(pt, "cv")
    return res


def t2(data, splits, version):
    e = pd.read_parquet(os.path.join(data, "episodes.parquet"), filters=[("t_news_version", "==", version)]).merge(splits, on="case_id")
    e["y"] = (e.role == "suspected").astype(int)
    X = e[T2_FEATURES].astype(float)
    res = {"n_rows": int(len(e)), "n_suspected": int(e.y.sum()),
           "won_post_rate_by_role": {k: round(float(v), 4) for k, v in e.groupby("role").won_post.mean().items()},
           "base_result": "matched same-side controls win about as often as documented episodes: outcome alone does not separate them"}
    for name, m in models().items():
        cv = np.full(len(e), np.nan)
        for a, b in GroupKFold(5).split(X, e.y, e.case_id):
            m.fit(X.iloc[a], e.y.iloc[a]); cv[b] = m.predict_proba(X.iloc[b])[:, 1]
        res[f"{name}_grouped_cv"] = dict(auc=round(roc_auc_score(e.y, cv), 4), log_loss=round(log_loss(e.y, np.clip(cv, 1e-6, 1 - 1e-6)), 4))
        tr, te = e.split == "train", e.split == "test"
        if e[te].y.nunique() == 2:
            m.fit(X[tr], e.y[tr]); pr = m.predict_proba(X[te])[:, 1]
            res[f"{name}_test"] = dict(auc=round(roc_auc_score(e.y[te], pr), 4), log_loss=round(log_loss(e.y[te], np.clip(pr, 1e-6, 1 - 1e-6)), 4), n=int(te.sum()))
    return res


def t3_features(data, version):
    mm = pd.read_parquet(os.path.join(data, "market_minutes.parquet"), filters=[("t_news_version", "==", version)])
    mm = mm[mm.minutes_from_cut < 0]
    k = ["market_set", "case_id", "condition_id"]
    def agg(g):
        g = g.sort_values("minute_ts"); last = lambda h: g[g.minutes_from_cut >= -60 * h]
        def chg(h):
            a = g[g.minutes_from_cut < -60 * h]; b = g
            return (b.last_price.iloc[-1] - a.last_price.iloc[-1]) if len(a) and len(b) else np.nan
        return pd.Series(dict(log_usdc_48h=np.log1p(g.usdc.sum()), log_usdc_24h=np.log1p(last(24).usdc.sum()), log_usdc_1h=np.log1p(last(1).usdc.sum()),
            usdc_share_last_6h=last(6).usdc.sum() / g.usdc.sum() if g.usdc.sum() else np.nan, log_n_wallets_48h=np.log1p(g.n_wallets.sum()),
            new_wallet_share_48h=g.n_new_wallets.sum() / g.n_wallets.sum() if g.n_wallets.sum() else np.nan,
            price_change_24h=chg(24), price_change_6h=chg(6), price_change_1h=chg(1),
            abs_max_minute_move_24h=last(24).last_price.diff().abs().max(),
            taker_buy_share_24h=last(24).taker_buy_usdc.sum() / (last(24).taker_buy_usdc.sum() + last(24).taker_sell_usdc.sum()) if (last(24).taker_buy_usdc.sum() + last(24).taker_sell_usdc.sum()) else np.nan))
    f = mm.groupby(k).apply(agg, include_groups=False).reset_index()
    p = pd.read_parquet(os.path.join(data, "positions.parquet"), columns=k + ["t_news_version", "wallet", "buy_usdc_pre", "account_age_days_at_first_buy", "gate1", "vwap_pre"],
                        filters=[("t_news_version", "==", version)])
    def pagg(g):
        tot = g.buy_usdc_pre.sum(); w = g.groupby("wallet").buy_usdc_pre.sum().sort_values(ascending=False)
        return pd.Series(dict(log_n_buyers=np.log1p(g.wallet.nunique()), top10_buy_share=w.head(10).sum() / tot if tot else np.nan,
                              fresh_buyer_share=(g.account_age_days_at_first_buy <= 7).mean(), gate1_rate=g.gate1.astype(float).mean(),
                              longshot_buy_share=g.loc[g.vwap_pre <= 0.35, "buy_usdc_pre"].sum() / tot if tot else np.nan))
    q = p.groupby(k).apply(pagg, include_groups=False).reset_index()
    return f.merge(q, on=k, how="outer")


def t3(data, splits, version):
    pl = pd.read_csv(os.path.join(data, "placebo_markets.csv"))
    pl = pl[pl.placebo_condition_id.notna()]
    f = t3_features(data, version)
    case = f[f.market_set == "case"].merge(pl[["case_id", "case_condition_id"]].drop_duplicates(), left_on=["case_id", "condition_id"], right_on=["case_id", "case_condition_id"])
    plc = f[f.market_set == "placebo"].merge(pl[["case_id", "placebo_condition_id"]], left_on=["case_id", "condition_id"], right_on=["case_id", "placebo_condition_id"])
    d = pd.concat([case.assign(y=1), plc.assign(y=0)], ignore_index=True).merge(splits, on="case_id")
    X = d[T3_FEATURES].astype(float)
    res = {"n_case_markets": int(d.y.sum()), "n_placebo_markets": int((d.y == 0).sum())}
    for name, m in models().items():
        cv = np.full(len(d), np.nan)
        for a, b in GroupKFold(5).split(X, d.y, d.case_id):
            m.fit(X.iloc[a], d.y.iloc[a]); cv[b] = m.predict_proba(X.iloc[b])[:, 1]
        res[f"{name}_grouped_cv_auc"] = round(roc_auc_score(d.y, cv), 4)
        tr, te = d.split == "train", d.split == "test"
        m.fit(X[tr], d.y[tr]); res[f"{name}_test_auc"] = round(roc_auc_score(d.y[te], m.predict_proba(X[te])[:, 1]), 4)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--data", default=os.path.join(here, "..", "data")); ap.add_argument("--out", default=os.path.join(here, "baselines.json"))
    a = ap.parse_args()
    splits = pd.read_csv(os.path.join(here, "splits.csv"))[["case_id", "split"]]
    out = dict(seed=SEED, protocol="A15", leakage=dict(T1=T1_LEAKAGE, T2=T2_LEAKAGE, T3=T3_LEAKAGE),
               features=dict(T1=T1_FEATURES, T2=T2_FEATURES, T3=T3_FEATURES))
    for v in ["precise", "day"]:
        out[v] = dict(T1=t1(a.data, splits, v), T2=t2(a.data, splits, v), T3=t3(a.data, splits, v)); print(v, "done", flush=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({v: {t: {k: x for k, x in r.items() if not isinstance(x, dict) or "ap" in x} for t, r in out[v].items()} for v in ["precise", "day"]}, indent=1, default=float)[:6000])
