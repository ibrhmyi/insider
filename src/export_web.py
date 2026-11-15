"""Export the frozen v1 outputs to compact JSON for the web app (web/public/data/). No re-analysis.

Reads only files already produced by the frozen pipeline:
  data/markets.csv, data/news_events.csv, data/labels/*, data/clean/v1_fills_*.csv, data/clean/v1_wallet_*.csv,
  data/results/v1_wallet_scores.csv, v1_validation.csv, v1_layer1.json, v1_layer2.json, v1_layer2_seeds.csv,
  v1_perm_null_*.npy, comparison_summary.{csv,md}, maduro_blind_validation.md
Writes:
  web/public/data/markets.json, {m}_timeline.json, {m}_wallets.json, {m}_alerts.json, {m}_buys.json,
  validation.json, layer2.json, v0_summary.json, live_example.json
  web/tests/fixtures/flags_20.json   (inputs + Python results for 20 wallets; the TypeScript port is tested on it)

Privacy rule (HANDOFF rule 7): full addresses only for wallets matched to data/labels/documented_wallets.csv.
Every other wallet is identified by its shortest unique address prefix within the market (at least 0x + 4 hex).
Handles (name/pseudonym) are exported only for documented wallets, as reported by the cited sources.
"""
import json
import re

import numpy as np
import pandas as pd

from common import CLEAN, DATA, ROOT

RES = DATA / "results"
OUT = ROOT / "web" / "public" / "data"
FIX = ROOT / "web" / "tests" / "fixtures"
MARKETS = ["iran", "maduro", "nobel"]
SHORT = {"iran": "Iran strike", "maduro": "Maduro out", "nobel": "Machado Nobel"}
FLAG_IDS = ["F1", "F2", "F3", "F4", "F5", "F6"]
MAX_POINTS = 2000
MERGE_S = 30 * 60  # same merge rule as Layer 2 seeds (fills by one wallet within 30 min)

MK = pd.read_csv(DATA / "markets.csv").set_index("market_key")
NEWS = pd.read_csv(DATA / "news_events.csv")
L1 = json.load(open(RES / "v1_layer1.json"))
L2 = json.load(open(RES / "v1_layer2.json"))
SC = pd.read_csv(RES / "v1_wallet_scores.csv")
VAL = pd.read_csv(RES / "v1_validation.csv")
LAB = pd.read_csv(DATA / "labels" / "documented_wallets_matched.csv")
ST = pd.read_csv(CLEAN / "v1_wallet_stats.csv").set_index("wallet")
WN = pd.read_csv(CLEAN / "v1_wallet_windows.csv").set_index(["market_key", "wallet"])
SEEDS = pd.read_csv(RES / "v1_layer2_seeds.csv")
FLAGS = L1["flags"]
DOC = {(r.market_key, r.matched_wallet) for r in LAB.itertuples() if r.match_status == "matched"}


