"""Tasks 5-6: run the FROZEN v0 rules on every extracted market; first comparison + Maduro blind validation.

Aborts if src/measures.py changed since freezing (sha256 in rules/frozen_v0.json).
Outputs:
  data/results/ripple_<key>_q<quantile>.csv       one row per seed
  data/results/comparison_summary.csv / .md       per-market + pooled numbers, all quantiles
  data/results/maduro_blind_validation.md
"""
import hashlib
import json

import numpy as np
import pandas as pd

import measures as M
from common import DATA, ROOT, RULES, iso

RES = DATA / "results"
RES.mkdir(exist_ok=True)
FROZEN = json.load(open(RULES / "frozen_v0.json"))
sha = hashlib.sha256(open(ROOT / "src" / "measures.py", "rb").read()).hexdigest()
assert sha == FROZEN["measures_py_sha256"], "measures.py changed after freezing - refusing to run"

MK = pd.read_csv(DATA / "markets.csv").set_index("market_key")
QUANTS = [0.95, FROZEN["seed_quantile"], 0.995]


def run(key, q):
    news = M.load_news(key)
    first = min(news)
    end_ts = first - FROZEN["news_buffer_min"] * 60
    df, seeds, anchors, rt = M.run_market(key, FROZEN, end_ts, first_news=first, q=q)
    if len(rt):
        rt["label"] = MK.loc[key, "label"]
        rt["quantile"] = q
        rt["seed_utc"] = rt["timestamp"].map(iso)
        rt["alert"] = (rt["phase"] == "pre-news") & (~rt["news_overlap_excluded"]) & \
                      (rt["excess_wallets"] > FROZEN["alert_threshold_excess_wallets"])
    return df, seeds, anchors, rt


def summarise(rt, key, q, n_trades, n_anchors):
    used = rt[(rt["phase"] == "pre-news") & (~rt["news_overlap_excluded"])] if len(rt) else rt
    m = used.dropna(subset=["excess_wallets"]) if len(used) else used
    f = lambda s: round(float(s), 2) if len(m) else np.nan
    return dict(market_key=key, label=MK.loc[key, "label"], quantile=q, n_trades=n_trades, n_anchors=n_anchors,
                n_seeds=len(rt), n_news_excluded=int(rt["news_overlap_excluded"].sum()) if len(rt) else 0,
                n_post_news=int(((rt["phase"] == "post-news") & ~rt["news_overlap_excluded"]).sum()) if len(rt) else 0,
                n_pre_news=len(used), n_unmatched=len(used) - len(m), n_compared=len(m),
                mean_obs_wallets=f(m["obs_wallets"].mean()) if len(m) else np.nan,
                mean_exp_wallets=f(m["exp_wallets"].mean()) if len(m) else np.nan,
                mean_excess_wallets=f(m["excess_wallets"].mean()) if len(m) else np.nan,
                median_excess_wallets=f(m["excess_wallets"].median()) if len(m) else np.nan,
                mean_excess_trades=f(m["excess_trades"].mean()) if len(m) else np.nan,
                mean_excess_volume_usd=f(m["excess_volume"].mean()) if len(m) else np.nan,
                mean_log_ratio=round(float(m["log_ratio_wallets"].mean()), 3) if len(m) else np.nan,
                n_alerts=int(rt["alert"].sum()) if len(rt) else 0)


