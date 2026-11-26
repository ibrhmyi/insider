"""Phase 3: assemble fills (PROTOCOL A6.4). Writes, in 'wallet leg' form (one row per wallet per fill):
  out/fills/label_wallet_legs.parquet   every leg of every labelled address (wallet_labels.csv, all polarities), all time
  out/fills/case_market_legs.parquet    every leg of every fill in every market of data/markets.csv
Sources: hf_polymarket_v1 (HF pass outputs A/B) up to HF_END; data_api_v2 after HF_END, and for case markets with no
HF fills (activity rows for labelled wallets; /v2/trades?condition=..&taker_only=false for markets).
HF legs: taker leg side = taker_direction; maker leg side = the opposite (A6.4). fill_id = hf_file:hf_row.
Data API legs have wallet_role 'unknown' (the API does not say maker or taker); fill_id = transaction_hash:n.
Usage: python3 build/assemble_fills.py <hf_pass_work_dir> <api_trades_dir>
"""
import csv, glob, gzip, json, os, sys
import duckdb

D = os.path.join(os.path.dirname(__file__), "..")
WORK, APIT = sys.argv[1], sys.argv[2]
OUT = os.path.join(D, "out", "fills"); os.makedirs(OUT, exist_ok=True)
HF_END = 1777374040  # last block_timestamp in Polymarket-v1 (2026-04-28 11:00:40 UTC)
c = duckdb.connect(); c.sql("SET memory_limit='8GB'; SET enable_progress_bar=false")

LEG = """
  SELECT 'hf_polymarket_v1' source, hf_file || ':' || hf_row fill_id, '' tx_hash, block_timestamp ts, condition_id, asset_id,
         outcome_label, outcome_seq, price, usdc_amount usdc, usdc_amount / nullif(price, 0) shares, fee_usdc,
         taker wallet, 'taker' wallet_role, taker_direction wallet_side, taker_direction aggressor_side, maker, taker, market_slug
  FROM {src}
  UNION ALL
  SELECT 'hf_polymarket_v1', hf_file || ':' || hf_row, '', block_timestamp, condition_id, asset_id, outcome_label, outcome_seq, price,
         usdc_amount, usdc_amount / nullif(price, 0), fee_usdc, maker, 'maker',
         CASE taker_direction WHEN 'BUY' THEN 'SELL' ELSE 'BUY' END, taker_direction, maker, taker, market_slug
  FROM {src}"""

import pyarrow as pa


def insert_rows(table, rows):
    """bulk insert via Arrow (row-by-row executemany is far too slow for millions of rows)."""
    if not rows:
        return
    names = [x.strip() for x in cols.split(",")]
    t = pa.table({n: [r[i] for r in rows] for i, n in enumerate(names)})
    c.register("_tmp_rows", t)
    c.sql(f"INSERT INTO {table} ({cols}) SELECT {', '.join(f'CAST({n} AS {{}})'.format(TYPES[n]) for n in names)} FROM _tmp_rows")
    c.unregister("_tmp_rows")


cols = "source, fill_id, tx_hash, ts, condition_id, asset_id, outcome_label, outcome_seq, price, usdc, shares, fee_usdc, wallet, wallet_role, wallet_side, aggressor_side, maker, taker, market_slug"
TYPES = dict(source="VARCHAR", fill_id="VARCHAR", tx_hash="VARCHAR", ts="BIGINT", condition_id="VARCHAR", asset_id="VARCHAR",
             outcome_label="VARCHAR", outcome_seq="BIGINT", price="DOUBLE", usdc="DOUBLE", shares="DOUBLE", fee_usdc="DOUBLE",
             wallet="VARCHAR", wallet_role="VARCHAR", wallet_side="VARCHAR", aggressor_side="VARCHAR", maker="VARCHAR", taker="VARCHAR",
             market_slug="VARCHAR")
labels = sorted({r["address"] for r in csv.DictReader(open(os.path.join(D, "data", "wallet_labels.csv")))})
c.execute("CREATE TABLE lab(a VARCHAR)"); c.executemany("INSERT INTO lab VALUES (?)", [(a,) for a in labels])

