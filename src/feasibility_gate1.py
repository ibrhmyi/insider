"""Gate 1 feasibility check (counts and power only). Writes data/results/feasibility_gate1.md (+ .json).

BLINDNESS: no outcome or resolution VALUE is loaded. Columns dropped at load: yes_won, won, excess, prior_excess,
yes_px_at_cutoff, yes_px_at_dec (prices after the decision ~ the outcome), resolution (markets.csv), after_resolution.
Resolution DATES (res_ts, resolution_utc) are used only to assign the period, as the brief asks.

Episode (draft): on one token side, a wallet's net buys (buy USD - sell USD of that token) inside a rolling 24 h window
reach >= T at a buy VWAP <= cap; trigger = the buy fill where that becomes true (rising edge). Triggers on the same side
chain into one episode while consecutive triggers are <= 24 h apart; t_a = first trigger.
p_a = size-weighted price (in the episode's token) of all fills in (t_a, t_a + 10 min]; else last fill before t_a;
else the trigger fill. Keep p_a < 0.50 and t_a < T_dec; second version also needs t_a < T_dec - 24 h.

v2 markets: exact if data/raw/v2_fills/<conditionId>.csv.gz exists, else a PROXY from data/v2/positions.csv.gz."""
import json, math
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "data"; OUT = DATA / "results"
DAY, TEN = 86400, 600
P1_END = pd.Timestamp("2026-05-06", tz="UTC").timestamp()  # P1: resolved 2025-01-01 .. 2026-05-05; P2: 2026-05-06 .. 2026-10-31
CATS = ["military_gov", "company", "appointment", "award_committee", "central_bank"]
CATNAME = dict(military_gov="military/government", company="company", appointment="appointment", award_committee="award", central_bank="central bank")
DEFS = {"main ($2,500, cap 0.35)": (2500, .35), "$1,000, cap 0.35": (1000, .35), "$10,000, cap 0.35": (10000, .35), "$2,500, cap 0.20": (2500, .20)}
MAIN = "main ($2,500, cap 0.35)"
BANNED = {"yes_won", "won", "excess", "prior_excess", "yes_px_at_cutoff", "yes_px_at_dec", "resolution", "after_resolution", "outcome_prices", "outcomePrices", "payout", "pnl"}
safe = lambda c: c not in BANNED
period = lambda ts: "P1" if ts < P1_END else "P2"
iso = lambda ts: pd.Timestamp(int(ts), unit="s", tz="UTC").strftime("%Y-%m-%d %H:%M") if pd.notna(ts) else "n/a"

# ---------------- episode detection on fills ----------------
def triggers(d, T, cap):
    """d: fills of ONE token side (ts, wallet, side, size, price), sorted by ts. Returns [(ts, wallet, idx)]."""
    out = []
    d = d.assign(usd=d["size"] * d["price"])
    big = d[d.side == "BUY"].groupby("wallet").usd.sum(); big = set(big[big >= T].index)
    for w, g in d[d.wallet.isin(big)].groupby("wallet", sort=False):
        ts = g.ts.values; buy = (g.side == "BUY").values
        bu = np.where(buy, g.usd.values, 0.0); bs = np.where(buy, g["size"].values, 0.0); su = np.where(~buy, g.usd.values, 0.0)
        cb, cs, cu = (np.concatenate([[0], np.cumsum(x)]) for x in (bu, bs, su))
        lo = np.searchsorted(ts, ts - DAY, side="right"); hi = np.arange(1, len(ts) + 1)
        b_usd, b_sh, s_usd = cb[hi] - cb[lo], cs[hi] - cs[lo], cu[hi] - cu[lo]
        with np.errstate(divide="ignore", invalid="ignore"):
            cond = (b_usd - s_usd >= T) & (b_usd / b_sh <= cap) & buy
        prev = False
        for i in np.where(buy)[0]:
            if cond[i] and not prev: out.append((int(ts[i]), w, g.index[i]))
            prev = bool(cond[i])
    return out