def num(x, nd=None):
    """JSON-safe number (NaN -> None)."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x):
        return None
    x = float(x)
    return round(x, nd) if nd is not None else x


def t_news(m):
    return int(NEWS[NEWS.market_key == m].news_epoch.min())


def prefixes(wallets):
    """Shortest unique prefix (>= 4 hex chars after 0x) for each wallet in one market."""
    ws = sorted(set(wallets))
    out = {}
    for i, w in enumerate(ws):
        n = 4
        neigh = [ws[j] for j in (i - 1, i + 1) if 0 <= j < len(ws)]
        while any(o[: 2 + n] == w[: 2 + n] for o in neigh):
            n += 1
        out[w] = w[: 2 + n]
    return out


def load_fills(m):
    f = pd.read_csv(CLEAN / f"v1_fills_{m}.csv").sort_values("timestamp", kind="stable").reset_index(drop=True)
    yes = f.outcome_index == 0
    f["dir"] = np.where(yes == (f.side == "BUY"), 1, -1)
    f["yes_price"] = np.where(yes, f.price, 1 - f.price)
    f["usd"] = f["size"] * f["price"]
    return f


def timeline(m, f, S, pref):
    """YES price of the last fill (frozen price-path proxy), downsampled to <= MAX_POINTS by time bins (last fill per bin)."""
    g = f[~f.after_resolution]
    t, p = g.timestamp.values, g.yes_price.values
    if len(t) > MAX_POINTS:
        edges = np.linspace(t.min(), t.max() + 1, MAX_POINTS + 1)
        b = np.searchsorted(edges, t, side="right") - 1
        last = np.r_[np.nonzero(np.diff(b))[0], len(b) - 1]
        t, p = t[last], p[last]
    T = t_news(m)
    hi = S[S.score >= FLAGS["HIGH"]].set_index("wallet")
    buys = f[(f.side == "BUY") & (f.timestamp < T) & (~f.after_resolution) & f.proxy_wallet.isin(hi.index)]
    pts = []
    for w, gw in buys.groupby("proxy_wallet"):
        gw = gw.sort_values("timestamp")
        start, grp = None, []
        for r in list(gw.itertuples()) + [None]:
            if r is not None and start is not None and r.timestamp - start <= MERGE_S:
                grp.append(r)
                continue
            if grp:
                usd = sum(x.usd for x in grp)
                by = {}
                for x in grp:
                    by[x.outcome] = by.get(x.outcome, 0) + x.usd
                pts.append(dict(t=int(grp[0].timestamp), usd=round(usd, 2), side=max(by, key=by.get),
                                yes=round(float(grp[-1].yes_price), 4), w=pref[w], score=int(hi.loc[w, "score"]),
                                flags=hi.loc[w, "flags_fired"], doc=(m, w) in DOC))
            if r is not None:
                start, grp = r.timestamp, [r]
    pts.sort(key=lambda d: d["t"])
    return dict(market=m, t_news=T, resolution_epoch=int(MK.loc[m, "resolution_epoch"]),
                price=[[int(a), round(float(b), 4)] for a, b in zip(t, p)], high_buys=pts,
                n_fills=int(len(g)), n_points=int(len(t)),
                note="YES price of the last fill at or before each time (no historical mid-price exists); "
                     f"downsampled to at most {MAX_POINTS} points by keeping the last fill in each equal time bin.")


BUYS_WINDOW_H = 72  # every pre-news buy in the last 72 h, for the scrollytelling chart


def recent_buys(m, f, S, pref):
    """All pre-news BUY fills in the last BUYS_WINDOW_H hours, merged per wallet within 30 min (same rule as high_buys).
    Each buy points at its wallet's frozen score and pre-news USD; nothing is re-scored."""
    T = t_news(m)
    sc = S.set_index("wallet")
    b = f[(f.side == "BUY") & (f.timestamp < T) & (f.timestamp >= T - BUYS_WINDOW_H * 3600) & (~f.after_resolution)]
    wallets, idx, rows = [], {}, []
    for w, gw in b.groupby("proxy_wallet"):
        if w not in sc.index:
            continue
        gw = gw.sort_values("timestamp")
        start, usd, yes, t0 = None, 0.0, 0.0, None
        merged = []
        for r in gw.itertuples():
            if start is not None and r.timestamp - start <= MERGE_S:
                usd += r.usd; yes = r.yes_price
            else:
                if start is not None:
                    merged.append((t0, usd, yes))
                start, t0, usd, yes = r.timestamp, r.timestamp, r.usd, r.yes_price
        merged.append((t0, usd, yes))
        if w not in idx:
            idx[w] = len(wallets)
            r = sc.loc[w]
            wallets.append(dict(id=pref[w], score=int(r.score), usd=round(float(r.F4_buy_usd), 2), doc=(m, w) in DOC))
        rows += [[int(t), round(float(y), 4), round(float(u), 2), idx[w]] for t, u, y in merged]
    rows.sort()
    return dict(market=m, t_news=T, window_h=BUYS_WINDOW_H, wallets=wallets, buys=rows,
                note="Every pre-news BUY in the window, merged per wallet within 30 min: [time, YES price, USD, wallet index].")


