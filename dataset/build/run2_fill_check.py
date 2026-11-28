"""Run 2 check: pull Data API v2 activity for an address and sum BUY usdc per market title.

Usage: python3 build/run2_fill_check.py <address> [title substring]
Used to settle the AlphaRaccoon conflict (0xee50...: 'd4vd be the #1 searched' Yes buys = $10,650.04)
and to check that Gamma-resolved handles traded their case markets. Output saved to logs/gamma_raw/.
Data API v1 (/trades, /activity) returns 410 since its retirement; v2 is used.
"""
import gzip, json, os, sys, urllib.parse, urllib.request
from collections import defaultdict

def activity(addr):
    out, cur = [], None
    while True:
        q = {"user": addr, "limit": 500}
        if cur:
            q["cursor"] = cur
        req = urllib.request.Request("https://data-api.polymarket.com/v2/activity?" + urllib.parse.urlencode(q),
                                     headers={"User-Agent": "curl/8.5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        out += d["data"]; p = d.get("pagination", {})
        if not p.get("has_more") or len(out) >= 20000:
            return out
        cur = p["next_cursor"]

if __name__ == "__main__":
    a = sys.argv[1].lower(); pat = (sys.argv[2] if len(sys.argv) > 2 else "").lower()
    t = activity(a)
    raw = os.path.join(os.path.dirname(__file__), "..", "logs", "gamma_raw", f"activity_{a}.json.gz")
    with gzip.open(raw, "wt") as f:
        json.dump(t, f)
    s = defaultdict(lambda: [0.0, 0])
    for x in t:
        if x["type"] == "TRADE" and x["side"] == "BUY" and pat in x["title"].lower():
            k = (x["title"], x["outcome"]); s[k][0] += x["usdc_size"]; s[k][1] += 1
    for k, v in sorted(s.items(), key=lambda kv: -kv[1][0])[:20]:
        print(f"{v[0]:12.2f} usdc  {v[1]:4d} fills  {k[1]:>4s}  {k[0]}")
