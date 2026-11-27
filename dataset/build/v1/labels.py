"""wallet_labels.csv updates for v1.0.
  confirm     PROTOCOL A12.5: trade_confirmed = the address has >= 1 fill (any side, any source) in a market attached to its case;
              also refreshes case_market_traded, first_case_fill_utc and case_buy_usdc from out/v1/fills/fills_case.parquet.
              Also sets label_family (A19): manipulation for polarity manipulation, else the family of the case's claims.
  drop_rule_rows  PROTOCOL A17: removes L4_coordinated rule rows (the A13 output lives in data/coordinated_candidates.csv).
Usage: python3 build/v1/labels.py confirm|drop_rule_rows
"""
import os, sys
import duckdb, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
P = os.path.join(D, "data", "wallet_labels.csv")
W = pd.read_csv(P, dtype=str, keep_default_na=False)
if sys.argv[1] == "confirm":
    mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
    c = duckdb.connect()
    c.register("mk", mk.assign(condition_id=mk.condition_id.str.lower())[["case_id", "condition_id"]])
    c.register("w", W[["address", "case_id"]].drop_duplicates())
    s = c.sql(f"""SELECT w.address, w.case_id, count(l.leg_id) n_legs, min(l.ts) first_ts,
                         sum(l.usdc) FILTER (WHERE l.wallet_side = 'BUY') buy_usdc
                  FROM w JOIN mk USING (case_id) JOIN '{D}/out/v1/fills/fills_case.parquet' l ON l.condition_id = mk.condition_id AND l.wallet = w.address
                  GROUP BY 1, 2""").df()
    W = W.drop(columns=[x for x in ["trade_confirmed"] if x in W.columns]).merge(s, on=["address", "case_id"], how="left")
    W["trade_confirmed"] = (W.n_legs.fillna(0) > 0).map({True: "true", False: "false"})
    W["case_market_traded"] = W.trade_confirmed
    W["first_case_fill_utc"] = pd.to_datetime(W.first_ts, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")
    W["case_buy_usdc"] = W.buy_usdc.round(2).astype(str).replace("nan", "")
    W = W.drop(columns=["n_legs", "first_ts", "buy_usdc"])
    cl = pd.read_csv(os.path.join(D, "data", "claims.csv"), dtype=str, keep_default_na=False)
    fam = cl.groupby("case_id").family.agg(lambda s: ";".join(sorted(set(s))))
    W["label_family"] = [("manipulation" if p_ == "manipulation" else fam.get(c_, "")) for p_, c_ in zip(W.polarity, W.case_id)]
    print(W.groupby(["polarity", "trade_confirmed"]).size())
elif sys.argv[1] == "drop_rule_rows":
    n0 = len(W); W = W[W.label_tier != "L4_coordinated"]; print("rule rows removed", n0 - len(W))
else:
    raise SystemExit("the 'candidates' mode was retired by PROTOCOL A17")
    C = pd.read_csv(os.path.join(D, "data", "coordinated_candidates.csv"), dtype=str, keep_default_na=False)
    C = C.sort_values(["t_news_version", "trigger_utc"], ascending=[False, True])  # 'precise' first
    rows = []
    for (a, case), g in C.groupby(["candidate_wallet", "case_id"], sort=True):
        f = g.iloc[0]
        rows.append(dict(address=a, handle="", case_id=case, role="trader", label_tier="L4_coordinated", polarity="candidate",
                         source="PROTOCOL A13 rule (build/v1/coordinated.py)", source_url="", verification="rule_based",
                         notes=f"trigger_wallet={f.trigger_wallet}; trigger_fill_leg_id={f.trigger_fill_leg_id}; versions={';'.join(sorted(set(g.t_news_version)))}; n_triggers={len(g)}",
                         case_market_traded="true", first_case_fill_utc=f.cand_first_buy_utc, case_buy_usdc="", case_redeem_usdc="", case_check_note="",
                         trade_confirmed="true"))
    W = pd.concat([W, pd.DataFrame(rows)], ignore_index=True)
    print("candidates added", len(rows))
W.to_csv(P, index=False)
