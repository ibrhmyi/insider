"""Headline figure for the dataset card: every case on a timeline (event date) by evidence grade, sized by documented wallets.
Writes release/docs/cases_timeline.png. Usage: python3 build/v1/figure.py"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
c = pd.read_csv(os.path.join(D, "data", "cases.csv"), dtype=str, keep_default_na=False)
w = pd.read_csv(os.path.join(D, "data", "wallet_labels.csv"), dtype=str, keep_default_na=False)
n = w[w.label_broad == "true"].groupby("case_id").size()
c["t"] = pd.to_datetime(c.event_date_earliest, errors="coerce"); c = c[c.t.notna() & (c.t >= "2022-06-01")]
c["n"] = c.case_id.map(n).fillna(0)
G = ["E1", "E2", "E3", "E4", "E5", "E6"]
col = {"E1": "#1b4f72", "E2": "#2e86c1", "E3": "#48c9b0", "E4": "#f5b041", "E5": "#dc7633", "E6": "#95a5a6"}
fig, ax = plt.subplots(figsize=(11, 4.2), dpi=150)
for g in G:
    s = c[c.case_grade == g]
    ax.scatter(s.t, [G.index(g)] * len(s), s=30 + 12 * s.n, color=col[g], alpha=0.8, edgecolor="white", linewidth=0.6, label=f"{g} ({len(s)})")
ax.set_yticks(range(len(G))); ax.set_yticklabels(["E1 adjudicated / sanction", "E2 charged", "E3 official inquiry", "E4 analyst, transaction-level", "E5 pattern claim", "E6 rule-based screen"])
ax.invert_yaxis(); ax.grid(axis="x", alpha=0.3)
ax.set_title(f"PMITC v1.2: {len(c)} cases (event dates from mid-2022) of suspected informed trading by event date and strongest evidence grade\n(dot size = documented wallets; labels are allegations by the named sources, not findings)", fontsize=10)
for k, (_, r) in enumerate(c.sort_values("n", ascending=False).head(4).iterrows()):
    ax.annotate(f"{r.case_id} ({int(r.n)})", (r.t, G.index(r.case_grade)), xytext=(-150 + 40 * k, 22 + 14 * k), textcoords="offset points", fontsize=7,
                color="#333", arrowprops=dict(arrowstyle="-", color="#999", lw=0.6))
plt.tight_layout(); plt.savefig(os.path.join(D, "release", "docs", "cases_timeline.png")); print("ok", len(c))
