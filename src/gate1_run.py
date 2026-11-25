"""Gate 1: the frozen test in rules/frozen_gate1.md / .json. Run ONCE, after the freeze commit is pushed.
Checks the input hashes, then loads outcomes (yes_won) for the first time in the Gate 1 work.
Writes data/results/gate1_result.md and .json."""
import hashlib, json, math, subprocess
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "data"; OUT = DATA / "results"
FZ = json.load(open(ROOT / "rules" / "frozen_gate1.json"))
for p, h in FZ["inputs_sha256"].items():
    got = hashlib.sha256(open(ROOT / p, "rb").read()).hexdigest()
    assert got == h, f"hash mismatch for {p}: frozen {h}, now {got}"
freeze_commit = subprocess.run(["git", "log", "-1", "--format=%H %cI", "--", "rules/frozen_gate1.json"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
assert freeze_commit, "freeze file is not committed"

P1_END = pd.Timestamp("2026-05-06", tz="UTC").timestamp()
CATNAME = dict(military_gov="military/government", company="company", appointment="appointment", award_committee="award", central_bank="central bank")
MAIN = FZ["primary"]["definition"]; SEED = FZ["primary"]["ci"]["seed"]; B = FZ["primary"]["ci"]["resamples"]

mi = pd.read_csv(DATA / "v3" / "market_info.csv", dtype={"event_id": str, "series_id": str})
mi["core"] = mi.source.str.contains("v2_165|mil_rest|mil_over12m|v1")
mi["unit_event"] = mi.event_id.fillna(mi.conditionId)
mi["unit_series"] = np.where(mi.series_id.notna(), "s:" + mi.series_id.astype(str), "e:" + mi.unit_event)
mi["period"] = np.where(mi.res_ts < P1_END, "P1", "P2")
mi["new_in_v3"] = ~mi.source.str.contains("v2_165")
ep = pd.read_csv(DATA / "v3" / "episodes.csv.gz")

# ---- outcomes: first load in the Gate 1 work ----
oc = pd.read_csv(DATA / "v2" / "markets_candidates.csv", usecols=["conditionId", "yes_won"])
ep = ep.merge(mi[["conditionId", "core", "excluded", "category", "period", "unit_event", "unit_series", "new_in_v3", "source"]], on="conditionId").merge(oc, on="conditionId", how="left")
ep["y"] = np.where(ep.side == "Yes", ep.yes_won, 1 - ep.yes_won)
ep["e"] = ep.y - ep.p_a

def est(d, unit, seed=SEED):
    d = d[d.y.notna()]
    if d.empty: return dict(n_units=0, n_markets=0, n_episodes=0)
    v = d.groupby(unit).e.mean().values
    rng = np.random.default_rng(seed)
    bs = v[rng.integers(0, len(v), (B, len(v)))].mean(1) if len(v) > 1 else np.array([v.mean()])
    t = stats.ttest_1samp(v, 0) if len(v) > 1 else None
    return dict(n_units=len(v), n_markets=d.conditionId.nunique(), n_episodes=len(d), estimate=float(v.mean()),
                ci_lo=float(np.percentile(bs, 2.5)), ci_hi=float(np.percentile(bs, 97.5)),
                t_p=float(t.pvalue) if t is not None else None, mean_y=float(d.y.mean()), mean_pa=float(d.p_a.mean()))

base = ep[ep.core & ~ep.excluded]
prim_d = base[(base.definition == MAIN) & base.keep]
missing_y = int(prim_d.y.isna().sum()); assert missing_y == 0, f"{missing_y} primary episodes without outcome"
P = est(prim_d, "unit_event")
dec = "POSITIVE" if P["ci_lo"] > 0 else ("NEGATIVE" if P["ci_hi"] < 0 else "NULL")

S = []
def add(label, d, unit="unit_event"): S.append(dict(label=label, **est(d, unit)))
add("market unit", prim_d, "conditionId")
add("series unit", prim_d, "unit_series")
add("t_a < T_dec - 24 h", base[(base.definition == MAIN) & base.keep24])
for dn in ["$1,000, cap 0.35", "$10,000, cap 0.35", "$2,500, cap 0.20"]: add(dn, base[(base.definition == dn) & base.keep])
for c in CATNAME: add(f"category: {CATNAME[c]}", prim_d[prim_d.category == c])
for per in ("P1", "P2"): add(f"period {per}", prim_d[prim_d.period == per])
add("v2's 165 markets (seen in v2 work)", prim_d[~prim_d.new_in_v3])
add("markets new in v3 (out of sample)", prim_d[prim_d.new_in_v3])

bands = []
for lo in np.arange(0, .5, .1):
    d = prim_d[(prim_d.p_a >= lo) & (prim_d.p_a < lo + .1)]
    if len(d): bands.append(dict(band=f"{lo:.1f}-{lo + .1:.1f}", n=len(d), mean_pa=float(d.p_a.mean()), mean_y=float(d.y.mean()), excess=float(d.e.mean())))

fm = pd.read_csv(DATA / "v3" / "ffic_match.csv", usecols=["case_id", "case_title", "conditionId"])
fe = ep[(ep.definition == MAIN) & ep.keep & ~ep.excluded & ep.conditionId.isin(fm.conditionId)].merge(fm, on="conditionId")
ffic = [dict(case=f"{k} {g.case_title.iloc[0]}", markets=g.conditionId.nunique(), episodes=len(g), with_outcome=int(g.y.notna().sum()),
             mean_excess=float(g.e.mean()) if g.y.notna().any() else None) for k, g in fe.groupby("case_id")]

f3 = lambda x: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.3f}" if isinstance(x, float) else f"{x:,}"
f3u = lambda x: "n/a" if x is None else f"{x:.3f}"
L = [f"# Gate 1 result\n\nFrozen test: `rules/frozen_gate1.md` (freeze commit {freeze_commit}). Input hashes checked: match. Run by `src/gate1_run.py`, once.\n",
     f"## Primary\n\nCore universe, main definition ($2,500 within 24 h at a buy VWAP <= 0.35, p_a < 0.50, t_a < T_dec), event as the unit.\n\n"
     f"- Events: {P['n_units']:,}; markets: {P['n_markets']:,}; episodes: {P['n_episodes']:,}.\n"
     f"- Mean excess (outcome - p_a), averaged within event and then across events: **{P['estimate']:+.4f}**. 95% bootstrap CI {P['ci_lo']:+.4f} to {P['ci_hi']:+.4f}; t-test p = {P['t_p']:.3g}.\n"
     f"- Episode level: alert side won {P['mean_y']:.3f} of the time vs mean p_a {P['mean_pa']:.3f}.\n"
     f"- **Decision: {dec}.** " + {"POSITIVE": "Alert sides won more often than the price right after the alert implied. This is before fees and spread, and it is evidence of informed flow on average, not proof about any wallet.",
                                    "NEGATIVE": "Alert sides won LESS often than the price right after the alert implied.",
                                    "NULL": "No excess detectable at this sample size (the feasibility MDE was about 0.04 to 0.05). This is a null result, stated plainly."}[dec] + "\n",
     "## Secondary (they decide nothing)\n\n| analysis | units | markets | episodes | mean excess | 95% CI | t-test p |\n|---|---|---|---|---|---|---|\n" +
     "".join(f"| {s['label']} | {s['n_units']:,} | {s.get('n_markets', 0):,} | {s.get('n_episodes', 0):,} | {f3(s.get('estimate'))} | {f3(s.get('ci_lo'))} to {f3(s.get('ci_hi'))} | {f3u(s.get('t_p'))} |\n" for s in S),
     "\nUnit is the event unless the row says otherwise.\n\n## Calibration (episode level, primary set)\n\n| p_a band | episodes | mean p_a | share won | excess |\n|---|---|---|---|---|\n" +
     "".join(f"| {b['band']} | {b['n']:,} | {b['mean_pa']:.3f} | {b['mean_y']:.3f} | {b['excess']:+.3f} |\n" for b in bands),
     "\n## FFIC markets (descriptive only)\n\nMain definition, kept episodes, markets not excluded. FFIC markets outside v2's candidate list have no outcome in this data, because only the candidate list carries outcomes; those episodes show n/a.\n\n| case | markets | episodes | with outcome | mean excess |\n|---|---|---|---|---|\n" +
     "".join(f"| {r['case']} | {r['markets']} | {r['episodes']} | {r['with_outcome']} | {f3(r['mean_excess'])} |\n" for r in ffic),
     "\n## Notes\n\n- The 165 v2 markets were used, with their outcomes, in the v2 model work on 2026-11-18. The 'markets new in v3' row is the clean out-of-sample check.\n- Excess is before fees and spread. One episode can involve several wallets; no wallet is named.\n"]
(OUT / "gate1_result.md").write_text("\n".join(L))
json.dump(dict(freeze_commit=freeze_commit, primary=P, decision=dec, secondary=S, calibration=bands, ffic=ffic), open(OUT / "gate1_result.json", "w"), indent=1)
print("\n".join(L))