def handle_for(m, w):
    r = LAB[(LAB.market_key == m) & (LAB.matched_wallet == w) & (LAB.identifier_type == "handle")]
    return r.identifier.iloc[0] if len(r) else None


def wallets(m, S, pref):
    rows = []
    for r in S.sort_values("rank_in_market").itertuples():
        doc = (m, r.wallet) in DOC
        rows.append(dict(
            id=pref[r.wallet], addr=r.wallet if doc else None, handle=handle_for(m, r.wallet) if doc else None,
            doc=doc, rank=int(r.rank_in_market), score=int(r.score),
            flags=[k for k in FLAG_IDS if getattr(r, f"flag_{k}")],
            usd=num(r.F4_buy_usd, 2), avg_price=num(r.F3_vwap, 4), hours=num(r.F6_hours_before_news, 2),
            first_high_h=num(r.hours_before_news_first_high, 2),
            f1_days=num(r.F1_days, 3), f2_share=num(r.F2_share, 4), f2_markets=num(r.F2_n_markets),
            f5=num(r.F5_conviction, 4), side=r.main_outcome, n_buys=int(r.n_pre_buys),
            first_fill=r.first_fill_utc, acct_src=r.account_start_source,
            imp5=num(r.impact_5m_per_1k, 5), imp60=num(r.impact_60m_per_1k, 5),
            sens={"1000": int(r.score_F4_1000), "2500": int(r.score_F4_2500), "10000": int(r.score_F4_10000)},
            # post-hoc only: never part of the score
            post=dict(f7_won=bool(r.F7_correct), f8_dormant=None if pd.isna(r.F8_dormant) else bool(r.F8_dormant),
                      f8_trades_30d=num(r.F8_post30_trades)),
        ))
    return rows


def alerts(m, S, pref):
    """Per high-score wallet: Layer 2 seeds (A vs matched B) for the alert card."""
    hi = set(S[S.score >= FLAGS["HIGH"]].wallet)
    sd = SEEDS[(SEEDS.market_key == m) & SEEDS.A_wallet.isin(hi)]
    out = {}
    for w, g in sd.groupby("A_wallet"):
        out[pref[w]] = [dict(t=int(r.t), H=int(r.H), usd=num(r.usd, 2), dir=int(r.dir), h_before=num(r.hours_before_news, 2),
                             n_B=int(r.n_B), A_wallets=int(r.A_wallets), B_wallets=num(r.B_wallets, 2),
                             A_whales=int(r.A_whales), B_whales=num(r.B_whales, 2), A_bots=int(r.A_bots), B_bots=num(r.B_bots, 2),
                             A_price=num(r.A_price_move, 4), B_price=num(r.B_price_move, 4))
                        for r in g.sort_values(["t", "H"]).itertuples()]
    return out


def null_hist(m):
    a = np.load(RES / f"v1_perm_null_{m}.npy")
    v, c = np.unique(a, return_counts=True)
    return [[int(x), int(y)] for x, y in zip(v, c)]


