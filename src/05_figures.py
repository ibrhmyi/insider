"""Task 5 figures (frozen v0 results; all times UTC).

Figure 1  figures/fig1_iran_timeline.png       price + trades + news timeline, seeds marked
Figure 2  figures/fig2_ripple_distribution.png excess ripple: control vs insider-possible, with counts
Figure 3  figures/fig3_alert_card.png          example alert card (unusual activity for review)
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import measures as M
from common import DATA, FIG, RULES, iso

FROZEN = json.load(open(RULES / "frozen_v0.json"))
Q = FROZEN["seed_quantile"]
RES = DATA / "results"
MK = pd.read_csv(DATA / "markets.csv").set_index("market_key")
NEWS = pd.read_csv(DATA / "news_events.csv")

# reference palette (validated: scripts/validate_palette.js, light mode, all checks pass)
YES, NO = "#2a78d6", "#eb6834"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})
FOOT = "Unusual activity for review - not proof of insider trading. Source: Polymarket Data API v2 (taker trades)."


def ts(x):
    return pd.to_datetime(x, unit="s", utc=True)


def fig1():
    key = "iran"
    df = M.load_trades(key)
    df = df[df["timestamp"] <= MK.loc[key, "resolution_epoch"] + 600]
    rt = pd.read_csv(RES / f"ripple_{key}_q{Q}.csv")
    news = NEWS[NEWS.market_key == key]
    res_t = ts(MK.loc[key, "resolution_epoch"])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 7.2), sharex=True, gridspec_kw=dict(height_ratios=[1.3, 1]))
    a1.plot(ts(df["timestamp"]), df["yes_price"], color=INK2, lw=1.2, drawstyle="steps-post", label="YES price (last trade)")
    for _, s in rt.iterrows():
        col = YES if s["direction"] == 1 else NO
        mk = "^" if s["direction"] == 1 else "v"
        hollow = s["news_overlap_excluded"] or s["phase"] == "post-news"
        a1.scatter(ts(s["timestamp"]), s["yes_price"], marker=mk, s=70, zorder=5,
                   facecolors="none" if hollow else col, edgecolors=col, linewidths=1.6)
        if s.get("alert", False):
            a1.annotate("alert", (ts(s["timestamp"]), s["yes_price"]), xytext=(0, 14), textcoords="offset points",
                        ha="center", fontsize=9, color=INK)
    a1.set_ylabel("Implied probability of YES")
    a1.set_ylim(-0.03, 1.05)
    a1.set_title("Figure 1 - 'US military action against Iran by Sunday?': price, trades and news (UTC)", loc="left", fontsize=12)
    for ax in (a1, a2):
        for _, n in news.iterrows():
            t = ts(n["news_epoch"])
            ax.axvspan(t - pd.Timedelta(minutes=30), t + pd.Timedelta(minutes=30), color=GRID, alpha=0.9, lw=0)
            ax.axvline(t, color=INK, lw=1.2, ls="--")
        ax.axvline(res_t, color=INK2, lw=1.2, ls=":")
    t0 = ts(news.iloc[0]["news_epoch"])
    a1.text(t0 - pd.Timedelta(minutes=40), 0.75, "public news 23:46 UTC\n(Trump post; grey band =\n+-30 min exclusion)  ", fontsize=9, va="center", ha="right")
    a1.text(res_t, 0.62, "  resolution\n  02:41:50 UTC", fontsize=9, ha="left", color=INK2)
    for d, col, lab in [(1, YES, "toward YES (buy Yes / sell No)"), (-1, NO, "toward NO (sell Yes / buy No)")]:
        x = df[df["direction"] == d]
        a2.scatter(ts(x["timestamp"]), x["notional"], s=8, color=col, alpha=0.55, lw=0, label=lab)
    a2.set_yscale("log")
    a2.set_ylabel("Trade size (USD, log scale)")
    a2.legend(loc="upper left", frameon=False, markerscale=2.5)
    # seed legend on top panel
    h = [plt.Line2D([], [], marker="^", ls="", color=YES, ms=8, label=f"seed toward YES (> rolling {Q*100:g}th pct)"),
         plt.Line2D([], [], marker="v", ls="", color=NO, ms=8, label="seed toward NO"),
         plt.Line2D([], [], marker="^", ls="", mfc="none", mec=INK2, ms=8, label="seed excluded (news window) or post-news"),
         plt.Line2D([], [], color=INK2, lw=1.2, label="YES price (last trade)")]
    a1.legend(handles=h, loc="upper left", frameon=False, fontsize=9)
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M", tz="UTC"))
    a2.set_xlabel("Time (UTC)")
    n_seed = len(rt)
    fig.text(0.01, 0.005, f"{len(df)} taker trades; {n_seed} seeds at q={Q} ({int(rt['news_overlap_excluded'].sum())} news-excluded, "
             f"{int((rt['phase']=='post-news').sum())} post-news). " + FOOT, fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG / "fig1_iran_timeline.png", dpi=200)
    plt.close(fig)


def fig2():
    R = pd.read_csv(RES / "ripple_all.csv")
    P = R[(R["phase"] == "pre-news") & (~R["news_overlap_excluded"])].dropna(subset=["excess_wallets"])
    quants = sorted(P["quantile"].unique())
    fig, axes = plt.subplots(1, len(quants), figsize=(13, 5.6), sharey=True)
    shapes = {"iran": "o", "maduro": "s", "nobel": "D", "ctrl_btc110k_jun17": "o", "ctrl_btc94k_jan5": "s",
              "ctrl_btcupdown_oct14": "D"}
    rng = np.random.default_rng(1)
    for ax, q in zip(axes, quants):
        groups = [("insider-impossible", "Controls\n(insider-impossible)", NO), ("insider-possible", "Insider-possible", YES)]
        for i, (lab, name, col) in enumerate(groups):
            g = P[(P["quantile"] == q) & (P["label"] == lab)]
            bp = ax.boxplot(g["excess_wallets"], positions=[i], widths=0.5, showfliers=False, patch_artist=True,
                            medianprops=dict(color=INK, lw=2), whiskerprops=dict(color=INK2),
                            capprops=dict(color=INK2), boxprops=dict(facecolor=col + "33", edgecolor=col, lw=1.4))
            for mkey, gg in g.groupby("market_key"):
                ax.scatter(i + rng.uniform(-0.18, 0.18, len(gg)), gg["excess_wallets"], s=16, marker=shapes[mkey],
                           color=col, alpha=0.6, lw=0)
            per = ", ".join(f"{k.replace('ctrl_','')}: {v}" for k, v in g["market_key"].value_counts().items())
            ax.text(i, -0.17, f"n = {len(g)} seeds\n{g['market_key'].nunique()} markets\nmean {g['excess_wallets'].mean():+.2f}\nmedian {g['excess_wallets'].median():+.2f}",
                    transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=8.5)
        ax.axhline(0, color=INK, lw=0.8)
        ax.axhline(2.45, color=INK2, lw=0.9, ls="--")
        ax.set_xticks([0, 1], [g[1] for g in groups])
        ax.set_yscale("symlog", linthresh=5)
        ax.set_yticks([-20, -10, -5, 0, 5, 10, 20, 40], ["-20", "-10", "-5", "0", "5", "10", "20", "40"])
        ax.set_title(f"seed = above rolling {q*100:g}th pct" + ("  (primary)" if q == Q else ""), fontsize=10)
    axes[0].set_ylabel("Excess ripple = observed - expected\ndistinct same-direction wallets in 30 min (symlog)")
    axes[-1].text(1.45, 2.45, "placebo bias\n(+2.45)", fontsize=8, color=INK2, va="center")
    h = [plt.Line2D([], [], marker=m, ls="", color=INK2, label=l) for m, l in
         [("o", "Iran (insider-possible) | BTC>\\$110k Jun 17 (control)"), ("s", "Maduro | BTC>\\$94k Jan 5"),
          ("D", "Nobel | BTC Up/Down Oct 14 (0 usable control seeds)")]]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.01, 0.94), frameon=False, fontsize=8.5, ncol=3, title="marker = market pair")
    fig.suptitle("Figure 2 - Ripple after seed trades: pre-news seeds only, news windows excluded", x=0.01, ha="left", fontsize=12)
    fig.text(0.01, 0.005, "Each dot = one seed. Pilot sample: 3 insider-possible vs 2 usable control markets; seeds within a market are not independent. "
             "Label-permutation p (primary) = 0.72.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.86))
    fig.savefig(FIG / "fig2_ripple_distribution.png", dpi=200)
    plt.close(fig)


def fig3(key="nobel", seed_utc="2025-10-09T22:42:57Z"):
    rt = pd.read_csv(RES / f"ripple_{key}_q{Q}.csv")
    s = rt[rt["seed_utc"] == seed_utc].iloc[0]
    news = NEWS[NEWS.market_key == key].iloc[0]
    hrs = (news["news_epoch"] - s["timestamp"]) / 3600
    fig = plt.figure(figsize=(10, 6.4))
    fig.patch.set_facecolor(SURF)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0.02, 0.03), 0.96, 0.94, fill=False, ec=INK2, lw=1.2))
    ax.add_patch(plt.Rectangle((0.02, 0.86), 0.96, 0.11, color="#fab219", alpha=0.25, lw=0))
    ax.text(0.04, 0.915, "UNUSUAL ACTIVITY FOR REVIEW", fontsize=17, weight="bold", va="center")
    ax.text(0.96, 0.915, "Figure 3 - example alert card (frozen v0)", fontsize=9, ha="right", va="center", color=INK2)
    dir_txt = "toward YES (Machado wins)" if s["direction"] == 1 else "toward NO"
    rows = [("Market", MK.loc[key, "market_name"]),
            ("Direction", f"{dir_txt}: {s['side']} {s['outcome']} at YES price {s['yes_price']:.3f}"),
            ("Seed time", f"{s['seed_utc'].replace('T', ' ').replace('Z', '')} UTC"),
            ("Why a seed", f"\\${s['notional']:,.0f} trade > \\${s['threshold_usd']:,.0f} = rolling {Q*100:g}th pct of trade size, prior 24 h"),
            ("News context", f"Official announcement {news['news_utc'].replace('T',' ').replace('Z','')} UTC = {hrs:.1f} h AFTER this seed;\n"
                             "no public news inside the 30-min window (+-30 min buffer). Media reported the price\n"
                             "spike only afterwards; the Nobel Institute later said it would look into possible leaks."),
            ("Baseline", f"{int(s['n_matches'])} matched no-seed windows in the same market (price, activity 1h/5min,\n"
                         f"time-to-announcement; within +-{FROZEN['time_caliper_h']} h). Few matches = weaker baseline.")]
    y = 0.80
    for k, v in rows:
        ax.text(0.04, y, k, fontsize=10.5, weight="bold", va="top")
        ax.text(0.20, y, v, fontsize=10.5, va="top")
        y -= 0.055 + 0.032 * v.count("\n")
    # observed vs expected bars
    bx = fig.add_axes([0.20, 0.13, 0.42, 0.17])
    labels = ["distinct wallets", "trades"]
    obs = [s["obs_wallets"], s["obs_trades"]]
    exp = [s["exp_wallets"], s["exp_trades"]]
    yy = np.arange(2)
    bx.barh(yy + 0.18, obs, height=0.34, color=YES, label="observed (30 min after seed, same direction)")
    bx.barh(yy - 0.18, exp, height=0.34, color=INK2, label="expected (matched no-seed windows)")
    for i in range(2):
        bx.text(obs[i] + 0.4, i + 0.18, f"{obs[i]:.0f}", va="center", fontsize=9)
        bx.text(exp[i] + 0.4, i - 0.18, f"{exp[i]:.1f}", va="center", fontsize=9)
    bx.set_yticks(yy, labels); bx.grid(axis="y", visible=False)
    bx.legend(loc="lower left", frameon=False, fontsize=8.5, bbox_to_anchor=(0.0, 1.0), ncol=2)
    bx.set_xlim(0, max(obs) * 1.25)
    ax.text(0.67, 0.215, f"Excess ripple: +{s['excess_wallets']:.1f} wallets\n(alert threshold +{FROZEN['alert_threshold_excess_wallets']:.1f})\n"
                        f"Volume: \\${s['obs_volume']:,.0f} observed\nvs \\${s['exp_volume']:,.0f} expected", fontsize=11, va="center")
    ax.text(0.04, 0.055, "This card describes trading activity only. It is NOT evidence that any wallet had inside information, "
                         "and no wallet is named.\n" + FOOT.split(".")[1].strip() + ". Rules: rules/frozen_v0.md.",
            fontsize=8.5, color=INK2)
    fig.savefig(FIG / "fig3_alert_card.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig1(); fig2(); fig3()
    print("figures written to", FIG)
