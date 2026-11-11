"""v1 figures (UTC): fig4 score distribution, fig5 Maduro + Nobel timelines, fig6 Layer 2 A vs B, fig7 alert card v1."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import CLEAN, DATA, FIG

RES = DATA / "results"
S = pd.read_csv(RES / "v1_wallet_scores.csv")
V = pd.read_csv(RES / "v1_validation.csv")
L1 = json.load(open(RES / "v1_layer1.json"))
L2 = json.load(open(RES / "v1_layer2.json"))
R2 = pd.read_csv(RES / "v1_layer2_seeds.csv")
NEWS = pd.read_csv(DATA / "news_events.csv")
MK = pd.read_csv(DATA / "markets.csv").set_index("market_key")
T_NEWS = {k: int(NEWS[NEWS.market_key == k].news_epoch.min()) for k in ["iran", "maduro", "nobel"]}
NAME = {"iran": "Iran strike (Jun 2025)", "maduro": "Maduro out by Jan 31 (Jan 2026)", "nobel": "Machado Nobel (Oct 2025)"}

# validated reference palette (light): slot 1 blue, slot 2 orange; neutral inks
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
FOOT = "Unusual activity for review — this does not identify an owner or prove insider trading."


def fig4():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2), sharey=False)
    for ax, m in zip(axes, ["iran", "maduro", "nobel"]):
        s = S[S.market_key == m]
        cnt = s.score.value_counts().reindex(range(7), fill_value=0)
        cols = [ORANGE if k >= 4 else "#b9b8b2" for k in cnt.index]
        ax.bar(cnt.index, cnt.values, color=cols, width=0.8, edgecolor=SURF, linewidth=2)
        ax.set_yscale("log")
        for k, v in cnt.items():
            ax.text(k, v * 1.15 if v else 1, str(v), ha="center", fontsize=8.5, color=INK2)
        v = V[(V.market_key == m) & V.in_population].drop_duplicates("wallet")
        lines = []
        for _, r in v.iterrows():
            lab = " = ".join(V[(V.wallet == r.wallet)].identifier.astype(str))
            ax.scatter([r.score], [cnt[r.score] * 1.9], marker="v", s=70, color=BLUE, zorder=5)
            lines.append(f"{lab}: score {int(r.score)}, rank {int(r['rank'])}/{int(r.n_in_market)}, {r.hours_before_news_first_high:.0f} h early")
        ax.text(0.98, 0.97, "Documented wallets\n" + "\n".join(lines), transform=ax.transAxes, ha="right", va="top", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.4", fc=SURF, ec=GRID))
        p = [x for x in L1["permutation"] if x["market_key"] == m][0]
        ax.set_title(f"{NAME[m]}\nn = {len(s)} pre-news buyers; score>=4: {p['observed_high']} "
                     f"(null mean {p['null_mean']:.0f}, p = {p['p_value']:.3f})", fontsize=9.5, loc="left")
        ax.set_xlabel("Ex-ante score (flags F1-F6 fired)")
        ax.set_xticks(range(7)); ax.set_ylim(0.8, cnt.max() * 400)
    axes[0].set_ylabel("Wallets (log scale)")
    h = [plt.Rectangle((0, 0), 1, 1, color=ORANGE, label="high score (>= 4)"),
         plt.Rectangle((0, 0), 1, 1, color="#b9b8b2", label="score 0-3"),
         plt.Line2D([], [], marker="v", ls="", color=BLUE, label="documented wallet (public reporting)")]
    fig.legend(handles=h, loc="upper right", ncol=3, frameon=False, fontsize=9)
    fig.suptitle("Figure 4 - Wallet suspicion scores (frozen v1) with publicly documented wallets marked", x=0.01, ha="left", fontsize=12)
    fig.text(0.01, 0.01, "Null = 1,000 timestamp permutations per market (buy times redrawn from the market's pre-news activity). " + FOOT,
             fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(FIG / "fig4_score_distribution.png", dpi=200)
    plt.close(fig)


def load(m):
    f = pd.read_csv(CLEAN / f"v1_fills_{m}.csv").sort_values("timestamp")
    yes = f.outcome_index == 0
    f["yes_price"] = np.where(yes, f.price, 1 - f.price)
    f["usd"] = f["size"] * f["price"]
    return f


def fig5():
    fig, axes = plt.subplots(2, 1, figsize=(13, 8.5))
    for ax, m, hrs in [(axes[0], "maduro", 48), (axes[1], "nobel", 24)]:
        T = T_NEWS[m]
        f = load(m)
        f = f[(f.timestamp >= T - hrs * 3600) & (f.timestamp <= T + 2 * 3600)]
        t = pd.to_datetime(f.timestamp, unit="s", utc=True)
        ax.plot(t, f.yes_price, color=INK2, lw=1, drawstyle="steps-post", label="YES price (last fill)")
        high = set(S[(S.market_key == m) & (S.score >= 4)].wallet)
        doc = set(V[(V.market_key == m)].wallet)
        b = f[(f.side == "BUY") & f.proxy_wallet.isin(high) & (f.timestamp < T)]
        bo = b[~b.proxy_wallet.isin(doc)]
        bd = b[b.proxy_wallet.isin(doc)]
        sz = lambda u: 8 + np.sqrt(u) * 1.2
        ax.scatter(pd.to_datetime(bo.timestamp, unit="s", utc=True), bo.yes_price, s=sz(bo.usd), color=ORANGE, alpha=0.55,
                   lw=0, label="buy by high-score wallet (score >= 4)")
        ax.scatter(pd.to_datetime(bd.timestamp, unit="s", utc=True), bd.yes_price, s=sz(bd.usd), facecolors="none",
                   edgecolors=BLUE, lw=1.6, label="buy by documented wallet (public reporting)")
        for k, (_, n) in enumerate(NEWS[NEWS.market_key == m].iterrows()):
            tn = pd.to_datetime(n.news_epoch, unit="s", utc=True)
            ax.axvline(tn, color=INK, ls="--", lw=1.2)
            ax.text(tn, 0.95 - 0.17 * k, "  " + n.description.split("(")[0].split(":")[0][:40] + f"\n  {tn:%H:%M} UTC", fontsize=8.5, va="top")
        ax.set_ylim(-0.02, 1.02)
        ax.set_ylabel("Implied probability of YES")
        nh = S[(S.market_key == m) & (S.score >= 4)].shape[0]
        ax.set_title(f"{MK.loc[m,'market_name']} - last {hrs} h before T_news ({nh} high-score wallets in market; "
                     f"{len(b)} of their pre-news buy fills shown; marker area ~ USD)", loc="left", fontsize=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M", tz="UTC"))
        ax.legend(loc="center left", frameon=False, fontsize=8.5)
    fig.suptitle("Figure 5 - Pre-news buying by high-score wallets (UTC)", x=0.01, ha="left", fontsize=12)
    fig.text(0.01, 0.005, "Blue rings: wallets named in public reporting (Lookonchain, CFTC complaint, Bloomberg/WSJ coverage); "
             "orange: other high-score wallets. " + FOOT, fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    fig.savefig(FIG / "fig5_timelines_maduro_nobel.png", dpi=200)
    plt.close(fig)


def fig6():
    T = pd.DataFrame(L2["tests"])
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6), gridspec_kw=dict(width_ratios=[1.25, 1]))
    ax = axes[0]
    scopes = ["pooled", "iran", "maduro", "nobel"]
    for j, H in enumerate([30, 120]):
        q = T[(T.outcome == "wallets") & (T.H == H)].set_index("scope").loc[scopes]
        y = np.arange(len(scopes)) + (0.17 if H == 30 else -0.17)
        lo = q.mean_diff - q.ci95.str[0]; hi = q.ci95.str[1] - q.mean_diff
        ax.errorbar(q.mean_diff, y, xerr=[lo, hi], fmt="o" if H == 30 else "s", color=BLUE if H == 30 else ORANGE,
                    ms=7, capsize=3, lw=1.6, label=f"{H}-min window")
        for yy, (_, r) in zip(y, q.iterrows()):
            ax.text(ax.get_xlim()[1] if False else r.ci95[1] + 0.8, yy, f"n={r.n_A_seeds} A seeds ({r.n_A_wallets} wallets), p={r.p_signflip:.3f}",
                    va="center", fontsize=7.8, color=INK2)
    ax.axvline(0, color=INK, lw=1)
    ax.set_yticks(range(len(scopes)), [s.capitalize() for s in scopes])
    ax.invert_yaxis()
    ax.set_xlabel("A - B: extra distinct same-direction taker wallets after the seed\n(A = high-score wallet buy; B = similar-size buy by established wallet, +-6 h)")
    ax.set_title("Follow-on: suspicious vs established-wallet buys (mean, 95% bootstrap CI)", loc="left", fontsize=10)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, -0.17), ncol=2, fontsize=8.5)
    ax.set_xlim(-40, 60)
    ax = axes[1]
    q = T[(T.scope == "pooled") & (T.H == 30) & T.outcome.isin(["whales", "bots", "others"])].set_index("outcome").loc[["whales", "bots", "others"]]
    x = np.arange(3)
    ax.bar(x - 0.2, q.mean_A, 0.38, color=ORANGE, label="A: high-score wallet seeds", edgecolor=SURF, linewidth=2)
    ax.bar(x + 0.2, q.mean_B, 0.38, color="#8f8e88", label="B: matched established-wallet seeds", edgecolor=SURF, linewidth=2)
    for i, (_, r) in enumerate(q.iterrows()):
        ax.text(i - 0.2, r.mean_A + 0.3, f"{r.mean_A:.1f}", ha="center", fontsize=8.5)
        ax.text(i + 0.2, r.mean_B + 0.3, f"{r.mean_B:.1f}", ha="center", fontsize=8.5)
        ax.text(i, -2.6, f"diff {r.mean_diff:+.2f}\np={r.p_signflip:.2f}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(x, ["whales\n(top 1% lifetime vol.)", "bots\n(>= 50 trades/day)", "others"])
    ax.set_ylabel("Mean follower wallets per seed (30 min, pooled)")
    ax.set_ylim(-3.6, max(q.mean_A.max(), q.mean_B.max()) * 1.2)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_title(f"Who follows? (n = {int(q.n_A_seeds.iloc[0])} A seeds with >= 1 B match)", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.suptitle("Figure 6 - Layer 2: do traders follow high-score wallets more than equally large ordinary trades?", x=0.01, ha="left", fontsize=12)
    ex = {f"{d['kind']}{d['H']}": d["n"] for d in L2["excluded_counts"]}
    fig.text(0.01, 0.005, f"Windows overlapping T_news +-15 min excluded (A: {ex.get('A30',0)} at 30 min, {ex.get('A120',0)} at 120 min). "
             f"A seeds with no B match dropped ({L2['A_seeds_without_B_H30']} at 30 min). Sign-flip p, 10,000 flips. Pilot: 3 markets.",
             fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(FIG / "fig6_layer2_followon.png", dpi=200)
    plt.close(fig)


def fig7_card(label="MAD-CFTC-1"):
    v = V[V.label_id == label].iloc[0]
    s = S[(S.market_key == v.market_key) & (S.wallet == v.wallet)].iloc[0]
    srcs = V[V.wallet == v.wallet]
    r2 = R2[(R2.A_wallet == v.wallet)]
    T = T_NEWS[v.market_key]
    fig = plt.figure(figsize=(11, 7.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0.02, 0.03), 0.96, 0.94, fill=False, ec=INK2, lw=1.2))
    ax.add_patch(plt.Rectangle((0.02, 0.87), 0.96, 0.10, color="#fab219", alpha=0.25, lw=0))
    ax.text(0.04, 0.92, "UNUSUAL ACTIVITY FOR REVIEW", fontsize=17, weight="bold", va="center")
    ax.text(0.96, 0.92, "Figure 7 - alert card v1 (frozen v1 rules)", fontsize=9, ha="right", va="center", color=INK2)
    flags = {"F1": f"fresh account: {s.F1_days:.1f} days from account start to first trade here (<= 7)",
             "F2": f"focus: {s.F2_share:.0%} of volume to T_news in this market; {int(s.F2_n_markets)} markets lifetime",
             "F3": f"longshot: avg price paid {s.F3_vwap:.3f} on {s.main_outcome} (<= 0.35)",
             "F4": f"size: \\${s.F4_buy_usd:,.0f} bought before news (>= \\$2,500)",
             "F5": f"conviction: {s.F5_conviction:.2f} net/gross (>= 0.8)",
             "F6": f"timing: main buying {s.F6_hours_before_news:.1f} h before first public news (<= 72 h)"}
    fired = s.flags_fired.split(",")
    rows = [("Market", MK.loc[v.market_key, "market_name"]),
            ("Wallet", f"{v.wallet[:6]}... (prefix as publicly reported); score {int(s.score)}/6, rank {int(s['rank_in_market'])} of {int(s.n_in_market)}"),
            ("Flags fired", "\n".join(("[x] " if k in fired else "[ ] ") + t for k, t in flags.items())),
            ("Price impact", f"median direction-signed YES price change per \\$1k bought: {s.impact_5m_per_1k:+.4f} (5 min), "
                             f"{s.impact_60m_per_1k:+.4f} (60 min)" if pd.notna(s.impact_60m_per_1k) else "not computable (windows cross news)"),
            ("Follow-on", (f"30 min after its {len(r2[r2.H==30])} seed(s): {r2[r2.H==30].A_wallets.mean():.1f} same-direction wallets vs "
                           f"{r2[r2.H==30].B_wallets.mean():.1f} after matched established-wallet buys (B)") if len(r2[r2.H == 30]) and r2[r2.H == 30].B_wallets.notna().any()
                          else "no matched established-wallet seeds (B) within +-6 h / +-30% size"),
            ("News context", f"First public news {pd.to_datetime(T, unit='s', utc=True):%Y-%m-%d %H:%M} UTC (explosions reported in Caracas, approx.);\n"
                             f"score first reached >= 4 about {s.hours_before_news_first_high:.0f} h before that (retrospective)."),
            ("Public record", "\n".join(f"{r.confidence.upper()}: {r.label_id} ({r.identifier})" for _, r in srcs.iterrows()) +
                              "  - see data/labels/documented_wallets.csv")]
    y = 0.83
    for k, t in rows:
        ax.text(0.04, y, k, fontsize=10.5, weight="bold", va="top")
        ax.text(0.19, y, t, fontsize=10, va="top")
        y -= 0.05 + 0.029 * t.count("\n")
    ax.text(0.04, 0.10, f"Post-hoc, NOT used in the score: position won = {'yes' if s.F7_correct else 'no'}; "
            f"no trades in the 30 days after resolution (dormant) = {'yes' if s.F8_dormant == 1 else 'no'}", fontsize=9.5, color=INK2)
    ax.text(0.04, 0.055, FOOT, fontsize=11, weight="bold")
    fig.savefig(FIG / "fig7_alert_card_v1.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig4(); fig5(); fig6(); fig7_card()
    print("ok")
