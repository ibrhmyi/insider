"""Phase 4: Polygon USDC / USDC.e money graph around suspected wallets (PROTOCOL A6.8, A8).

Steps (each cached under the cache dir, so the script resumes after a restart):
  1. window per suspected address (profile createdAt or first activity - 1 day, to last activity + 30 days) -> blocks
  2. all USDC/USDC.e Transfer logs to/from each suspected address in its window (10,000-block chunks)
  3. every counterparty that is not a documented Polymarket contract: scan its transfers over the union window of the
     suspected wallets it touches, counting distinct counterparties; stop at 501 -> hub
  4. one hop: counterparties of non-hub funders / cash-out addresses that have Data API v2 activity -> candidates
Outputs: out/transfers_raw.parquet (every log seen), data/edges_expanded.csv, data/wallet_labels_expanded.csv,
         logs/money_graph_counterparties.csv
Usage: python3 build/money_graph.py <cache_dir> [threads]
"""
import concurrent.futures as cf, csv, datetime, gzip, json, os, re, sys, threading, time, urllib.parse, urllib.request

D = os.path.join(os.path.dirname(__file__), "..")
CACHE = sys.argv[1]; os.makedirs(CACHE, exist_ok=True)
THREADS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
# An archive-capable Polygon RPC is required (eth_getLogs over historical blocks, >= 10,000-block ranges).
# Run 3: publicnode's free tier refuses archive requests; drpc and 1rpc free plans allow 100 / 50 blocks. Set POLYGON_RPC.
RPC = os.environ.get("POLYGON_RPC", "https://polygon-bor-rpc.publicnode.com")
TOK = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC.e", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
CHUNK = 10_000
HUB = 500
UTC = datetime.UTC
lock = threading.Lock()

# documented Polymarket contracts (logs/docs/polymarket_contracts.md, fetched 2026-11-26)
DOC = open(os.path.join(D, "logs", "docs", "polymarket_contracts.md")).read()
PM_CONTRACTS = {a.lower() for a in re.findall(r"0x[0-9a-fA-F]{40}", DOC)}


def rpc(method, params, tries=14):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(tries):
        try:
            r = urllib.request.Request(RPC, data=body, headers={"content-type": "application/json", "User-Agent": "curl/8.5.0"})
            d = json.load(urllib.request.urlopen(r, timeout=120))
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception as ex:
            if i == tries - 1:
                raise
            time.sleep(min(120, 2 ** i) + (20 if "403" in str(ex) or "429" in str(ex) else 0))  # public RPC rate limit


HEAD = int(rpc("eth_blockNumber", []), 16)
_bt = {}


def block_ts(b):
    if b not in _bt:
        _bt[b] = int(rpc("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
    return _bt[b]


def block_at(ts):
    """first block with timestamp >= ts (binary search)."""
    lo, hi = 1, HEAD
    if ts >= block_ts(HEAD):
        return HEAD
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def pad(a):
    return "0x" + "0" * 24 + a[2:].lower()


def logs_chunk(addr, frm, to, direction):
    """direction 'out': addr is sender; 'in': addr is receiver. Cached per chunk."""
    p = os.path.join(CACHE, "chunks", addr, f"{direction}_{frm}_{to}.json")
    if os.path.exists(p):
        return json.load(open(p))
    topics = [TRANSFER, pad(addr), None] if direction == "out" else [TRANSFER, None, pad(addr)]
    res = rpc("eth_getLogs", [{"fromBlock": hex(frm), "toBlock": hex(to), "address": list(TOK), "topics": topics}])
    out = [dict(token=TOK[x["address"].lower()], src="0x" + x["topics"][1][-40:], dst="0x" + x["topics"][2][-40:],
                amount=int(x["data"], 16) / 1e6, block=int(x["blockNumber"], 16), tx=x["transactionHash"],
                log_index=int(x["logIndex"], 16)) for x in res]
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w"))
    return out


def chunks(frm, to):
    b = frm
    while b <= to:
        yield b, min(b + CHUNK - 1, to)
        b += CHUNK


def address_logs(addr, frm, to, pool, stop_at=None):
    """All transfers in/out of addr in [frm, to]. With stop_at: return early once that many distinct counterparties."""
    out, seen = [], set()
    jobs = [(a, b, d) for a, b in chunks(frm, to) for d in ("in", "out")]
    if stop_at is None:
        for r in pool.map(lambda j: logs_chunk(addr, *j), jobs):
            out += r
        return out, False
    # sequential batches so we can stop early
    for i in range(0, len(jobs), THREADS * 2):
        for r in pool.map(lambda j: logs_chunk(addr, *j), jobs[i:i + THREADS * 2]):
            out += r
            for x in r:
                seen.add(x["dst"] if x["src"] == addr else x["src"])
        if len(seen) > stop_at:
            return out, True
    return out, False


def activity_exists(a):
    p = os.path.join(CACHE, "has_activity", a + ".json")
    if os.path.exists(p):
        return json.load(open(p))
    for i in range(6):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(
                "https://data-api.polymarket.com/v2/activity?" + urllib.parse.urlencode({"user": a, "limit": 1}),
                headers={"User-Agent": "curl/8.5.0"}), timeout=60))
            v = bool(d.get("data")); break
        except Exception:
            time.sleep(2 ** i)
    else:
        v = None
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(v, open(p, "w"))
    return v


