"""Gate 2: the frozen test in rules/frozen_gate2.md / .json. Run ONCE after the freeze commit is pushed.
Checks input hashes, then loads outcomes. Writes data/results/gate2_result.md/.json and data/v3/gate2_episodes_scored.csv.gz."""
import hashlib, json, math, subprocess
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "data"; OUT = DATA / "results"
FZ = json.load(open(ROOT / "rules" / "frozen_gate2.json"))
for p, h in FZ["inputs_sha256"].items():
    got = hashlib.sha256(open(ROOT / p, "rb").read()).hexdigest(); assert got == h, f"hash mismatch {p}"
fc = subprocess.run(["git", "log", "-1", "--format=%H %cI", "--", "rules/frozen_gate2.json"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
assert fc, "freeze not committed"
B, SEED, (QLO, QHI) = FZ["primary"]["bootstrap"]["resamples"], FZ["primary"]["bootstrap"]["seed"], FZ["primary"]["bootstrap"]["interval"]
T0 = FZ["primary"]["threshold"]
CAT = dict(military_gov="military/government", company="company", appointment="appointment", award_committee="award", central_bank="central bank")

E = pd.read_csv(DATA / "v3" / "gate2_episodes.csv.gz", dtype={"unit_event": str, "series_id": str})
E["unit_series"] = np.where(E.series_id.notna(), "s:" + E.series_id.astype(str), "e:" + E.unit_event)
mi = pd.read_csv(DATA / "v3" / "market_info.csv", usecols=["conditionId", "question", "source"])
E = E.merge(mi, on="conditionId", how="left")
E["new_in_v3"] = ~E.source.str.contains("v2_165")
g1 = pd.read_csv(DATA / "v3" / "episodes.csv.gz"); g1 = g1[(g1.definition == "main ($2,500, cap 0.35)") & g1.keep]
g1i = {k: np.sort(v.t_a.values) for k, v in g1.groupby(["conditionId", "side"])}
def ov(r):
    a = g1i.get((r.conditionId, r.side))
    if a is None: return False
    i = np.searchsorted(a, r.t_a); return any(abs(a[j] - r.t_a) <= 86400 for j in (i - 1, i) if 0 <= j < len(a))
E["gate1_overlap"] = E.apply(ov, axis=1)

# ---- outcomes: first load for Gate 2 ----
oc = pd.read_csv(DATA / "v2" / "markets_candidates.csv", usecols=["conditionId", "yes_won"])
E = E.merge(oc, on="conditionId", how="left")
E["y"] = np.where(E.side == "Yes", E.yes_won, 1 - E.yes_won)
E["e"] = E.y - E.p_a
E.drop(columns=["question", "source"]).to_csv(DATA / "v3" / "gate2_episodes_scored.csv.gz", index=False, compression="gzip")

def est(d, unit="unit_event"):
    d = d[d.y.notna()]
    if d.empty: return dict(units=0, markets=0, episodes=0, estimate=None, lo=None, hi=None, mean_y=None, mean_pa=None)
    v = d.groupby(unit).e.mean().values
    rng = np.random.default_rng(SEED)
    bs = v[rng.integers(0, len(v), (B, len(v)))].mean(1)
    return dict(units=len(v), markets=d.conditionId.nunique(), episodes=len(d), estimate=float(v.mean()), lo=float(np.percentile(bs, QLO)),
                hi=float(np.percentile(bs, QHI)), mean_y=float(d.y.mean()), mean_pa=float(d.p_a.mean()))

def sel(sig, T=T0, mode="std"): return E[(E.signal == sig) & (E.threshold == T) & (E["mode"] == mode) & E.keep & E.core]
V, R = {}, {}
for sig in ("A", "B"):
    d = sel(sig); assert d.y.notna().all(), "primary episode without outcome"
    P = est(d)
    V[sig] = dict(**P, verdict="PASS" if (P["estimate"] > 0 and P["lo"] > 0) else ("NULL (negative)" if P["hi"] < 0 else "NULL"))
    rows = [dict(label="market unit", **est(d, "conditionId")), dict(label="series unit", **est(d, "unit_series")),
            dict(label="live-realistic (no T_dec rule or exclusion)", **est(sel(sig, mode="live"))),
            dict(label="$1,000", **est(sel(sig, 1000))), dict(label="$10,000", **est(sel(sig, 10000))),
            dict(label="overlaps a Gate 1 episode", **est(d[d.gate1_overlap])), dict(label="does not overlap Gate 1", **est(d[~d.gate1_overlap])),
            dict(label="v2's 165 markets (seen in v2 work)", **est(d[~d.new_in_v3])), dict(label="markets new in v3", **est(d[d.new_in_v3]))]
    rows += [dict(label=f"category: {CAT.get(c, c)}", **est(g)) for c, g in d.groupby("category")]
    rows += [dict(label=f"period {p}", **est(g)) for p, g in d.groupby("period")]
    if sig == "B":
        bl = sel("B_last"); rows.append(dict(label="B_last comparison (last deadline, descriptive)", **est(bl)))
        rows.append(dict(label="B_last, live-realistic", **est(sel("B_last", mode="live"))))
    R[sig] = dict(rows=rows, overlap_share=float(d.gate1_overlap.mean()))

cal = {}
for sig in ("A", "B", "B_last"):
    d = sel(sig); cal[sig] = []
    for lo in np.arange(0, .5, .1):
        g = d[(d.p_a >= lo) & (d.p_a < lo + .1)]
        if len(g): cal[sig].append(dict(band=f"{lo:.1f}-{lo + .1:.1f}", n=len(g), mean_pa=float(g.p_a.mean()), won=float(g.y.mean()), excess=float(g.e.mean())))

fm = pd.read_csv(DATA / "v3" / "ffic_match.csv", usecols=["case_id", "case_title", "conditionId"])
FF = []
for sig in ("A", "B"):
    d = E[(E.signal == sig) & (E.threshold == T0) & (E["mode"] == "std") & E.keep].merge(fm, on="conditionId")
    for k, g in d.groupby("case_id"):
        FF.append(dict(signal=sig, case=f"{k} {g.case_title.iloc[0]}", markets=g.conditionId.nunique(), episodes=len(g), with_outcome=int(g.y.notna().sum()),
                       mean_excess=float(g.e.mean()) if g.y.notna().any() else None))

EX = {sig: sel(sig).sort_values(["n_wallets", "t_a"], ascending=[False, True]).head(5) for sig in ("A", "B")}

f = lambda x: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else (f"{x:+.3f}" if isinstance(x, float) else f"{x:,}")
iso = lambda t: pd.Timestamp(int(t), unit="s", tz="UTC").strftime("%Y-%m-%d %H:%M UTC")
L = [f"# Gate 2 result\n\nFrozen test: `rules/frozen_gate2.md` (freeze commit {fc}). Input hashes: match. Run once by `src/gate2_run.py`. Excess = outcome - p_a, before fees and spread. Unit = Gamma event, equal weight. Intervals: two-sided 97.5% bootstrap (10,000 resamples, seed 192), Bonferroni for two signals.\n",
     "## 1. Verdict\n\n| signal | verdict | mean excess | 97.5% interval | events | markets | episodes | won | mean p_a |\n|---|---|---|---|---|---|---|---|---|\n" +
     "".join(f"| {s} ({'price-insensitive accumulation' if s == 'A' else 'deadline choice'}) | **{v['verdict']}** | {f(v['estimate'])} | {f(v['lo'])} to {f(v['hi'])} | {v['units']:,} | {v['markets']:,} | {v['episodes']:,} | {v['mean_y']:.3f} | {v['mean_pa']:.3f} |\n" for s, v in V.items())]
L.append("\n## 2. Counts\n\nPrimary: $2,500, std mode, core markets. Blind counts and power for every threshold and mode are in `data/results/gate2_power.md`. "
         f"Ladders: 73 (311 markets). Share of primary episodes that overlap a Gate 1 episode (same market and side, within 24 h): A {R['A']['overlap_share']:.1%}, B {R['B']['overlap_share']:.1%}.\n")
L.append("\n## 3. Robustness (decides nothing)\n")
for sig in ("A", "B"):
    L.append(f"\n**Signal {sig}**\n\n| analysis | units | markets | episodes | mean excess | 97.5% interval |\n|---|---|---|---|---|---|\n" +
             "".join(f"| {r['label']} | {r['units']:,} | {r['markets']:,} | {r['episodes']:,} | {f(r['estimate'])} | {f(r['lo'])} to {f(r['hi'])} |\n" for r in R[sig]["rows"]))
L.append("\nUnits are events unless the row says otherwise.\n\n## 4. Calibration by p_a band (episode level, primary sets)\n")
for sig, rows in cal.items():
    L.append(f"\n**{sig}**\n\n| p_a band | episodes | mean p_a | share won | excess |\n|---|---|---|---|---|\n" + "".join(f"| {r['band']} | {r['n']} | {r['mean_pa']:.3f} | {r['won']:.3f} | {r['excess']:+.3f} |\n" for r in rows))
L.append("\n## 5. FFIC cases (descriptive only; hindsight-selected cases)\n\nFFIC markets outside v2's candidate list have no outcome in this data (n/a).\n\n| signal | case | markets | episodes | with outcome | mean excess |\n|---|---|---|---|---|---|\n" +
         "".join(f"| {r['signal']} | {r['case']} | {r['markets']} | {r['episodes']} | {r['with_outcome']} | {f(r['mean_excess'])} |\n" for r in FF))
L.append("\n## 6. Example episodes (chosen without outcomes: the most wallets, then earliest)\n\n*Unusual activity for review: this does not identify an owner or prove insider trading.*\n")
for sig, d in EX.items():
    L.append(f"\n**Signal {sig}**\n\n| market | side | t_a | p_a | wallets | outcome |\n|---|---|---|---|---|---|\n" +
             "".join(f"| {r.question} | {r.side} | {iso(r.t_a)} | {r.p_a:.3f} | {r.n_wallets}: {', '.join(w + '…' for w in r.wallets.split(';')[:4])}{' …' if r.n_wallets > 4 else ''} | {'won' if r.y == 1 else 'lost'} |\n" for r in d.itertuples()))
L.append("\n## Notes\n\n- Gate 2 was proposed after the Gate 1 NULL, on the same markets. The 'markets new in v3' rows are the cleanest check for v2's earlier look at 165 markets; no clean holdout exists for Gate 1.\n- Signal B only sees cached ladder rungs; v2's 3-markets-per-event cap hides some later deadlines.\n")
(OUT / "gate2_result.md").write_text("\n".join(L))
json.dump(dict(freeze_commit=fc, verdict=V, robustness=R, calibration=cal, ffic=FF), open(OUT / "gate2_result.json", "w"), indent=1, default=str)
print("\n".join(L))