def episodes_from_fills(f, t_dec, T, cap):
    """f: all fills of a market with columns ts, wallet, tok (Yes/No), side, size, price. Returns list of episode dicts."""
    f = f.sort_values("ts", kind="stable").reset_index(drop=True)
    eps = []
    for s in ("Yes", "No"):
        tr = sorted(triggers(f[f.tok == s], T, cap))
        if not tr: continue
        px = np.where(f.tok == s, f.price, 1 - f.price); fts = f.ts.values; sz = f["size"].values
        groups, cur = [], [tr[0]]
        for a, b in zip(tr, tr[1:]):
            if b[0] - a[0] > DAY: groups.append(cur); cur = [b]
            else: cur.append(b)
        groups.append(cur)
        for gr in groups:
            ta, _, idx = gr[0]
            win = (fts > ta) & (fts <= ta + TEN)
            if win.any() and sz[win].sum() > 0: pa, src = float((px[win] * sz[win]).sum() / sz[win].sum()), "10min"
            else:
                before = np.where(fts < ta)[0]
                pa, src = (float(px[before[-1]]), "last_before") if len(before) else (float(px[idx]), "trigger")
            eps.append(dict(side=s, t_a=ta, p_a=pa, pa_src=src, wallets=sorted({w for _, w, _ in gr}),
                            keep=(pa < .5) and (ta < t_dec), keep24=(pa < .5) and (ta < t_dec - DAY)))
    return eps

def episodes_proxy(p, t_dec, T, cap):
    """PROXY from position aggregates up to T_dec (net-long-at-close units only; no fills). A unit counts if all its
    pre-T_dec buys lie within 24 h, it did not sell before T_dec, USD bought >= T and its buy VWAP <= cap.
    t_a ~ last pre-T_dec buy (t_a can only be earlier); p_a ~ the wallet's own buy VWAP (true p_a unknown)."""
    q = p[(p.usd_bought_dec >= T) & (p.vwap_dec <= cap) & (p.last_buy_ts_dec - p.first_buy_ts_dec <= DAY)
          & (p.net_shares_dec >= p.shares_bought_dec * (1 - 1e-6))]
    eps = []
    for s, g in q.groupby("side_name"):
        g = g.sort_values("last_buy_ts_dec"); t = g.last_buy_ts_dec.values
        start = np.r_[True, np.diff(t) > DAY]; gid = np.cumsum(start)
        for k in np.unique(gid):
            gg = g[gid == k]; ta = float(gg.last_buy_ts_dec.iloc[0])
            pa = float((gg.usd_bought_dec.sum()) / gg.shares_bought_dec.sum())
            eps.append(dict(side=s, t_a=ta, p_a=pa, pa_src="proxy_vwap", wallets=sorted(gg.proxy_wallet),
                            keep=(pa < .5) and (ta < t_dec), keep24=(pa < .5) and (ta < t_dec - DAY)))
    return eps

# ---------------- load (blind) ----------------
mi = pd.read_csv(DATA / "v2" / "market_info.csv", usecols=safe)
rk = pd.read_csv(DATA / "v2" / "markets_ranked.csv", usecols=safe, dtype={"yes_token": str, "no_token": str})
cand = pd.read_csv(DATA / "v2" / "markets_candidates.csv", usecols=safe)
fl = pd.read_csv(DATA / "v2" / "fetch_log.csv", usecols=safe)
dlog = json.load(open(DATA / "v2" / "data_log.json"))
assert not (BANNED & (set(mi) | set(rk) | set(cand) | set(fl)))
mi = mi.merge(rk[["conditionId", "end_ts", "closed_ts", "yes_token", "no_token"]], on="conditionId", how="left").merge(fl[["conditionId", "pages", "rows"]], on="conditionId", how="left")

fill_dir = DATA / "raw" / "v2_fills"
have_fills = {c for c in mi.conditionId if (fill_dir / f"{c}.csv.gz").exists()}
pos = None
if len(have_fills) < len(mi):
    pos = pd.read_csv(DATA / "v2" / "positions.csv.gz", usecols=safe)
    assert not (BANNED & set(pos))
    pos = pos[pos.usd_bought_dec.notna()]

