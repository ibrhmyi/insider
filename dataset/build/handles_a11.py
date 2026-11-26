"""Run 7 (PROTOCOL A11, B5): every username named in any claim gets a Gamma profile lookup (exact name, then exact
pseudonym), then a fill check against the case's markets. Writes logs/handle_checks_run7.csv (merged into
logs/handle_checks.csv by the caller) and updates data/handles_to_resolve.csv status for A11 resolutions.
Raw responses: logs/gamma_raw/search_run7/<handle>.json. Activity: logs/gamma_raw/activity_<address>.json.gz.
Usage: python3 build/handles_a11.py
"""
import csv, gzip, json, os, subprocess, sys, time, urllib.parse, urllib.request
import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(D, "logs", "gamma_raw")
# handle -> (case_id, claimed outcome label or None, claim ids). Claimed side read from the claim text.
H = {
 "Burdensome-Mix": ("maduro-2026-01", "Yes", "CL0003"), "AlphaRaccoon": ("google-yis-2025", "Yes", "CL0011;CL0013"),
 "0xafEe": ("google-yis-2025", "Yes", "CL0011"), "ricosuave666": ("israel-rising-lion-2025-06", None, "CL0014;CL0015"),
 "rundeep": ("israel-rising-lion-2025-06", None, "seed"), "Magamyman": ("us-iran-strike-2026-02-28", "Yes", "CL0023"),
 "djijaij83jdo4jdlwjflsg": ("us-iran-ceasefire-2026-04-07", "Yes", "CL0033"), "Elonfax89678": ("us-iran-ceasefire-2026-04-07", "Yes", "CL0033"),
 "Skoobidoobnj": ("us-iran-ceasefire-2026-04-07", "Yes", "CL0033;CL0087"), "Bama124": ("walz-vp-2024", "Yes", "CL0040"),
 "OnlyBibi2026": ("netanyahu-odds-support-2026", None, "CL0043"), "romanticpaul": ("taylor-swift-engagement", "Yes", "CL0048"),
 "BornTooLate.eth": ("uma-ukraine-minerals-2025", None, "CL0071"), "BlueHorseshoe86": ("us-iran-ceasefire-2026-04-07", "Yes", "CL0089"),
 "mintblade": ("world-cup-2026-06", None, "CL0091"), "GRIMDRIP": ("world-cup-2026-06", None, "CL0091"),
 "endlessFate": ("world-cup-2026-06", None, "CL0091"), "HD2": ("fed-chair-nomination-2026", "Yes", "CL0098"),
 "dirtycup": ("nobel-peace-2025", None, "CL0100"), "whopperlover": ("bubblemaps-military-cluster", None, "seed"),
 "aenews0": ("nobel-peace-2025", None, "seed"), "hogriddahhhh": ("spotify-wrapped-2025", None, "seed"),
}


def get(url):
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"}), timeout=60))
        except Exception as ex:
            err = str(ex); time.sleep(2 ** i)
    return {"error": err}


mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str)
cases = pd.read_csv(os.path.join(D, "data", "cases.csv"), dtype=str).set_index("case_id")
sys.path.insert(0, os.path.dirname(__file__))
from dates import parse_date  # noqa


def window_end(case):
    ev = cases.loc[case, "event_date"] if case in cases.index else ""
    try:
        lo, hi, _ = parse_date(ev)
        return pd.Timestamp(hi, tz="UTC") + pd.Timedelta(hours=23, minutes=59, seconds=59)
    except Exception:
        return None


def activity(addr):
    p = os.path.join(RAW, f"activity_{addr}.json.gz")
    if not os.path.exists(p):
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "pull_activity.py"), addr], check=False)
    return json.load(gzip.open(p, "rt")) if os.path.exists(p) else []


