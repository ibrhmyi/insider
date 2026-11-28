"""Release table 6 (fills) in parts: release/data/fills_partNNN_<market_set>_<source>.parquet, at most PART_ROWS rows each,
streamed by DuckDB COPY (types per build/v1/schema.py; ts_utc is timestamp with time zone UTC). Usage: python3 build/v1/fills_release.py <tmp_dir>"""
import glob, os, sys
import duckdb

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V1, OUT = os.path.join(D, "out", "v1", "fills"), os.path.join(D, "release", "data")
PART_ROWS = 15_000_000
c = duckdb.connect(); c.sql(f"SET memory_limit='3GB'; SET threads=2; SET enable_progress_bar=false; SET temp_directory='{sys.argv[1]}'; SET preserve_insertion_order=true")
import hashlib, re
NAMES = {x.strip() for x in open(os.path.join(D, "tests", "name_hashes.txt")) if x.strip() and not x.startswith("#")}
def has_name(v):  # A39
    w = re.findall(r"[a-z]+", str(v).lower())
    return any(hashlib.sha256(" ".join(w[i:i + n]).encode()).hexdigest() in NAMES for n in (1, 2, 3) for i in range(len(w) - n + 1))
_slugs = [r[0] for r in c.sql(f"SELECT DISTINCT market_slug FROM read_parquet('{V1}/fills_*.parquet') WHERE market_slug IS NOT NULL").fetchall()]
_ns = [x for x in _slugs if has_name(x)]
_labs = [r[0] for r in c.sql(f"SELECT DISTINCT outcome_label FROM read_parquet('{V1}/fills_*.parquet') WHERE outcome_label IS NOT NULL").fetchall()]
_nl = [x for x in _labs if has_name(x)]
lit = lambda xs: "(" + ", ".join("'" + x.replace("'", "''") + "'" for x in xs) + ")" if xs else "(NULL)"
SL, OL = lit(_ns), lit(_nl)  # constant lists: a subquery here would make the LIMIT/OFFSET pages non-deterministic
print("A39 slugs / outcome labels with a withheld name:", len(_ns), len(_nl), flush=True)
for f in glob.glob(os.path.join(OUT, "fills_part*")):
    os.remove(f)
n_part = total = 0
for ms in ["case", "placebo", "twin", "label_other"]:
    for src in ["hf_polymarket_v1", "data_api_v2"]:
        q = f"(SELECT * FROM '{V1}/fills_{ms}.parquet' WHERE source = '{src}')"
        if not os.path.exists(f"{V1}/fills_{ms}.parquet"):
            continue
        n = c.sql(f"SELECT count(*) FROM {q}").fetchall()[0][0]
        for off in range(0, n, PART_ROWS):
            n_part += 1
            out = os.path.join(OUT, f"fills_part{n_part:03d}_{ms}_{src}.parquet")
            c.sql(f"""COPY (SELECT market_set, leg_id, source, fill_id, tx_hash, ts::BIGINT ts_unix, to_timestamp(ts) ts_utc, condition_id, asset_id, CASE WHEN outcome_label IN {OL} THEN NULL ELSE outcome_label END outcome_label,
                         outcome_seq::BIGINT outcome_seq, price::DOUBLE price_usdc, usdc::DOUBLE usdc, shares::DOUBLE shares,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE fee_usdc::DOUBLE END fee_usdc, wallet,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE wallet_role END wallet_role,
                         (source = 'hf_polymarket_v1') role_fields_available, wallet_side,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE aggressor_side END aggressor_side,
                         CASE WHEN source = 'data_api_v2' THEN NULL ELSE maker END maker, CASE WHEN source = 'data_api_v2' THEN NULL ELSE taker END taker,
                         CASE WHEN market_slug IN {SL} THEN NULL ELSE market_slug END market_slug, econ_side, econ_asset_id, CASE WHEN econ_outcome_label IN {OL} THEN NULL ELSE econ_outcome_label END econ_outcome_label, econ_price_usdc::DOUBLE econ_price_usdc,
                         econ_size_usdc::DOUBLE econ_size_usdc, econ_inferred, econ_partial, econ_excess_shares::DOUBLE econ_excess_shares,
                         econ_excess_asset_id, CASE WHEN econ_excess_outcome_label IN {OL} THEN NULL ELSE econ_excess_outcome_label END econ_excess_outcome_label, econ_excess_price_usdc::DOUBLE econ_excess_price_usdc,
                         econ_excess_size_usdc::DOUBLE econ_excess_size_usdc FROM {q} LIMIT {PART_ROWS} OFFSET {off})
                      TO '{out}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)""")
            total += min(PART_ROWS, n - off)
print("fills", total, "rows in", n_part, "parts")
