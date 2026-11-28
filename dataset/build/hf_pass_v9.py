"""Run 9 (PROTOCOL A22): one pass over Polymarket-v1 (HF) cleaned layers writing layer B only, for the twin markets of
data/twin_markets.csv. Output <work>/B9/<file>.parquet with the same columns as build/hf_pass.py layer B.
Usage: python3 build/hf_pass_v9.py <hf_dir> <work_dir> [procs]"""
import csv, glob, os, sys, time
import multiprocessing as mp
import duckdb

D = os.path.join(os.path.dirname(__file__), "..")
HF, WORK = sys.argv[1], sys.argv[2]
PROCS = int(sys.argv[3]) if len(sys.argv) > 3 else 4
TW = sorted({r["twin_condition_id"] for r in csv.DictReader(open(os.path.join(D, "data", "twin_markets.csv"))) if r["twin_condition_id"]})
os.makedirs(os.path.join(WORK, "B9"), exist_ok=True)


def one(path):
    name = os.path.basename(os.path.dirname(path)) + "__" + os.path.basename(path)
    out = os.path.join(WORK, "B9", name)
    if os.path.exists(out):
        return name, 0
    c = duckdb.connect(); c.sql("SET threads=1; SET memory_limit='2GB'; SET enable_progress_bar=false")
    c.execute("CREATE TEMP TABLE tw(c VARCHAR)"); c.executemany("INSERT INTO tw VALUES (?)", [(m,) for m in TW])
    c.sql(f"""COPY (SELECT '{name}' AS hf_file, file_row_number AS hf_row, asset_id, block_timestamp, price, lower(maker) maker, lower(taker) taker,
              taker_direction, usdc_amount, fee_usdc, lower(condition_id) condition_id, outcome_seq, outcome_label, winning_outcome_label,
              resolution_status, category, category_refined, market_slug, neg_risk
              FROM read_parquet('{path}', file_row_number=true) WHERE lower(condition_id) IN (SELECT c FROM tw)) TO '{out}.tmp' (FORMAT parquet)""")
    os.replace(out + ".tmp", out)
    return name, 1


if __name__ == "__main__":
    files = sorted(glob.glob(f"{HF}/daily_aligned/*.parquet")) + sorted(glob.glob(f"{HF}/daily_aligned_multi/*.parquet"))
    files.sort(key=os.path.getsize, reverse=True)
    t0 = time.time()
    with mp.Pool(PROCS) as pool:
        for i, (name, n) in enumerate(pool.imap_unordered(one, files), 1):
            if i % 100 == 0 or i == len(files):
                print(f"{i}/{len(files)} files, {time.time() - t0:.0f}s", flush=True)
