"""Gate 1 feasibility check (counts and power only). Writes data/results/feasibility_gate1.md (+ .json).

BLINDNESS: no outcome or resolution VALUE is loaded. Columns dropped at load: yes_won, won, excess, prior_excess,
yes_px_at_cutoff, yes_px_at_dec (prices after the decision ~ the outcome), resolution (markets.csv), after_resolution.
Resolution DATES (res_ts, resolution_utc) are used only to assign the period, as the brief asks.

Episode (draft): on one token side, a wallet's net buys (buy USD - sell USD of that token) inside a rolling 24 h window
reach >= T at a buy VWAP <= cap; trigger = the buy fill where that becomes true (rising edge). Triggers on the same side
chain into one episode while consecutive triggers are <= 24 h apart; t_a = first trigger.
p_a = size-weighted price (in the episode's token) of all fills in (t_a, t_a + 10 min]; else last fill before t_a;
else the trigger fill. Keep p_a < 0.50 and t_a < T_dec; second version also needs t_a < T_dec - 24 h.

Markets: data/v3/market_info.csv (core = v2's 165 + unfetched military/government + military/government over $12M + v1;
plus FFIC markets, reported separately). Fills: exact, from the local cache data/raw/v2_fills/ (rebuild from
data/v2/fills_manifest.csv with `python src/v3_01_fetch.py --manifest`). No proxy. Power by market and by Gamma event."""
import json, math
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "data"; OUT = DATA / "results"
DAY, TEN = 86400, 600
P1_END = pd.Timestamp("2026-05-06", tz="UTC").timestamp(); PRE2025 = pd.Timestamp("2025-01-01", tz="UTC").timestamp()  # P1: resolved 2025-01-01 .. 2026-05-05; P2: 2026-05-06 .. 2026-10-31
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


# ---------------- load (blind) ----------------
fill_dir = DATA / "raw" / "v2_fills"
mi = pd.read_csv(DATA / "v3" / "market_info.csv", usecols=safe, dtype={"event_id": str, "series_id": str})
tg = pd.read_csv(DATA / "v3" / "targets.csv", usecols=["conditionId", "yes_token", "no_token"], dtype=str).set_index("conditionId")
cand = pd.read_csv(DATA / "v2" / "markets_candidates.csv", usecols=safe)
rk = pd.read_csv(DATA / "v2" / "markets_ranked.csv", usecols=safe)
fm = pd.read_csv(DATA / "v3" / "ffic_match.csv", usecols=["case_id", "case_title", "prefix", "label", "conditionId", "matched_by"])
assert not (BANNED & (set(mi) | set(cand) | set(rk) | set(fm)))
CORE = ("v2_165", "mil_rest", "mil_over12m", "v1")
mi["core"] = mi.source.map(lambda s: any(k in s for k in CORE))
mi["ffic"] = mi.source.str.contains("ffic")
mi["period"] = mi.res_ts.map(lambda t: "pre-2025" if t < PRE2025 else period(t))
mi["event_unit"] = mi.event_id.fillna("m:" + mi.conditionId)
mi["series_unit"] = np.where(mi.series_id.notna(), "s:" + mi.series_id.astype(str), "e:" + mi.event_unit)

def run_market(cid):
    r = mi.set_index("conditionId").loc[cid]; tk = tg.loc[cid]
    d = pd.read_csv(fill_dir / f"{cid}.csv.gz", dtype={"token_id": str}, usecols=["proxy_wallet", "token_id", "timestamp", "size", "price", "side"])
    d["tok"] = np.where(d.token_id == tk.yes_token, "Yes", np.where(d.token_id == tk.no_token, "No", "?"))
    f = d[d.tok != "?"].rename(columns=dict(proxy_wallet="wallet", timestamp="ts"))
    return cid, {dn: episodes_from_fills(f, r.t_dec, T, cap) for dn, (T, cap) in DEFS.items()}

