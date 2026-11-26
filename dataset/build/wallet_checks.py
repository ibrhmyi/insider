"""Phase 1: settle open wallet checks with Polymarket Data API v2 activity (PROTOCOL A6.7).

Run after build_seed.py and build_markets.py (and pull_activity.py for every labelled address).
Writes:
  logs/handle_checks.csv     evidence for handle lookups, the romanticpaul market check and the Maduro/CFTC check
  data/wallet_labels.csv     adds case_market_traded, first_case_fill_utc, case_buy_usdc, case_redeem_usdc,
                             case_check_note for every wallet (computed for polarity=suspected; blank otherwise)
  data/contradictions.csv    appends rows where fills contradict a recorded claim (never edits the claim)
"""
import csv, datetime, gzip, json, os
from collections import defaultdict

D = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(D, "logs", "gamma_raw")
UTC = datetime.UTC


def iso(t):
    return datetime.datetime.fromtimestamp(t, UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if t else ""


def act(a):
    p = os.path.join(RAW, f"activity_{a}.json.gz")
    return json.load(gzip.open(p, "rt")) if os.path.exists(p) else None


markets = list(csv.DictReader(open(os.path.join(D, "data", "markets.csv"))))
mk = defaultdict(dict)
for r in markets:
    mk[r["case_id"]][r["condition_id"]] = r
cases = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(D, "data", "cases.csv")))}


def summarize(rows, cids, typ="TRADE", side="BUY", outcome=None, until=None):
    sel = [x for x in rows if x["condition_id"].lower() in cids and x["type"] == typ
           and (side is None or x.get("side") == side) and (outcome is None or x.get("outcome") == outcome)
           and (until is None or x["timestamp"] <= until)]
    usd = sum(x["usdc_size"] for x in sel); sh = sum(x["size"] for x in sel)
    return dict(n_fills=len(sel), first_fill_utc=iso(min((x["timestamp"] for x in sel), default=0)),
                last_fill_utc=iso(max((x["timestamp"] for x in sel), default=0)), usdc=round(usd, 2),
                shares=round(sh, 2), avg_price=round(usd / sh, 4) if sh else "")


def end_of_day(d):
    return datetime.datetime.fromisoformat(d).replace(tzinfo=UTC).timestamp() + 86399


checks, contra = [], []
F = ["check_id", "check_type", "subject", "address", "case_id", "market_condition_id", "market_question", "side", "outcome",
     "window_end_utc", "n_fills", "first_fill_utc", "last_fill_utc", "usdc", "shares", "avg_price", "result", "evidence_file", "notes"]


def add(**k):
    k["check_id"] = f"HC{len(checks) + 1:03d}"
    checks.append({f: k.get(f, "") for f in F})


# 1.1 case-insensitive handle candidates (run-2 failures)
for handle, addr, case, qmatch, outcome in [
        ("Elonfax89678", "0x1fa1be3eab546e06e4290839bf4c1d7abfbf1fa9", "us-iran-ceasefire-2026-04-07", "US x Iran ceasefire by April 7?", "Yes"),
        ("Bama124", "0xe5c8026239919339b988fdb150a7ef4ea196d3e7", "walz-vp-2024", "Will Tim Walz be the 2024 Democratic VP nominee?", "Yes")]:
    rows = act(addr)
    m = [r for r in mk[case].values() if r["question"] == qmatch][0]
    end = end_of_day(cases[case]["event_date_earliest"])
    s = summarize(rows, {m["condition_id"]}, outcome=outcome, until=end)
    ok = s["n_fills"] > 0
    add(check_type="handle_case_insensitive", subject=handle, address=addr, case_id=case, market_condition_id=m["condition_id"],
        market_question=m["question"], side="BUY", outcome=outcome, window_end_utc=iso(end), **s,
        result="accepted" if ok else "rejected", evidence_file=f"logs/gamma_raw/activity_{addr}.json.gz",
        notes="A6.7: profile name differs from the handle only by letter case; accepted because it bought the claimed outcome in the case market before the event" if ok else "no qualifying buys")

# bama124 amount vs claim CL (walz): event-level net
rows = act("0xe5c8026239919339b988fdb150a7ef4ea196d3e7"); cids = set(mk["walz-vp-2024"])
b = summarize(rows, cids)["usdc"]; s_ = summarize(rows, cids, side="SELL")["usdc"]; r_ = summarize(rows, cids, typ="REDEEM", side=None)["usdc"]
net = round(s_ + r_ - b, 2)
claim = [c for c in csv.DictReader(open(os.path.join(D, "data", "claims.csv"))) if c["case_id"] == "walz-vp-2024"][0]
if claim["amount_claimed_usd"] and abs(net - float(claim["amount_claimed_usd"])) / float(claim["amount_claimed_usd"]) > 0.01:
    contra.append(dict(claim_id=claim["claim_id"], case_id="walz-vp-2024", field="amount_claimed_usd",
                       claimed_value=claim["amount_claimed_usd"], observed_value=net,
                       evidence=f"bama124 proxy, all markets of event democratic-vp-nominee: sells {s_} + redemptions {r_} - buys {b} (Data API v2). Difference {100 * (net / float(claim['amount_claimed_usd']) - 1):.1f}%; the claim may count a different period or include unrealised value",
                       evidence_file="logs/gamma_raw/activity_0xe5c8026239919339b988fdb150a7ef4ea196d3e7.json.gz", phase="1"))

