"""Task 3: full trade extraction + field audit.

Source: Polymarket Data API v2  GET /v2/trades?condition=<id>&limit=1000, cursor-paginated.
- taker_only defaults to true: each fill served once, on its taker side (the initiator).
- the condition shape ignores start/end (fixed 3-year window), so time filtering is local.
- feed order is newest-first (keyset on (block_timestamp, sequence_id)).

Outputs per market:
  data/raw/trades/<key>/page_XXXX.json      raw pages (untouched API responses)
  data/raw/trades/<key>/batch_log.csv       per-page row count + min/max timestamp + ordering checks
  data/clean/trades_<key>.parquet|csv       deduped trades with flags
  data/audit/audit_<key>.md / .json         field audit

usage: python 02_extract_trades.py iran ctrl_btc110k_jun17 maduro ...
"""
import json
import sys
import time

import numpy as np
import pandas as pd

from common import AUDIT, CLEAN, DATA, DATA_API, HTTP_EVENTS, RAW, dump, get_json, iso

KEY_COLS = ["transaction_hash", "proxy_wallet", "token_id", "timestamp", "size", "price"]


def paginate(cond, outdir, refetch=False):
    outdir.mkdir(parents=True, exist_ok=True)
    batches, rows, cursor, page = [], [], None, 0
    while True:
        page += 1
        f = outdir / f"page_{page:04d}.json"
        if f.exists() and not refetch:
            js = json.load(open(f))
        else:
            params = dict(condition=cond, limit=1000) if cursor is None else dict(condition=cond, cursor=cursor)
            js = get_json(f"{DATA_API}/trades", params=params)
            dump(js, f)
            time.sleep(0.25)  # stay well under per-client allowance
        d = js.get("data") or []
        pg = js.get("pagination") or {}
        ts = [x["timestamp"] for x in d]
        b = dict(page=page, n=len(d), ts_min=min(ts) if ts else None, ts_max=max(ts) if ts else None,
                 has_more=pg.get("has_more"), cursor_present=bool(pg.get("next_cursor")),
                 sorted_desc=all(ts[i] >= ts[i + 1] for i in range(len(ts) - 1)) if ts else None)
        if batches and ts and batches[-1]["ts_min"] is not None:
            b["overlap_with_prev_s"] = max(0, b["ts_max"] - batches[-1]["ts_min"])  # >0 => this page reaches above previous page's floor
            b["gap_to_prev_s"] = batches[-1]["ts_min"] - b["ts_max"]
        batches.append(b)
        rows += d
        if page % 20 == 0:
            print(f"  page {page}: {len(rows)} rows, oldest so far {iso(b['ts_min']) if b['ts_min'] else '-'}", flush=True)
        cursor = pg.get("next_cursor")
        if not pg.get("has_more") or not cursor:
            break
    return rows, pd.DataFrame(batches)


def all_sides_notional(cond):
    """Completeness cross-check: maker+taker rows (taker_only=false) notional should ~= Gamma volume."""
    n, notional, cur = 0, 0.0, None
    while True:
        p = dict(condition=cond, limit=1000, taker_only="false") if cur is None else dict(condition=cond, cursor=cur, taker_only="false")
        js = get_json(f"{DATA_API}/trades", params=p)
        d = js.get("data") or []
        n += len(d)
        notional += sum(x["size"] * x["price"] for x in d)
        cur = (js.get("pagination") or {}).get("next_cursor")
        if not (js.get("pagination") or {}).get("has_more") or not cur:
            return n, notional
        time.sleep(0.2)


