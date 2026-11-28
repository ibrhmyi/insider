"""Fetch Gamma public-profile (createdAt, name, pseudonym) per address -> logs/gamma_raw/profile_<address>.json.
Usage: python3 build/pull_profiles.py <address-file or address> ...   (skips addresses already fetched)"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
RAW = os.path.join(os.path.dirname(__file__), "..", "logs", "gamma_raw")
addrs = []
for a in sys.argv[1:]:
    addrs += [x.strip().lower() for x in open(a)] if os.path.exists(a) else [a.lower()]
for a in addrs:
    p = os.path.join(RAW, f"profile_{a}.json")
    if not a or os.path.exists(p):
        continue
    for i in range(5):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(
                "https://gamma-api.polymarket.com/public-profile?" + urllib.parse.urlencode({"address": a}),
                headers={"User-Agent": "curl/8.5.0"}), timeout=60)); break
        except urllib.error.HTTPError as ex:
            if ex.code == 404:
                d = {"error": "not_found"}; break
            time.sleep(2 ** i)
        except Exception:
            time.sleep(2 ** i)
    else:
        d = {"error": "fetch_failed"}
    json.dump(d, open(p, "w")); time.sleep(0.15)
