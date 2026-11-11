"""Write data/results/v1_summary.md from saved v1 result files (no new analysis)."""
import json

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

from common import DATA

RES = DATA / "results"
S = pd.read_csv(RES / "v1_wallet_scores.csv")
V = pd.read_csv(RES / "v1_validation.csv")
L1 = json.load(open(RES / "v1_layer1.json"))
L2 = json.load(open(RES / "v1_layer2.json"))
v0 = pd.read_csv(RES / "comparison_summary.csv")
v0 = v0[(v0["quantile"] == 0.99) & (v0.label == "insider-possible")].set_index("market_key")
S["band"] = pd.cut(S.F4_buy_usd, [0, 1000, 2500, 10000, np.inf], right=False, labels=["<1k", "1k-2.5k", "2.5k-10k", ">=10k"])
M = ["iran", "maduro", "nobel"]
fmt = lambda x, d=2: "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"

o = ["# v1 results: wallet-market suspicion screen and follow-on test (PILOT)", "",
     "Rules: `rules/frozen_v1.md` (frozen and committed before any v1 feature was computed). 3 insider-possible markets; this is a pilot, not a validated model.",
     "A high score means **consistent with informed trading / unusual activity for review**. It never identifies an owner or proves insider trading.", "",
     "## Finding #1 (v0, unchanged)",
     "Ripple after large trades did not differ between insider-possible markets and BTC controls: +1.98 vs +1.58 extra wallets "
     "(n = 147 vs 50 seeds, permutation p = 0.72). See `data/results/comparison_summary.md`. BTC controls are kept only as an appendix.", "",
     "## Layer 1: screen and timestamp-permutation null", "",
     "| market | pre-news buyers (wallets) | score >= 4 observed | null mean | null 95th pct | null range | p (1,000 perms) |", "|---|---|---|---|---|---|---|"]
for p in L1["permutation"]:
    o.append(f"| {p['market_key']} | {p['n_wallets']} | {p['observed_high']} | {p['null_mean']:.1f} | {p['null_p95']:.0f} | {p['null_min']}-{p['null_max']} | {p['p_value']:.3f} |")
o += ["", "Only **Nobel** has more high-score wallets than random timing produces. Iran and Maduro are at or below the null: their high scores come mostly from flags that do not depend on timing.", "",
      "Score distribution (wallets per score 0-6): " + "; ".join(f"{m}: {L1['score_dist'][m]}" for m in M), "",
      "**F4 sensitivity** (high-score wallets per market): " + "; ".join(f"${r['F4_threshold']:,}: " + ", ".join(f"{m} {r[m]}" for m in M) for r in L1["sensitivity"]), "",
      "**Scorable trades vs v0:** v0 could compare " + ", ".join(f"{m} {int(v0.loc[m,'n_compared'])}" for m in M) +
      f" seeds (Nobel {int(v0.loc['nobel','n_unmatched'])} unmatched). v1 scores every pre-news buyer: " +
      ", ".join(f"{p['market_key']} {p['n_wallets']} wallets / {p['pre_news_buy_fills']} buy fills ({p['pre_news_buy_fills_last6h']} in the last 6 h)" for p in L1["permutation"]) +
      ". Run-up hours are now included.", "",
      "**Flag firing rates** (share of pre-news buyers): " + "; ".join(
          f"{m}: " + ", ".join(f"F{i} {S[S.market_key==m][f'flag_F{i}'].mean():.0%}" for i in range(1, 7)) for m in M) + ".",
      "- **F6 fires for 100% of Iran buyers**: the market lived ~49 h before T_news, so the 72 h timing flag is uninformative there and the Iran permutation null cannot test timing.",
      "- **F5 (conviction) fires for 71-73%** of buyers in Iran and Maduro (most small wallets buy one side only), so it adds little discrimination.", "",
      "## Validation against publicly documented wallets", "",
      "| label | market | identifier | confidence | score | flags fired | rank / n | first score >= 4 (h before T_news) | F7 won | F8 dormant |", "|---|---|---|---|---|---|---|---|---|---|"]