V1 = dict(iran="military_gov", maduro="military_gov", nobel="award_committee")
v1m = pd.read_csv(DATA / "markets.csv", usecols=["market_key", "market_name", "condition_id", "open_utc", "end_date_utc", "closed_utc", "resolution_utc", "first_news_utc"]).set_index("market_key")
ep = lambda s: pd.Timestamp(s).timestamp()

markets, integ = [], []  # markets: dict(id, name, cat, period, source, t_dec, fills|pos)
for r in mi.itertuples():
    src = "exact" if r.conditionId in have_fills else "proxy"
    markets.append(dict(id=r.conditionId, name=r.question, cat=r.category, period=period(r.res_ts), source=src, t_dec=r.t_dec))
    integ.append(dict(market=r.question[:70], set="v2", cat=r.category, open="not saved", first_fill=r.first_fill_ts, last_fill=r.last_fill_ts,
                      end=r.end_ts, closed=r.closed_ts, t_dec=r.t_dec, n_fills=r.n_fills, pages=r.pages, fills_here=src == "exact"))
for k, cat in V1.items():
    m = v1m.loc[k]
    f = pd.read_csv(DATA / "clean" / f"v1_fills_{k}.csv", usecols=["proxy_wallet", "timestamp", "size", "price", "side", "outcome"])  # outcome = token label Yes/No, not the result
    f = f.rename(columns=dict(proxy_wallet="wallet", timestamp="ts", outcome="tok"))
    t_dec = ep(m.first_news_utc)
    markets.append(dict(id=m.condition_id, name=m.market_name, cat=cat, period=period(ep(m.resolution_utc)), source="exact (v1)", t_dec=t_dec, fills=f))
    pre = np.sort(f.ts[f.ts < t_dec].unique())
    integ.append(dict(market=m.market_name[:70], set="v1", cat=cat, open=ep(m.open_utc), first_fill=f.ts.min(), last_fill=f.ts.max(), end=ep(m.end_date_utc),
                      closed=ep(m.closed_utc), t_dec=t_dec, n_fills=len(f), pages=None, fills_here=True, max_gap_h=float(np.diff(pre).max() / 3600) if len(pre) > 1 else None))

def load_v2_fills(m):
    r = mi.set_index("conditionId").loc[m["id"]]
    d = pd.read_csv(fill_dir / f"{m['id']}.csv.gz", dtype={"token_id": str}, usecols=["proxy_wallet", "token_id", "timestamp", "size", "price", "side"])
    d["tok"] = np.where(d.token_id == r.yes_token, "Yes", np.where(d.token_id == r.no_token, "No", "?"))
    return d[d.tok != "?"].rename(columns=dict(proxy_wallet="wallet", timestamp="ts"))

# ---------------- run ----------------
res = {}
posg = dict(tuple(pos.groupby("conditionId"))) if pos is not None else {}
for m in markets:
    if m["source"] != "proxy":
        f = m.get("fills")
        if f is None:
            f = load_v2_fills(m)
            ii = next(i for i in integ if i["market"] == m["name"][:70]); pre = np.sort(f.ts[f.ts < m["t_dec"]].unique())
            ii["max_gap_h"] = float(np.diff(pre).max() / 3600) if len(pre) > 1 else None
        for dn, (T, cap) in DEFS.items(): res[(m["id"], dn)] = episodes_from_fills(f, m["t_dec"], T, cap)
    else:
        p = posg.get(m["id"], pos.iloc[:0])
        for dn, (T, cap) in DEFS.items(): res[(m["id"], dn)] = episodes_proxy(p, m["t_dec"], T, cap)

