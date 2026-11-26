"""Gate 2, blind step: ladders, Signal A and Signal B episodes, counts and power from p_a only. NO outcome is loaded.

Inputs: data/v3/market_info.csv (Gate 1 universe and exclusions), data/v3/targets.csv (tokens), fill cache data/raw/v2_fills/.
Outputs: data/v3/gate2_ladders.csv, data/v3/gate2_episodes.csv.gz (blind), data/results/gate2_power.md/.json.
Rules: rules/frozen_gate2.md."""
import json, math, re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "data"; FD = DATA / "raw" / "v2_fills"; RES = DATA / "results"
DAY, TEN = 86400, 600
TS = (1000, 2500, 10000); MAIN_T = 2500
P0_MAX, MULT, ADD, SELL_SHARE, LATER_SHARE = 0.35, 1.5, 0.03, 0.10, 0.10
P1_END = pd.Timestamp("2026-05-06", tz="UTC").timestamp()
BANNED = {"yes_won", "won", "excess", "outcomePrices", "resolution", "after_resolution"}

mi = pd.read_csv(DATA / "v3" / "market_info.csv", dtype={"event_id": str, "series_id": str})
assert not (BANNED & set(mi))
tg = pd.read_csv(DATA / "v3" / "targets.csv", usecols=["conditionId", "yes_token", "no_token"], dtype=str).set_index("conditionId")
mi["core"] = mi.source.str.contains("v2_165|mil_rest|mil_over12m|v1")
mi["ffic"] = mi.source.str.contains("ffic")
mi = mi[(mi.core | mi.ffic) & (mi.status == "ok")].copy()
mi["unit_event"] = mi.event_id.fillna(mi.conditionId)
mi["grp"] = np.where(mi.series_id.notna(), "s:" + mi.series_id.astype(str), "e:" + mi.unit_event)
M = mi.set_index("conditionId")

# ---------------- ladders (titles and dates only) ----------------
DL = re.compile(r"^(?P<stem>.*\S)\s+(?:by|before)\s+(?P<dl>(?:(?!\s(?:by|before)\s).)+?)\s*\??\s*$", re.I)
def stem(q):
    m = DL.match(str(q).strip())
    return re.sub(r"\s+", " ", m.group("stem").lower()).strip() if m else None
mi["stem"] = mi.question.map(stem)
lad = []
for (g, s), d in mi[mi.core & mi.stem.notna()].groupby(["grp", "stem"]):
    d = d.sort_values("start_ts")
    life_end = np.minimum(d.end_ts.fillna(d.res_ts), d.res_ts)
    comp, cur_end, k = [], -1, -1
    for st, en in zip(d.start_ts.fillna(d.first_fill_ts), life_end):  # overlapping lives -> one ladder
        if st > cur_end: k += 1
        comp.append(k); cur_end = max(cur_end, en)
    d = d.assign(comp=comp)
    for c, dd in d.groupby("comp"):
        if dd.end_ts.nunique() >= 3:
            last = dd.end_ts.max()
            for r in dd.itertuples():
                lad.append(dict(ladder_id=f"{g}|{s}|{c}", grp=g, stem=s, conditionId=r.conditionId, question=r.question,
                                deadline_ts=int(r.end_ts), is_last=bool(r.end_ts == last), n_markets=len(dd), n_deadlines=dd.end_ts.nunique(), excluded=bool(r.excluded)))
LAD = pd.DataFrame(lad)
LAD.to_csv(DATA / "v3" / "gate2_ladders.csv", index=False)

# ---------------- helpers ----------------
def load(cid):
    tk = tg.loc[cid]
    d = pd.read_csv(FD / f"{cid}.csv.gz", dtype={"token_id": str}, usecols=["proxy_wallet", "token_id", "timestamp", "size", "price", "side"])
    d["tok"] = np.where(d.token_id == tk.yes_token, "Yes", np.where(d.token_id == tk.no_token, "No", "?"))
    d = d[d.tok != "?"].rename(columns=dict(proxy_wallet="wallet", timestamp="ts"))
    d["usd"] = d["size"] * d["price"]; d["buy"] = d.side == "BUY"
    return d.sort_values("ts", kind="stable").reset_index(drop=True)

def episodes(f, side, trig, t_dec, mode):
    """trig: list of (ts, wallet, price). Chain same-side triggers <= 24 h apart; p_a as in Gate 1."""
    if not trig: return []
    trig = sorted(trig)
    px = np.where(f.tok == side, f.price, 1 - f.price); fts = f.ts.values; sz = f["size"].values
    groups, cur = [], [trig[0]]
    for a, b in zip(trig, trig[1:]):
        if b[0] - a[0] > DAY: groups.append(cur); cur = [b]
        else: cur.append(b)
    groups.append(cur); out = []
    for gr in groups:
        ta, _, tp = gr[0]
        win = (fts > ta) & (fts <= ta + TEN)
        if win.any() and sz[win].sum() > 0: pa, src = float((px[win] * sz[win]).sum() / sz[win].sum()), "10min"
        else:
            bf = np.where(fts < ta)[0]
            pa, src = (float(px[bf[-1]]), "last_before") if len(bf) else (float(tp), "trigger")
        keep = pa < 0.5 and (mode == "live" or ta < t_dec)
        out.append(dict(side=side, t_a=int(ta), p_a=pa, pa_src=src, n_wallets=len({w for _, w, _ in gr}),
                        wallets=";".join(sorted({w[:8] for _, w, _ in gr})), keep=keep))
    return out

