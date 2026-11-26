"""Phase F amount checks: every claim with an amount and a trade-confirmed wallet is compared with that wallet's fills in its
case markets. A claim is linked to a wallet only when its subject is a full address or a handle resolved in data/handles_to_resolve.csv
or logs/handle_checks_run7.csv (and the wallet is documented for the claim's case).
Observed values, from the fills table (leg sides, A6.4) and from Data API activity (economic sides: a mint-matched maker SELL of
one token is a BUY of the other there): stake (buys), payout (sells + redemptions) and net (payout - buys). The gap is the
smallest relative difference to the six; if > 10%, a row is appended to data/contradictions.csv (claims are never edited).
Writes logs/amount_checks.csv. Usage: python3 build/v1/amount_checks.py
"""
import gzip, json, os, re
import duckdb, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
rd = lambda p: pd.read_csv(os.path.join(D, p), dtype=str, keep_default_na=False)
cl, W, mk = rd("data/claims.csv"), rd("data/wallet_labels.csv"), rd("data/markets.csv")
h = rd("data/handles_to_resolve.csv"); h7 = rd("logs/handle_checks_run7.csv")
hmap = {r.handle.lower(): r.resolved_address for r in h.itertuples() if r.resolved_address}
hmap.update({r.subject.lower(): r.address for r in h7.itertuples() if r.result.startswith("resolved") and r.address})
doc = W[(W.polarity == "suspected") & (W.trade_confirmed == "true")]
one = doc.groupby("case_id").address.agg(list)
rows = []
for r in cl[cl.amount_claimed_usd != ""].itertuples():
    addrs = re.findall(r"0x[0-9a-fA-F]{40}", r.subject)
    if not addrs:
        toks = [t.strip().lower() for t in re.split(r"[;,/()]| and ", r.subject) if t.strip()]
        addrs = [hmap[t] for t in toks if t in hmap]
    addrs = [a.lower() for a in addrs if a.lower() in set(doc[doc.case_id == r.case_id].address)]
    if addrs:
        rows.append(dict(claim_id=r.claim_id, case_id=r.case_id, wallets=";".join(addrs), claimed=float(r.amount_claimed_usd)))
A = pd.DataFrame(rows)
c = duckdb.connect()
mk["condition_id"] = mk.condition_id.str.lower(); c.register("mk", mk[["case_id", "condition_id"]])
out = []
for r in A.itertuples():
    ws = r.wallets.split(";")
    q = c.sql(f"""SELECT sum(usdc) FILTER (WHERE wallet_side='BUY') b, sum(usdc) FILTER (WHERE wallet_side='SELL') s
                  FROM '{D}/out/v1/fills/fills_case.parquet' l JOIN mk USING (condition_id)
                  WHERE mk.case_id = '{r.case_id}' AND l.wallet IN ({",".join("'" + w + "'" for w in ws)})""").fetchall()[0]
    buys, sells = q[0] or 0.0, q[1] or 0.0
    cids = set(mk[mk.case_id == r.case_id].condition_id); red = ab = asl = 0.0
    for w in ws:
        p = os.path.join(D, "logs", "gamma_raw", f"activity_{w}.json.gz")
        if os.path.exists(p):
            for x in json.load(gzip.open(p, "rt")):
                if x["condition_id"].lower() in cids:
                    v = float(x.get("usdc_size") or 0)
                    if x["type"] == "REDEEM": red += v
                    elif x["type"] == "TRADE" and x.get("side") == "BUY": ab += v
                    elif x["type"] == "TRADE" and x.get("side") == "SELL": asl += v
    obs = dict(stake_buy_usdc=buys, payout_sell_plus_redeem=sells + red, net_payout_minus_buys=sells + red - buys,
               activity_stake_buy_usdc=ab, activity_payout_sell_plus_redeem=asl + red, activity_net=asl + red - ab)
    gaps = {k: abs(v - r.claimed) / r.claimed for k, v in obs.items() if r.claimed}
    best = min(gaps, key=gaps.get)
    out.append(dict(claim_id=r.claim_id, case_id=r.case_id, wallets=r.wallets, claimed_usd=r.claimed, **{k: round(v, 2) for k, v in obs.items()},
                    closest_measure=best, closest_gap=round(gaps[best], 4), over_10pct=gaps[best] > 0.10))
O = pd.DataFrame(out); O.to_csv(os.path.join(D, "logs", "amount_checks.csv"), index=False)
cx = rd("data/contradictions.csv"); cx = cx[cx.phase != "run7_amount_check"]
n = max(int(x[2:]) for x in cx.contradiction_id)
new = []
for r in O[O.over_10pct].itertuples():
    n += 1
    new.append(dict(contradiction_id=f"CX{n:03d}", claim_id=r.claim_id, case_id=r.case_id, field="amount_claimed_usd", claimed_value=str(r.claimed_usd),
                    observed_value=f"fills: stake {r.stake_buy_usdc}, payout {r.payout_sell_plus_redeem}, net {r.net_payout_minus_buys}; activity: stake {r.activity_stake_buy_usdc}, payout {r.activity_payout_sell_plus_redeem}, net {r.activity_net}",
                    evidence=f"closest measure {r.closest_measure}, gap {r.closest_gap:.1%} (> 10%); case-market fills of {r.wallets}; the claim may count other markets, unrealised value or a different period",
                    evidence_file="release/data/fills (case markets); logs/amount_checks.csv", phase="run7_amount_check", found_utc="2026-11-26T00:00:00Z"))
pd.concat([cx, pd.DataFrame(new)]).to_csv(os.path.join(D, "data", "contradictions.csv"), index=False)
print(O.to_string()); print("contradictions added", len(new))