# ---------------- tables ----------------
def cell_rows(dn, key, subset):
    rows = []
    for c in CATS:
        for per in ("P1", "P2"):
            ms = [m for m in subset if m["cat"] == c and m["period"] == per]
            E = {m["id"]: [e for e in res[(m["id"], dn)] if e[key]] for m in ms}
            wal = {w for es in E.values() for e in es for w in e["wallets"]}
            pas = {i: [e["p_a"] for e in es] for i, es in E.items() if es}
            v_ind = [sum(p * (1 - p) for p in v) / len(v) ** 2 for v in pas.values()]     # episodes independent
            v_cor = [float(np.mean([p * (1 - p) for p in v])) for v in pas.values()]       # episodes fully correlated within market
            M = len(pas)
            se_i = math.sqrt(sum(v_ind)) / M if M else None; se_c = math.sqrt(sum(v_cor)) / M if M else None
            rows.append(dict(cat=CATNAME[c], period=per, markets=len(ms), mkts_ep=M, episodes=sum(len(v) for v in E.values()), wallets=len(wal),
                             se_ind=se_i, mde_ind=2.8 * se_i if se_i else None, se_cor=se_c, mde_cor=2.8 * se_c if se_c else None))
    return rows

fmt = lambda x, d=3: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else (f"{x:.{d}f}" if isinstance(x, float) else f"{x:,}" if isinstance(x, (int, np.integer)) else str(x))
def md_table(rows, cols, heads):
    s = "| " + " | ".join(heads) + " |\n|" + "---|" * len(heads) + "\n"
    return s + "".join("| " + " | ".join(fmt(r[c]) for c in cols) + " |\n" for r in rows)

v2set = [m for m in markets if m["source"] != "exact (v1)"]; v1set = [m for m in markets if m["source"] == "exact (v1)"]
n_exact_v2 = sum(m["source"] == "exact" for m in v2set)
L = []
L.append(f"# Gate 1 feasibility check (draft episode definition)\n\nGenerated by `src/feasibility_gate1.py`. Feasibility only: counts, prices at alert and power. **No outcome was looked at**: no won/lost flag, outcome price, payout, PnL or win rate was loaded, joined, printed or computed. Outcome columns are dropped at load (`{', '.join(sorted(BANNED))}`). Resolution *dates* are used only to assign the period.\n")
L.append("## 0. Read this first: what is exact and what is a proxy\n")
L.append(f"- **v1 markets (Maduro, Nobel, Iran): exact.** Every maker and taker fill is in the repo (`data/clean/v1_fills_*.csv`). T_dec = the first public news time in `data/markets.csv` (the v1 decision time).\n"
         f"- **v2 markets (165): {'exact' if n_exact_v2 == len(v2set) else 'PROXY'}.** {n_exact_v2} of {len(v2set)} have fills in this container. "
         + ("" if n_exact_v2 == len(v2set) else "The v2 fill cache `data/raw/v2_fills/` is git-ignored and was never committed, so it is not in this container. The brief says fetch nothing new, so nothing was re-fetched. For those markets the episode counts below come from `data/v2/positions.csv.gz` (wallet x market x side aggregates up to T_dec). That proxy (a) only sees wallets still net long at close (244,312 sold-out units are missing), (b) only counts a wallet whose pre-T_dec buys all fall inside 24 h with no sells, (c) sets t_a to the wallet's last pre-T_dec buy (the true t_a can only be earlier) and (d) sets p_a to the wallet's own buy VWAP, because the market price in the 10 minutes after t_a needs the fills. **The proxy undercounts episodes and wallets, and its p_a is not the specified p_a.** Rerunning this script after re-pulling the 165 fill files gives the exact numbers without any code change. Section 5 gives the time estimate.")
         + "\n- Main definition: $2,500 of net buys within 24 h at a buy VWAP <= 0.35. Variants: $1,000 and $10,000 at a cap of 0.35, and $2,500 at a cap of 0.20. Every count is shown twice: episodes with t_a < T_dec, and episodes with t_a < T_dec - 24 h.\n"
         "- Definition choices made here (the draft did not fix them): net buys = buy USD minus sell USD of the same token by the same wallet in the window. VWAP = the wallet's buy VWAP in the window. A trigger is the buy fill where the condition first becomes true (it must turn false and then true again to trigger again). Episodes chain: same side, consecutive triggers <= 24 h apart. p_a uses fills strictly after t_a; 'last fill before t_a' means strictly earlier; if there is none, the trigger fill's price is used.\n")