use = mi[(mi.core | mi.ffic) & ~mi.excluded]
missing = [c for c in use.conditionId if not (fill_dir / f"{c}.csv.gz").exists()]
assert not missing, f"{len(missing)} fill files missing: rebuild the cache with `python src/v3_01_fetch.py --manifest`"
res = {}
from concurrent.futures import ProcessPoolExecutor  # fork: workers inherit the loaded tables
with ProcessPoolExecutor(4) as ex:
    for cid, out in ex.map(run_market, use.conditionId.tolist(), chunksize=4):
        for dn, eps in out.items(): res[(cid, dn)] = eps

mrec = use.set_index("conditionId")
def M(subset): return [dict(id=c, cat=r.category, period=r.period, ev=r.event_unit, se=r.series_unit) for c, r in subset.iterrows()]
core = M(mrec[mrec.core]); ffic = M(mrec[mrec.ffic])

def var_parts(pas):
    """pas: list of p_a lists, one per unit. Returns (SE indep, SE corr, n units)."""
    pas = [v for v in pas if v]; U = len(pas)
    if not U: return None, None, 0
    si = math.sqrt(sum(sum(p * (1 - p) for p in v) / len(v) ** 2 for v in pas)) / U
    sc = math.sqrt(sum(float(np.mean([p * (1 - p) for p in v])) for v in pas)) / U
    return si, sc, U

def units(ms, dn, key, unit):
    g = {}
    for m in ms:
        g.setdefault(m[unit], []).extend(e["p_a"] for e in res[(m["id"], dn)] if e[key])
    return list(g.values())

def count_rows(dn, ms_all, cats, periods):
    rows = []
    for c in cats:
        for per in periods:
            ms = [m for m in ms_all if (c is None or m["cat"] == c) and m["period"] == per]
            if not ms: continue
            row = dict(cat=CATNAME.get(c, c) if c else "all", period=per, markets=len(ms), events=len({m["ev"] for m in ms}))
            for key, sfx in (("keep", ""), ("keep24", "24")):
                E = {m["id"]: [e for e in res[(m["id"], dn)] if e[key]] for m in ms}
                row["mkts_ep" + sfx] = sum(1 for v in E.values() if v)
                row["ev_ep" + sfx] = len({m["ev"] for m in ms if E[m["id"]]})
                row["episodes" + sfx] = sum(map(len, E.values()))
                row["wallets" + sfx] = len({w for v in E.values() for e in v for w in e["wallets"]})
            rows.append(row)
    return rows

def power_rows(dn, key, ms_all):
    rows = []
    for c in CATS + [None]:
        for per in ("P1", "P2", "both"):
            ms = [m for m in ms_all if (c is None or m["cat"] == c) and (per == "both" or m["period"] == per)]
            if not ms or (c is None and per != "both"): continue
            mi_, mc, nm = var_parts(units(ms, dn, key, "id")); ei, ec, ne = var_parts(units(ms, dn, key, "ev"))
            row = dict(cat=CATNAME[c] if c else "all categories", period=per, nm=nm, ne=ne, n=sum(len(v) for v in units(ms, dn, key, "id")),
                       m_i=2.8 * mi_ if mi_ else None, m_c=2.8 * mc if mc else None, e_i=2.8 * ei if ei else None, e_c=2.8 * ec if ec else None)
            if c is None:
                si, sc, ns = var_parts(units(ms, dn, key, "se")); row.update(ns=ns, s_c=2.8 * sc if sc else None)
            rows.append(row)
    return rows

fmt = lambda x, d=3: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else (f"{x:.{d}f}" if isinstance(x, float) else f"{x:,}" if isinstance(x, (int, np.integer)) else str(x))
def md_table(rows, cols, heads):
    s = "| " + " | ".join(heads) + " |\n|" + "---|" * len(heads) + "\n"
    return s + "".join("| " + " | ".join(fmt(r.get(c)) for c in cols) + " |\n" for r in rows)