# 1.2 romanticpaul on the engagement market
addr = "0xf5cfe6f998d597085e366f915b140e82e0869fc6"; rows = act(addr); m = list(mk["taylor-swift-engagement"].values())[0]
for oc in ("Yes", "No"):
    s = summarize(rows, {m["condition_id"]}, outcome=oc)
    add(check_type="market_check", subject="romanticpaul", address=addr, case_id="taylor-swift-engagement", market_condition_id=m["condition_id"],
        market_question=m["question"], side="BUY", outcome=oc, **s, result="traded" if s["n_fills"] else "not_traded",
        evidence_file=f"logs/gamma_raw/activity_{addr}.json.gz",
        notes="Yes is the claimed side; No buys are the hedge the claim mentions" if oc == "No" else "")
red = summarize(rows, {m["condition_id"]}, typ="REDEEM", side=None)
cut = datetime.datetime(2025, 8, 25, 17, 4, tzinfo=UTC).timestamp()
last24 = sum(x["usdc_size"] for x in rows if x["condition_id"].lower() == m["condition_id"] and x["type"] == "TRADE"
             and x["side"] == "BUY" and x["outcome"] == "Yes" and x["timestamp"] >= cut)
add(check_type="market_check", subject="romanticpaul", address=addr, case_id="taylor-swift-engagement", market_condition_id=m["condition_id"],
    market_question=m["question"], side="REDEEM", outcome="all", **red, result="consistent_with_claim",
    evidence_file=f"logs/gamma_raw/activity_{addr}.json.gz",
    notes=f"redeemed {red['usdc']} vs Yes cost {summarize(rows, {m['condition_id']}, outcome='Yes')['usdc']} (claim: about $3k profit); Yes buys in the 24 h before the last Yes fill (2025-08-26 17:04 UTC): {round(last24, 2)}")

# 1.3 Maduro proxy vs the CFTC complaint (436,000+ Yes shares, about $0.074 average, account created about 2025-12-26)
addr = "0x31a56e9e690c621ed21de08cb559e9524cdb8ed9"; rows = act(addr)
m = [r for r in mk["maduro-2026-01"].values() if r["question"].startswith("Maduro out by January 31, 2026")][0]
s = summarize(rows, {m["condition_id"]}, outcome="Yes")
prof = json.load(open(os.path.join(RAW, "profile_0x31a56e9e690c621ed21de08cb559e9524cdb8ed9.json")))
match = s["shares"] >= 436000 and abs(s["avg_price"] - 0.074) < 0.002 and prof["createdAt"].startswith("2025-12-26")
add(check_type="cftc_complaint_match", subject="CFTC complaint account (maduro-2026-01)", address=addr, case_id="maduro-2026-01",
    market_condition_id=m["condition_id"], market_question=m["question"], side="BUY", outcome="Yes", **s,
    result="match" if match else "no_match", evidence_file=f"logs/gamma_raw/activity_{addr}.json.gz; logs/gamma_raw/profile_{addr}.json",
    notes=f"complaint: 436,000+ Yes shares at about $0.074, account created about 2025-12-26; observed {s['shares']} shares at {s['avg_price']}, "
          f"profile createdAt {prof['createdAt']}; profile pseudonym is 'Burdensome-Mix' (the handle in handles_to_resolve; Gamma name is the default address-based name)")

with open(os.path.join(D, "logs", "handle_checks.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=F); w.writeheader(); w.writerows(checks)

# 1.4 every suspected wallet: did it trade its case market?
W = list(csv.DictReader(open(os.path.join(D, "data", "wallet_labels.csv"))))
NEW = ["case_market_traded", "first_case_fill_utc", "case_buy_usdc", "case_redeem_usdc", "case_check_note"]
base = [k for k in W[0] if k not in NEW]
for r in W:
    for k in NEW:
        r[k] = ""
    if r["polarity"] != "suspected":
        continue
    rows = act(r["address"]); cids = set(mk.get(r["case_id"], {}))
    if rows is None:
        r["case_check_note"] = "no activity file"; continue
    if not cids:
        r["case_check_note"] = "case has no market in markets.csv"; continue
    tr = [x for x in rows if x["type"] == "TRADE" and x["condition_id"].lower() in cids]
    r["case_market_traded"] = str(bool(tr)).lower()
    r["first_case_fill_utc"] = iso(min((x["timestamp"] for x in tr), default=0))
    r["case_buy_usdc"] = round(sum(x["usdc_size"] for x in tr if x.get("side") == "BUY"), 2)
    r["case_redeem_usdc"] = round(sum(x["usdc_size"] for x in rows if x["type"] == "REDEEM" and x["condition_id"].lower() in cids), 2)
    if not tr:
        r["case_check_note"] = "FLAG: no fill in any case market" + ("; Data API v2 returned no activity at all" if not rows else "")
with open(os.path.join(D, "data", "wallet_labels.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=base + NEW); w.writeheader(); w.writerows(W)

# contradictions (append, numbered)
p = os.path.join(D, "data", "contradictions.csv")
old = list(csv.DictReader(open(p)))
keep = [c for c in old if c["phase"] != "1"]
now = datetime.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
allc = [dict(c, found_utc=now) for c in contra] + keep  # phase-1 rows first: stable ids (CX001 = Walz)
FC = ["contradiction_id", "claim_id", "case_id", "field", "claimed_value", "observed_value", "evidence", "evidence_file", "phase", "found_utc"]
for i, c in enumerate(allc, 1):
    c["contradiction_id"] = f"CX{i:03d}"
with open(p, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FC); w.writeheader(); w.writerows(allc)
sus = [r for r in W if r["polarity"] == "suspected"]
print(len(checks), "checks;", sum(r["case_market_traded"] == "true" for r in sus), "of", len(sus), "suspected traded their case market;",
      sum(r["case_market_traded"] == "false" for r in sus), "flagged;", len(contra), "contradictions")
