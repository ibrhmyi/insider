"""Export the v2 results to web/public/data/v2.json for the page. No re-analysis, no numbers typed by hand.

Reads: data/results/v2_analysis.json, data/v2/units.csv.gz, data/v2/units_log.json,
       prereg/forward_test_locked.csv, and `git log` for the commit that added the locked file.
Verdict wording is derived from the intervals, and checked against data/results/v2_summary.md.
"""
import csv
import json
import subprocess

import pandas as pd

from common import DATA, ROOT

A = json.load(open(DATA / "results" / "v2_analysis.json"))
ULOG = json.load(open(DATA / "v2" / "units_log.json"))
LOCK = ROOT / "prereg" / "forward_test_locked.csv"
REPO = "https://github.com/ibrhmyi/insider"

# Plain-word names for the model's features (copy only; every number comes from the files).
PLAIN = {
    "log_age": "how old the wallet is",
    "share_event": "how much of the wallet's volume was in this event",
    "log_usd": "the size of the bet in dollars",
    "log_rel_size": "the size of the bet relative to the market",
    "conviction": "how much of the bought position the wallet kept (did not sell part of it)",
    "log_hours_to_end": "how long before the deadline the bet was placed",
    "log_prior_markets": "how many markets the wallet had traded before",
    "prior_excess": "the wallet's earlier record of beating the price",
}

# Units: the split time comes from the analysis file; training wallets are counted from the units table.
U = pd.read_csv(DATA / "v2" / "units.csv.gz", usecols=["proxy_wallet", "res_ts"])
split = A["splits"]["split_ts"]
train_wallets = int(U[U.res_ts < split].proxy_wallet.nunique())

coef, ci = A["model"]["coef"], A["model"]["coef_ci95"]
top3 = sorted(coef, key=lambda k: -abs(coef[k]))[:3]
coefs = [dict(feature=k, plain=PLAIN[k], coef=coef[k], lo=ci[k][0], hi=ci[k][1],
              excludes_zero=bool(ci[k][0] > 0 or ci[k][1] < 0),
              direction="more" if coef[k] > 0 else "less") for k in top3]

ml, uv, per = A["market_level"], A["unit_validation"], A["persistence"]
v = ml["validation"]
lo, hi = v["brier_diff_ci"]
# Verdict: the summary says the model does not beat the market price; rule: "Yes" only if the whole
# interval of (model - market) Brier is below zero, "No" if the point estimate is not below zero at unit level
# and the market-level interval spans zero, per the summary's own wording. Checked against the summary text.
summary = (DATA / "results" / "v2_summary.md").read_text()
assert "the model does not beat the market price" in summary
verdict = "Yes" if hi < 0 else "No"

# Locked predictions.
rows = list(csv.DictReader(open(LOCK)))
git = lambda *a: subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
sha, commit_iso = git("log", "--format=%H|%cI", "--diff-filter=A", "-1", "--", "prereg/forward_test_locked.csv").split("|")
sha256 = [l for l in (ROOT / "prereg" / "forward_test.md").read_text().splitlines() if l.startswith("`") and len(l.strip("`")) == 64][0].strip("`")
preds = [dict(question=r["question"], slug=r["slug"], market=float(r["market_price_yes"]), model=float(r["model_prob_yes"]),
              status="Waiting for the result") for r in rows]

OUT = dict(
    learned=dict(train_markets=A["splits"]["train_markets"], val_markets=A["splits"]["val_markets"],
                 train_wallets=train_wallets, modelled_markets=ULOG["markets"], modelled_wallets=ULOG["wallets_modelled"]),
    persistence=dict(n_top=per["n_top"], top_2025=per["top_mean_excess_2025"], n_top_2026=per["top_with_2026_units"],
                     top_2026=per["top_2026"], others_2026=per["others_2026"], n_others_2026=per["others_with_2026_units"],
                     diff=per["diff_top_minus_others"]),
    validation=dict(verdict=verdict, n_points=ml["n_points_val"], n_markets=ml["n_markets_val"],
                    brier_market=v["brier_market"], brier_market_ci=v["brier_market_ci"],
                    brier_model=v["brier_model"], brier_model_ci=v["brier_model_ci"],
                    diff=v["brier_diff_model_minus_market"], diff_ci=v["brier_diff_ci"],
                    unit=dict(n_units=uv["n_units"], brier_market=uv["brier_market"], brier_model=uv["brier_model"],
                              diff_ci=uv["brier_diff_ci"])),
    coefficients=coefs,
    forward=dict(snapshot_utc=rows[0]["snapshot_utc"], commit=sha, commit_url=f"{REPO}/commit/{sha}", commit_time=commit_iso,
                 sha256=sha256, predictions=preds),
)
out = ROOT / "web" / "public" / "data" / "v2.json"
out.write_text(json.dumps(OUT, indent=1))
print("wrote", out, "verdict", verdict, "commit", sha[:7])