# --- label wallets
c.sql(f"CREATE TEMP VIEW a AS SELECT * FROM read_parquet('{WORK}/A/*.parquet', union_by_name=true)")
c.sql(f"CREATE TABLE hf_lab AS SELECT * FROM ({LEG.format(src='a')}) WHERE wallet IN (SELECT a FROM lab)")
api = []
for a in labels:
    p = os.path.join(D, "logs", "gamma_raw", f"activity_{a}.json.gz")
    if not os.path.exists(p):
        continue
    for i, x in enumerate(json.load(gzip.open(p, "rt"))):
        if x["type"] == "TRADE" and x["timestamp"] > HF_END:
            api.append(("data_api_v2", f"{x.get('transaction_hash', '')}:{i}", x.get("transaction_hash", ""), x["timestamp"],
                        x["condition_id"].lower(), str(x.get("token_id") or x.get("asset") or ""), x.get("outcome"), x.get("outcome_index"),
                        x["price"], x["usdc_size"], x["size"], None, a, "unknown", x.get("side"), None, None, None, x.get("slug")))
cols = "source, fill_id, tx_hash, ts, condition_id, asset_id, outcome_label, outcome_seq, price, usdc, shares, fee_usdc, wallet, wallet_role, wallet_side, aggressor_side, maker, taker, market_slug"
c.sql(f"CREATE TABLE api_lab AS SELECT * FROM hf_lab WHERE false")
insert_rows("api_lab", api)
c.sql(f"COPY (SELECT * FROM hf_lab UNION ALL SELECT * FROM api_lab ORDER BY wallet, ts) TO '{OUT}/label_wallet_legs.parquet' (FORMAT parquet, COMPRESSION zstd)")

# --- case markets
mk = list(csv.DictReader(open(os.path.join(D, "data", "markets.csv"))))
c.sql(f"CREATE TEMP VIEW b AS SELECT * FROM read_parquet('{WORK}/B/*.parquet', union_by_name=true)")
c.sql(f"CREATE TABLE hf_mkt AS {LEG.format(src='b')}")
hf_cids = {r[0] for r in c.sql("SELECT DISTINCT condition_id FROM hf_mkt").fetchall()}
api = []
for p in glob.glob(os.path.join(APIT, "trades_*.json.gz")):
    cid = os.path.basename(p)[7:-8].lower()
    for i, x in enumerate(json.load(gzip.open(p, "rt"))):
        if x["timestamp"] > HF_END or cid not in hf_cids:   # no double counting with HF
            api.append(("data_api_v2", f"{x.get('transaction_hash', '')}:{i}", x.get("transaction_hash", ""), x["timestamp"], cid,
                        str(x.get("token_id") or ""), x.get("outcome"), x.get("outcome_index"), x["price"], x["size"] * x["price"], x["size"],
                        None, (x.get("proxy_wallet") or "").lower(), "unknown", x.get("side"), None, None, None, x.get("slug")))
c.sql("CREATE TABLE api_mkt AS SELECT * FROM hf_mkt WHERE false")
insert_rows("api_mkt", api)
c.sql(f"COPY (SELECT * FROM hf_mkt UNION ALL SELECT * FROM api_mkt ORDER BY condition_id, ts) TO '{OUT}/case_market_legs.parquet' (FORMAT parquet, COMPRESSION zstd)")

# --- counts per case
c.execute("CREATE TABLE m(case_id VARCHAR, condition_id VARCHAR)"); c.executemany("INSERT INTO m VALUES (?,?)", [(r["case_id"], r["condition_id"]) for r in mk])
res = c.sql(f"""SELECT m.case_id, l.source, count(*) legs, count(DISTINCT l.fill_id) fills, count(DISTINCT l.wallet) wallets, round(sum(l.usdc)/2) usdc_per_side
               FROM m JOIN '{OUT}/case_market_legs.parquet' l USING (condition_id) GROUP BY ALL ORDER BY 1, 2""").fetchall()
with open(os.path.join(D, "logs", "fills_counts_by_case.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["case_id", "source", "legs", "distinct_fills", "distinct_wallets", "usdc_half_of_legs"]); w.writerows(res)
lab = c.sql(f"SELECT source, count(*), count(DISTINCT wallet) FROM '{OUT}/label_wallet_legs.parquet' GROUP BY 1").fetchall()
print("label legs", lab); print("case-market legs by case written to logs/fills_counts_by_case.csv"); [print(r) for r in res]
