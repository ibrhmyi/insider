"""v3 step 1: fetch maker+taker fills (/v2/trades?condition=&taker_only=false, newest-first cursor pages), same request
settings as src/v2_02_fetch.py, for every market in data/v3/targets.csv -- or, with --manifest, rebuild the local cache
from the committed manifest data/v2/fills_manifest.csv (fetches every market whose file is missing or has a different
row count).

Cache (outside git, see .gitignore): data/raw/v2_fills/<conditionId>.csv.gz, same columns as v2.
Resumable: pages are appended to data/raw/v2_fills/_part/<cid>.csv and the cursor is saved after every page.
Page cap: max_pages from the target list (400 for the v2 rule sets; none for mil_over12m, v1, ffic). Over the cap the
market is dropped and logged, as in v2. Rate limits: 6 workers; ANY non-200 or network error pauses ALL workers
(backoff doubling from 2 s up to 120 s, honouring Retry-After), and the request is retried (max 8 tries).
Logs: data/v3/fetch_log.csv (per market), data/v3/fetch_run_log.json (requests, errors, time, largest page count)."""
import sys, time, json, threading, argparse
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from common import *

ap = argparse.ArgumentParser(); ap.add_argument("--manifest", action="store_true"); ap.add_argument("--workers", type=int, default=6)
A = ap.parse_args()
FD = RAW / "v2_fills"; PD = FD / "_part"; PD.mkdir(parents=True, exist_ok=True)
OUT = DATA / "v3"; OUT.mkdir(exist_ok=True)
KEY = ["transaction_hash", "proxy_wallet", "token_id", "timestamp", "size", "price"]
COLS = KEY + ["side", "outcome_index"]
lock = threading.Lock()
ST = dict(requests=0, errors=0, retries=0, pause_s=0.0, error_kinds={})
pause_until = [0.0]; backoff = [2.0]

def get(params):
    for attempt in range(1, 9):
        while True:
            w = pause_until[0] - time.time()
            if w <= 0: break
            time.sleep(min(w, 5))
        with lock: ST["requests"] += 1
        try:
            r = SESSION.get(f"{DATA_API}/trades", params=params, timeout=90)
            if r.status_code == 200:
                with lock: backoff[0] = max(2.0, backoff[0] * 0.9)
                return r.json()
            kind, ra = str(r.status_code), r.headers.get("Retry-After")
        except requests.RequestException as e:
            kind, ra = "network:" + type(e).__name__, None
        with lock:
            ST["errors"] += 1; ST["retries"] += 1; ST["error_kinds"][kind] = ST["error_kinds"].get(kind, 0) + 1
            wait = max(float(ra) if ra else 0, backoff[0]); backoff[0] = min(backoff[0] * 2, 120)
            pause_until[0] = max(pause_until[0], time.time() + wait); ST["pause_s"] += wait
        if kind.isdigit() and int(kind) in (400, 404): break
    raise RuntimeError(f"gave up: {params} last={kind}")

