"""v1 data: maker+taker fills for the insider-possible markets, then wallet profiles.

usage:
  python v1_01_fetch.py trades            # /v2/trades?taker_only=false, cached pages -> data/clean/v1_fills_<m>.csv
  python v1_01_fetch.py wallets           # /v2/user-stats for every wallet; /v2/user-volume windows for pre-news buyers
Re-download justification (log): v0 kept taker fills only; wallet-level features need every fill a wallet made, incl. limit orders (maker).
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from common import CLEAN, DATA, DATA_API, HTTP_EVENTS, RAW, dump, get_json, iso

MARKETS = ["iran", "maduro", "nobel"]
KEY = ["transaction_hash", "proxy_wallet", "token_id", "timestamp", "size", "price"]
MK = pd.read_csv(DATA / "markets.csv", dtype={"token_id_yes": str, "token_id_no": str}).set_index("market_key")
NEWS = pd.read_csv(DATA / "news_events.csv")
T_NEWS = {k: int(NEWS[NEWS.market_key == k].news_epoch.min()) for k in MARKETS}


def fetch_trades():
    for m in MARKETS:
        out = RAW / "trades_allsides" / m
        out.mkdir(parents=True, exist_ok=True)
        rows, cur, page, log = [], None, 0, []
        while True:
            page += 1
            f = out / f"page_{page:04d}.json"
            if f.exists():
                js = json.load(open(f))
            else:
                p = dict(condition=MK.loc[m, "condition_id"], limit=1000, taker_only="false")
                if cur:
                    p = dict(condition=MK.loc[m, "condition_id"], cursor=cur, taker_only="false")
                js = get_json(f"{DATA_API}/trades", params=p)
                dump(js, f)
                time.sleep(0.2)
            d = js.get("data") or []
            ts = [x["timestamp"] for x in d]
            log.append(dict(page=page, n=len(d), ts_min=min(ts) if ts else None, ts_max=max(ts) if ts else None,
                            sorted_desc=all(ts[i] >= ts[i + 1] for i in range(len(ts) - 1))))
            rows += d
            pg = js.get("pagination") or {}
            cur = pg.get("next_cursor")
            if not pg.get("has_more") or not cur:
                break
        pd.DataFrame(log).to_csv(out / "batch_log.csv", index=False)
        df = pd.DataFrame(rows)
        df["token_id"] = df["token_id"].astype(str)
        n_raw = len(df)
        df = df.drop_duplicates(subset=KEY).copy()
        taker = pd.read_csv(CLEAN / f"trades_{m}.csv", dtype={"token_id": str})
        tk = set(map(tuple, taker[KEY].astype(str).values))
        df["role"] = ["taker" if tuple(map(str, r)) in tk else "maker" for r in df[KEY].values]
        df["after_resolution"] = df["timestamp"] > int(MK.loc[m, "resolution_epoch"])
        keep = KEY + ["side", "outcome", "outcome_index", "condition_id", "name", "pseudonym", "role", "after_resolution"]
        df[keep].sort_values("timestamp").to_csv(CLEAN / f"v1_fills_{m}.csv", index=False)
        print(f"{m}: pages {page}, rows {n_raw}, dupes {n_raw-len(df)}, taker {int((df.role=='taker').sum())} "
              f"(v0 taker file {len(taker)}), maker {int((df.role=='maker').sum())}, wallets {df.proxy_wallet.nunique()}, "
              f"unsorted pages {sum(not x['sorted_desc'] for x in log)}", flush=True)


def _stats(w):
    js = get_json(f"{DATA_API}/user-stats", params=dict(user=w))
    d = js.get("data")
    if d is None:
        return dict(wallet=w, known=False)
    p = d.get("all_time_pnl") or {}
    return dict(wallet=w, known=True, n_markets=d.get("trades"), join_date=d.get("join_date"),
                life_volume_usdc=p.get("volume_usdc"), life_trade_count=p.get("trade_count"),
                pnl_obs_ts=p.get("timestamp"))


def _vol(w, start, end):
    js = get_json(f"{DATA_API}/user-volume", params=dict(user=w, start=start, end=end))
    d = js.get("data") or {}
    return d.get("volume_usdc"), d.get("trade_count")


def _first_activity(w):
    js = get_json(f"{DATA_API}/activity", params=dict(user=w, start=1, sort_direction="ASC", limit=1))
    d = js.get("data") or []
    return d[0]["timestamp"] if d else None


def pmap(fn, items, workers=8, label=""):
    out, done = [], 0
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, *it) if isinstance(it, tuple) else ex.submit(fn, it): it for it in items}
        for f in as_completed(futs):
            try:
                out.append((futs[f], f.result()))
            except Exception as e:  # recorded, not fatal
                out.append((futs[f], e))
            done += 1
            if done % 1000 == 0:
                print(f"  {label} {done}/{len(items)}", flush=True)
    return out


def fetch_wallets():
    fills = {m: pd.read_csv(CLEAN / f"v1_fills_{m}.csv") for m in MARKETS}
    allw = sorted(set().union(*[set(f.proxy_wallet) for f in fills.values()]))
    cache = DATA / "clean" / "v1_wallet_stats.csv"
    have = pd.read_csv(cache) if cache.exists() else pd.DataFrame(columns=["wallet"])
    todo = [w for w in allw if w not in set(have.wallet)]
    print(f"wallets total {len(allw)}, stats to fetch {len(todo)}", flush=True)
    res = pmap(_stats, todo, label="stats")
    ok = [r for _, r in res if isinstance(r, dict)]
    err = [(w, str(r)[:150]) for w, r in res if not isinstance(r, dict)]
    st = pd.concat([have, pd.DataFrame(ok)], ignore_index=True)
    st.to_csv(cache, index=False)
    print("stats errors", len(err))

    # windowed volumes for pre-news buyers (F2 denominator, F8 dormancy) + first activity when join_date unknown
    rows = []
    for m in MARKETS:
        f = fills[m]
        buyers = sorted(set(f[(f.side == "BUY") & (f.timestamp < T_NEWS[m])].proxy_wallet))
        res_ts = int(MK.loc[m, "resolution_epoch"])
        for w in buyers:
            rows.append((m, w, res_ts))
    vcache = DATA / "clean" / "v1_wallet_windows.csv"
    vhave = pd.read_csv(vcache) if vcache.exists() else pd.DataFrame(columns=["market_key", "wallet"])
    done = set(zip(vhave.market_key, vhave.wallet))
    rows = [r for r in rows if (r[0], r[1]) not in done]
    print(f"pre-news buyer wallet-markets to fetch: {len(rows)}", flush=True)
    jd = st.set_index("wallet")["join_date"].to_dict()

    def one(m, w, res_ts):
        pre_v, pre_n = _vol(w, 1, T_NEWS[m])
        post_v, post_n = _vol(w, res_ts + 86400, res_ts + 30 * 86400)
        fa = _first_activity(w) if pd.isna(jd.get(w)) else None
        return dict(market_key=m, wallet=w, vol_to_tnews_usdc=pre_v, trades_to_tnews=pre_n,
                    post30_volume_usdc=post_v, post30_trade_count=post_n, first_activity_ts=fa)

    res = pmap(one, rows, label="windows")
    ok = [r for _, r in res if isinstance(r, dict)]
    err2 = [(it, str(r)[:150]) for it, r in res if not isinstance(r, dict)]
    pd.concat([vhave, pd.DataFrame(ok)], ignore_index=True).to_csv(vcache, index=False)
    print("window errors", len(err2))
    dump(dict(stats_errors=err, window_errors=err2, http_events=HTTP_EVENTS[-500:], n_http_events=len(HTTP_EVENTS)),
         RAW / "v1_wallet_fetch_errors.json")


if __name__ == "__main__":
    {"trades": fetch_trades, "wallets": fetch_wallets}[sys.argv[1]]()
