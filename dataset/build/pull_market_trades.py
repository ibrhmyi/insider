"""Pull every fill in a market from the Polymarket Data API v2 (/v2/trades?condition=..., taker_only=false: maker and
taker rows). Used for case markets, or parts of them, after the last Polymarket-v1 (HF) timestamp (PROTOCOL A6.4).
Usage: python3 build/pull_market_trades.py <out_dir> <condition_id> ...   (one gzip JSON per condition; resumable)
Note: the condition shape serves a fixed three-year window (docs.polymarket.com, List trades)."""
import gzip, json, os, sys, time, urllib.parse, urllib.request
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)


def get(url):
    for i in range(8):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"}), timeout=120))
        except Exception:
            time.sleep(min(60, 2 ** i))
    raise RuntimeError(url)


for cid in sys.argv[2:]:
    p = os.path.join(OUT, f"trades_{cid}.json.gz")
    if os.path.exists(p):
        continue
    rows, cur = [], None
    while True:
        q = {"condition": cid, "limit": 1000, "taker_only": "false", "filter_amount": 0}
        if cur:
            q = {"cursor": cur, "taker_only": "false", "condition": cid, "filter_amount": 0}
        d = get("https://data-api.polymarket.com/v2/trades?" + urllib.parse.urlencode(q))
        rows += d["data"]; pg = d.get("pagination", {})
        if not pg.get("has_more"):
            break
        cur = pg["next_cursor"]; time.sleep(0.1)
    with gzip.open(p + ".tmp", "wt") as f:
        json.dump(rows, f)
    os.replace(p + ".tmp", p)
    print(cid, len(rows), flush=True)