for _, r in V.iterrows():
    o.append(f"| {r.label_id} | {r.market_key} | {r.identifier} | {r.confidence} | {int(r.score)} | {r.flags_fired} | {int(r['rank'])} / {int(r.n_in_market)} | "
             f"{fmt(r.hours_before_news_first_high,1)} | {bool(r.F7_correct)} | {'yes' if r.F8_dormant == 1 else 'no'} |")
nd = V.wallet.nunique(); nh = V.drop_duplicates("wallet").high.sum()
o += ["", f"- **Recall:** {nh} of {nd} distinct documented wallets (8 labels; the CFTC handle and Lookonchain's 0x31a5 resolve to the same wallet) score >= 4 at the frozen $2,500 F4 threshold. Sensitivity: " + "; ".join(
          f"${t:,}: {int((V.drop_duplicates('wallet')[f'score_F4_{t}'] >= 4).sum())}/{nd}" for t in [1000, 2500, 10000]) +
      " (below 4 at $10,000: " + (", ".join(V.drop_duplicates('wallet').loc[V.drop_duplicates('wallet').score_F4_10000 < 4, 'identifier']) or "none") + ").",
      "- Chance check (if the high-score set were random within each market): " + "; ".join(
          f"{m} P = {hypergeom((S.market_key==m).sum(), int(((S.market_key==m)&S.is_high).sum()), k).pmf(k):.2g}" for m, k in [("iran", 2), ("maduro", 3), ("nobel", 2)]) + ".",
      "- **Circularity caveat:** journalists and Lookonchain found these wallets with similar cues (new, focused, large longshot bets before news), so high recall is partly by construction. It shows the screen reproduces public reporting, not that it finds hidden cases.",
      "- 'Hours early' is retrospective: F6 uses T_news, which is not known in real time.", "",
      "### Precision proxy (post-hoc F7/F8; never in the score)", "",
      "| size band | group | n | win rate (F7) | dormant 30 d (F8) |", "|---|---|---|---|---|"]
for r in L1["precision"]:
    o.append(f"| {r['size_band']} | {'score >= 4' if r['is_high'] else 'other'} | {r['n']} | {r['win_rate']:.2f} | {r['dormant_rate']:.2f} |")
w = S[S.F7_correct].groupby(["band", "is_high"], observed=True).agg(n=("wallet", "size"), d=("F8_dormant", "mean")).reset_index()
q = S[S.flag_F3].groupby(["band", "is_high"], observed=True).agg(n=("wallet", "size"), win=("F7_correct", "mean")).reset_index()
o += ["", "**Confound:** all three markets resolved in favour of the side that was the longshot for most of their life, so any longshot screen 'wins' more. "
      "Holding longshot buying fixed (F3 flagged), high-score wallets win **less** often than other longshot buyers: " +
      "; ".join(f"{r.band} {r.win:.2f} (n={r.n}) vs {q[(q.band==r.band)&(~q.is_high)].win.iloc[0]:.2f} (n={q[(q.band==r.band)&(~q.is_high)].n.iloc[0]})" for _, r in q[q.is_high].iterrows()) +
      ". So F7 does **not** support precision here.",
      "**Dormancy among winners** (same outcome held fixed): " +
      "; ".join(f"{r.band}: high {r.d:.2f} (n={r.n}) vs other {w[(w.band==r.band)&(~w.is_high)].d.iloc[0]:.2f} (n={w[(w.band==r.band)&(~w.is_high)].n.iloc[0]})" for _, r in w[w.is_high].iterrows()) +
      ". Larger high-score winners go dormant far more often, consistent with single-use accounts; partly mechanical because F1/F2 already select new, focused accounts.", "",
      "### Price impact per $1,000 (taker buys; YES price of last fill as mid-price proxy; windows crossing T_news dropped)", "",
      "| window | high-score median (n) | all others median (n) | p | others >= $2.5k median (n) | p |", "|---|---|---|---|---|---|"]
for k, v in L1["impact"].items():
    o.append(f"| {k.split('_')[1]} | {v['high_median']:.4f} ({v['high_n']}) | {v['other_median']:.4f} ({v['other_n']}) | {v['p_mwu']:.3f} | "
             f"{v['other_ge2500_median']:.4f} ({v['other_ge2500_n']}) | {v['p_mwu_vs_ge2500']:.3f} |")
