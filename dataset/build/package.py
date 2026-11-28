"""Phase 8: codebook, manifest and blind-check sample.

Writes CODEBOOK.md (every column of every table; fails if a column has no description), out/MANIFEST.json (row counts
and SHA-256 of every table, in git or not) and logs/blind_check_sample.csv (seed 192, 20% of claims, claim_id and url only;
left blank for a second extractor, PROTOCOL A4).
"""
import csv, glob, hashlib, json, os, random
import duckdb

D = os.path.join(os.path.dirname(__file__), "..")
os.chdir(D)

LEG = {"source": "hf_polymarket_v1 (Polymarket-v1 on Hugging Face, cleaned layers) or data_api_v2 (Polymarket Data API v2)",
       "fill_id": "HF: <day file>:<row number in that file>; API: <transaction hash>:<row index in the pull>",
       "tx_hash": "transaction hash (API rows only; the HF cleaned layers carry none)", "ts": "block timestamp, Unix seconds UTC",
       "condition_id": "market condition id (lower-case hex)", "asset_id": "outcome token id", "outcome_label": "label of the traded outcome token",
       "outcome_seq": "outcome position in the market (HF 1/2; API outcome_index 0/1)", "price": "price paid per share, USDC",
       "usdc": "USDC notional of the fill (API: size x price)", "shares": "outcome-token shares (HF: usdc / price)",
       "fee_usdc": "fee charged on the fill (HF only)", "wallet": "the wallet this leg belongs to (proxy address, lower-case)",
       "wallet_role": "maker, taker, or unknown (API rows)", "wallet_side": "BUY or SELL of this outcome token by this wallet (A6.4)",
       "aggressor_side": "taker_direction of the fill (HF only); the taker is the aggressor", "maker": "maker address (HF only)",
       "taker": "taker address (HF only)", "market_slug": "market slug"}
