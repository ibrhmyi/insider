"""v1.0 table 6, fills (PROTOCOL A6.4, A14, A12.6). One row per wallet leg of a fill (an HF fill has a taker leg and a maker leg;
a Data API row is one leg). Writes out/v1/fills/fills_<market_set>.parquet with market_set in {case, placebo, label_other}:
  case        every leg in every case market (data/markets.csv)
  placebo     every leg in every placebo market (data/placebo_markets.csv)
  label_other legs of labelled wallets (data/wallet_labels.csv, any polarity) in all other markets
Sources: hf_polymarket_v1 (pass outputs A and B of build/hf_pass_v7.py) up to HF_END; data_api_v2 after HF_END and for markets/wallets
the HF pass did not cover. Withheld markets (A12.6) get market_slug NULL.
Usage: python3 build/v1/fills.py <hf_pass_work_dir> <api_trades_dir> <tmp_dir>
"""
import csv, glob, gzip, json, os, sys
import duckdb, pyarrow as pa, pyarrow.parquet as pq

D = os.path.join(os.path.dirname(__file__), "..", "..")
WORK, APIT, TMPD = sys.argv[1:4]
OUT = os.path.join(D, "out", "v1", "fills"); os.makedirs(OUT, exist_ok=True)
HF_END = 1777374040
c = duckdb.connect(); c.sql(f"SET memory_limit='9GB'; SET temp_directory='{TMPD}'; SET enable_progress_bar=false; SET preserve_insertion_order=false")
mk = list(csv.DictReader(open(os.path.join(D, "data", "markets.csv"))))
case = sorted({r["condition_id"].lower() for r in mk}); withheld = sorted({r["condition_id"].lower() for r in mk if r.get("title_withheld") == "true"})
plc = sorted({r["placebo_condition_id"] for r in csv.DictReader(open(os.path.join(D, "data", "placebo_markets.csv"))) if r.get("placebo_condition_id")})
labels = sorted({r["address"].lower() for r in csv.DictReader(open(os.path.join(D, "data", "wallet_labels.csv")))})
hfp = sorted({x.strip().lower() for x in open(os.path.join(D, "logs", "hf_pass_label_addresses.txt")) if x.strip()})
for name, vals in [("cm", case), ("wh", withheld), ("pm", plc), ("lab", labels), ("hfp", hfp)]:
    c.execute(f"CREATE TABLE {name}(v VARCHAR PRIMARY KEY)"); c.executemany(f"INSERT INTO {name} VALUES (?)", [(v,) for v in vals])

COLS = ["source", "fill_id", "leg_id", "tx_hash", "ts", "condition_id", "asset_id", "outcome_label", "outcome_seq", "price", "usdc", "shares",
        "fee_usdc", "wallet", "wallet_role", "wallet_side", "aggressor_side", "maker", "taker", "market_slug"]
LEG = """SELECT 'hf_polymarket_v1' source, hf_file || ':' || hf_row fill_id, hf_file || ':' || hf_row || ':t' leg_id, NULL::VARCHAR tx_hash,
         block_timestamp ts, lower(condition_id) condition_id, asset_id, outcome_label, outcome_seq, price, usdc_amount usdc,
         usdc_amount / nullif(price, 0) shares, fee_usdc, lower(taker) wallet, 'taker' wallet_role, taker_direction wallet_side,
         taker_direction aggressor_side, lower(maker) maker, lower(taker) taker, market_slug FROM {src}
  UNION ALL
  SELECT 'hf_polymarket_v1', hf_file || ':' || hf_row, hf_file || ':' || hf_row || ':m', NULL, block_timestamp, lower(condition_id), asset_id,
         outcome_label, outcome_seq, price, usdc_amount, usdc_amount / nullif(price, 0), fee_usdc, lower(maker), 'maker',
         CASE taker_direction WHEN 'BUY' THEN 'SELL' ELSE 'BUY' END, taker_direction, lower(maker), lower(taker), market_slug FROM {src}"""
PT = pa.schema([("source", pa.string()), ("fill_id", pa.string()), ("leg_id", pa.string()), ("tx_hash", pa.string()), ("ts", pa.int64()),
                ("condition_id", pa.string()), ("asset_id", pa.string()), ("outcome_label", pa.string()), ("outcome_seq", pa.int64()),
                ("price", pa.float64()), ("usdc", pa.float64()), ("shares", pa.float64()), ("fee_usdc", pa.float64()), ("wallet", pa.string()),
                ("wallet_role", pa.string()), ("wallet_side", pa.string()), ("aggressor_side", pa.string()), ("maker", pa.string()),
                ("taker", pa.string()), ("market_slug", pa.string())])

# --- Data API legs: market trades (case markets) and labelled-wallet activity, one parquet per input file
API = os.path.join(TMPD, "api_legs_v1"); os.makedirs(API, exist_ok=True)
c.sql(f"CREATE TABLE hfc AS SELECT DISTINCT lower(condition_id) v FROM read_parquet('{WORK}/B/*.parquet')")
hf_cids = {r[0] for r in c.sql("SELECT v FROM hfc").fetchall()}


def write(rows, p):
    t = pa.table({f.name: pa.array([r[i] for r in rows], type=f.type) for i, f in enumerate(PT)}, schema=PT)
    pq.write_table(t, p)


