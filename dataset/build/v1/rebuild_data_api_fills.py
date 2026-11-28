"""Rebuild the fills parts with source = data_api_v2 (withheld from release_safe/) from the public Polymarket Data API v2.

Uses only released files: data/markets.parquet and data/wallets.parquet, plus the Polymarket-v1 fill parts present in data/.
  1. case markets: every row of /v2/trades?condition=<id>&taker_only=false after 2026-04-28 11:00:40 UTC (end of
     Polymarket-v1), or all rows for markets with no Polymarket-v1 fills  -> fills_partNNN_case_data_api_v2.parquet
  2. labelled wallets: /v2/activity TRADE rows after that time (all time for wallets with no Polymarket-v1 legs), outside
     case and placebo markets                                            -> fills_partNNN_label_other_data_api_v2.parquet
Same schema as the other parts (CODEBOOK, table fills). The API keeps adding rows, so the rebuilt files will not match
the SHA-256 of the full release; row ids follow build/v1/fills.py. Usage:
    python3 scripts/rebuild_data_api_fills.py [--data ../data]
Requires: pandas, pyarrow, duckdb. Network: data-api.polymarket.com.
"""
import argparse, glob, json, os, time, urllib.parse, urllib.request
import duckdb, pyarrow as pa, pyarrow.parquet as pq

HF_END = 1777374040
API = "https://data-api.polymarket.com/v2/"
SCHEMA = pa.schema([("market_set", pa.string()), ("leg_id", pa.string()), ("source", pa.string()), ("fill_id", pa.string()), ("tx_hash", pa.string()),
                    ("ts", pa.int64()), ("ts_utc", pa.timestamp("s", tz="UTC")), ("condition_id", pa.string()), ("asset_id", pa.string()),
                    ("outcome_label", pa.string()), ("outcome_seq", pa.int64()), ("price", pa.float64()), ("usdc", pa.float64()), ("shares", pa.float64()),
                    ("fee_usdc", pa.float64()), ("wallet", pa.string()), ("wallet_role", pa.string()), ("wallet_side", pa.string()),
                    ("aggressor_side", pa.string()), ("maker", pa.string()), ("taker", pa.string()), ("market_slug", pa.string())])


def get(path, q):
    for i in range(8):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(API + path + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "pmitc-rebuild"}), timeout=120))
        except Exception:
            time.sleep(min(60, 2 ** i))
    raise RuntimeError(path)


def paged(path, q):
    rows, cur = [], None
    while True:
        d = get(path, dict(q, cursor=cur) if cur else q)
        rows += d["data"]; pg = d.get("pagination", {})
        if not pg.get("has_more"):
            return rows
        cur = pg["next_cursor"]; time.sleep(0.1)


def leg(ms, lid, h, ts, cid, tok, out, oidx, price, usdc, size, wallet, side, slug):
    return dict(market_set=ms, leg_id=lid, source="data_api_v2", fill_id=lid, tx_hash=h or None, ts=int(ts), ts_utc=int(ts), condition_id=cid,
                asset_id=tok or None, outcome_label=out, outcome_seq=oidx, price=price, usdc=usdc, shares=size, fee_usdc=None, wallet=wallet,
                wallet_role="unknown", wallet_side=side, aggressor_side=None, maker=None, taker=None, market_slug=slug)


def write(rows, path):
    cols = {f.name: [r[f.name] for r in rows] for f in SCHEMA}
    pq.write_table(pa.table(cols, schema=SCHEMA), path, compression="zstd")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")); a = ap.parse_args()
    mk = duckdb.sql(f"SELECT DISTINCT condition_id, in_hf, title_withheld FROM '{a.data}/markets.parquet'").df()
    hf_parts = glob.glob(os.path.join(a.data, "fills_part*_hf_polymarket_v1.parquet"))
    hf_cids = {r[0] for r in duckdb.sql(f"SELECT DISTINCT condition_id FROM read_parquet({hf_parts!r}) WHERE market_set = 'case'").fetchall()}
    withheld = set(mk[mk.title_withheld == True].condition_id)  # noqa: E712
    n = max([int(os.path.basename(p)[10:13]) for p in glob.glob(os.path.join(a.data, "fills_part*.parquet"))] + [0])
    rows = []
    for cid in sorted(mk.condition_id):
        for i, x in enumerate(paged("trades", {"condition": cid, "limit": 1000, "taker_only": "false", "filter_amount": 0})):
            if x["timestamp"] > HF_END or cid not in hf_cids:
                h = x.get("transaction_hash") or ""
                rows.append(leg("case", f"{h}:{i}", h, x["timestamp"], cid, str(x.get("token_id") or ""), x.get("outcome"), x.get("outcome_index"),
                                float(x["price"]), float(x["size"]) * float(x["price"]), float(x["size"]), (x.get("proxy_wallet") or "").lower(),
                                x.get("side"), None if cid in withheld else x.get("slug")))
    n += 1; write(rows, os.path.join(a.data, f"fills_part{n:03d}_case_data_api_v2.parquet")); print("case legs", len(rows))
    wallets = sorted({r[0] for r in duckdb.sql(f"SELECT DISTINCT wallet FROM '{a.data}/wallets.parquet'").fetchall()})
    hf_w = {r[0] for r in duckdb.sql(f"SELECT DISTINCT wallet FROM read_parquet({hf_parts!r})").fetchall()}
    skip = hf_cids | {r[0] for r in duckdb.sql(f"SELECT DISTINCT placebo_condition_id FROM '{a.data}/placebo_markets.parquet' WHERE placebo_condition_id IS NOT NULL").fetchall()} | set(mk.condition_id)
    rows = []
    for w in wallets:
        for i, x in enumerate(paged("activity", {"user": w, "limit": 500, "start": 1})):
            if x["type"] == "TRADE" and (x["timestamp"] > HF_END or w not in hf_w) and x["condition_id"].lower() not in skip:
                h = x.get("transaction_hash") or ""
                rows.append(leg("label_other", f"{h}:w{i}:{w}", h, x["timestamp"], x["condition_id"].lower(), str(x.get("token_id") or x.get("asset") or ""),
                                x.get("outcome"), x.get("outcome_index"), float(x["price"]), float(x["usdc_size"]), float(x["size"]), w, x.get("side"), x.get("slug")))
    n += 1; write(rows, os.path.join(a.data, f"fills_part{n:03d}_label_other_data_api_v2.parquet")); print("label_other legs", len(rows))