def horizon(cid, mode):
    r = M.loc[cid]
    return (int(r.res_ts) - 3600) if mode == "live" else int(r.t_dec)

# ---------------- Signal A ----------------
def signal_a_market(cid):
    r = M.loc[cid]; f = load(cid); rows = []
    for mode in ("std", "live"):
        if mode == "std" and r.excluded: continue
        h = horizon(cid, mode); ff = f[f.ts < h]
        for side in ("Yes", "No"):
            d = ff[ff.tok == side]
            tot = d[d.buy].groupby("wallet").usd.sum(); cand = set(tot[tot >= min(TS)].index)
            trig = {T: [] for T in TS}
            for w, g in d[d.wallet.isin(cand)].groupby("wallet", sort=False):
                b = g.buy.values; ts = g.ts.values; p = g.price.values; u = g.usd.values
                if not b.any(): continue
                i0 = np.argmax(b); p0, t0 = p[i0], ts[i0]
                if p0 > P0_MAX: continue
                # sums over fills with a STRICTLY earlier timestamp than each fill
                bu = np.where(b, u, 0.0); su = np.where(~b, u, 0.0)
                cb, cs = np.concatenate([[0], np.cumsum(bu)]), np.concatenate([[0], np.cumsum(su)])
                first_idx = np.searchsorted(ts, ts, side="left")
                bb, sb = cb[first_idx], cs[first_idx]
                ok_price = b & (ts > t0) & (p >= max(MULT * p0, p0 + ADD))
                ok_sell = sb < SELL_SHARE * bb
                for T in TS:
                    hit = np.where(ok_price & ok_sell & (bb - sb >= T))[0]
                    if len(hit): trig[T].append((int(ts[hit[0]]), w, float(p[hit[0]])))
            for T in TS:
                for e in episodes(f, side, trig[T], r.t_dec, mode):
                    rows.append(dict(signal="A", conditionId=cid, threshold=T, mode=mode, **e))
    return rows

# ---------------- Signal B ----------------
def signal_b_ladder(lid):
    L = LAD[LAD.ladder_id == lid].sort_values("deadline_ts")
    F = {c: load(c) for c in L.conditionId}
    Y = {c: F[c][F[c].tok == "Yes"].assign(net=lambda d: np.where(d.buy, d.usd, -d.usd)) for c in F}
    rows = []
    for r in L.itertuples():
        for kind in ("B", "B_last"):
            if kind == "B" and r.is_last: continue
            if kind == "B_last" and not r.is_last: continue
            others = L[L.deadline_ts > r.deadline_ts] if kind == "B" else L[L.deadline_ts < r.deadline_ts]
            for mode in ("std", "live"):
                if mode == "std" and r.excluded: continue
                h = horizon(r.conditionId, mode)
                d = Y[r.conditionId]; d = d[d.ts < h]
                o = pd.concat([Y[c] for c in others.conditionId]) if len(others) else d.iloc[:0]
                tot = d[d.buy].groupby("wallet").usd.sum(); cand = set(tot[tot >= min(TS)].index)
                og = dict(tuple(o[o.wallet.isin(cand)].sort_values("ts", kind="stable").groupby("wallet")))
                trig = {T: [] for T in TS}
                for w, g in d[d.wallet.isin(cand)].groupby("wallet", sort=False):
                    ts = g.ts.values; net = g.net.values; b = g.buy.values
                    c = np.concatenate([[0], np.cumsum(net)]); hi = np.arange(1, len(ts) + 1); lo = np.searchsorted(ts, ts - DAY, side="right")
                    win = c[hi] - c[lo]
                    if w in og:
                        ot, on = og[w].ts.values, og[w].net.values; oc = np.concatenate([[0], np.cumsum(on)])
                        ohi = np.searchsorted(ot, ts, side="right"); olo = np.searchsorted(ot, ts - DAY, side="right")
                        owin = oc[ohi] - oc[olo]
                    else: owin = np.zeros(len(ts))
                    for T in TS:
                        cond = b & (win >= T) & (owin < LATER_SHARE * win)
                        prev = False
                        for i in np.where(b)[0]:
                            if cond[i] and not prev: trig[T].append((int(ts[i]), w, float(g.price.values[i])))
                            prev = bool(cond[i])
                for T in TS:
                    for e in episodes(F[r.conditionId], "Yes", trig[T], M.loc[r.conditionId].t_dec, mode):
                        rows.append(dict(signal=kind, conditionId=r.conditionId, threshold=T, mode=mode, ladder_id=lid, **e))
    return rows

