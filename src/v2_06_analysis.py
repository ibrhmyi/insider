"""v2 steps 2 and 3: persistence test, logistic model with price offset, market-level validation. Writes data/results/v2_*.{json,csv}."""
import json, numpy as np, pandas as pd
from common import *
from v2_features import FEATS, K_SHRINK
rng = np.random.default_rng(191)
RES = DATA / "results"; RES.mkdir(exist_ok=True)
U = pd.read_csv(DATA / "v2" / "units.csv.gz")
SPLIT = parse_ts("2026-04-01T00:00:00Z"); Y2026 = parse_ts("2026-01-01T00:00:00Z")
OUT = {}
logit = lambda p: np.log(p / (1 - p)); sig = lambda z: 1 / (1 + np.exp(-z))

# ---------------- STEP 2: persistence ----------------
a = U[U.res_ts < Y2026]; b = U[U.res_ts >= Y2026]
g25 = a.groupby("proxy_wallet").excess.agg(["mean", "size"]); g25 = g25[g25["size"] >= 5]
cut = g25["mean"].quantile(0.95); top = set(g25[g25["mean"] >= cut].index)
w26 = b.groupby("proxy_wallet").excess.agg(["mean", "size"])
def boot_mean(x, B=4000):
    x = np.asarray(x); idx = rng.integers(0, len(x), (B, len(x))); m = x[idx].mean(1); return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
t26 = w26[w26.index.isin(top)]["mean"].values
o26 = w26[~w26.index.isin(top)]["mean"].values
o26_eligible = w26[w26.index.isin(set(g25.index) - top)]["mean"].values
d = rng.integers
def boot_diff(x, y, B=4000):
    bx = np.asarray(x)[rng.integers(0, len(x), (B, len(x)))].mean(1); by = np.asarray(y)[rng.integers(0, len(y), (B, len(y)))].mean(1)
    dd = bx - by; return float(np.mean(x) - np.mean(y)), float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))
OUT["persistence"] = dict(n_wallets_ge5_markets_2025=len(g25), top5pct_cutoff_mean_excess_2025=float(cut), n_top=len(top),
    top_mean_excess_2025=float(g25.loc[list(top), "mean"].mean()),
    top_with_2026_units=len(t26), top_2026=boot_mean(t26) if len(t26) > 1 else None,
    others_with_2026_units=len(o26), others_2026=boot_mean(o26),
    eligible_others_with_2026_units=len(o26_eligible), eligible_others_2026=boot_mean(o26_eligible),
    diff_top_minus_others=boot_diff(t26, o26) if len(t26) > 1 else None,
    diff_top_minus_eligible_others=boot_diff(t26, o26_eligible) if len(t26) > 1 and len(o26_eligible) > 1 else None,
    top_2026_unit_level_mean=float(b[b.proxy_wallet.isin(top)].excess.mean()), top_2026_units=int(b.proxy_wallet.isin(top).sum()))

# ---------------- STEP 3: model ----------------
def fit(X, y, off, lam, iters=50):
    Xa = np.c_[np.ones(len(X)), X]; w = np.zeros(Xa.shape[1]); R = lam * np.eye(Xa.shape[1]); R[0, 0] = 0
    for _ in range(iters):
        p = sig(Xa @ w + off); g = Xa.T @ (p - y) + R @ w
        H = (Xa * (p * (1 - p))[:, None]).T @ Xa + R + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(H, g); w -= step
        if np.abs(step).max() < 1e-7: break
    return w
def pred(w, X, off): return sig(np.c_[np.ones(len(X)), X] @ w + off)
def ll(p, y): p = np.clip(p, 1e-6, 1 - 1e-6); return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
tr = U[U.res_ts < SPLIT].reset_index(drop=True); va = U[U.res_ts >= SPLIT].reset_index(drop=True)
mu, sd = tr[FEATS].mean(), tr[FEATS].std().replace(0, 1)
Z = lambda df: ((df[FEATS] - mu) / sd).values
off = lambda df: logit(df.price.values)
Xtr, ytr, otr = Z(tr), tr.won.values, off(tr)
# lambda chosen on an inner time split of the training set (earliest 75% fit, latest 25% hold out)
cut_t = tr.res_ts.quantile(0.75); i1 = (tr.res_ts <= cut_t).values
lam_res = {}
for lam in [1, 10, 100, 1000, 10000]:
    w = fit(Xtr[i1], ytr[i1], otr[i1], lam); lam_res[lam] = ll(pred(w, Xtr[~i1], otr[~i1]), ytr[~i1])
LAM = min(lam_res, key=lam_res.get); W = fit(Xtr, ytr, otr, LAM)
OUT["model"] = dict(lambda_grid_inner_logloss=lam_res, lam=LAM, n_train_units=len(tr), n_train_markets=int(tr.conditionId.nunique()),
                    n_val_units=len(va), n_val_markets=int(va.conditionId.nunique()), intercept=float(W[0]), coef=dict(zip(FEATS, map(float, W[1:]))),
                    feat_mean=mu.to_dict(), feat_sd=sd.to_dict())