rows, n = [], 0
for h, (case, side, cl) in H.items():
    p = os.path.join(RAW, "search_run7", f"{h}.json")
    if not os.path.exists(p):
        d = get("https://gamma-api.polymarket.com/public-search?" + urllib.parse.urlencode({"q": h, "search_profiles": "true", "limit_per_type": 50}))
        json.dump(d, open(p, "w")); time.sleep(0.3)
    d = json.load(open(p))
    profs = d.get("profiles") or []
    exact_name = [x for x in profs if x.get("name") == h]
    exact_pseu = [x for x in profs if x.get("pseudonym") == h]
    ci_name = [x for x in profs if (x.get("name") or "").lower() == h.lower() and x not in exact_name]
    # Gamma public-search matches names, not pseudonyms: also scan the stored public-profile responses
    # (logs/gamma_raw/profile_<address>.json, fetched for every labelled address) for an exact pseudonym or name
    for f in sorted(os.listdir(RAW)):
        if f.startswith("profile_") and f.endswith(".json"):
            q = json.load(open(os.path.join(RAW, f)))
            if isinstance(q, dict) and q.get("proxyWallet") and q.get("pseudonym") == h and all(q["proxyWallet"] != y.get("proxyWallet") for y in exact_pseu):
                exact_pseu.append(dict(name=q.get("name"), pseudonym=q.get("pseudonym"), proxyWallet=q["proxyWallet"], _via="stored_profile"))
            if isinstance(q, dict) and q.get("proxyWallet") and q.get("name") == h and all(q["proxyWallet"] != y.get("proxyWallet") for y in exact_name):
                exact_name.append(dict(name=q.get("name"), pseudonym=q.get("pseudonym"), proxyWallet=q["proxyWallet"], _via="stored_profile"))
    cands = [("name_exact", x) for x in exact_name] + [("pseudonym_exact", x) for x in exact_pseu] + [("name_case_insensitive", x) for x in ci_name]
    if not cands:
        n += 1
        rows.append(dict(check_id=f"HC7{n:03d}", check_type="gamma_lookup", subject=h, address=None, case_id=case, claim_ids=cl,
                         match_type="none", n_profiles_returned=len(profs), result="failed_no_match" if profs else "failed_no_profiles"))
        continue
    cm = mk[mk.case_id == case]
    cids = set(cm.condition_id.str.lower()); created = dict(zip(cm.condition_id.str.lower(), cm.created_utc))
    wend = window_end(case)
    for mt, x in cands:
        a = (x.get("proxyWallet") or "").lower(); n += 1
        acts = [t for t in activity(a) if t.get("type") == "TRADE" and t.get("condition_id", "").lower() in cids]
        buys = [t for t in acts if t.get("side") == "BUY" and (side is None or (t.get("outcome") or "") == side)]
        inwin = [t for t in buys if (wend is None or t["timestamp"] <= wend.timestamp())
                 and t["timestamp"] >= pd.Timestamp(created.get(t["condition_id"].lower()) or "2000-01-01", tz="UTC").timestamp()]
        ok = len(inwin) > 0
        if mt == "name_exact":
            res = "resolved_name_exact_fills_confirmed" if ok else ("resolved_name_exact_fills_not_confirmed" if acts else "rejected_exact_match_no_fills")
        elif mt == "pseudonym_exact":
            res = "resolved_pseudonym_with_fills" if ok else "rejected_pseudonym_no_fills"
        else:
            res = "resolved_case_insensitive_with_fills" if ok else "rejected_case_insensitive_no_fills"
        ts = sorted(t["timestamp"] for t in inwin)
        rows.append(dict(check_id=f"HC7{n:03d}", check_type="gamma_lookup+fill_check", subject=h, address=a, case_id=case, claim_ids=cl,
                         match_type=mt, lookup_via=x.get("_via", "gamma_public_search"), profile_name=x.get("name"), profile_pseudonym=x.get("pseudonym"), n_profiles_returned=len(profs),
                         claimed_outcome=side, window_end_utc=wend.strftime("%Y-%m-%dT%H:%M:%SZ") if wend is not None else None,
                         n_case_trades=len(acts), n_confirming_buys=len(inwin),
                         confirming_buy_usdc=round(sum(float(t.get("usdc_size") or 0) for t in inwin), 2),
                         first_confirming_buy_utc=pd.Timestamp(ts[0], unit="s", tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None,
                         last_confirming_buy_utc=pd.Timestamp(ts[-1], unit="s", tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None,
                         result=res))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(D, "logs", "handle_checks_run7.csv"), index=False)
print(out[["subject", "address", "match_type", "n_case_trades", "n_confirming_buys", "confirming_buy_usdc", "result"]].to_string())