allm = mi[mi.core | mi.ffic]; coreall = mi[mi.core]
L = []
L.append(f"# Gate 1 feasibility check (draft episode definition), v2: exact fills, larger universe\n\nGenerated by `src/feasibility_gate1.py`. Feasibility only: counts, prices at alert and power. **No outcome was looked at**: no won/lost flag, outcome price, payout, PnL or win rate was loaded, joined, printed or computed. Outcome columns are dropped at load (`{', '.join(sorted(BANNED))}`). Resolution *dates* are used only to assign the period. Gate 1 itself was not run.\n")
L.append("## 0. What changed since the first version\n")
L.append(f"- **Exact fills everywhere; no proxy.** All maker and taker fills were fetched from `/v2/trades` into the local cache (see `data/v2/fills_manifest.csv`; rebuild with `python src/v3_01_fetch.py --manifest`). The episode code is unchanged.\n"
         f"- **Universe ('core', {int(coreall.shape[0]):,} markets fetched or attempted):** the 165 v2 markets; every military/government market in v2's ranked list that v2 had not fetched (1,835); the 58 military/government markets over $12M that Amendment B excluded (no page cap); the v1 Maduro, Nobel and Iran markets. **FFIC markets** ({int(mi.ffic.sum())}) are reported in their own block (section 6) and enter the core tables only if they are also in the core set. Each market is counted once: the first version counted Nobel twice (it is both a v1 market and one of the 165).\n"
         f"- **Exclusions.** A market is excluded if T_dec is within 24 h of its first fill (no usable pre-decision period), if the fetch failed or hit the 400-page cap (v2 rule sets only), or if it has no fills before the cutoff. {int((coreall.excluded).sum()):,} core markets are excluded; reasons in section 1.\n"
         "- **Event unit.** Every market has Gamma's `event_id`. Power is reported with the market as the unit and with the event as the unit (episodes pooled within event, then averaged across events). Gamma often puts 'by Friday' and 'by Sunday' markets in *different* events that share a Gamma *series*. A series-level row (series id where Gamma has one, else the event) is added as a sensitivity check.\n"
         "- T_dec: price-path rule from v2 (the rolling median Yes price leaves 0.05 to 0.95 for good, before resolution minus 1 h). v1 markets use the first news time.\n"
         "- Definition details, unchanged from the first version: net buys = buy USD minus sell USD of the same token by the same wallet in the 24 h window. VWAP = the wallet's buy VWAP in that window. A trigger is a rising edge at a buy fill. Episodes chain same-side triggers that are <= 24 h apart. p_a is taken from fills strictly after t_a, then the last fill strictly before t_a, then the trigger fill.\n")

# 1 integrity
c = coreall
ok = c[c.status == "ok"]
L.append("## 1. Data integrity\n")
L.append(f"- Fetch status (core): {c.status.value_counts().to_dict()}. Largest page count: {int(ok.pages.max()):,} in the core set, {int(allm.pages.max()):,} over all fetched markets incl. FFIC (cursor pagination; no cap for the over-$12M, v1 and FFIC sets). No v2-rule market reached the 400-page cap. Run totals are in the process log and `data/v3/fetch_run_log.json`.\n"
         f"- Gamma start date vs first fill: median {((ok.first_fill_ts - ok.start_ts) / 3600).median():.1f} h after the start; {int(((ok.first_fill_ts - ok.start_ts) > 7 * DAY).sum())} markets have their first fill more than 7 days after the start; {int(((ok.first_fill_ts - ok.start_ts) < -DAY).sum())} market(s) have fills more than 1 day before the Gamma start date.\n"
         f"- Last fill vs resolution: median {((ok.res_ts - ok.last_fill_ts) / 3600).median():.1f} h before; {int(((ok.res_ts - ok.last_fill_ts) > 2 * DAY).sum())} markets have their last fill more than 2 days before resolution.\n"
         f"- Earliest first fill: {iso(ok.first_fill_ts.min())}. `/v2/trades` serves a fixed window of about three years, so no core market is cut at the start.\n"
         f"- Largest gap between fills before T_dec: median {ok.max_gap_pre_dec_h.median():.1f} h; {int((ok.max_gap_pre_dec_h > 7 * 24).sum())} markets have a gap of more than 7 days. Thin markets trade rarely, so a gap is not by itself missing data.\n"
         f"- T_dec present: {int(ok.t_dec.notna().sum()):,} of {len(ok):,} fetched. T_dec equal to the cutoff (price never left 0.05 to 0.95): {int((ok.t_dec >= ok.res_ts - 3600).sum())}.\n")
