"""v2 step 1c: fetch maker+taker fills (taker_only=false) for the ranked candidate markets, newest-first cursor pages.
Stops after TARGET successful markets. Max 400 pages per market; larger -> logged as data gap, market dropped.
Fills are cached compactly in data/raw/v2_fills/<conditionId>.csv.gz (not committed); fetch log -> data/v2/fetch_log.csv"""
import sys, time, gzip, json, threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from common import *
TARGET, MAXPAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 160, 400
FD = RAW / "v2_fills"; FD.mkdir(exist_ok=True)
cand = pd.read_csv(DATA / "v2" / "markets_ranked.csv")
KEY = ["transaction_hash", "proxy_wallet", "token_id", "timestamp", "size", "price"]
lock = threading.Lock(); done_ok = []; logrows = []

def fetch(r):
    cid = r.conditionId; f = FD / f"{cid}.csv.gz"
    if f.exists():
        return dict(conditionId=cid, status="cached", pages=None, rows=None)
    rows, cur, page, t0 = [], None, 0, time.time()
    while True:
        page += 1
        if page > MAXPAGES:
            return dict(conditionId=cid, status="dropped_over_%d_pages" % MAXPAGES, pages=page - 1, rows=len(rows))
        p = dict(condition=cid, cursor=cur, taker_only="false") if cur else dict(condition=cid, limit=1000, taker_only="false")
        js = get_json(f"{DATA_API}/trades", params=p)
        d = js.get("data") or []
        rows += [(x["transaction_hash"], x["proxy_wallet"], x["token_id"], x["timestamp"], x["size"], x["price"], x["side"], x.get("outcome_index")) for x in d]
        pg = js.get("pagination") or {}
        cur = pg.get("next_cursor")
        if not pg.get("has_more") or not cur: break
    df = pd.DataFrame(rows, columns=KEY + ["side", "outcome_index"])
    n_raw = len(df); df = df.drop_duplicates(subset=KEY)
    df.to_csv(f, index=False, compression="gzip")
    return dict(conditionId=cid, status="ok", pages=page, rows=n_raw, dupes=n_raw - len(df), wallets=df.proxy_wallet.nunique(), secs=round(time.time() - t0))

def work(r):
    with lock:
        if len(done_ok) >= TARGET: return None
    try: res = fetch(r)
    except Exception as e: res = dict(conditionId=r.conditionId, status="error:" + str(e)[:100])
    with lock:
        logrows.append(res)
        if res["status"] in ("ok", "cached"): done_ok.append(r.conditionId)
        print(len(done_ok), res, flush=True)
    return res

with ThreadPoolExecutor(6) as ex: list(ex.map(work, list(cand.itertuples())))
pd.DataFrame(logrows).to_csv(DATA / "v2" / "fetch_log.csv", index=False)
print("ok markets", len(done_ok), "HTTP non-200 events", len(HTTP_EVENTS))
