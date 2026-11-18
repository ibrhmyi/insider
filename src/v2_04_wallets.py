"""v2 step 1e: /v2/user-stats for every wallet with a position of >= USD 100 (join_date, n markets, lifetime volume). Cached incrementally."""
import time, threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from common import *
pos = pd.read_csv(DATA / "v2" / "positions.csv.gz")
ws = sorted(pos[pos.usd_bought_cut >= 100].proxy_wallet.unique())
cache = DATA / "v2" / "wallet_stats.csv"
have = pd.read_csv(cache) if cache.exists() else pd.DataFrame(columns=["wallet"])
hs = set(have.wallet); todo = [w for w in ws if w not in hs]
print("wallets", len(ws), "todo", len(todo), flush=True)
rows, errs, lock = [], [], threading.Lock()
def one(w):
    try:
        js = get_json(f"{DATA_API}/user-stats", params=dict(user=w), max_tries=4, timeout=40)
        d = js.get("data")
        if d is None: r = dict(wallet=w, known=False)
        else:
            p = d.get("all_time_pnl") or {}
            r = dict(wallet=w, known=True, n_markets=d.get("trades"), join_date=d.get("join_date"), life_volume_usdc=p.get("volume_usdc"),
                     life_trade_count=p.get("trade_count"), obs_ts=p.get("timestamp"))
    except Exception as e:
        with lock: errs.append((w, str(e)[:100])); return
    with lock:
        rows.append(r)
        if len(rows) % 2000 == 0:
            pd.concat([have, pd.DataFrame(rows)]).to_csv(cache, index=False); print(len(rows), len(errs), flush=True)
with ThreadPoolExecutor(12) as ex: list(ex.map(one, todo))
pd.concat([have, pd.DataFrame(rows)]).to_csv(cache, index=False)
dump(dict(n_errors=len(errs), errors=errs[:200], n_http_events=len(HTTP_EVENTS)), DATA / "v2" / "wallet_fetch_errors.json")
print("done", len(rows), "errors", len(errs))