def audit(key, mk, raw_rows, batches, df_raw, df):
    n_raw = len(df_raw)
    miss = {}
    for c in df_raw.columns:
        s = df_raw[c]
        miss[c] = int(s.isna().sum() + (s.astype(str).str.strip() == "").sum())
    res_ts = int(mk["resolution_epoch"])
    a = dict(
        market_key=key, condition_id=mk["condition_id"], source="Polymarket Data API v2 /v2/trades (taker_only=true)",
        pages=len(batches), rows_raw=n_raw, duplicates_removed=int(n_raw - len(df)), rows_clean=len(df),
        missing_per_field=miss,
        outcome_index_999=int((df_raw["outcome_index"] == 999).sum()),
        nonpositive_size=int((df_raw["size"] <= 0).sum()),
        price_out_of_0_1=int(((df_raw["price"] < 0) | (df_raw["price"] > 1)).sum()),
        condition_mismatch=int((df_raw["condition_id"].str.lower() != mk["condition_id"].lower()).sum()),
        token_not_in_market=int((~df_raw["token_id"].isin([str(mk["token_id_yes"]), str(mk["token_id_no"])])).sum()),
        first_trade_utc=iso(df["timestamp"].min()), last_trade_utc=iso(df["timestamp"].max()),
        span_first_to_last_hours=round((df["timestamp"].max() - df["timestamp"].min()) / 3600, 2),
        market_open_utc=mk["open_utc"], resolution_utc=mk["resolution_utc"],
        first_trade_minus_open_hours=round((df["timestamp"].min() - pd.Timestamp(mk["open_utc"]).timestamp()) / 3600, 2),
        trades_after_resolution_flagged=int(df["after_resolution"].sum()),
        largest_gap_between_trades_hours=round(df["timestamp"].sort_values().diff().max() / 3600, 2),
        largest_gap_starts_utc=iso(df["timestamp"].sort_values().values[int(np.nanargmax(df["timestamp"].sort_values().diff().values)) - 1]),
        batch_pages_not_sorted_desc=int((batches["sorted_desc"] == False).sum()),
        batch_max_overlap_s=float(batches.get("overlap_with_prev_s", pd.Series([0])).fillna(0).max()),
        batch_negative_gap_pages=int((batches.get("gap_to_prev_s", pd.Series([0])).fillna(0) < 0).sum()),
        last_page_has_more=bool(batches.iloc[-1]["has_more"]),
        taker_notional_usd_pre_resolution=round(float((df.loc[~df.after_resolution, "size"] * df.loc[~df.after_resolution, "price"]).sum()), 2),
        taker_notional_usd_all=round(float((df["size"] * df["price"]).sum()), 2),
        shares_all=round(float(df["size"].sum()), 2),
        gamma_volume_usd=float(mk["volume_usd"]),
        sides=df["side"].value_counts().to_dict(), outcomes=df["outcome"].value_counts().to_dict(),
        distinct_wallets=int(df["proxy_wallet"].nunique()),
    )
    a["notional_over_gamma_volume"] = round(a["taker_notional_usd_all"] / a["gamma_volume_usd"], 3)
    n_all, notional_all = all_sides_notional(mk["condition_id"])
    a["all_sides_rows"] = n_all
    a["all_sides_notional_usd"] = round(notional_all, 2)
    a["all_sides_notional_over_gamma_volume"] = round(notional_all / a["gamma_volume_usd"], 3)
    dump(a, AUDIT / f"audit_{key}.json")
    md = [f"# Field audit: {mk['market_name']} (`{key}`)", "",
          f"- Source: {a['source']}; condition `{mk['condition_id']}`",
          f"- Pages fetched: {a['pages']} (last page has_more={a['last_page_has_more']})",
          f"- Rows raw: **{n_raw}**; duplicates removed (composite key {', '.join(KEY_COLS)}): **{a['duplicates_removed']}**; rows clean: **{a['rows_clean']}**",
          f"- Distinct wallets: {a['distinct_wallets']}; sides {a['sides']}; outcomes {a['outcomes']}",
          f"- Timestamp coverage: first {a['first_trade_utc']} -> last {a['last_trade_utc']} (span {a['span_first_to_last_hours']} h)",
          f"- Market open {a['market_open_utc']} (first trade {a['first_trade_minus_open_hours']} h after open); resolution {a['resolution_utc']}",
          f"- Trades after resolution (flagged, kept): **{a['trades_after_resolution_flagged']}**",
          f"- Largest gap between consecutive trades: {a['largest_gap_between_trades_hours']} h (starting {a['largest_gap_starts_utc']})",
          f"- Batch checks: pages not sorted newest-first = {a['batch_pages_not_sorted_desc']}; pages overlapping previous page's floor = max {a['batch_max_overlap_s']} s; pages with negative gap = {a['batch_negative_gap_pages']}",
          f"- Validity: outcome_index=999: {a['outcome_index_999']}; size<=0: {a['nonpositive_size']}; price outside [0,1]: {a['price_out_of_0_1']}; wrong condition: {a['condition_mismatch']}; token not in market: {a['token_not_in_market']}",
          f"- Completeness check: taker notional (size x price) ${a['taker_notional_usd_all']:,.0f} vs Gamma volume ${a['gamma_volume_usd']:,.0f} -> ratio {a['notional_over_gamma_volume']} (taker-only; varies with price level because makers on the complementary token pay 1-p)",
          f"- Completeness cross-check: maker+taker rows (taker_only=false) = {a['all_sides_rows']}, notional ${a['all_sides_notional_usd']:,.0f} -> ratio to Gamma volume **{a['all_sides_notional_over_gamma_volume']}** (~1.0 means no missing history)",
          "", "## Missing values per field (null or empty string)", "", "| field | missing |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in miss.items()]
    (AUDIT / f"audit_{key}.md").write_text("\n".join(md) + "\n")
    return a


def main(keys):
    markets = pd.read_csv(DATA / "markets.csv", dtype={"token_id_yes": str, "token_id_no": str, "gamma_market_id": str})
    for key in keys:
        mk = markets.set_index("market_key").loc[key].to_dict()
        print(f"== {key}: {mk['market_name']}", flush=True)
        outdir = RAW / "trades" / key
        rows, batches = paginate(mk["condition_id"], outdir)
        batches.to_csv(outdir / "batch_log.csv", index=False)
        df_raw = pd.DataFrame(rows)
        df_raw["token_id"] = df_raw["token_id"].astype(str)
        df = df_raw.drop_duplicates(subset=KEY_COLS, keep="first").copy()
        df["after_resolution"] = df["timestamp"] > int(mk["resolution_epoch"])
        df["source"] = "data-api-v2"
        keep = ["timestamp", "transaction_hash", "proxy_wallet", "side", "outcome", "outcome_index", "token_id",
                "size", "price", "condition_id", "after_resolution", "source"]
        df = df.sort_values(["timestamp", "transaction_hash"]).reset_index(drop=True)
        df[keep].to_csv(CLEAN / f"trades_{key}.csv", index=False)
        a = audit(key, mk, rows, batches, df_raw, df)
        print(f"   rows raw {a['rows_raw']}, dupes {a['duplicates_removed']}, clean {a['rows_clean']}, "
              f"{a['first_trade_utc']} -> {a['last_trade_utc']}, post-res {a['trades_after_resolution_flagged']}, "
              f"notional/gamma {a['notional_over_gamma_volume']}", flush=True)
    dump(HTTP_EVENTS, RAW / "trades" / f"http_events_{'_'.join(keys)}.json")
    print("HTTP non-200 events:", len(HTTP_EVENTS))


if __name__ == "__main__":
    main(sys.argv[1:])