# 1 integrity
L.append("## 1. Data integrity per market\n")
I = pd.DataFrame(integ)
v1i = I[I.set == "v1"]
L.append("**v1 (exact fills):**\n\n| market | open | first fill | last fill | end date | closed | T_dec | fills | largest gap before T_dec (h) |\n|---|---|---|---|---|---|---|---|---|\n" +
         "".join(f"| {r.market} | {iso(r.open)} | {iso(r.first_fill)} | {iso(r.last_fill)} | {iso(r.end)} | {iso(r.closed)} | {iso(r.t_dec)} | {r.n_fills:,} | {fmt(r.max_gap_h, 1)} |\n" for r in v1i.itertuples()))
v2i = I[I.set == "v2"].copy()
v2i["life_d"] = (v2i.closed - v2i.first_fill) / DAY
v2i["pre_dec_d"] = (v2i.t_dec - v2i.first_fill) / DAY
v2i["tail_d"] = (v2i.closed - v2i.last_fill) / DAY
probs = []
for r in v2i.itertuples():
    why = []
    if pd.isna(r.t_dec): why.append("T_dec missing")
    if r.pre_dec_d < 1: why.append(f"T_dec {r.pre_dec_d * 24:.0f} h after first fill (no usable pre-decision period)")
    if r.t_dec >= r.closed - 3600 - 1: why.append("T_dec = cutoff (price never left 0.05-0.95 before close - 1 h)")
    if r.tail_d > 2: why.append(f"last fill {r.tail_d:.1f} d before close")
    if r.pages is not None and r.pages >= 400: why.append("hit 400-page cap")
    if not r.fills_here: pass
    if why: probs.append((r.market, iso(r.first_fill), iso(r.t_dec), "; ".join(why)))
L.append(f"\n**v2 (165 markets).** Gamma open date (`startDate`) was not saved in the v2 files, so the first fill stands in for the open; first fill vs open cannot be checked without a new Gamma call. "
         f"Fetch: all 165 'ok', max pages {int(v2i.pages.max())} (cap 400, none hit), 0 HTTP errors (v2 log). `/v2/trades` uses cursor pagination with no offset cap. T_dec present for {int(v2i.t_dec.notna().sum())}/165. "
         f"Fill-level gap checks need the fills: {'done' if n_exact_v2 else 'not possible here'}. Markets with no fills before the cutoff: {len(dlog.get('markets_no_pre_cutoff_fills', []))}.\n\n"
         f"- Life (first fill to close), days: median {v2i.life_d.median():.0f}, min {v2i.life_d.min():.1f}, max {v2i.life_d.max():.0f}.\n"
         f"- First fill to T_dec, days: median {v2i.pre_dec_d.median():.1f}, min {v2i.pre_dec_d.min():.2f}.\n"
         f"- Last fill to close, days: median {v2i.tail_d.median():.2f}, max {v2i.tail_d.max():.1f}.\n"
         f"- Earliest first fill: {iso(v2i.first_fill.min())} (the `/v2/trades` three-year window starts about Nov 2023, so no market is cut at the start).\n\n"
         f"**Problem markets ({len(probs)}):**\n\n| market | first fill | T_dec | problem |\n|---|---|---|---|\n" + "".join(f"| {a} | {b} | {c} | {d} |\n" for a, b, c, d in probs))
if v1i.max_gap_h.max() > 48: L.append("\nv1 gap note: a gap of more than 48 h before T_dec is in the table above; on thin early markets this is quiet trading, not missing data (cursor pagination returned every page).\n")

# 2 counts + 4 power
out_json = {}
for dn in DEFS:
    L.append(f"\n## 2. Counts: {dn}\n")
    for title, subset in (("v2, 165 markets" + ("" if n_exact_v2 == len(v2set) else " (PROXY, undercount)"), v2set), ("v1, 3 markets (exact)", v1set)):
        a = cell_rows(dn, "keep", subset); b = cell_rows(dn, "keep24", subset)
        rows = [dict(**x, mkts_ep24=y["mkts_ep"], episodes24=y["episodes"], wallets24=y["wallets"]) for x, y in zip(a, b)]
        rows = [r for r in rows if r["markets"]]
        out_json[f"{dn} | {title}"] = dict(t_lt_dec=a, t_lt_dec_minus24h=b)
        L.append(f"**{title}**\n\n" + md_table(rows, ["cat", "period", "markets", "mkts_ep", "episodes", "wallets", "mkts_ep24", "episodes24", "wallets24"],
                 ["category", "period", "markets", "with episode", "episodes", "wallets", "with ep. (24 h)", "episodes (24 h)", "wallets (24 h)"]) + "\n")

