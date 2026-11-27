"""PROTOCOL A34, A34.1: economic-side exposure (A34.1: a SELL larger than the econ holding = held SELL + inferred BUY of the complement for the excess;
the econ_excess_* columns describe that BUY). Adds econ_side, econ_asset_id, econ_outcome_label, econ_price_usdc, econ_size_usdc, econ_inferred
to out/v1/fills/fills_{case,placebo,twin,label_other}.parquet (raw columns unchanged). A SELL of token X by a wallet holding no X
(<= 1e-6 shares, from its own earlier legs in that market; inferred acquisitions count) is an economic BUY of the complementary token
at 1 - p, size = shares. Computed in one sequential pass per (wallet, market) in time order. Writes logs/econ_summary.json.
Usage: python3 build/v1/econ.py <tmp_dir>"""
import json, os, sys
import duckdb, pandas as pd

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
F = os.path.join(D, "out", "v1", "fills")
TMP = sys.argv[1]
EPS, NB = 1e-6, 16
c = duckdb.connect(); c.sql(f"SET memory_limit='5GB'; SET enable_progress_bar=false; SET temp_directory='{TMP}'; SET preserve_insertion_order=false")

# complementary tokens: case markets from markets.token_ids / outcomes, all markets from the two tokens seen in legs
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
pairs = []
for r in mk.itertuples():
    t = [x.strip() for x in r.token_ids.split(";") if x.strip()]
    o = [x.strip() for x in r.outcomes.split(";") if x.strip()]
    if len(t) == 2:
        for i in (0, 1):
            pairs.append((r.condition_id.lower(), t[i], t[1 - i], o[1 - i] if len(o) == 2 else None))
c.register("pm_df", pd.DataFrame(pairs, columns=["condition_id", "asset_id", "comp_asset_id", "comp_label"]).drop_duplicates(["condition_id", "asset_id"]))

summary = {}
SETS_RUN = sys.argv[2].split(",") if len(sys.argv) > 2 else ["case", "placebo", "twin", "label_other"]
if os.path.exists(os.path.join(D, "logs", "econ_summary.json")):
    summary = json.load(open(os.path.join(D, "logs", "econ_summary.json")))