# coefficient CIs: bootstrap over training markets
mk = tr.conditionId.values; ums = np.unique(mk); bi = {m: np.where(mk == m)[0] for m in ums}; BC = []
for _ in range(200):
    pick = rng.choice(ums, len(ums)); ix = np.concatenate([bi[m] for m in pick]); BC.append(fit(Xtr[ix], ytr[ix], otr[ix], LAM))
BC = np.array(BC); OUT["model"]["coef_ci95"] = {f: [float(np.percentile(BC[:, i + 1], 2.5)), float(np.percentile(BC[:, i + 1], 97.5))] for i, f in enumerate(FEATS)}
# unit-level validation
Xva, yva, ova = Z(va), va.won.values, off(va); pva = pred(W, Xva, ova); pmk = sig(ova)
def clus_boot(df, f, B=1000):
    m = df.conditionId.values; um = np.unique(m); ix = {k: np.where(m == k)[0] for k in um}; out = []
    for _ in range(B):
        j = np.concatenate([ix[k] for k in rng.choice(um, len(um))]); out.append(f(j))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))
brier = lambda p, y: float(np.mean((p - y) ** 2))
OUT["unit_validation"] = dict(n_units=len(va), logloss_market=ll(pmk, yva), logloss_model=ll(pva, yva), brier_market=brier(pmk, yva), brier_model=brier(pva, yva),
    logloss_diff_model_minus_market=ll(pva, yva) - ll(pmk, yva),
    logloss_diff_ci=clus_boot(va, lambda j: ll(pva[j], yva[j]) - ll(pmk[j], yva[j])), brier_diff_ci=clus_boot(va, lambda j: brier(pva[j], yva[j]) - brier(pmk[j], yva[j])))
# score = model linear predictor without offset, centred on training mean
tr["score"] = Xtr @ W[1:]; va["score"] = Xva @ W[1:]
# out-of-fold scores for training units (5 folds over training markets) so the market-level stage does not use in-sample scores
folds = {m: rng.integers(0, 5) for m in ums}; fo = np.array([folds[m] for m in mk]); oof = np.zeros(len(tr))
for k in range(5):
    wk = fit(Xtr[fo != k], ytr[fo != k], otr[fo != k], LAM); oof[fo == k] = Xtr[fo == k] @ wk[1:]
tr["score_oof"] = oof
SC = pd.concat([tr[["proxy_wallet", "conditionId", "side_name", "score_oof"]].rename(columns={"score_oof": "score"}),
                va[["proxy_wallet", "conditionId", "side_name", "score"]]])

# ---------------- market level ----------------
MI = pd.read_csv(DATA / "v2" / "market_info.csv").set_index("conditionId")
buys = pd.read_csv(DATA / "v2" / "buys.csv.gz"); buys = buys[buys.pre]
buys = buys.merge(SC, on=["proxy_wallet", "conditionId", "side_name"], how="left"); buys["score"] = buys.score.fillna(0.0)
buys["sgn"] = np.where(buys.side_name == "Yes", 1.0, -1.0); buys["ws"] = buys.sgn * buys.usd * buys.score
bg = {c: g.sort_values("timestamp") for c, g in buys.groupby("conditionId")}
cand = pd.read_csv(DATA / "v2" / "markets_ranked.csv", usecols=["conditionId", "yes_won"]).set_index("conditionId")
Ns = [1, 3, 6, 12, 24, 48, 72]; FR = [0.25, 0.5, 0.75]; pts = []
for c in U.conditionId.unique():
    f = pd.read_csv(RAW / "v2_fills" / f"{c}.csv.gz", usecols=["timestamp", "token_id", "side", "price", "size"], dtype={"token_id": str})
    m = MI.loc[c]; yt = pd.read_csv(DATA / "v2" / "markets_ranked.csv", usecols=["conditionId", "yes_token"], dtype={"yes_token": str}).set_index("conditionId").loc[c, "yes_token"] if False else None
    f = f[f.timestamp <= m.cutoff_ts].sort_values("timestamp", kind="stable")
    ypx = np.where(f.token_id.values == f.token_id.values[0], f.price.values, 1 - f.price.values)  # placeholder, fixed below
    pts.append((c, f))
# yes price needs the Yes token id
RK = pd.read_csv(DATA / "v2" / "markets_ranked.csv", usecols=["conditionId", "yes_token"], dtype={"yes_token": str}).set_index("conditionId")
rows = []
for c, f in pts:
    m = MI.loc[c]; ypx = np.where(f.token_id.values == RK.loc[c, "yes_token"], f.price.values, 1 - f.price.values); ts = f.timestamp.values
    b = bg.get(c)
    if b is None or len(f) < 50: continue
    for fr in FR:
        te = ts[0] + fr * (m.cutoff_ts - ts[0]); k = np.searchsorted(ts, te, side="right")
        if k < 20: continue
        pm = float(np.median(ypx[k - 10:k]))
        if not (0.03 <= pm <= 0.97): continue
        r = dict(conditionId=c, frac=fr, t_eval=int(te), p_mkt=pm, y=int(cand.loc[c, "yes_won"]), res_ts=int(m.res_ts))
        bt, bu, bw = b.timestamp.values, b.usd.values, b.ws.values
        for N in Ns:
            s = (bt <= te) & (bt > te - N * 3600); den = bu[s].sum()
            r[f"Z{N}"] = float(bw[s].sum() / den) if den > 0 else 0.0; r[f"usd{N}"] = float(den)
        rows.append(r)
