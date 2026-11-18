"""Scores prereg/forward_test_locked.csv per prereg/forward_test.md. NOT run at creation time (2026-11-18); run after 2026-12-10.
Metrics: (1) Brier(model) vs Brier(market) over resolved markets; (2) hit rate where |model - market| >= 5 points. Missing/void markets reported and excluded."""
import json, hashlib, sys
from pathlib import Path
import numpy as np, pandas as pd, requests
ROOT = Path(__file__).resolve().parents[1]; CSV = ROOT / "prereg" / "forward_test_locked.csv"
print("sha256", hashlib.sha256(CSV.read_bytes()).hexdigest(), "(compare with prereg/forward_test.md)")
L = pd.read_csv(CSV); res = []
for _, r in L.iterrows():
    js = requests.get("https://gamma-api.polymarket.com/markets", params=dict(condition_ids=r.condition_id, closed="true"), timeout=60).json()
    y = None
    if js:
        try:
            pr = [float(x) for x in json.loads(js[0]["outcomePrices"])]
            y = 1 if pr == [1.0, 0.0] else 0 if pr == [0.0, 1.0] else None
        except Exception: pass
    res.append(y)
L["y"] = res; ok = L.dropna(subset=["y"]).copy(); ok["y"] = ok.y.astype(int)
print(f"resolved cleanly: {len(ok)} of {len(L)}; missing/void/open: {len(L) - len(ok)}")
if len(ok):
    bm = float(np.mean((ok.market_price_yes - ok.y) ** 2)); bd = float(np.mean((ok.model_prob_yes - ok.y) ** 2))
    print(f"Brier market {bm:.4f}  Brier model {bd:.4f}  -> primary criterion {'MET' if bd < bm else 'NOT met'} (n={len(ok)})")
    big = ok[ok.diff_points.abs() >= 5]
    hit = ((big.diff_points > 0) & (big.y == 1)) | ((big.diff_points < 0) & (big.y == 0))
    print(f"markets with |diff| >= 5 points: {len(big)}; hits {int(hit.sum())}" + (f" ({hit.mean():.0%})" if len(big) else ""))
    print(ok[["question", "market_price_yes", "model_prob_yes", "diff_points", "y"]].to_string())