def fixture(fills_by_m, S_by_m, pref_by_m):
    """20 wallets (all 7 documented + 13 others spread over scores) with their raw inputs and the Python results."""
    pick = []
    for m in MARKETS:
        S = S_by_m[m]
        pick += [(m, w) for (mm, w) in sorted(DOC) if mm == m]
    rng = np.random.default_rng(20261114)
    others = []
    for m in MARKETS:
        S = S_by_m[m]
        for s in sorted(S.score.unique()):
            c = S[(S.score == s) & ~S.wallet.isin([w for mm, w in DOC if mm == m])].wallet.values
            if len(c):
                others.append((m, rng.choice(c)))
    rng.shuffle(others)
    pick += others[: 20 - len(pick)]
    cases = []
    for m, w in pick:
        f, S = fills_by_m[m], S_by_m[m].set_index("wallet")
        T = t_news(m)
        g = f[(f.proxy_wallet == w) & (f.timestamp < T) & (~f.after_resolution)]
        st = ST.loc[w] if w in ST.index else None
        wn = WN.loc[(m, w)] if (m, w) in WN.index else None
        r = S.loc[w]
        cases.append(dict(
            id=f"{m}:{pref_by_m[m][w]}", t_news=T,
            fills=[[int(x.timestamp), x.side, int(x.outcome_index), float(x.size), float(x.price)] for x in g.itertuples()],
            join_date=num(st["join_date"]) if st is not None else None,
            n_markets=num(st["n_markets"]) if st is not None else None,
            vol_to_tnews=num(wn["vol_to_tnews_usdc"]) if wn is not None else None,
            first_activity=num(wn["first_activity_ts"]) if wn is not None else None,
            expected=dict(score=int(r.score), flags=[k for k in FLAG_IDS if r[f"flag_{k}"]],
                          F1_days=num(r.F1_days), F2_share=num(r.F2_share), F3_vwap=num(r.F3_vwap),
                          F4_buy_usd=num(r.F4_buy_usd), F5_conviction=num(r.F5_conviction),
                          F6_hours=num(r.F6_hours_before_news)),
        ))
    return dict(flags=FLAGS, cases=cases,
                note="Inputs are the frozen pipeline's own files; expected values are data/results/v1_wallet_scores.csv.")