ex = c[c.excluded]
L.append(f"\n**Excluded core markets by reason ({len(ex):,}):**\n\n" + md_table([dict(reason=k, n=int(v)) for k, v in ex.exclude_reason.value_counts().items()], ["reason", "n"], ["reason", "markets"]))
L.append("\nThe full list, with the reason for each market, is in `data/v2/fills_manifest.csv` (columns `excluded` and `exclude_reason`).\n")

# 2 counts
heads = ["category", "period", "markets", "events", "markets with ep.", "events with ep.", "episodes", "wallets", "markets with ep. (24 h)", "events with ep. (24 h)", "episodes (24 h)", "wallets (24 h)"]
cols = ["cat", "period", "markets", "events", "mkts_ep", "ev_ep", "episodes", "wallets", "mkts_ep24", "ev_ep24", "episodes24", "wallets24"]
# episode table for the frozen Gate 1 run (blind: no outcome here)
ep_rows = [dict(conditionId=cid, definition=dn, side=e["side"], t_a=e["t_a"], p_a=e["p_a"], pa_src=e["pa_src"], n_wallets=len(e["wallets"]),
                keep=e["keep"], keep24=e["keep24"]) for (cid, dn), eps in res.items() for e in eps]
pd.DataFrame(ep_rows).sort_values(["definition", "conditionId", "t_a", "side"]).to_csv(DATA / "v3" / "episodes.csv.gz", index=False, compression="gzip")
out_json = {}
for dn in DEFS:
    rows = count_rows(dn, core, CATS, ("P1", "P2"))
    out_json[dn] = rows
    L.append(f"\n## 2. Counts, core universe: {dn}\n\n'(24 h)' = only episodes with t_a < T_dec - 24 h.\n\n" + md_table(rows, cols, heads))

# 3 p_a
L.append("\n## 3. Distribution of p_a by category, main definition, t_a < T_dec\n")
rows = []
for cc in CATS:
    ps = [e["p_a"] for m in core if m["cat"] == cc for e in res[(m["id"], MAIN)] if e["keep"]]
    if ps:
        q = np.quantile(ps, [0, .1, .25, .5, .75, .9, 1]); rows.append(dict(cat=CATNAME[cc], n=len(ps), **{k: float(v) for k, v in zip(["min", "p10", "p25", "p50", "p75", "p90", "max"], q)}))
L.append(md_table(rows, ["cat", "n", "min", "p10", "p25", "p50", "p75", "p90", "max"], ["category", "episodes", "min", "10%", "25%", "median", "75%", "90%", "max"]))
src = pd.Series([e["pa_src"] for m in core for e in res[(m["id"], MAIN)] if e["keep"]]).value_counts().to_dict()
L.append(f"\np_a source (main): {src} (10min = fills in the 10 minutes after t_a; last_before / trigger = fallbacks).\n")

# 4 power
L.append("\n## 4. Power from p_a only (no outcomes)\n\nExcess per episode = outcome - p_a; under no edge its variance is p_a(1 - p_a). The unit's mean excess = the mean over its episodes; the cell estimate = the mean over units with at least one episode. MDE = 2.8 x SE (5% two-sided, 80% power). "
         "**indep.** treats a unit's episodes as independent (variance of the unit mean = sum p(1-p) / n^2). **corr.** treats them as fully dependent (variance = mean p(1-p)), because same-side episodes in one market share an outcome and markets in one event are linked. The truth lies between the two, near corr. for events. "
         "Market unit = each market. Event unit = Gamma event id: all episodes of the event's markets in the cell are pooled, then averaged across events. Series = Gamma series where there is one (else the event), shown for the pooled row only (n/a in category rows).\n")