# 3 p_a distribution
L.append(f"\n## 3. Distribution of p_a by category, main definition, t_a < T_dec\n")
for title, subset in (("v2" + ("" if n_exact_v2 == len(v2set) else " (PROXY: wallet's own buy VWAP, not the market price after t_a)"), v2set), ("v1 (exact)", v1set)):
    rows = []
    for c in CATS:
        ps = [e["p_a"] for m in subset if m["cat"] == c for e in res[(m["id"], MAIN)] if e["keep"]]
        if ps:
            q = np.quantile(ps, [0, .1, .25, .5, .75, .9, 1])
            rows.append(dict(cat=CATNAME[c], n=len(ps), **{k: float(v) for k, v in zip(["min", "p10", "p25", "p50", "p75", "p90", "max"], q)}))
    L.append(f"**{title}**\n\n" + (md_table(rows, ["cat", "n", "min", "p10", "p25", "p50", "p75", "p90", "max"], ["category", "episodes", "min", "10%", "25%", "median", "75%", "90%", "max"]) if rows else "No episodes.\n") + "\n")
src_counts = pd.Series([e["pa_src"] for m in v1set for e in res[(m["id"], MAIN)] if e["keep"]]).value_counts().to_dict()
L.append(f"v1 p_a source (main): {src_counts} (10min = fills in the 10 minutes after t_a; last_before = fallback).\n")

# 4 power
L.append("\n## 4. Power from p_a only (no outcomes)\n\nExcess per episode = outcome - p_a; under no edge its variance is p_a(1 - p_a). Market-level mean excess = mean over the market's episodes; cell estimate = mean over markets with at least one episode. "
         "Two SEs: **independent** treats episodes in a market as independent (variance of the market mean = sum p(1-p) / n^2), as the brief specifies; **correlated** treats them as fully dependent, because all same-side episodes in a market share one outcome (variance = mean p(1-p)). The truth lies between and is near the correlated value when a market's episodes are on one side. "
         "MDE = 2.8 x SE (5% two-sided, 80% power). v2 rows use the proxy p_a where the fills are missing; 'all' pools v2 and v1.\n")
for dn in DEFS:
    for key, lab in (("keep", "t_a < T_dec"), ("keep24", "t_a < T_dec - 24 h")):
        if dn != MAIN and key == "keep24": continue
        rows = []
        for c in CATS:
            for per in ("P1", "P2", "both"):
                ms = [m for m in markets if m["cat"] == c and (per == "both" or m["period"] == per)]
                if not ms: continue
                pas = [[e["p_a"] for e in res[(m["id"], dn)] if e[key]] for m in ms]; pas = [v for v in pas if v]
                M = len(pas)
                si = math.sqrt(sum(sum(p * (1 - p) for p in v) / len(v) ** 2 for v in pas)) / M if M else None
                sc = math.sqrt(sum(float(np.mean([p * (1 - p) for p in v])) for v in pas)) / M if M else None
                rows.append(dict(cat=CATNAME[c], period=per, M=M, n=sum(map(len, pas)), si=si, mi=2.8 * si if si else None, sc=sc, mc=2.8 * sc if sc else None))
        allp = [[e["p_a"] for e in res[(m["id"], dn)] if e[key]] for m in markets]; allp = [v for v in allp if v]; M = len(allp)
        si = math.sqrt(sum(sum(p * (1 - p) for p in v) / len(v) ** 2 for v in allp)) / M if M else None
        sc = math.sqrt(sum(float(np.mean([p * (1 - p) for p in v])) for v in allp)) / M if M else None
        rows.append(dict(cat="all categories", period="both", M=M, n=sum(map(len, allp)), si=si, mi=2.8 * si if si else None, sc=sc, mc=2.8 * sc if sc else None))
        L.append(f"\n**{dn}, {lab}**\n\n" + md_table(rows, ["cat", "period", "M", "n", "si", "mi", "sc", "mc"], ["category", "period", "markets with ep.", "episodes", "SE indep.", "MDE indep.", "SE corr.", "MDE corr."]))