PT = pd.DataFrame(rows); PT.to_csv(RES / "v2_market_eval_points.csv", index=False)
ptr = PT[PT.res_ts < SPLIT]; pva_ = PT[PT.res_ts >= SPLIT]
def fit_gamma(df, N):
    Zs = df[f"Z{N}"].values; y = df.y.values; o = logit(df.p_mkt.values); g = 0.0
    for _ in range(50):
        p = sig(o + g * Zs); gr = np.sum(Zs * (p - y)) + 1.0 * g * 0; h = np.sum(Zs ** 2 * p * (1 - p)) + 1e-6
        st = gr / h; g -= st
        if abs(st) < 1e-8: break
    return g
gres = {}
for N in Ns:
    g = fit_gamma(ptr, N); gres[N] = dict(gamma=float(g), train_logloss=ll(sig(logit(ptr.p_mkt.values) + g * ptr[f"Z{N}"].values), ptr.y.values))
base_tr = ll(ptr.p_mkt.values, ptr.y.values); NSEL = min(gres, key=lambda n: gres[n]["train_logloss"]); GAM = gres[NSEL]["gamma"]
OUT["market_level"] = dict(n_points_train=len(ptr), n_markets_train=int(ptr.conditionId.nunique()), n_points_val=len(pva_), n_markets_val=int(pva_.conditionId.nunique()),
    train_logloss_market=base_tr, per_N=gres, N_selected=NSEL, gamma=GAM, eval_fractions=FR)
pm_ = pva_.p_mkt.values; pmod = sig(logit(pm_) + GAM * pva_[f"Z{NSEL}"].values); yv = pva_.y.values; mv = pva_.conditionId.values
def mboot(f, B=2000):
    um = np.unique(mv); ix = {k: np.where(mv == k)[0] for k in um}; o = []
    for _ in range(B):
        j = np.concatenate([ix[k] for k in rng.choice(um, len(um))]); o.append(f(j))
    return float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5))
OUT["market_level"]["validation"] = dict(brier_market=brier(pm_, yv), brier_model=brier(pmod, yv), logloss_market=ll(pm_, yv), logloss_model=ll(pmod, yv),
    brier_diff_model_minus_market=brier(pmod, yv) - brier(pm_, yv), brier_diff_ci=mboot(lambda j: brier(pmod[j], yv[j]) - brier(pm_[j], yv[j])),
    logloss_diff_ci=mboot(lambda j: ll(pmod[j], yv[j]) - ll(pm_[j], yv[j])),
    brier_market_ci=mboot(lambda j: brier(pm_[j], yv[j])), brier_model_ci=mboot(lambda j: brier(pmod[j], yv[j])))
# calibration table (validation, model probability vs market probability)
bins = [0, .1, .2, .35, .5, .65, .8, .9, 1.0001]; cal = []
for nm, pp in [("model", pmod), ("market", pm_)]:
    cb = pd.cut(pp, bins, right=False)
    for k, gdf in pd.DataFrame(dict(p=pp, y=yv, c=cb)).groupby("c", observed=True): cal.append(dict(which=nm, bin=str(k), n=len(gdf), mean_pred=float(gdf.p.mean()), observed=float(gdf.y.mean())))
pd.DataFrame(cal).to_csv(RES / "v2_calibration.csv", index=False)
# documented wallets: where do they rank among units of their market (percentile of score)
lab = pd.read_csv(DATA / "labels" / "documented_wallets_matched.csv"); doc = []
allU = pd.concat([tr.assign(score=tr.score), va])
for _, r in lab.iterrows():
    w = r.matched_wallet
    if not isinstance(w, str): doc.append(dict(label=r.label_id, status="no matched address")); continue
    s = allU[allU.proxy_wallet == w]
    if s.empty: doc.append(dict(label=r.label_id, wallet=w[:8] + "..", status="not in the v2 universe or below $100/no stats (market not in the 165, or no position)")); continue
    for _, u in s.iterrows():
        pool = allU[allU.conditionId == u.conditionId]
        doc.append(dict(label=r.label_id, wallet=w[:8] + "..", market=MI.loc[u.conditionId, "question"], side=u.side_name, usd=float(u.usd_bought_dec),
                        rank=int((pool.score > u.score).sum() + 1), of=len(pool), pct=float((pool.score < u.score).mean()), in_train=bool(u.res_ts < SPLIT), won=int(u.won)))
OUT["documented"] = doc
OUT["splits"] = dict(split_ts=SPLIT, train_markets=int(tr.conditionId.nunique()), val_markets=int(va.conditionId.nunique()))
json.dump(OUT, open(RES / "v2_analysis.json", "w"), indent=1, default=str)
print(json.dumps(OUT, indent=1, default=str)[:9000])