def main():
    rows, all_rt = [], []
    for q in QUANTS:
        for key in MK.index:
            df, seeds, anchors, rt = run(key, q)
            rt.to_csv(RES / f"ripple_{key}_q{q}.csv", index=False)
            rows.append(summarise(rt, key, q, len(df), len(anchors)))
            all_rt.append(rt)
            print(rows[-1], flush=True)
    S = pd.DataFrame(rows)
    S.to_csv(RES / "comparison_summary.csv", index=False)
    R = pd.concat(all_rt)
    R.to_csv(RES / "ripple_all.csv", index=False)

    # pooled comparison (pre-news, matched)
    P = R[(R["phase"] == "pre-news") & (~R["news_overlap_excluded"])].dropna(subset=["excess_wallets"])
    pooled = P.groupby(["quantile", "label"]).agg(n_seeds=("excess_wallets", "size"),
                                                  n_markets=("market_key", "nunique"),
                                                  mean_excess=("excess_wallets", "mean"),
                                                  median_excess=("excess_wallets", "median"),
                                                  mean_log_ratio=("log_ratio_wallets", "mean")).round(3).reset_index()
    # permutation test on the primary quantile (label shuffled across seeds) - descriptive only
    pq = P[P["quantile"] == FROZEN["seed_quantile"]]
    rng = np.random.default_rng(0)
    x, lab = pq["excess_wallets"].values, (pq["label"] == "insider-possible").values
    obs = x[lab].mean() - x[~lab].mean() if lab.any() and (~lab).any() else np.nan
    perm = [x[p].mean() - x[~p].mean() for p in (rng.permutation(lab) for _ in range(5000))] if not np.isnan(obs) else []
    pval = float(np.mean(np.abs(perm) >= abs(obs))) if perm else np.nan
    md = ["# First comparison (frozen v0)", "",
          f"Rules: `rules/frozen_v0.md` (frozen {FROZEN['frozen_utc']}). Primary quantile {FROZEN['seed_quantile']}.",
          "Only pre-news seeds whose window does not overlap news +-30 min, and that found matched windows, are compared.", "",
          "## Per market", "", S.to_markdown(index=False), "", "## Pooled by label", "", pooled.to_markdown(index=False), "",
          f"Difference in mean excess wallets (insider-possible minus control) at q={FROZEN['seed_quantile']}: "
          f"{obs:.2f}; two-sided label-permutation p = {pval:.3f} (5000 permutations, seeds treated as independent, "
          f"which they are not; descriptive only).", "",
          f"Placebo bias on controls: +2.45 wallets on average (see frozen rules)."]
    (RES / "comparison_summary.md").write_text("\n".join(md) + "\n")
    print(pooled.to_string(), "\nperm diff", obs, "p", pval)
    blind_validation(R)


def blind_validation(R):
    key = "maduro"
    news = M.load_news(key)
    first = min(news)
    lines = ["# Blind validation: Maduro out by January 31, 2026?", "",
             f"Frozen rules only (`rules/frozen_v0.md`, frozen {FROZEN['frozen_utc']}); no parameter was changed after seeing this market.",
             f"Earliest public news used: {iso(first)} (first reports of explosions in Caracas, approximate); "
             f"Trump post {iso(max(news))}. Resolution {MK.loc[key, 'resolution_utc']}.", ""]
    for q in QUANTS:
        r = R[(R["market_key"] == key) & (R["quantile"] == q)]
        pre = r[(r["phase"] == "pre-news") & (~r["news_overlap_excluded"])]
        al = pre[pre["alert"]]
        last24 = pre[pre["timestamp"] >= first - 24 * 3600]
        lines += [f"## Seed quantile {q}", "",
                  f"- seeds: {len(r)}; pre-news usable: {len(pre)}; excluded for news overlap: {int(r['news_overlap_excluded'].sum())}; post-news: {int((r['phase']=='post-news').sum())}",
                  f"- pre-news seeds in the final 24 h before first news: {len(last24)}",
                  f"- **alerts (excess wallets > {FROZEN['alert_threshold_excess_wallets']:.2f}) before public news: {len(al)}**"]
        if len(al):
            lines += ["", "| seed UTC | hours before first news | direction | notional USD | YES price | observed wallets | expected | excess |",
                      "|---|---|---|---|---|---|---|---|"]
            for _, a in al.sort_values("timestamp").iterrows():
                lines.append(f"| {a['seed_utc']} | {(first - a['timestamp'])/3600:.1f} | {'toward YES (Maduro out)' if a['direction']==1 else 'toward NO'} | {a['notional']:,.0f} | {a['yes_price']:.3f} | {a['obs_wallets']} | {a['exp_wallets']:.1f} | {a['excess_wallets']:.1f} |")
        if len(last24):
            lines += ["", "Pre-news seeds in final 24 h (all, alert or not):", "",
                      "| seed UTC | dir | notional USD | YES price | obs | exp | excess | alert |", "|---|---|---|---|---|---|---|---|"]
            for _, a in last24.sort_values("timestamp").iterrows():
                lines.append(f"| {a['seed_utc']} | {a['direction']:+d} | {a['notional']:,.0f} | {a['yes_price']:.3f} | {a['obs_wallets']} | {a['exp_wallets'] if pd.notna(a['exp_wallets']) else float('nan'):.1f} | {a['excess_wallets'] if pd.notna(a['excess_wallets']) else float('nan'):.1f} | {bool(a['alert'])} |")
        lines.append("")
    lines += ["All flags are **unusual activity for review, not proof of insider trading**. "
              "Wallet addresses are deliberately not listed in this report."]
    (RES / "maduro_blind_validation.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