DESC = {
 "data/claims.csv": {
  "claim_id": "row id, CLnnnn; stable across runs (new rows appended)", "case_id": "case this claim belongs to (cases.csv)",
  "platform": "polymarket, kalshi, or both", "family": "informed_trading, manipulation, oracle/resolution, wash, data leak, control, rule screen (PROTOCOL 2)",
  "subject_type": "address, handle, account, cluster, market or aggregate", "subject": "what the claim points at, copied from the source; prefixes kept as prefixes",
  "claim_text": "our paraphrase, under 30 words", "evidence_grade": "E1 to E6 (PROTOCOL 5)", "amount_claimed_usd": "amount the source states (USD), blank if none",
  "n_accounts_claimed": "number of accounts the source names", "event_date": "date of the underlying event (partial dates allowed, A6.3)",
  "claim_date": "date of the claim (partial dates allowed)", "source_class": "S1 official, S2 research, S3 press, S4 X analysts, S5 code/data",
  "source_name": "outlet or author; 'X via Y' when the post reached us through Y", "url": "source URL (for S4 via search engine: the quoting page until the post URL is recovered)",
  "accessed_date": "date the source was accessed", "extractor": "who extracted the row", "notes": "free notes (via=search_engine etc.)",
  "run": "collection run that added the row (A6.2)", "verified": "true / pending / false (A6.1)",
  "stance": "alleges, disputes, clears or context (A9.1); clearing party in notes"},
 "data/cases.csv": {
  "case_id": "case key", "title": "short title (no personal names)", "category": "topic category", "platform": "platforms in the case's claims",
  "family": "families in the case's claims", "case_grade": "strongest evidence grade among its claims", "grades_present": "all grades present",
  "event_date": "earliest event_date as written in the claims", "event_date_earliest": "earliest possible day of event_date (A6.3)",
  "event_date_precision": "day, month, quarter, year or range", "first_claim_date": "earliest claim_date as written",
  "first_claim_date_earliest": "its earliest possible day", "first_claim_date_precision": "precision of first_claim_date",
  "n_claims": "number of claims", "n_sources": "distinct URLs", "n_wallet_addresses": "addresses in wallet_labels for the case (suspected, ambiguous, controls, manipulation)",
  "max_amount_claimed_usd": "largest amount claimed", "amounts_disagree": "true if claims state different amounts",
  "investigation_outcome": "sanctioned, charged, cleared_official, cleared_analyst, disputed, under_investigation, unresolved (A9.2)", "status_note": "free note"},
 "data/wallet_labels.csv": {
  "address": "Polymarket proxy (or owner key) address, lower-case", "handle": "public label or username as the source gives it",
  "case_id": "case", "role": "trader, owner_key, ...", "label_tier": "L2 official-case wallet, L3 analyst full address / handle resolved, L4 cluster member, A ambiguous, NC negative control, M manipulation",
  "polarity": "suspected, ambiguous, negative_control, manipulation, context", "source": "file or method the row came from", "source_url": "source URL",
  "verification": "how the address was obtained", "notes": "free notes", "case_market_traded": "true if the wallet has a fill in a markets.csv market of its case (suspected rows; A6.7)",
  "first_case_fill_utc": "first such fill (Data API v2)", "case_buy_usdc": "BUY USDC in case markets", "case_redeem_usdc": "redemptions in case markets",
  "case_check_note": "FLAG when no case-market fill; other notes"},
 "data/wallet_edges.csv": {
  "src": "sender", "dst": "receiver", "kind": "funding, relay handoff, safe owner, cash-out, transfer", "case_id": "case", "chain": "chain or route",
  "amount_usd": "amount", "tx": "transaction hash or evidence", "utc": "time", "source": "source file", "source_url": "source URL"},
 "data/handles_to_resolve.csv": {
  "handle": "public username from a source", "case_id": "case", "source_url": "where the handle appears", "resolved_address": "proxy address, blank if not resolved",
  "resolved_via": "lookup method", "status": "resolved, resolved_case_insensitive_with_fills, failed_*, rejected_*", "notes": "evidence"},
 "data/markets.csv": {
  "case_id": "case", "condition_id": "market condition id", "question": "market question", "slug": "market slug", "event_id": "Gamma event id",
  "event_slug": "Gamma event slug (the deadline ladder)", "series_id": "Gamma series id(s)", "selected_as": "what was selected: event:<slug>, ffic_prefix:<prefix>, hf_slug:<slug>",
  "found_via": "gamma_search, claimed_wallets, ffic_prefix, hf_slug (A6.5)", "reason": "why the market belongs to the case (from the claims)",
  "selection_level": "event (whole event chosen), market (the named market), ladder (another market in its event)",
  "created_utc": "market creation (Gamma)", "deadline_utc": "market end date (Gamma)", "resolved_utc": "closed/resolved time (Gamma, else HF)",
  "outcome": "winning outcome label", "outcomes": "outcome labels", "token_ids": "CLOB token ids", "neg_risk": "Gamma negRisk flag",
  "volume_gamma": "Gamma volume", "volume_hf_usdc": "USDC volume in Polymarket-v1", "in_hf": "market has fills in Polymarket-v1",
  "ladder_rank": "rank of the deadline within the event (1 = earliest); blank if the event has one end date",
  "t_news_utc": "news time used for pre/post splits (A6.6, A7)", "t_news_method": "claim_min, ff_tier1, ff_tier3", "t_news_precision": "day, month, year, range or timestamp",
  "ff_tier": "ForesightFlow tier if the market is in its t_news file", "ff_tier2_tnews": "ForesightFlow tier-2 proxy time (stored, not used)"},
 "data/contradictions.csv": {
  "contradiction_id": "CXnnn", "claim_id": "claim contradicted (never edited)", "case_id": "case", "field": "claim field", "claimed_value": "value in the claim",
  "observed_value": "value observed", "evidence": "how it was observed", "evidence_file": "raw file", "phase": "run-3 phase", "found_utc": "when recorded"},
 "data/event_times.csv": {"case_id": "case", "event_label": "what happened at this time", "t_utc": "time (UTC) or date",
  "t_precision": "minute, approx_15min, approx_hour, window_..., day, day_morning_ET, day_afternoon_ET",
  "basis": "official_post, first_report, operation_start, scheduled_release, official_release", "source_name": "who reported the time",
  "url": "source", "verified": "pending until the page is read", "notes": "notes"},
 "logs/source_candidates.csv": {"source": "dataset, paper or API", "kind": "type", "license": "license", "what_it_adds": "content",
  "status": "not_ingested, not_reproduced, not_used", "notes": "how it could be used"},
 "logs/page_reads_run6.csv": {"url": "page fetched", "claims_or_leads": "claims or leads it serves", "http_status": "HTTP status (403 = site bot block)",
  "read": "page text was read", "n_full_addresses": "full 0x addresses found in the page", "x_post_urls": "X post links found in the page", "read_utc": "date"},
 "logs/handle_checks.csv": {
  "check_id": "HCnnn", "check_type": "handle_case_insensitive, market_check, cftc_complaint_match", "subject": "handle or account checked", "address": "proxy",
  "case_id": "case", "market_condition_id": "market", "market_question": "question", "side": "BUY / REDEEM", "outcome": "outcome checked",
  "window_end_utc": "end of the window checked", "n_fills": "fills found", "first_fill_utc": "first", "last_fill_utc": "last", "usdc": "USDC",
  "shares": "shares", "avg_price": "usdc / shares", "result": "accepted, rejected, match, no_match, traded, ...", "evidence_file": "raw file(s)", "notes": "notes"},
 "logs/needs_page_read.csv": {"claim_id_or_lead": "claim id or lead:<name>", "url": "page to read", "what_to_check": "what to verify", "added_run": "run"},
 "logs/markets_not_found.csv": {"case_id": "case", "kind": "no_market_found or the failed lookup kind", "value": "lookup value", "reason": "why"},
 "logs/fills_counts_by_case.csv": {"case_id": "case", "source": "fill source", "legs": "wallet legs", "distinct_fills": "distinct fill ids",
  "distinct_wallets": "distinct wallets", "usdc_half_of_legs": "half the USDC of all legs (HF: = fill notional; API: approximate)"},
 "logs/search_log.csv": {"n": "query number", "date": "date run", "source_class": "S1-S5", "query": "query text", "engine": "engine", "result": "what it produced"},
 "logs/repos.csv": {"repo": "GitHub repo", "commit": "commit used", "cloned_utc": "clone date", "used_for": "use"},
 "out/fills/label_wallet_legs.parquet": LEG, "out/fills/case_market_legs.parquet": LEG,
 "out/hf_market_catalog.parquet": {
  "condition_id": "condition id", "asset_id": "outcome token", "outcome_seq": "outcome position", "outcome_label": "outcome label", "market_slug": "slug",
  "category": "Polymarket category", "category_refined": "Polymarket-v1 refined category (ACDC market type, A6.9)", "neg_risk": "neg-risk flag",
  "neg_risk_market_id": "neg-risk group id", "winning_outcome_label": "winner per HF metadata", "resolution_status": "resolution status per HF metadata",
  "opens_at": "open time", "close_at": "close time", "resolved_at": "resolution time", "first_fill_ts": "first fill (Unix s)", "last_fill_ts": "last fill",
  "n_fills": "fills", "usdc_volume": "USDC volume"},
 "out/weak_labels.parquet": {
  "address": "wallet", "n_markets": "distinct markets traded in Polymarket-v1", "n_fills": "fill legs", "buy_usdc": "BUY USDC", "sell_usdc": "SELL USDC",
  "first_fill_utc": "first fill", "last_fill_utc": "last fill", "n_longshots": "ACDC longshot bets (A6.9)", "longshot_win_rate": "share of longshots won",
  "n_longshot_types": "distinct market types among longshots", "military_longshot_share": "share of longshots on military-keyword markets",
  "acdc_class": "Orca, longshot_wallet or blank (reconstruction; not used as a label, see logs/acdc_reconstruction.json)",
  "acdc_military_orca": "Orca with >= half military longshots", "realised_pnl": "Inca PnL on resolved markets (A6.9)",
  "inca_flag": "<= 10 markets and realised_pnl >= $30,000", "evidence_grade": "E6 (rule label)", "data_scope": "data used"},
 "out/acdc_longshots.parquet": {
  "wallet": "wallet", "asset_id": "token", "condition_id": "market", "hour": "UTC clock hour (Unix s // 3600)", "usdc": "BUY USDC in the hour",
  "shares": "shares", "vwap": "usdc / shares", "n_fills": "fills", "outcome_label": "token label", "winning_outcome_label": "winner",
  "won": "token won", "category_refined": "market type", "market_slug": "slug", "military_market": "slug matches the A6.9 military pattern"},
 "out/market_minutes.parquet": {
  "case_id": "case", "condition_id": "market", "minute_ts": "minute start (Unix s)", "minute_utc": "minute start", "minutes_from_tnews": "minutes relative to t_news",
  "t_news_precision": "precision of t_news", "source": "hf_polymarket_v1 and/or data_api_v2", "n_fills_hf": "fills (HF, counted once)",
  "n_legs_api": "Data API legs (maker and taker rows; not fills)", "usdc": "volume (HF taker legs + API legs)", "vwap": "volume-weighted price",
  "last_price": "last trade price in the minute", "taker_buy_usdc": "aggressor BUY volume (HF only)", "taker_sell_usdc": "aggressor SELL volume (HF only)",
  "n_wallets": "distinct wallets", "n_new_wallets": "wallets whose first Polymarket-v1 fill was within 7 days", "n_wallets_age_unknown": "wallets absent from Polymarket-v1"},
 "out/controls.parquet": {
  "episode_id": "suspected episode the control belongs to", "control_type": "same_side or other_side_large_buyer (A6.10)",
  "relaxation": "base, window_72h, price_0.10, size_0.25_4x, none_available", "n_eligible": "eligible wallets before sampling",
  "case_id": "case", "condition_id": "market", "asset_id": "token bought", "outcome_label": "token label", "wallet": "control wallet",
  "first_buy_ts": "first pre-news BUY (Unix s)", "first_buy_price": "its price", "size_usdc": "pre-news BUY USDC", "n_buys": "pre-news BUY legs"},
 "out/episodes.parquet": {
  "row_id": "ERnnnnnn", "role": "suspected, control_same_side, control_other_side_large_buyer", "control_of": "episode row a control belongs to",
  "case_id": "case", "condition_id": "market", "event_slug": "ladder event", "asset_id": "token", "outcome_label": "token label", "wallet": "wallet",
  "source_pre": "fill source of pre-news legs", "account_age_days_at_first_buy": "days since the wallet's first Polymarket-v1 fill",
  "prior_markets": "markets traded before this first buy (Polymarket-v1)", "prior_net_long_win_rate": "share of earlier resolved markets where the wallet ended net long the winner",
  "case_share_of_lifetime_volume": "this market-token's USDC / lifetime USDC", "first_price": "first pre-news buy price", "vwap": "pre-news VWAP",
  "max_price_paid": "max pre-news buy price", "n_buy_fills": "pre-news buy legs", "median_fill_usdc": "median buy size", "fill_size_cv": "buy-size coefficient of variation",
  "taker_share": "share of pre-news buys as taker (HF legs only)", "hour_of_day_first_buy": "UTC hour of first buy", "pre_buy_usdc": "pre-news BUY USDC",
  "pre_buy_shares": "pre-news BUY shares", "signal_a_rebuy_1_5x": "bought again at >= 1.5x the first price before t_news (Signal A)",
  "size_price_slope": "OLS slope of buy size on price (pre-news)", "hours_last_buy_to_tnews": "hours from last pre-news buy to t_news",
  "ladder_rank": "deadline rank of this market", "is_shortest_sufficient": "earliest-deadline Yes-resolving market in its event (Signal B)",
  "share_on_this_ladder_market": "share of the wallet's pre-news ladder buys on this market", "hours_first_buy_to_tnews": "hours from first buy to t_news",
  "hours_funding_to_first_trade": "empty: phase 4 blocked", "funding_source_type": "empty: phase 4 blocked", "funder_shared_with_labelled": "empty: phase 4 blocked",
  "follower_wallets_60m": "other wallets buying the same token within 60 min after each pre-news buy", "follower_buy_usdc_60m": "their BUY USDC",
  "share_sold_before_resolution_post": "shares sold before resolution / shares bought (uses post-news data)", "won_post": "token won",
  "pnl_post": "sells - buys + winning shares held (all fills)", "redemption_delay_hours_post": "hours from resolution to first redemption (suspected, Data API)"},
}
OPTIONAL = {"data/edges_expanded.csv", "data/wallet_labels_expanded.csv"}