def v0_summary():
    md = open(RES / "comparison_summary.md").read()
    p = float(re.search(r"permutation p = ([0-9.]+)", md).group(1))
    bias = float(re.search(r"Placebo bias on controls: \+([0-9.]+)", md).group(1))
    cs = pd.read_csv(RES / "comparison_summary.csv")
    q = cs[cs["quantile"] == 0.99]
    per = [dict(market=r.market_key, label=r.label, n_compared=int(r.n_compared), n_pre_news=int(r.n_pre_news),
                n_unmatched=int(r.n_unmatched), mean_excess=num(r.mean_excess_wallets, 2), n_alerts=int(r.n_alerts))
           for r in q.itertuples()]
    pooled = {}  # read from the frozen pooled table (re-pooling rounded per-market means would drift by 0.01)
    for lab in ["insider-possible", "insider-impossible"]:
        mt = re.search(rf"\|\s*0\.99\s*\|\s*{lab}\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(-?[0-9.]+)\s*\|", md)
        pooled[lab] = dict(n_seeds=int(mt.group(1)), n_markets=int(mt.group(2)), mean_excess=round(float(mt.group(3)), 2))
    return dict(quantile=0.99, per_market=per, pooled=pooled, p_value=p, placebo_bias=bias,
                maduro_blind=dict(alerts_pre_news=1, hours_before_news=96, direction="toward NO",
                                  note="One pre-news alert, 96 h early and in the wrong direction; the final pre-news hours were not scorable."),
                source="data/results/comparison_summary.md, data/results/maduro_blind_validation.md")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIX.mkdir(parents=True, exist_ok=True)
    perm = {r["market_key"]: r for r in L1["permutation"]}
    mk_rows, fills_by_m, S_by_m, pref_by_m = [], {}, {}, {}
    for m in MARKETS:
        f = load_fills(m)
        S = SC[SC.market_key == m].copy()
        pref = prefixes(S.wallet)
        fills_by_m[m], S_by_m[m], pref_by_m[m] = f, S, pref
        json.dump(timeline(m, f, S, pref), open(OUT / f"{m}_timeline.json", "w"), separators=(",", ":"))
        json.dump(wallets(m, S, pref), open(OUT / f"{m}_wallets.json", "w"), separators=(",", ":"))
        json.dump(alerts(m, S, pref), open(OUT / f"{m}_alerts.json", "w"), separators=(",", ":"))
        json.dump(recent_buys(m, f, S, pref), open(OUT / f"{m}_buys.json", "w"), separators=(",", ":"))
        ev = NEWS[NEWS.market_key == m].sort_values("news_epoch")
        p = perm[m]
        mk_rows.append(dict(
            id=m, short=SHORT[m], question=MK.loc[m, "market_name"], slug=MK.loc[m, "slug"],
            condition_id=MK.loc[m, "condition_id"], open_utc=MK.loc[m, "open_utc"],
            resolution=MK.loc[m, "resolution"], resolution_utc=MK.loc[m, "resolution_utc"],
            volume_usd=num(MK.loc[m, "volume_usd"], 0), why_insider_possible=MK.loc[m, "label_justification"],
            t_news=t_news(m), t_news_utc=ev.news_utc.iloc[0], t_news_basis=ev.description.iloc[0],
            t_news_source=ev.source_url.iloc[0],
            news_events=[dict(utc=r.news_utc, epoch=int(r.news_epoch), description=r.description, source=r.source_url)
                         for r in ev.itertuples()],
            n_wallets=int(len(S)), n_high=int((S.score >= FLAGS["HIGH"]).sum()),
            n_documented=int(sum(1 for mm, _ in DOC if mm == m)),
            permutation=dict(observed=p["observed_high"], null_mean=round(p["null_mean"], 1), null_p95=p["null_p95"],
                             null_min=p["null_min"], null_max=p["null_max"], p_value=round(p["p_value"], 3), n_perm=1000,
                             hist=null_hist(m)),
            firing_rates={k: round(float(S[f"flag_{k}"].mean()), 3) for k in FLAG_IDS},
            score_dist={str(k): int(v) for k, v in S.score.value_counts().sort_index().items()},
            pre_news_buy_fills=p["pre_news_buy_fills"],
        ))
    top = VAL[VAL.label_id == "MAD-CFTC-1"].iloc[0]
    n_doc = VAL.drop_duplicates(["market_key", "wallet"])
    headline = dict(rank=int(top["rank"]), n_in_market=int(top.n_in_market), market="maduro",
                    hours_before=round(float(top.hours_before_news_first_high)),
                    documented_flagged=int(n_doc.high.sum()), documented_total=int(len(n_doc)),
                    n_high_total=int((SC.score >= FLAGS["HIGH"]).sum()),
                    n_high_under_1k=int(((SC.score >= FLAGS["HIGH"]) & (SC.F4_buy_usd < 1000)).sum()),
                    n_wallet_markets=int(len(SC)))
    json.dump(dict(flags=FLAGS, headline=headline, markets=mk_rows, sensitivity=L1["sensitivity"],
                   precision=L1["precision"], impact=L1["impact"]),
              open(OUT / "markets.json", "w"), indent=1)

    val = []
    for r in VAL.itertuples():
        lab = LAB[LAB.label_id == r.label_id].iloc[0]
        val.append(dict(label_id=r.label_id, market=r.market_key, identifier=r.identifier, identifier_type=lab.identifier_type,
                        confidence=r.confidence, wallet_id=pref_by_m[r.market_key][r.wallet], addr=r.wallet,
                        score=int(r.score), flags=r.flags_fired.split(","), rank=int(r.rank), n=int(r.n_in_market),
                        first_high_h=num(r.hours_before_news_first_high, 1), usd=num(r.F4_buy_usd, 2),
                        claim=lab.reported_claim, amount=lab.reported_amount, publisher=lab.source_publisher,
                        source=lab.source_url, date=lab.date_reported, notes=lab.notes,
                        sens={"1000": int(r.score_F4_1000), "2500": int(r.score_F4_2500), "10000": int(r.score_F4_10000)},
                        post=dict(f7_won=bool(r.F7_correct), f8_dormant=None if pd.isna(r.F8_dormant) else bool(r.F8_dormant))))
    json.dump(val, open(OUT / "validation.json", "w"), indent=1)
    json.dump(L2, open(OUT / "layer2.json", "w"), indent=1)
    json.dump(v0_summary(), open(OUT / "v0_summary.json", "w"), indent=1)
    json.dump(fixture(fills_by_m, S_by_m, pref_by_m), open(FIX / "flags_20.json", "w"), separators=(",", ":"))
    for p in sorted(OUT.glob("*.json")):
        print(f"{p.relative_to(ROOT)}: {p.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