# 5 more markets
L.append("\n## 5. Markets that could still be pulled\n")
fetched = set(mi.conditionId)
rest = rk[~rk.conditionId.isin(fetched)].copy()
rest["period"] = rest.res_ts.map(period)
f2 = fl.merge(rk[["conditionId", "volumeNum"]], on="conditionId")
rows_per_usd = float((f2.rows / f2.volumeNum).median()); sec_per_page = float(f2.secs.sum() / f2.pages.sum())
rest["est_pages"] = np.maximum(1, np.ceil(rest.volumeNum * rows_per_usd / 1000))
tab = []
for c in CATS:
    g = rest[rest.category == c]
    tab.append(dict(cat=CATNAME[c], n=len(g), p1=int((g.period == "P1").sum()), p2=int((g.period == "P2").sum()), ge100k=int((g.volumeNum >= 1e5).sum()), pages=int(g.est_pages.sum())))
tab.append(dict(cat="total", n=len(rest), p1=int((rest.period == "P1").sum()), p2=int((rest.period == "P2").sum()), ge100k=int((rest.volumeNum >= 1e5).sum()), pages=int(rest.est_pages.sum())))
L.append(f"Of the {len(rk):,} eligible candidates ranked by v2 (volume $20k to $12M, text screen, max 3 per event), {len(fetched)} were fetched; {len(rest):,} were not.\n\n" +
         md_table(tab, ["cat", "n", "p1", "p2", "ge100k", "pages"], ["category", "not fetched", "resolved P1", "resolved P2", "volume >= $100k", "est. fill pages"]))
tp = rest.est_pages.sum(); hrs1 = tp * sec_per_page / 3600
big = cand[cand.volumeNum > 12e6].category.value_counts().reindex(CATS, fill_value=0)
L.append(f"\nFetch-time estimate. On the 165 fetched markets: median {rows_per_usd * 1e6:,.0f} fill rows per $1M of volume and {sec_per_page:.2f} s per 1,000-row page per worker "
         f"({int(f2.pages.sum()):,} pages, {int(f2.secs.sum()):,} worker-seconds). The unfetched markets are smaller (median volume ${rest.volumeNum.median():,.0f} vs ${f2.volumeNum.median():,.0f}), so the pages are estimated from volume: about {int(tp):,} pages, "
         f"about {hrs1:.1f} worker-hours, about {hrs1 / 6 * 60:.0f} minutes with the 6 parallel workers v2 used if the API allows that rate (v2 saw no HTTP errors at 6). Rows per dollar may be higher in small markets, so treat this as a lower estimate and allow 2x. "
         f"Re-pulling the 165 v2 fill files that are missing here: {int(f2.pages.sum()):,} pages, about {f2.secs.sum() / 60:.0f} worker-minutes.\n\n"
         f"Not in the 4,192: {int(big.sum())} markets over $12M were excluded up front by Amendment B ({', '.join(f'{CATNAME[c]} {int(v)}' for c, v in big.items())}). Each may exceed the 400-page cap.\n")
L.append("\n## Caveats\n\n- Category labels are v2's keyword screen. The v2 log says the screen is imperfect.\n- T_dec for v2 is the price-path marker (the rolling median Yes price leaves 0.05-0.95 for good). For v1 it is the first news time. Both are ex-post markers.\n- These numbers are for deciding whether a test is feasible. No hypothesis was tested.\n")
(OUT / "feasibility_gate1.md").write_text("\n".join(L))
json.dump(dict(defs={k: list(v) for k, v in DEFS.items()}, v2_exact_markets=n_exact_v2, counts=out_json), open(OUT / "feasibility_gate1.json", "w"), indent=1, default=str)
print("\n".join(L))