def cols(p):
    if p.endswith(".csv"):
        return next(csv.reader(open(p)))
    return [r[0] for r in duckdb.sql(f"DESCRIBE SELECT * FROM '{p}'").fetchall()]


def nrows(p):
    if p.endswith(".csv"):
        return sum(1 for _ in csv.reader(open(p))) - 1
    return duckdb.sql(f"SELECT count(*) FROM '{p}'").fetchall()[0][0]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


missing = []
md = ["# PMITC codebook", "", "Every column of every table. Generated by `build/package.py`, which fails if a column lacks a description.", ""]
for p, d in DESC.items():
    if not os.path.exists(p):
        continue
    cs = cols(p)
    missing += [f"{p}:{c}" for c in cs if c not in d]
    md += [f"## `{p}`", "", "| Column | Meaning |", "|---|---|"] + [f"| `{c}` | {d.get(c, '')} |" for c in cs] + [""]
assert not missing, missing
open("CODEBOOK.md", "w").write("\n".join(md))

files = sorted(set(glob.glob("data/*.csv") + glob.glob("out/*.parquet") + glob.glob("out/fills/*.parquet") + list(k for k in DESC if k.startswith("logs/"))))
man = {"generated_by": "build/package.py", "hf_source": "TimeSeventeen/Polymarket-v1 @ 6d1bcd5279cbbd8e833feaeba9a56a0aee139144", "files": []}
ign = open(os.path.join("..", ".gitignore")).read()
for p in files:
    man["files"].append(dict(path=p, rows=nrows(p), bytes=os.path.getsize(p), sha256=sha(p),
                             in_git=("dataset/" + p) not in ign, over_50mb=os.path.getsize(p) > 50 * 1024 * 1024))
json.dump(man, open("out/MANIFEST.json", "w"), indent=1)

# the blind sample is drawn once (run 3, 92 claims) and never redrawn; later claims get their own sample when A4 is done
if os.path.exists("logs/blind_check_sample.csv"):
    print("blind sample kept (already drawn)"); raise SystemExit(0)
claims = [r["claim_id"] for r in csv.DictReader(open("data/claims.csv"))]
url = {r["claim_id"]: r["url"] for r in csv.DictReader(open("data/claims.csv"))}
k = round(0.2 * len(claims))
pick = sorted(random.Random(192).sample(claims, k))
with open("logs/blind_check_sample.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["claim_id", "url"]); [w.writerow([c, url[c]]) for c in pick]
print("codebook tables", sum(os.path.exists(p) for p in DESC), "manifest files", len(files), "blind sample", k)
