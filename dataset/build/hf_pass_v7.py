"""Run 7 (A14): case markets plus placebo markets in layer B. One pass over Polymarket-v1 (HF) cleaned layers, per day file, in parallel (PROTOCOL A6.4, A6.9).

For each file writes, under <work>/:
  A/<file>.parquet  fills where maker or taker is a labelled address (data/wallet_labels.csv, all polarities)
  B/<file>.parquet  fills in any case market (data/markets.csv)
  C/<file>.parquet  ACDC longshot candidates: one wallet's BUYs on one token in one UTC clock hour,
                    >= $2,500 at VWAP <= 0.35, market resolved in the HF metadata
  P/<file>.parquet  per (wallet, condition_id, asset_id) buy/sell USDC and shares (for Inca PnL and market counts)
Side convention (A6.4): taker = aggressor, side = taker_direction; maker side = opposite on the same token.
Shares = usdc_amount / price (the cleaned layers carry no token amount).
Usage: python3 build/hf_pass.py <hf_dir> <work_dir> [procs]
"""
import csv, glob, os, sys, time
import multiprocessing as mp
import duckdb

D = os.path.join(os.path.dirname(__file__), "..")
HF, WORK = sys.argv[1], sys.argv[2]
PROCS = int(sys.argv[3]) if len(sys.argv) > 3 else 4
LABELS = sorted({r["address"] for r in csv.DictReader(open(os.path.join(D, "data", "wallet_labels.csv")))})
MARKETS = sorted({r["condition_id"].lower() for r in csv.DictReader(open(os.path.join(D, "data", "markets.csv")))} | {r["placebo_condition_id"] for r in csv.DictReader(open(os.path.join(D, "data", "placebo_markets.csv"))) if r["placebo_condition_id"]})
for s in "ABCP":
    os.makedirs(os.path.join(WORK, s), exist_ok=True)


def one(path):
    name = os.path.basename(os.path.dirname(path)) + "__" + os.path.basename(path)
    done = os.path.join(WORK, "P", name)
    if os.path.exists(done):
        return name, 0
    c = duckdb.connect(); c.sql("SET threads=1; SET memory_limit='3GB'; SET enable_progress_bar=false")
    c.sql(f"""CREATE TEMP TABLE f AS SELECT file_row_number AS hf_row, asset_id, block_timestamp, price, lower(maker) maker, lower(taker) taker,
              taker_direction, usdc_amount, fee_usdc, lower(condition_id) condition_id, outcome_seq, outcome_label, winning_outcome_label,
              resolution_status, category, category_refined, market_slug, neg_risk
              FROM read_parquet('{path}', file_row_number=true)""")
    c.execute("CREATE TEMP TABLE lab(a VARCHAR)"); c.executemany("INSERT INTO lab VALUES (?)", [(a,) for a in LABELS])
    c.execute("CREATE TEMP TABLE mkt(c VARCHAR)"); c.executemany("INSERT INTO mkt VALUES (?)", [(m,) for m in MARKETS])
    src = f"'{name}' AS hf_file"
    c.sql(f"COPY (SELECT {src}, * FROM f WHERE maker IN (SELECT a FROM lab) OR taker IN (SELECT a FROM lab)) TO '{WORK}/A/{name}' (FORMAT parquet)")
    c.sql(f"COPY (SELECT {src}, * FROM f WHERE condition_id IN (SELECT c FROM mkt)) TO '{WORK}/B/{name}' (FORMAT parquet)")
    # wallet-side view: both legs of every fill
    c.sql("""CREATE TEMP VIEW legs AS
             SELECT taker AS wallet, asset_id, condition_id, block_timestamp, price, usdc_amount, taker_direction AS side, 'taker' AS role,
                    outcome_label, winning_outcome_label, resolution_status, category_refined, market_slug FROM f
             UNION ALL
             SELECT maker, asset_id, condition_id, block_timestamp, price, usdc_amount,
                    CASE taker_direction WHEN 'BUY' THEN 'SELL' ELSE 'BUY' END, 'maker',
                    outcome_label, winning_outcome_label, resolution_status, category_refined, market_slug FROM f""")
    c.sql(f"""COPY (SELECT wallet, asset_id, condition_id, block_timestamp // 3600 AS hour, sum(usdc_amount) usdc,
                     sum(usdc_amount / nullif(price, 0)) shares, count(*) n_fills,
                     any_value(outcome_label) outcome_label, any_value(winning_outcome_label) winning_outcome_label,
                     any_value(category_refined) category_refined, any_value(market_slug) market_slug
              FROM legs WHERE side = 'BUY' AND resolution_status = 'resolved' AND winning_outcome_label IS NOT NULL
              GROUP BY ALL HAVING sum(usdc_amount) >= 2500 AND sum(usdc_amount) / sum(usdc_amount / nullif(price, 0)) <= 0.35)
              TO '{WORK}/C/{name}' (FORMAT parquet)""")
    c.sql(f"""COPY (SELECT wallet, condition_id, asset_id,
                     sum(CASE WHEN side='BUY' THEN usdc_amount ELSE 0 END) buy_usdc,
                     sum(CASE WHEN side='BUY' THEN usdc_amount / nullif(price, 0) ELSE 0 END) buy_shares,
                     sum(CASE WHEN side='SELL' THEN usdc_amount ELSE 0 END) sell_usdc,
                     sum(CASE WHEN side='SELL' THEN usdc_amount / nullif(price, 0) ELSE 0 END) sell_shares,
                     count(*) n_fills, min(block_timestamp) first_ts, max(block_timestamp) last_ts
              FROM legs GROUP BY ALL) TO '{done}.tmp' (FORMAT parquet, COMPRESSION zstd)""")
    os.replace(done + ".tmp", done)
    n = c.sql("SELECT count(*) FROM f").fetchall()[0][0]
    return name, n


if __name__ == "__main__":
    files = sorted(glob.glob(f"{HF}/daily_aligned/*.parquet")) + sorted(glob.glob(f"{HF}/daily_aligned_multi/*.parquet"))
    files.sort(key=os.path.getsize, reverse=True)  # big first for load balance
    t0, tot = time.time(), 0
    with mp.Pool(PROCS) as pool:
        for i, (name, n) in enumerate(pool.imap_unordered(one, files), 1):
            tot += n
            if i % 50 == 0 or i == len(files):
                print(f"{i}/{len(files)} files, {tot:,} rows this run, {time.time() - t0:.0f}s", flush=True)