pc = ["cat", "period", "nm", "ne", "n", "m_i", "m_c", "e_i", "e_c", "ns", "s_c"]
ph = ["category", "period", "markets with ep.", "events with ep.", "episodes", "MDE market indep.", "MDE market corr.", "MDE event indep.", "MDE event corr.", "series with ep.", "MDE series corr."]
for dn in DEFS:
    for key, lab in (("keep", "t_a < T_dec"), ("keep24", "t_a < T_dec - 24 h")):
        if dn != MAIN and key == "keep24": continue
        L.append(f"\n**{dn}, {lab}**\n\n" + md_table(power_rows(dn, key, core), pc, ph))

# 5 more markets
L.append("\n## 5. Markets still not pulled\n")
got = set(mi.conditionId)
rest = rk[~rk.conditionId.isin(got)].copy(); rest["period"] = rest.res_ts.map(period)
tab = [dict(cat=CATNAME[cc], n=int((rest.category == cc).sum()), p1=int(((rest.category == cc) & (rest.period == "P1")).sum()), p2=int(((rest.category == cc) & (rest.period == "P2")).sum())) for cc in CATS]
tab.append(dict(cat="total", n=len(rest), p1=int((rest.period == "P1").sum()), p2=int((rest.period == "P2").sum())))
big = cand[(cand.volumeNum > 12e6) & ~cand.conditionId.isin(got)].category.value_counts()
L.append(f"Of v2's 4,192 ranked candidates, {len(rest):,} are still not fetched (none of them military/government):\n\n" + md_table(tab, ["cat", "n", "p1", "p2"], ["category", "not fetched", "resolved P1", "resolved P2"]) +
         f"\nOver $12M and not fetched: {', '.join(f'{CATNAME.get(k, k)} {int(v)}' for k, v in big.items())}.\n")

# 6 FFIC
L.append("\n## 6. FFIC documented markets (ForesightFlow Insider Cases v1)\n")
L.append(f"Source: `ForesightFlow/datasets`, `ffic-inventory/ffic-v1.csv` (CC-BY-4.0, companion to Nechepurenko 2026), commit 5ba4127. It lists 32 markets in 8 cases, given as 8-hex-digit condition-id prefixes. The `resolution_outcome` column was dropped at load. Matching, prefix to full id: v2 candidate list first, then Gamma `public-search`. All 32 matched; per-market detail is in `data/v3/ffic_match.csv`. "
         "FFIC includes election markets (2024 US and Romanian presidential races), which the v2 universe rule excludes. They are fetched but kept out of the core tables.\n")
fr = []
for case, g in fm.groupby("case_id"):
    ids = set(g.conditionId.dropna()); sub = mi[mi.conditionId.isin(ids)]
    usable = [m for m in ffic if m["id"] in ids]
    eps = sum(1 for m in usable for e in res[(m["id"], MAIN)] if e["keep"])
    fr.append(dict(case=f"{case} {g.case_title.iloc[0]}", n=len(g), matched=len(ids), fetched=int((sub.status == "ok").sum()), usable=len(usable), in_core=int(sub.core.sum()),
                   mkts_ep=sum(1 for m in usable if any(e["keep"] for e in res[(m["id"], MAIN)])), eps=eps,
                   excl="; ".join(sorted(set(sub[sub.excluded].exclude_reason))) or ""))
L.append(md_table(fr, ["case", "n", "matched", "fetched", "usable", "in_core", "mkts_ep", "eps", "excl"], ["case", "markets", "matched", "fetched", "usable (not excluded)", "also in core", "with episode (main)", "episodes (main)", "exclusion reasons"]))
L.append("\n## Caveats\n\n- Category labels come from v2's keyword screen, which the v2 log calls imperfect. FFIC-only markets have no v2 category.\n- T_dec is an ex-post marker (price path, or news time for v1).\n- These numbers are for deciding whether a test is feasible. No hypothesis was tested and Gate 1 was not run.\n")
(OUT / "feasibility_gate1.md").write_text("\n".join(L))
json.dump(dict(defs={k: list(v) for k, v in DEFS.items()}, counts=out_json), open(OUT / "feasibility_gate1.json", "w"), indent=1, default=str)
print("\n".join(L))