for p in sorted(glob.glob(os.path.join(APIT, "trades_*.json.gz"))):
    cid = os.path.basename(p)[7:-8].lower(); outp = os.path.join(API, "m_" + cid + ".parquet")
    if os.path.exists(outp) and os.path.getmtime(outp) > os.path.getmtime(p):
        continue
    rows = []
    for i, x in enumerate(json.load(gzip.open(p, "rt"))):
        if x["timestamp"] > HF_END or cid not in hf_cids:
            h = x.get("transaction_hash") or ""
            rows.append(("data_api_v2", f"{h}:{i}", f"{h}:{i}", h or None, int(x["timestamp"]), cid, str(x.get("token_id") or "") or None,
                         x.get("outcome"), x.get("outcome_index"), float(x["price"]), float(x["size"]) * float(x["price"]), float(x["size"]),
                         None, (x.get("proxy_wallet") or "").lower() or None, "unknown", x.get("side"), None, None, None, x.get("slug")))
    write(rows, outp)
hfp_set = set(hfp)
for a in labels:
    p = os.path.join(D, "logs", "gamma_raw", f"activity_{a}.json.gz"); outp = os.path.join(API, "w_" + a + ".parquet")
    if not os.path.exists(p) or (os.path.exists(outp) and os.path.getmtime(outp) > os.path.getmtime(p)):
        continue
    rows = []
    for i, x in enumerate(json.load(gzip.open(p, "rt"))):
        if x["type"] == "TRADE" and (x["timestamp"] > HF_END or a not in hfp_set):
            h = x.get("transaction_hash") or ""
            rows.append(("data_api_v2", f"{h}:w{i}:{a}", f"{h}:w{i}:{a}", h or None, int(x["timestamp"]), x["condition_id"].lower(),
                         str(x.get("token_id") or x.get("asset") or "") or None, x.get("outcome"), x.get("outcome_index"), float(x["price"]),
                         float(x["usdc_size"]), float(x["size"]), None, a, "unknown", x.get("side"), None, None, None, x.get("slug")))
    write(rows, outp)

sel = ", ".join(COLS[:-1]) + ", CASE WHEN condition_id IN (SELECT v FROM wh) THEN NULL ELSE market_slug END market_slug"
# case markets: HF B legs + API market legs (wallet activity rows in case markets are already in the market trades, or HF)
c.sql(f"""COPY (SELECT 'case' market_set, {sel} FROM (
            SELECT * FROM ({LEG.format(src="read_parquet('" + WORK + "/B/*.parquet', union_by_name=true)")}) WHERE condition_id IN (SELECT v FROM cm)
            UNION ALL SELECT * FROM read_parquet('{API}/m_*.parquet') WHERE condition_id IN (SELECT v FROM cm))
          ORDER BY condition_id, ts, leg_id) TO '{OUT}/fills_case.parquet' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)""")
print("case", c.sql(f"SELECT count(*) FROM '{OUT}/fills_case.parquet'").fetchall(), flush=True)
c.sql(f"""COPY (SELECT 'placebo' market_set, {sel} FROM ({LEG.format(src="read_parquet('" + WORK + "/B/*.parquet', union_by_name=true)")})
          WHERE condition_id IN (SELECT v FROM pm) AND condition_id NOT IN (SELECT v FROM cm)
          ORDER BY condition_id, ts, leg_id) TO '{OUT}/fills_placebo.parquet' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)""")
print("placebo", c.sql(f"SELECT count(*) FROM '{OUT}/fills_placebo.parquet'").fetchall(), flush=True)
# labelled wallets elsewhere: HF A legs (wallets in the pass list) + API wallet activity
c.sql(f"""COPY (SELECT 'label_other' market_set, {sel} FROM (
            SELECT * FROM ({LEG.format(src="read_parquet('" + WORK + "/A/*.parquet', union_by_name=true)")})
              WHERE wallet IN (SELECT v FROM lab) AND wallet IN (SELECT v FROM hfp)
            UNION ALL SELECT * FROM read_parquet('{API}/w_*.parquet'))
          WHERE condition_id NOT IN (SELECT v FROM cm) AND condition_id NOT IN (SELECT v FROM pm)
          ORDER BY wallet, ts, leg_id) TO '{OUT}/fills_label_other.parquet' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)""")
print("label_other", c.sql(f"SELECT count(*) FROM '{OUT}/fills_label_other.parquet'").fetchall(), flush=True)
# counts per case (logs/fills_counts_by_case.csv)
c.execute("CREATE TABLE m(case_id VARCHAR, condition_id VARCHAR)"); c.executemany("INSERT INTO m VALUES (?,?)", [(r["case_id"], r["condition_id"].lower()) for r in mk])
res = c.sql(f"""SELECT m.case_id, l.source, count(*) legs, count(DISTINCT l.fill_id) fills, count(DISTINCT l.wallet) wallets, round(sum(l.usdc)/2) usdc
               FROM m JOIN '{OUT}/fills_case.parquet' l USING (condition_id) GROUP BY ALL ORDER BY 1, 2""").fetchall()
with open(os.path.join(D, "logs", "fills_counts_by_case.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["case_id", "source", "legs", "distinct_fills", "distinct_wallets", "usdc_half_of_legs"]); w.writerows(res)
print(len(res), "count rows")