if __name__ == "__main__":
    with ProcessPoolExecutor(4) as ex:
        A = [x for out in ex.map(signal_a_market, mi.conditionId.tolist(), chunksize=4) for x in out]
        Bs = [x for out in ex.map(signal_b_ladder, LAD.ladder_id.unique().tolist()) for x in out]
    E = pd.DataFrame(A + Bs)
    E = E.merge(mi[["conditionId", "unit_event", "series_id", "category", "res_ts", "core", "ffic", "excluded"]], on="conditionId")
    E["period"] = np.where(E.res_ts < P1_END, "P1", "P2")
    E.drop(columns=["res_ts"]).sort_values(["signal", "threshold", "mode", "conditionId", "t_a"]).to_csv(DATA / "v3" / "gate2_episodes.csv.gz", index=False, compression="gzip")

    # ---------------- blind power ----------------
    Z = 2.241 + 0.842  # two-sided 97.5% (Bonferroni over 2 signals) and 80% power
    def mde(d, unit):
        v = [g.p_a.values for _, g in d.groupby(unit)]
        if not v: return dict(units=0, mde_ind=None, mde_cor=None)
        U = len(v); si = math.sqrt(sum((p * (1 - p)).sum() / len(p) ** 2 for p in v)) / U; sc = math.sqrt(sum((p * (1 - p)).mean() for p in v)) / U
        return dict(units=U, mde_ind=Z * si, mde_cor=Z * sc)
    rows = []
    for sig in ("A", "B", "B_last"):
        for T in TS:
            for mode in ("std", "live"):
                d = E[(E.signal == sig) & (E.threshold == T) & (E["mode"] == mode) & E.keep & E.core]
                rows.append(dict(signal=sig, threshold=T, mode=mode, markets=d.conditionId.nunique(), events=d.unit_event.nunique(), episodes=len(d),
                                 **{f"event_{k}": v for k, v in mde(d, "unit_event").items()}, **{f"market_{k}": v for k, v in mde(d, "conditionId").items()}))
    cat = []
    for sig in ("A", "B"):
        d = E[(E.signal == sig) & (E.threshold == MAIN_T) & (E["mode"] == "std") & E.keep & E.core]
        for (c, per), g in d.groupby(["category", "period"]):
            cat.append(dict(signal=sig, category=c, period=per, markets=g.conditionId.nunique(), events=g.unit_event.nunique(), episodes=len(g), **mde(g, "unit_event")))
    pa = {sig: np.quantile(E[(E.signal == sig) & (E.threshold == MAIN_T) & (E["mode"] == "std") & E.keep & E.core].p_a, [.1, .25, .5, .75, .9]).round(3).tolist()
          for sig in ("A", "B", "B_last") if len(E[(E.signal == sig) & (E.threshold == MAIN_T) & E.keep & E.core])}
    f = lambda x: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else (f"{x:.3f}" if isinstance(x, float) else f"{x:,}")
    md = ["# Gate 2: blind counts and power (no outcome loaded)\n\nGenerated by `src/gate2_signals.py` before the Gate 2 freeze. Core universe and exclusions as in Gate 1. "
          "MDE = (2.241 + 0.842) x SE: two-sided 97.5% (Bonferroni for the two signals), 80% power; SE from p_a(1 - p_a) only. "
          "'indep.' treats a unit's episodes as independent; 'corr.' as fully dependent. Mode 'std' = fills before T_dec, Gate 1 exclusions. Mode 'live' = fills up to resolution - 1 h, no T_dec exclusion. B_last is the descriptive comparison group (concentration on the last deadline).\n",
          f"Ladders found: {LAD.ladder_id.nunique()} ladders, {len(LAD)} markets ({int(LAD.is_last.sum())} last-deadline contracts). The full list is in `data/v3/gate2_ladders.csv`.\n",
          "| signal | threshold | mode | markets | events | episodes | MDE event indep. | MDE event corr. | MDE market indep. | MDE market corr. |\n|---|---|---|---|---|---|---|---|---|---|\n" +
          "".join(f"| {r['signal']} | ${r['threshold']:,} | {r['mode']} | {r['markets']:,} | {r['events']:,} | {r['episodes']:,} | {f(r['event_mde_ind'])} | {f(r['event_mde_cor'])} | {f(r['market_mde_ind'])} | {f(r['market_mde_cor'])} |\n" for r in rows),
          "\n**By category x period ($2,500, std):**\n\n| signal | category | period | markets | events | episodes | MDE event indep. | MDE event corr. |\n|---|---|---|---|---|---|---|---|\n" +
          "".join(f"| {r['signal']} | {r['category']} | {r['period']} | {r['markets']} | {r['events']} | {r['episodes']} | {f(r['mde_ind'])} | {f(r['mde_cor'])} |\n" for r in cat),
          f"\np_a quantiles (10/25/50/75/90%, $2,500, std): {pa}\n"]
    (RES / "gate2_power.md").write_text("\n".join(md))
    json.dump(dict(rows=rows, by_cat=cat, pa_quantiles=pa, n_ladders=int(LAD.ladder_id.nunique()), n_ladder_markets=len(LAD)), open(RES / "gate2_power.json", "w"), indent=1)
    print("\n".join(md))