o += ["", "Against similarly sized other wallets there is **no significant difference** in price impact per dollar. We do not reproduce Gomez-Cram et al.'s larger impact for suspected insider accounts (different proxy, 3 markets).", "",
      "## Layer 2: do others follow high-score wallets more than matched established-wallet buys?", "",
      f"Follower types: whales = top 1% lifetime volume (>= ${L2['whale_cut_usd']:,.0f}; {L2['n_whales']} wallets), bots = >= 50 trades/day since join ({L2['n_bots']} wallets).",
      f"A seeds without any B match dropped: {L2['A_seeds_without_B_H30']} (30 min), {L2['A_seeds_without_B_H120']} (120 min). "
      "Windows overlapping T_news +-15 min excluded: " + ", ".join(f"{d['kind']} {d['H']} min: {d['n']}" for d in L2["excluded_counts"]) +
      " (listed in `v1_layer2_excluded_windows.csv`).", "",
      "| window | outcome | scope | A seeds (wallets) | mean A | mean B | A - B [95% CI] | p (sign-flip) | wallet-clustered A - B (p) |", "|---|---|---|---|---|---|---|---|---|"]
for t in L2["tests"]:
    if t["outcome"] in ("wallets", "usd", "price_move", "whales", "bots") and (t["scope"] == "pooled" or t["outcome"] == "wallets"):
        d = 0 if t["outcome"] == "usd" else 3 if t["outcome"] == "price_move" else 2
        o.append(f"| {t['H']} | {t['outcome']} | {t['scope']} | {t['n_A_seeds']} ({t['n_A_wallets']}) | {fmt(t['mean_A'],d)} | {fmt(t['mean_B'],d)} | "
                 f"{fmt(t['mean_diff'],d)} [{fmt(t['ci95'][0],d)}, {fmt(t['ci95'][1],d)}] | {fmt(t['p_signflip'],3)} | {fmt(t['wallet_clustered_mean_diff'],d)} ({fmt(t['wallet_clustered_p'],3)}) |")
o += ["", "**Result:** pooled, high-score buys attract **fewer** same-direction followers than matched established-wallet buys, "
      "with no difference in whale or bot followers at 30 min and slightly fewer whales at 120 min. This does **not** support the claim that whales and bots "
      "piggyback on suspicious wallets in general. **Nobel is the exception** (more followers after high-score buys), consistent with the publicly reported "
      "pre-announcement spike, where many traders bought the same side within minutes.",
      "**Limitation:** B seeds are matched on market, size (+-30%) and time (+-6 h), not on local activity; within 6 h activity varies a lot, so part of the "
      "differences can reflect busier or quieter moments rather than trader type. Seeds from the same wallet are not independent (see wallet-clustered column).", "",
      "## What could not be computed, and why",
      "- **On-chain funding sources:** not done. Polygonscan, Dune and Bitquery are not reachable from this session and no API key is available.",
      "- **Additional markets (2-3 more):** not added in this session; time went to the frozen screen, permutation null and validation.",
      "- **Mid-price impact:** no historical order-book mid-price for these dates (price history is 12-hour grain); last-fill price used as proxy.",
      "- **Threshold sources:** the Bock & Guenthoer PDF and ACDC figures could not be opened from this session; thresholds follow the brief as cited.",
      "- **Documented wallets:** only 7 public cases (1 charged, 6 alleged); Bloomberg's two other Nobel accounts were not named in the coverage found.",
      "- **F2 'event cluster':** measured on the single market, not sibling markets in the same event (e.g. other Maduro dates), which can understate focus.",
      "- **Duplicates:** with maker rows, the composite key removed 199 / 420 / 14 rows (Iran / Maduro / Nobel); some may be genuine repeated fills (no log index in the API).",
      "", "All high-score wallets that are not in public reporting are **unusual activity for review, not insiders**. No wallet addresses are listed in this summary except those already published."]
(RES / "v1_summary.md").write_text("\n".join(o) + "\n")
print("\n".join(o))