def main():
    W = list(csv.DictReader(open(os.path.join(D, "data", "wallet_labels.csv"))))
    labelled = {r["address"] for r in W}
    sus = sorted({r["address"] for r in W if r["polarity"] == "suspected"})
    seed_kind = {}
    for e in csv.DictReader(open(os.path.join(D, "data", "wallet_edges.csv"))):
        for a in (e["src"], e["dst"]):
            seed_kind.setdefault(a, set()).add(e["kind"])
    pool = cf.ThreadPoolExecutor(THREADS)

    # 1. windows
    wp = os.path.join(CACHE, "windows.json")
    win = json.load(open(wp)) if os.path.exists(wp) else {}
    for a in sus:
        if a in win:
            continue
        act = json.load(gzip.open(os.path.join(D, "logs", "gamma_raw", f"activity_{a}.json.gz"), "rt"))
        if not act:
            win[a] = None; continue
        first, last = min(x["timestamp"] for x in act), max(x["timestamp"] for x in act)
        try:
            c = json.load(open(os.path.join(D, "logs", "gamma_raw", f"profile_{a}.json"))).get("createdAt")
        except FileNotFoundError:
            c = None
        start = datetime.datetime.fromisoformat(c.replace("Z", "+00:00")).timestamp() if c else first - 86400
        end = last + 30 * 86400
        win[a] = dict(start_ts=int(start), end_ts=int(end), start_block=block_at(start), end_block=min(HEAD, block_at(end)),
                      start_source="profile_createdAt" if c else "first_activity_minus_1d")
        json.dump(win, open(wp, "w"))
    print("windows", sum(v is not None for v in win.values()), flush=True)

    # 2. suspected wallets' transfers
    raw, cp_windows = [], {}
    for i, a in enumerate(sus):
        w = win.get(a)
        if not w:
            continue
        lg, _ = address_logs(a, w["start_block"], w["end_block"], pool)
        for x in lg:
            x.update(focal=a, focal_role="suspected")
            cp = x["dst"] if x["src"] == a else x["src"]
            if cp in PM_CONTRACTS:
                continue
            cw = cp_windows.setdefault(cp, [w["start_block"], w["end_block"], set()])
            cw[0] = min(cw[0], w["start_block"]); cw[1] = max(cw[1], w["end_block"]); cw[2].add(a)
        raw += lg
        print(f"suspected {i + 1}/{len(sus)} {a} logs={len(lg)}", flush=True)
    print("counterparties", len(cp_windows), flush=True)

    # 3. hub test for every counterparty; keep full logs of non-hubs
    cps = []
    for j, (cp, (frm, to, touched)) in enumerate(sorted(cp_windows.items())):
        p = os.path.join(CACHE, "cp", cp + ".json")
        if os.path.exists(p):
            info = json.load(open(p))
        else:
            lg, hub = address_logs(cp, frm, to, pool, stop_at=HUB)
            others = sorted({x["dst"] if x["src"] == cp else x["src"] for x in lg})
            info = dict(hub=hub, n_counterparties_seen=len(others), counterparties=[] if hub else others)
            os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(info, open(p, "w"))
        cps.append((cp, frm, to, touched, info))
        if j % 25 == 0:
            print(f"cp {j}/{len(cp_windows)} hub={info['hub']} n={info['n_counterparties_seen']}", flush=True)

    # 4. one hop
    cand = {}
    for cp, frm, to, touched, info in cps:
        if info["hub"]:
            continue
        lg, _ = address_logs(cp, frm, to, pool)  # cached
        for x in lg:
            x.update(focal=cp, focal_role="funder_or_cashout")
        raw += lg
        for o in info["counterparties"]:
            if o in labelled or o in PM_CONTRACTS or o == cp:
                continue
            if activity_exists(o):
                link = [x for x in lg if o in (x["src"], x["dst"])][0]
                cand.setdefault(o, []).append((cp, sorted(touched), link))

    # write outputs
    import pyarrow as pa, pyarrow.parquet as pq
    seen, rows = set(), []
    for x in raw:
        k = (x["tx"], x["log_index"])
        if k not in seen:
            seen.add(k); rows.append({k2: x[k2] for k2 in ("token", "src", "dst", "amount", "block", "tx", "log_index")})
    pq.write_table(pa.Table.from_pylist(rows), os.path.join(D, "out", "transfers_raw.parquet"), compression="zstd")

    hubs = {cp for cp, *_, info in cps if info["hub"]}
    def tag(a):
        if a in PM_CONTRACTS: return "polymarket_contract"
        if a in hubs: return "hub"
        if a in seed_kind: return "seed_edge:" + ";".join(sorted(seed_kind[a]))
        if a in labelled: return "labelled_wallet"
        return "unknown"
    E = []
    for x in rows:
        if x["src"] in PM_CONTRACTS or x["dst"] in PM_CONTRACTS:
            continue
        if x["src"] in hubs or x["dst"] in hubs:
            continue
        E.append(dict(src=x["src"], dst=x["dst"], token=x["token"], amount_usd=round(x["amount"], 6), block=x["block"], tx=x["tx"],
                      log_index=x["log_index"], src_tag=tag(x["src"]), dst_tag=tag(x["dst"])))
    # hub aggregates
    agg = {}
    for x in rows:
        for a, b in ((x["src"], x["dst"]), (x["dst"], x["src"])):
            if a in sus and (b in hubs or b in PM_CONTRACTS):
                k = (a, b, "out" if x["src"] == a else "in")
                v = agg.setdefault(k, [0, 0.0]); v[0] += 1; v[1] += x["amount"]
    with open(os.path.join(D, "data", "edges_expanded.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["src", "dst", "token", "amount_usd", "block", "tx", "log_index", "src_tag", "dst_tag", "n_transfers", "kind"])
        w.writeheader()
        for e in E:
            w.writerow(dict(e, n_transfers=1, kind="transfer"))
        for (a, b, d_), (n, s) in sorted(agg.items()):
            w.writerow(dict(src=a if d_ == "out" else b, dst=b if d_ == "out" else a, token="USDC+USDC.e", amount_usd=round(s, 2), block="", tx="",
                            log_index="", src_tag=tag(a if d_ == "out" else b), dst_tag=tag(b if d_ == "out" else a), n_transfers=n,
                            kind="aggregate_with_hub_or_polymarket_contract"))
    with open(os.path.join(D, "data", "wallet_labels_expanded.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["address", "label_tier", "polarity", "linked_via", "linked_suspected", "link_tx", "link_token", "link_amount_usd", "link_block", "source"])
        for o, links in sorted(cand.items()):
            for cp, touched, link in links:
                w.writerow([o, "L4_graph_expanded", "candidate", cp, ";".join(touched), link["tx"], link["token"], round(link["amount"], 6),
                            link["block"], "Polygon USDC/USDC.e logs via publicnode RPC; one hop through a non-hub funder/cash-out (A8)"])
    with open(os.path.join(D, "logs", "money_graph_counterparties.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["counterparty", "hub", "n_counterparties_seen", "touched_suspected", "window_start_block", "window_end_block", "tag"])
        for cp, frm, to, touched, info in cps:
            w.writerow([cp, info["hub"], info["n_counterparties_seen"], ";".join(sorted(touched)), frm, to, tag(cp)])
    json.dump(dict(head_block=HEAD, run_utc=datetime.datetime.now(UTC).isoformat(), n_suspected=len(sus),
                   n_with_window=sum(v is not None for v in win.values()), n_counterparties=len(cps), n_hubs=len(hubs),
                   n_candidates=len(cand), n_raw_logs=len(rows)), open(os.path.join(D, "logs", "money_graph_summary.json"), "w"), indent=1)
    print("done: counterparties", len(cps), "hubs", len(hubs), "candidates", len(cand), "raw logs", len(rows), flush=True)


if __name__ == "__main__":
    main()