def fetch(r):
    cid, cap = r["conditionId"], r.get("max_pages")
    cap = None if cap is None or pd.isna(cap) else int(cap)
    f = FD / f"{cid}.csv.gz"
    if f.exists() and not r.get("_force"): return dict(conditionId=cid, status="cached")
    part, st = PD / f"{cid}.csv", PD / f"{cid}.json"
    s = json.load(open(st)) if st.exists() and part.exists() else dict(cursor=None, pages=0, rows=0, secs=0.0)
    if s["pages"] == 0 and part.exists(): part.unlink()
    t0 = time.time()
    with open(part, "a") as fh:
        while True:
            if cap is not None and s["pages"] >= cap:
                fh.close(); part.unlink(); st.unlink(missing_ok=True)
                return dict(conditionId=cid, status=f"dropped_over_{cap}_pages", pages=s["pages"], rows=s["rows"])
            p = dict(condition=cid, cursor=s["cursor"], taker_only="false") if s["cursor"] else dict(condition=cid, limit=1000, taker_only="false")
            js = get(p); d = js.get("data") or []
            for x in d:
                fh.write(",".join(str(v) for v in (x["transaction_hash"], x["proxy_wallet"], x["token_id"], x["timestamp"], x["size"], x["price"], x["side"], x.get("outcome_index", ""))) + "\n")
            fh.flush()
            pg = js.get("pagination") or {}
            s.update(cursor=pg.get("next_cursor"), pages=s["pages"] + 1, rows=s["rows"] + len(d), secs=s["secs"] + time.time() - t0); t0 = time.time()
            json.dump(s, open(st, "w"))
            if not pg.get("has_more") or not s["cursor"]: break
    df = pd.read_csv(part, header=None, names=COLS, dtype={"token_id": str, "transaction_hash": str, "proxy_wallet": str})
    n_raw = len(df); df = df.drop_duplicates(subset=KEY)
    df.to_csv(f, index=False, compression="gzip"); part.unlink(); st.unlink()
    return dict(conditionId=cid, status="ok", pages=s["pages"], rows_raw=n_raw, rows=len(df), dupes=n_raw - len(df), wallets=df.proxy_wallet.nunique(),
                first_fill_ts=int(df.timestamp.min()) if len(df) else None, last_fill_ts=int(df.timestamp.max()) if len(df) else None, secs=round(s["secs"]))

logrows = []
T0 = time.time()
def work(r):
    try: res = fetch(r)
    except Exception as e: res = dict(conditionId=r["conditionId"], status="error:" + str(e)[:150])
    with lock:
        logrows.append(res); n = len(logrows)
        if res["status"] != "cached":
            with open(OUT / f"{'rebuild' if A.manifest else 'fetch'}_log.jsonl", "a") as fj: fj.write(json.dumps(res) + "\n")
        json.dump(dict(started_utc=iso(T0), elapsed_s=round(time.time() - T0), done=n, of=len(todo), **ST), open(OUT / "fetch_heartbeat.json", "w"))
        if res["status"] != "cached" or n % 100 == 0:
            print(n, ST["requests"], ST["errors"], {k: res.get(k) for k in ("conditionId", "status", "pages", "rows", "secs")}, flush=True)
    return res

if A.manifest:
    tg = pd.read_csv(DATA / "v2" / "fills_manifest.csv")
    tg = tg[tg.status == "ok"]
    def need(r):
        f = FD / f"{r.conditionId}.csv.gz"
        if not f.exists(): return True
        return sum(1 for _ in __import__("gzip").open(f, "rt")) - 1 != int(r.rows)
    todo = [dict(conditionId=r.conditionId, max_pages=None, _force=True) for r in tg.itertuples() if need(r)]
    print(f"rebuild: {len(todo)} of {len(tg)} files missing or different", flush=True)
    for r in todo: (FD / f"{r['conditionId']}.csv.gz").unlink(missing_ok=True)
else:
    tg = pd.read_csv(OUT / "targets.csv").sort_values("volumeNum", ascending=False)  # biggest first: they run longest
    todo = tg[["conditionId", "max_pages"]].to_dict("records")
with ThreadPoolExecutor(A.workers) as ex: list(ex.map(work, todo))
el = time.time() - T0
name = "rebuild_log" if A.manifest else "fetch_log"
log = pd.read_json(OUT / f"{name}.jsonl", lines=True).drop_duplicates("conditionId", keep="last")  # every run's results, latest per market
log.to_csv(OUT / f"{name}.csv", index=False)
runs = json.load(open(OUT / "fetch_run_log.json")) if (OUT / "fetch_run_log.json").exists() else []
runs.append(dict(mode=name, started_utc=iso(T0), elapsed_s=round(el), workers=A.workers, **ST, markets=len(todo),
                 status=log.status.value_counts().to_dict(), largest_pages=int(log.pages.max()) if "pages" in log and log.pages.notna().any() else None))
json.dump(runs, open(OUT / "fetch_run_log.json", "w"), indent=1)
print("done", runs[-1], flush=True)