for s in SETS_RUN:
    src = os.path.join(F, f"fills_{s}.parquet")
    cols = [r[0] for r in c.sql(f"DESCRIBE SELECT * FROM '{src}'").fetchall() if not r[0].startswith("econ_")]
    c.sql(f"""CREATE OR REPLACE TABLE toks AS SELECT lower(condition_id) condition_id, asset_id, any_value(outcome_label) lab
              FROM '{src}' GROUP BY 1, 2""")
    c.sql("""CREATE OR REPLACE TABLE comp AS
        WITH seen AS (SELECT a.condition_id, a.asset_id, b.asset_id comp_asset_id, b.lab comp_label FROM toks a JOIN toks b
                      ON a.condition_id = b.condition_id AND a.asset_id <> b.asset_id
                      WHERE a.condition_id IN (SELECT condition_id FROM toks GROUP BY 1 HAVING count(*) = 2))
        SELECT * FROM seen UNION ALL
        SELECT p.* FROM pm_df p WHERE NOT EXISTS (SELECT 1 FROM seen x WHERE x.condition_id = p.condition_id AND x.asset_id = p.asset_id)""")
    st = dict(legs=0, sell_legs=0, inferred=0, inferred_maker=0, inferred_taker=0, partial=0, iterations=[], wallets_changed=0, markets_no_complement=0)  # iterations = legs passed sequentially per bucket
    st["markets_no_complement"] = c.sql("SELECT count(DISTINCT condition_id) FROM toks WHERE (condition_id, asset_id) NOT IN (SELECT condition_id, asset_id FROM comp)").fetchall()[0][0]
    parts = []; wch = set()
    for b in range(NB):
        c.sql(f"""CREATE OR REPLACE TABLE L AS SELECT row_number() OVER () rid, l.*, k.comp_asset_id, k.comp_label
                  FROM (SELECT * FROM '{src}' WHERE hash(lower(condition_id)) % {NB} = {b}) l
                  LEFT JOIN comp k ON k.condition_id = lower(l.condition_id) AND k.asset_id = l.asset_id""")
        # candidate (wallet, market) groups: a SELL with no raw holding (the sequential balance is never below the raw one, so only these can change)
        c.sql(f"""CREATE OR REPLACE TABLE cand AS SELECT DISTINCT wallet, condition_id FROM (
                    SELECT wallet, condition_id, wallet_side, comp_asset_id,
                           sum(CASE WHEN wallet_side = 'BUY' THEN shares ELSE -shares END) OVER (PARTITION BY wallet, condition_id, asset_id ORDER BY ts, leg_id
                               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) rb FROM L WHERE wallet <> '')
                  WHERE wallet_side = 'SELL' AND comp_asset_id IS NOT NULL AND coalesce(rb, 0) < shares - {EPS}""")  # A34.1: partial sells too
        g = c.sql("""SELECT rid, wallet, condition_id, asset_id, comp_asset_id, wallet_side = 'SELL' sell, shares FROM L
                     WHERE (wallet, condition_id) IN (SELECT wallet, condition_id FROM cand) ORDER BY wallet, condition_id, ts, leg_id""").df()
        rid, wa, cd, aa, cc, se, sh = (g[x].tolist() for x in ["rid", "wallet", "condition_id", "asset_id", "comp_asset_id", "sell", "shares"])
        vv, bb, xx, key, bal = [], [], [], None, {}
        for i in range(len(rid)):  # one sequential pass per (wallet, market), in time order (A34)
            k = (wa[i], cd[i])
            if k != key:
                key, bal = k, {}
            x = bal.get(aa[i], 0.0)
            has_c = cc[i] is not None and cc[i] == cc[i]
            if not se[i]:
                bal[aa[i]] = x + sh[i]; vv.append(False); bb.append(x); xx.append(0.0)
            elif has_c and x <= EPS:  # A34: no holding -> the whole SELL is an economic BUY of the complement
                bal[cc[i]] = bal.get(cc[i], 0.0) + sh[i]; vv.append(True); bb.append(x); xx.append(0.0)
            elif has_c and x < sh[i] - EPS:  # A34.1: held part stays a SELL, the excess is an economic BUY of the complement
                bal[aa[i]] = 0.0; bal[cc[i]] = bal.get(cc[i], 0.0) + (sh[i] - x); vv.append(False); bb.append(x); xx.append(sh[i] - x)
            else:
                bal[aa[i]] = x - sh[i]; vv.append(False); bb.append(x); xx.append(0.0)
        c.register("seq_df", pd.DataFrame(dict(rid=rid, v=vv, bal=bb, xs=xx)))
        c.sql("CREATE OR REPLACE TABLE inf2 AS SELECT L.rid, coalesce(q.v, false) v, q.bal, coalesce(q.xs, 0) xs FROM L LEFT JOIN seq_df q USING (rid)")
        c.sql("CREATE OR REPLACE TABLE inf AS SELECT rid, v, xs FROM inf2")
        it = len(rid)
        st["iterations"].append(it)
        q = c.sql(f"""SELECT count(*), sum((wallet_side = 'SELL')::INT), sum(i.v::INT), sum((i.v AND wallet_role = 'maker')::INT), sum((i.v AND wallet_role = 'taker')::INT),
                             sum((i.xs > 0)::INT)
                      FROM L JOIN inf2 i USING (rid)""").fetchall()[0]
        for k, x in zip(["legs", "sell_legs", "inferred", "inferred_maker", "inferred_taker", "partial"], q):
            st[k] += int(x or 0)
        wch |= {r[0] for r in c.sql("SELECT DISTINCT wallet FROM L JOIN inf USING (rid) WHERE inf.v").fetchall()}
        out_b = os.path.join(TMP, f"econ_{s}_{b:02d}.parquet")
        sel = ", ".join(f"L.{x}" for x in cols)
        c.sql(f"""COPY (SELECT {sel},
                    CASE WHEN i.v THEN 'BUY' ELSE L.wallet_side END econ_side,
                    CASE WHEN i.v THEN L.comp_asset_id ELSE L.asset_id END econ_asset_id,
                    CASE WHEN i.v THEN L.comp_label ELSE L.outcome_label END econ_outcome_label,
                    CASE WHEN i.v THEN 1 - L.price ELSE L.price END econ_price_usdc,
                    CASE WHEN i.v THEN L.shares * (1 - L.price) WHEN i.xs > 0 THEN (L.shares - i.xs) * L.price ELSE L.usdc END econ_size_usdc,
                    i.v econ_inferred, i.xs > 0 econ_partial,
                    CASE WHEN i.xs > 0 THEN i.xs END econ_excess_shares, CASE WHEN i.xs > 0 THEN L.comp_asset_id END econ_excess_asset_id,
                    CASE WHEN i.xs > 0 THEN L.comp_label END econ_excess_outcome_label, CASE WHEN i.xs > 0 THEN 1 - L.price END econ_excess_price_usdc,
                    CASE WHEN i.xs > 0 THEN i.xs * (1 - L.price) END econ_excess_size_usdc
                  FROM L JOIN inf i USING (rid)) TO '{out_b}' (FORMAT parquet, COMPRESSION zstd)""")
        parts.append(out_b)
        print(s, b, it, flush=True)
    st["wallets_changed"] = len(wch); st["wallets"] = c.sql(f"SELECT count(DISTINCT wallet) FROM '{src}'").fetchall()[0][0]
    order = "condition_id, ts, leg_id" if s != "label_other" else "wallet, ts, leg_id"
    tmpf = src + ".econ_tmp"
    c.sql(f"COPY (SELECT * FROM read_parquet({parts}) ORDER BY {order}) TO '{tmpf}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)")
    os.replace(tmpf, src)
    for p in parts:
        os.remove(p)
    summary[s] = st
    print(s, st, flush=True)
json.dump(summary, open(os.path.join(D, "logs", "econ_summary.json"), "w"), indent=1)
