"""Pull Polymarket Data API v2 /activity for addresses (all types: TRADE, REDEEM, SPLIT, MERGE, REWARD, ...).

Usage: python3 build/pull_activity.py <address-file or address> ...
Writes logs/gamma_raw/activity_<address>.json.gz and appends a line to logs/gamma_raw/activity_index.csv
(address, n_rows, truncated, pulled_utc). Cap: 100,000 rows per address (truncated=true if hit).
"""
import csv, datetime, gzip, json, os, sys, time, urllib.parse, urllib.request

D = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(D, "logs", "gamma_raw")
CAP = 100_000


def get(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"})
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception as ex:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def activity(addr):
    out, cur = [], None
    while True:
        q = {"user": addr, "limit": 500, "start": 1}  # start=1: full history (default floors to 3 years back)
        if cur:
            q["cursor"] = cur
        d = get("https://data-api.polymarket.com/v2/activity?" + urllib.parse.urlencode(q))
        out += d["data"]
        p = d.get("pagination", {})
        if not p.get("has_more"):
            return out, False
        if len(out) >= CAP:
            return out, True
        cur = p["next_cursor"]
        time.sleep(0.15)


if __name__ == "__main__":
    addrs = []
    for a in sys.argv[1:]:
        addrs += [x.strip().lower() for x in open(a)] if os.path.exists(a) else [a.lower()]
    idx = os.path.join(RAW, "activity_index.csv")
    done = {r["address"] for r in csv.DictReader(open(idx))} if os.path.exists(idx) else set()
    new = not os.path.exists(idx)
    with open(idx, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["address", "n_rows", "truncated", "pulled_utc"])
        for a in addrs:
            if not a or a in done:
                continue
            try:
                rows, trunc = activity(a)
            except Exception as ex:
                print("FAIL", a, ex, flush=True); continue
            with gzip.open(os.path.join(RAW, f"activity_{a}.json.gz"), "wt") as g:
                json.dump(rows, g)
            w.writerow([a, len(rows), str(trunc).lower(), datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")]); f.flush()
            done.add(a)
            print(a, len(rows), trunc, flush=True)
