"""v1.0 release schema: every column of every table with dtype, unit, allowed values, source and leakage note.
Used by build/v1/tables.py (casts and checks) and build/v1/codebook.py (CODEBOOK.md). A column missing here fails the build.
Dtypes: string, int64, float64, bool, timestamp (UTC), date. 'pk' marks primary-key columns.
Leakage notes: 'pre' = uses only data before the cut time of its row; 'post' = outcome, never a feature; 'label' = target or label;
'meta' = identifier or provenance; 'static' = known at market creation.
"""
S, I, FL, B, T, DT = "string", "int64", "float64", "bool", "timestamp", "date"
GR = "E1;E2;E3;E4;E5;E6"
VER = "day;precise"


def col(name, dtype, desc, unit="", allowed="", source="", leak="meta", pk=False):
    return dict(name=name, dtype=dtype, desc=desc, unit=unit, allowed=allowed, source=source, leak=leak, pk=pk)


TABLES = {}
TABLES["cases"] = dict(desc="One row per case (underlying event). Derived from claims (build/build_cases.py) plus market and wallet counts.", cols=[
    col("case_id", S, "case key", pk=True, source="claims"), col("title", S, "short title; no names of alleged traders", source="hand-written"),
    col("category", S, "topic category", source="hand-written"), col("platform", S, "platforms in the case's claims, ';'-joined", allowed="polymarket;kalshi;both"),
    col("family", S, "families in the case's claims, ';'-joined (PROTOCOL 2)"), col("case_grade", S, "strongest evidence grade among the case's claims", allowed=GR, leak="label"),
    col("grades_present", S, "all grades present, ';'-joined"), col("investigation_outcome", S, "PROTOCOL A9.2", allowed="sanctioned;charged;cleared_official;cleared_analyst;disputed;under_investigation;unresolved", leak="label"),
    col("event_date", S, "earliest event_date as written (partial dates allowed, A6.3)"), col("event_date_earliest", DT, "earliest possible day of event_date"),
    col("event_date_precision", S, "precision of event_date", allowed="day;month;quarter;year;range"), col("first_claim_date", S, "earliest claim_date as written"),
    col("first_claim_date_earliest", DT, "earliest possible day of the first claim (used for the A15 time split)"),
    col("first_claim_date_precision", S, "precision of first_claim_date", allowed="day;month;quarter;year;range"),
    col("n_claims", I, "number of claims"), col("n_sources", I, "distinct source URLs"), col("n_markets", I, "case markets in markets"),
    col("n_wallets_suspected", I, "suspected wallets (any trade confirmation)"), col("n_documented_by_case", I, "documented wallets in this case (is_documented: suspected, trade_confirmed, informed_trading). Two cases hold 74 of 119 (A19)", leak="label"),
    col("n_wallets_coordinated_rule", I, "distinct wallets for which the A13 rule fired in this case (rule output, not an allegation; A17)", leak="label"), col("max_amount_claimed_usd", FL, "largest amount any claim states", unit="USD"),
    col("amounts_disagree", B, "claims state different amounts"), col("benchmark_split", S, "PROTOCOL A15 split", allowed="train;test"),
    col("status_note", S, "free note")])
TABLES["claims"] = dict(desc="One row per claim: one statement by one source at one time (PROTOCOL 2, 6). Claims are never edited; contradictions go to contradictions.", cols=[
    col("claim_id", S, "CLnnnn, stable", pk=True), col("case_id", S, "case (FK cases)"), col("platform", S, "platform", allowed="polymarket;kalshi;both"),
    col("family", S, "family (PROTOCOL 2)"), col("subject_type", S, "what the claim points at", allowed="address;handle;account;cluster;market;aggregate;notice"),
    col("subject", S, "subject as the source gives it (prefixes kept as prefixes); notice or release ID for official notices; never a personal name"),
    col("claim_text", S, "our paraphrase, under 30 words"), col("evidence_grade", S, "PROTOCOL 5 (A12.1 for employer findings)", allowed=GR, leak="label"),
    col("stance", S, "PROTOCOL A9.1", allowed="alleges;disputes;clears;context"), col("verified", S, "A6.1: true = page text read and supports the claim", allowed="true;pending;false"),
    col("run", I, "collection run that added the row (A6.2)"), col("amount_claimed_usd", FL, "amount the source states", unit="USD"),
    col("n_accounts_claimed", I, "accounts the source names"), col("event_date", S, "event date as written (A6.3)"), col("claim_date", S, "claim date as written (A6.3)"),
    col("source_class", S, "PROTOCOL 3", allowed="S1;S2;S3;S4;S5"), col("source_name", S, "outlet or author ('X via Y')"),
    col("url", S, "source URL; may contain names chosen by the source (official file names, article slugs)"), col("post_url", S, "X post URL recovered from the page (from notes)"),
    col("accessed_date", DT, "date accessed"), col("extractor", S, "who extracted the row"), col("notes", S, "free notes"),
    col("right_of_reply", S, "reply received from the subject, verbatim summary and date (A24); NULL if none")])
TABLES["wallets"] = dict(desc="One row per (wallet, case) label. Labels are allegations by the named source, not findings.", cols=[
    col("wallet", S, "Polymarket proxy (or owner key) address, lower-case 0x + 40 hex", pk=True), col("case_id", S, "case (FK cases)", pk=True),
    col("handle", S, "public username or label as the source gives it"), col("role", S, "trader, owner_key, ..."),
    col("label_tier", S, "L2 official-case wallet, L3 analyst full address / resolved handle, L4 cluster member, L4_coordinated (A13 rule), A ambiguous, NC negative control, M manipulation"),
    col("polarity", S, "label polarity", allowed="suspected;ambiguous;negative_control;manipulation;context;candidate", leak="label"),
    col("trade_confirmed", B, "A12.5: >= 1 fill in a market of its case (from fills)", leak="label"),
    col("label_family", S, "A19: manipulation for manipulation rows, else the family of the case's claims", allowed="informed_trading;public_data_leak;manipulation;negative_control;oracle_manipulation;pre_taped_leak;resolution_event;contested;multi_account", leak="label"),
    col("is_documented", B, "polarity = suspected and trade_confirmed and label_family = informed_trading (default positive label, A19)", leak="label"),
    col("doc_grade", S, "strongest grade among the case's claims about accounts, addresses, handles or clusters (not aggregates or markets)", allowed=GR, leak="label"),
    col("wallet_grade", S, "A20: strongest grade among the claims that name this wallet (data/claim_wallet_links.csv); NULL = link_only", allowed=GR, leak="label"),
    col("label_broad", B, "A20: trade_confirmed, informed_trading, doc_grade E1-E5 (= is_documented)", leak="label"),
    col("label_standard", B, "A20: label_broad and doc_grade E1-E4 (includes cluster members)", leak="label"),
    col("label_strict", B, "A20: label_standard and (wallet_grade E1-E3, or named by address or resolved handle in an E4 claim)", leak="label"),
    col("strict_no_prenews", B, "A26: meets the rest of the strict rule but has no BUY before its case markets' precise cuts (so not strict)", leak="label"),
    col("strict_basis", S, "why label_strict holds", allowed="wallet_grade_E1;wallet_grade_E2;wallet_grade_E3;named_in_E4_claim", leak="label"),
    col("hard_negative", B, "A21 cleared_case_wallet: a wallet in a case cleared by an official, platform or analyst", leak="label"),
    col("hard_negative_rule", S, "A21 rule", allowed="cleared_case_wallet", leak="label"),
    col("source", S, "file or method the row came from"), col("source_url", S, "source URL"), col("verification", S, "how the address was obtained"),
    col("first_case_fill_utc", T, "first fill in a case market", source="fills", leak="post"), col("case_buy_usdc", FL, "BUY USDC in case markets, all time", unit="USD", leak="post"),
    col("case_redeem_usdc", FL, "redemptions in case markets (Data API)", unit="USD", leak="post"), col("notes", S, "free notes")])
TABLES["markets"] = dict(desc="One row per (case, market). Ladders are full Gamma events (A6.5). Titles withheld where they name the alleged trader (A12.6).", cols=[
    col("case_id", S, "case (FK cases)", pk=True), col("condition_id", S, "market condition id, lower-case hex", pk=True), col("question", S, "market question; NULL when title_withheld", leak="static"),
    col("slug", S, "market slug; NULL when title_withheld"), col("event_id", S, "Gamma event id (or withheld-week-<date>)"), col("event_slug", S, "Gamma event slug; NULL when title_withheld"),
    col("selected_as", S, "how the market was selected"), col("found_via", S, "A6.5 method"), col("reason", S, "why the market belongs to the case"),
    col("selection_level", S, "event, market or ladder", allowed="event;market;ladder"), col("created_utc", T, "market creation", leak="static"),
    col("deadline_utc", T, "market end date", leak="static"), col("resolved_utc", T, "resolution / close time", leak="post"), col("outcome", S, "winning outcome label", leak="post"),
    col("outcomes", S, "outcome labels, ';'-joined"), col("token_ids", S, "outcome token ids, ';'-joined"), col("neg_risk", B, "Gamma negRisk"),
    col("volume_gamma", FL, "Gamma volume", unit="USD", leak="post"), col("volume_hf_usdc", FL, "Polymarket-v1 USDC volume", unit="USD", leak="post"),
    col("in_hf", B, "market has fills in Polymarket-v1"), col("ladder_rank", I, "deadline rank within the event (1 = earliest)", leak="static"),
    col("t_news_utc", T, "day-level news time (A6.6, A7)", leak="label"), col("t_news_method", S, "claim_min, ff_tier1, ff_tier3"),
    col("t_news_precision", S, "precision of t_news_utc", allowed="day;month;quarter;year;range;timestamp"),
    col("t_news_precise_utc", T, "exact news time (A10); equals t_news_utc where no exact time is sourced", leak="label"),
    col("t_news_precise_precision", S, "A10.1", allowed="minute;quarter_hour;hour;window;day_fallback"), col("t_news_precise_source", S, "URL of the event_times row; day_fallback; or rejected_outside_coarse_date (A18)"),
    col("t_news_precise_verified", S, "verified flag of the event_times row"), col("title_withheld", B, "A12.6"),
    col("t_news_market_utc", T, "A25: per-market exact cut (precise version): Gamma scheduled start, market deadline inside a coarse case date, or the case time", leak="label"),
    col("t_news_market_day_utc", T, "A25: per-market day-level cut (day version)", leak="label"),
    col("t_news_market_method", S, "A25 method (A30: a scheduled start is used only if before the market's close)", allowed="scheduled_start;market_deadline;case_time"), col("is_placebo_market", B, "always false here"),
    col("t_news_reliable", B, "A29: false for every market of a month- or year-dated case without a sourced exact time; excluded from default analyses and benchmarks", leak="label"),
    col("t_news_deadline_rule_utc", T, "A29: the A25 rule-2 deadline time where it set the cut; NULL otherwise", leak="label"),
    col("ff_tier", S, "ForesightFlow tier if listed"), col("ff_tier2_tnews", T, "ForesightFlow tier-2 proxy (stored, not used)")])
TABLES["placebo_markets"] = dict(desc="One row per placebo market (A14) with its matched case market; case-market rows that could not be matched appear with NULL placebo fields.", cols=[
    col("placebo_row_id", S, "row key: PRnnnnn (every row, matched or not)", pk=True), col("placebo_id", S, "PLnnnnn; NULL for unmatched case-market rows"), col("case_id", S, "matched case (FK cases)"), col("case_condition_id", S, "matched case market (FK markets)"),
    col("placebo_condition_id", S, "placebo market condition id (unique)"), col("placebo_category", S, "A14 category", allowed="crypto_price;weather_reading"),
    col("placebo_slug", S, "placebo market slug"), col("placebo_token_ids", S, "outcome token ids"), col("placebo_outcomes", S, "outcome labels"),
    col("placebo_outcome", S, "winning outcome", leak="post"), col("placebo_opens_utc", T, "opens_at"), col("placebo_close_utc", T, "close_at"),
    col("placebo_resolved_utc", T, "resolved_at (often NULL for weather)", leak="post"), col("placebo_end_utc", T, "resolved_at else close_at (A14.1)"),
    col("placebo_volume", FL, "Polymarket-v1 USDC volume", unit="USD", leak="post"), col("case_volume", FL, "case-market volume used for matching", unit="USD", leak="post"),
    col("case_volume_basis", S, "hf or gamma", allowed="hf;gamma"), col("volume_decile", I, "case market's volume decile (1-10)", leak="post"),
    col("duration_band", S, "case market's duration band"), col("resolution_month", S, "case market's end month YYYY-MM"),
    col("placebo_duration_band", S, "placebo duration band"), col("placebo_resolution_month", S, "placebo end month"),
    col("relaxation", S, "A14 relaxation step or reason unmatched"), col("n_eligible", I, "placebos eligible at that step"),
    col("case_tnews_fraction_day", FL, "position of t_news in the case market's life (0-1)"), col("case_tnews_fraction_precise", FL, "same for t_news_precise"),
    col("t_ref_day_utc", T, "placebo cut time, day version (A14)", leak="label"), col("t_ref_precise_utc", T, "placebo cut time, precise version", leak="label"),
    col("benchmark_split", S, "split of the matched case (A15)", allowed="train;test")])
FILL = [col("market_set", S, "which part of the fills table", allowed="case;placebo;twin;label_other"), col("leg_id", S, "unique leg id: <fill_id>:t|m (HF) or the API row id", pk=True),
    col("source", S, "A6.4", allowed="hf_polymarket_v1;data_api_v2"), col("fill_id", S, "HF <day file>:<row>; API <tx hash>:<row index>"),
    col("tx_hash", S, "transaction hash (Data API rows only)"), col("ts", I, "block time", unit="Unix seconds UTC"), col("ts_utc", T, "block time"),
    col("condition_id", S, "market"), col("asset_id", S, "outcome token id"), col("outcome_label", S, "label of the traded token"), col("outcome_seq", I, "outcome position (HF 1/2; API 0/1)"),
    col("price", FL, "price per share", unit="USDC"), col("usdc", FL, "notional", unit="USDC"), col("shares", FL, "shares (HF: usdc / price)", unit="shares"),
    col("fee_usdc", FL, "fee (HF only)", unit="USDC"), col("wallet", S, "wallet this leg belongs to"), col("wallet_role", S, "maker or taker (Polymarket-v1); NULL on Data API rows (A24)", allowed="maker;taker"),
    col("role_fields_available", B, "true for Polymarket-v1 rows; false for Data API rows, whose wallet_role, aggressor_side, maker, taker and fee are NULL (A24)"),
    col("wallet_side", S, "BUY or SELL of this token by this wallet (A6.4)", allowed="BUY;SELL"), col("aggressor_side", S, "taker_direction (HF only)", allowed="BUY;SELL"),
    col("maker", S, "maker address (HF only)"), col("taker", S, "taker address (HF only)"), col("market_slug", S, "market slug; NULL for withheld markets"),
    col("econ_side", S, "A34 economic side: BUY for an inferred leg (SELL of a token the wallet held none of = BUY of the complement), else wallet_side", allowed="BUY;SELL"),
    col("econ_asset_id", S, "A34 economic token (the complement for an inferred leg)"), col("econ_outcome_label", S, "A34 label of econ_asset_id"),
    col("econ_price_usdc", FL, "A34 economic price (1 - price_usdc for an inferred leg)"), col("econ_size_usdc", FL, "A34 economic size: shares x econ_price_usdc for an inferred leg, else usdc", unit="USDC"),
    col("econ_inferred", B, "A34: leg re-read as an economic BUY of the complement (split or mint inferred); raw columns unchanged"),
    col("econ_partial", B, "A34.1: SELL larger than the econ holding; the econ_* columns give the held SELL part, econ_excess_* the inferred BUY"),
    col("econ_excess_shares", FL, "A34.1: shares beyond the holding, re-read as an economic BUY of the complement", unit="shares"),
    col("econ_excess_asset_id", S, "A34.1: the complement token"), col("econ_excess_outcome_label", S, "A34.1: its label"),
    col("econ_excess_price_usdc", FL, "A34.1: 1 - price_usdc"), col("econ_excess_size_usdc", FL, "A34.1: econ_excess_shares x econ_excess_price_usdc", unit="USDC")]
TABLES["fills"] = dict(desc="Every leg of every fill in case and placebo markets, plus every leg of labelled wallets elsewhere. Parquet only (split into parts).", cols=FILL)
POS = [col("market_set", S, "case, placebo (A14) or twin (A22) market", allowed="case;placebo;twin", pk=True), col("case_id", S, "case (placebo: matched case)", pk=True),
    col("condition_id", S, "market", pk=True), col("asset_id", S, "outcome token", pk=True), col("wallet", S, "buyer", pk=True), col("t_news_version", S, "A10.2", allowed=VER, pk=True),
    col("outcome_label", S, "token label"), col("t_cut_ts", I, "cut time: the per-market cut (A25; case) or t_ref (placebo, twin)", unit="Unix s", leak="label"),
    col("is_shortest_sufficient", B, "this market is its event's shortest deadline that resolved Yes", leak="post"),
    col("n_buy_fills_pre", I, "BUY legs before the cut", leak="pre"), col("buy_usdc_pre", FL, "BUY USDC before the cut", unit="USDC", leak="pre"),
    col("buy_shares_pre", FL, "BUY shares before the cut", leak="pre"), col("first_buy_ts", I, "first pre-cut BUY", unit="Unix s", leak="pre"),
    col("last_buy_ts", I, "last pre-cut BUY", unit="Unix s", leak="pre"), col("first_buy_price", FL, "price of the first pre-cut BUY", leak="pre"),
    col("max_buy_price", FL, "highest pre-cut BUY price", leak="pre"), col("median_buy_fill_usdc", FL, "median pre-cut BUY leg", unit="USDC", leak="pre"),
    col("sell_usdc_pre", FL, "SELL USDC before the cut", unit="USDC", leak="pre"), col("sell_shares_pre", FL, "SELL shares before the cut", leak="pre"),
    col("taker_share_pre", FL, "share of pre-cut BUY legs as taker (HF only)", leak="pre"), col("source_pre", S, "sources of pre-cut legs", leak="pre"),
    col("econ_inferred_buy_usdc_pre", FL, "A34: part of buy_usdc_pre from inferred economic buys (econ view is the default)", unit="USDC", leak="pre"),
    col("raw_view_prenews_buy", B, "A34: the position also exists in the raw BUY-only view (a raw BUY before the cut)", leak="pre"),
    col("full_sets_pre_shares", FL, "A34.2: min(econ Yes holding, econ No holding) of this wallet in this market before the cut (full sets carry no direction)", unit="shares", leak="pre"),
    col("directional_shares_pre", FL, "A34.2: |econ Yes holding - econ No holding| before the cut (wallet-market level)", unit="shares", leak="pre"),
    col("directional_cost_usdc_pre", FL, "A34.2: FIFO cost of the excess shares on the directional token (0 on the other token); a FIFO accounting figure, not an entry price or time (A34.3)", unit="USDC", leak="pre"),
    col("directional_first_buy_utc", T, "A34.3: first econ BUY of the directional token before the cut (entry time; use for timing features)", leak="pre"),
    col("directional_first_buy_price", FL, "A34.3: price of that first econ BUY", leak="pre"),
    col("directional_vwap_pre", FL, "A34.3: VWAP of econ BUYs of the directional token before the cut", leak="pre"),
    col("directional_hours_first_buy_to_cut", FL, "A34.3: hours from that first econ BUY to the cut", unit="hours", leak="pre"),
    col("is_directional_position", B, "A34.2: this token is the wallet's directional token here and directional_shares_pre > 0; the pre-news position used by label sets, benchmarks, episodes, hard negatives and the coordinated rule", leak="pre"),
    col("is_market_maker", B, "A34.1 reporting flag, NOT a label: >= 20 active (market, minute) pairs with both tokens traded in > 50% of them; not used by any rule or benchmark"),
    col("vwap_pre", FL, "pre-cut BUY VWAP", leak="pre"), col("is_main_side", B, "token with the wallet's largest pre-cut BUY in this market", leak="pre"),
    col("account_age_days_at_first_buy", FL, "days from first Polymarket-v1 fill to first pre-cut BUY (NULL if no v1 history)", unit="days", leak="pre"),
    col("first_fill_in_market_ts", I, "first pre-cut fill in this market (any side)", unit="Unix s", leak="pre"),
    col("market_usdc_pre", FL, "all pre-cut USDC in this market (both sides, both tokens)", unit="USDC", leak="pre"),
    col("market_buy_usdc_pre", FL, "pre-cut BUY USDC in this market, both tokens (F4)", unit="USDC", leak="pre"),
    col("f5_conviction", FL, "F5 |net YES USDC| / gross USDC, pre-cut", leak="pre"),
    col("vol_to_day", FL, "Polymarket-v1 volume, all markets, up to the end of the cut's UTC day (A16 F2 denominator; includes the rest of that day as frozen v1 does)", unit="USDC", leak="pre"),
    col("lifetime_markets_v1", I, "lifetime distinct Polymarket-v1 markets (F2 market branch, as frozen v1; A16.1: ex-post count that can only understate the flag)", leak="pre"),
    col("f1_days_account_to_first_fill", FL, "F1 freshness (A16 substitution)", unit="days", leak="pre"), col("f2_share", FL, "F2 focus share", leak="pre"),
    col("f3_main_vwap", FL, "F3 main-side VWAP", leak="pre"), col("f6_hours_median_buy_to_tnews", FL, "F6 hours from USD-weighted median main-side buy to the cut", unit="hours", leak="pre"),
    col("flag_f1", B, "F1 <= 7 days", leak="pre"), col("flag_f2", B, "F2 share >= 0.8 or markets <= 2", leak="pre"), col("flag_f3", B, "F3 <= 0.35", leak="pre"),
    col("flag_f4", B, "F4 >= $2,500", leak="pre"), col("flag_f5", B, "F5 >= 0.8", leak="pre"), col("flag_f6", B, "F6 <= 72 h", leak="pre"),
    col("gate1_score", I, "number of F1-F6 flags (NULL outside Polymarket-v1)", leak="pre"), col("gate1", B, "gate1_score >= 4 (A16)", leak="label"),
    col("gate2a", B, "Signal A: a later pre-cut BUY at >= 1.5x the first price", leak="pre"),
    col("gate2b", B, "Signal B: largest pre-cut BUY in the event is on the shortest Yes deadline, Yes token (uses resolution: label only)", leak="post"),
    col("is_documented", B, "wallet is documented for this case", leak="label"), col("doc_grade", S, "wallet's doc_grade", allowed=GR, leak="label"),
    col("label_strict", B, "wallet in label_strict for this case (A20)", leak="label"), col("label_standard", B, "label_standard (A20)", leak="label"),
    col("label_broad", B, "label_broad (A20)", leak="label"),
    col("hard_negative", B, "A21: position matches the suspect profile but is a negative (loser, cleared case, or placebo winner)", leak="label"),
    col("hard_negative_rule", S, "A21 rule", allowed="lookalike_loser;cleared_case_lookalike;placebo_lookalike_winner", leak="label"),
    col("coordinated_rule_fired", B, "A13 rule fired for this wallet, token, market, case and version. Rule output; about 1/3 expected by chance; may include copy-traders; not an allegation (A17)", leak="label"),
    col("triggering_suspect", S, "documented wallet of the earliest A13 trigger (NULL if the rule did not fire)", leak="label"),
    col("placebo_rate", FL, "A13 placebo-to-real ratio of this version (share of hits expected by chance); NULL if the rule did not fire", leak="label"),
    col("is_control", B, "selected as a matched control in this market, version", leak="label"),
    col("is_placebo_market", B, "market_set = placebo", leak="label"), col("is_twin_market", B, "market_set = twin (A22)", leak="label"),
    col("t_news_reliable", B, "A29: the (matched) case's news time is reliable; default analyses and benchmarks use true only", leak="label"),
    col("buy_usdc_post", FL, "BUY USDC at or after the cut", unit="USDC", leak="post"), col("buy_shares_post", FL, "BUY shares at or after the cut", leak="post"),
    col("sell_usdc_post", FL, "SELL USDC at or after the cut", unit="USDC", leak="post"), col("sell_shares_post", FL, "SELL shares at or after the cut", leak="post"),
    col("won_post", B, "token won", leak="post"), col("pnl_post", FL, "sells - buys + winning shares held (no redemptions, fees)", unit="USDC", leak="post")]
TABLES["positions"] = dict(desc="All-buyer positions before the cut (C2): the full population a detector must search, case and placebo markets.", cols=POS)
EPI = [col("row_id", S, "row id within version", pk=True), col("episode_id", S, "stable id of a documented episode (hash of case, wallet, market, token); NULL on control rows"),
    col("t_news_version", S, "A10.2", allowed=VER, pk=True),
    col("control_design", S, "A27/A33: standard (A6.10), age_matched (plus account-age band; T2s), winrate_matched (plus prior win-rate band; T2w) or open (Orca/Inca wallets allowed; T2-open)", allowed="standard;age_matched;winrate_matched;open", pk=True),
    col("t_news_reliable", B, "A29: the case's news time is reliable (default analyses use true only)", leak="label"),
    col("relaxed_band", B, "A33: control chosen after the adjacent age / win-rate band was allowed; false on suspected rows and exact-band controls", leak="label"),
    col("role", S, "suspected, control_same_side, control_other_side_large_buyer", leak="label"),
    col("label_strict", B, "suspected row of a label_strict wallet (A20); false on control rows", leak="label"), col("label_standard", B, "label_standard (A20)", leak="label"),
    col("label_broad", B, "label_broad (A20)", leak="label"),
    col("control_of", S, "row_id... of the episode this control is matched to (its episode_id via controls)"), col("case_id", S, "case"), col("condition_id", S, "market"),
    col("event_slug", S, "Gamma event"), col("asset_id", S, "token"), col("outcome_label", S, "token label"), col("wallet", S, "wallet"), col("source_pre", S, "source of pre-news legs", leak="pre"),
    col("econ_inferred_buy_usdc_pre", FL, "A34: pre-news BUY USDC from inferred economic buys", unit="USDC", leak="pre"),
    col("raw_view_prenews_buy", B, "A34: the episode also exists in the raw BUY-only view", leak="pre"),
    col("directional_shares_pre", FL, "A34.2: directional shares of this wallet in this market before the cut", unit="shares", leak="pre"),
    col("full_sets_pre_shares", FL, "A34.2: full sets held before the cut", unit="shares", leak="pre"),
    col("directional_cost_usdc_pre", FL, "A34.2: FIFO cost of the directional shares (FIFO accounting figure, not entry timing; A34.3)", unit="USDC", leak="pre"),
    col("directional_first_buy_utc", T, "A34.3: first econ BUY of the directional token before the cut (entry time; use for timing features)", leak="pre"),
    col("directional_first_buy_price", FL, "A34.3: price of that first econ BUY", leak="pre"),
    col("directional_vwap_pre", FL, "A34.3: VWAP of econ BUYs of the directional token before the cut", leak="pre"),
    col("directional_hours_first_buy_to_cut", FL, "A34.3: hours from that first econ BUY to the cut", unit="hours", leak="pre"),
    col("account_age_days_at_first_buy", FL, "days from first Polymarket-v1 fill to first pre-news buy", unit="days", leak="pre"),
    col("prior_markets", I, "distinct Polymarket-v1 markets before the first buy", leak="pre"), col("prior_net_long_win_rate", FL, "win rate on earlier resolved net-long positions", leak="pre"),
    col("case_share_of_lifetime_volume", FL, "case volume / lifetime Polymarket-v1 volume (uses lifetime: ex-post denominator)", leak="post"),
    col("first_price", FL, "first pre-news buy price", leak="pre"), col("vwap", FL, "pre-news buy VWAP", leak="pre"), col("max_price_paid", FL, "max pre-news price", leak="pre"),
    col("n_buy_fills", I, "pre-news buy legs", leak="pre"), col("median_fill_usdc", FL, "median pre-news buy leg", unit="USDC", leak="pre"),
    col("fill_size_cv", FL, "coefficient of variation of pre-news buy legs", leak="pre"), col("taker_share", FL, "share of pre-news buys as taker", leak="pre"),
    col("hour_of_day_first_buy", I, "UTC hour of first buy", leak="pre"), col("pre_buy_usdc", FL, "pre-news buy USDC", unit="USDC", leak="pre"),
    col("pre_buy_shares", FL, "pre-news buy shares", leak="pre"), col("signal_a_rebuy_1_5x", B, "Signal A", leak="pre"), col("size_price_slope", FL, "slope of buy size on price", leak="pre"),
    col("hours_last_buy_to_tnews", FL, "hours from last pre-news buy to t_news", unit="hours", leak="pre"), col("ladder_rank", I, "deadline rank", leak="static"),
    col("is_shortest_sufficient", B, "market is the event's shortest deadline that resolved Yes", leak="post"), col("share_on_this_ladder_market", FL, "share of event buys on this market. LEAKY for suspected-vs-control tasks: controls are matched one market at a time, so it is 1 for every control", leak="label"),
    col("hours_first_buy_to_tnews", FL, "hours from first buy to t_news", unit="hours", leak="pre"),
    col("hours_funding_to_first_trade", FL, "empty: money graph not run (A12.2)", leak="pre"), col("funding_source_type", S, "empty (A12.2)", leak="pre"),
    col("funder_shared_with_labelled", B, "empty (A12.2)", leak="pre"), col("follower_wallets_60m", I, "other wallets buying the token within 60 min after a pre-news buy (may extend past t_news)", leak="post"),
    col("follower_buy_usdc_60m", FL, "their buy USDC (may extend past t_news)", unit="USDC", leak="post"),
    col("share_sold_before_resolution_post", FL, "share of shares sold before resolution", leak="post"), col("won_post", B, "token won", leak="post"),
    col("pnl_post", FL, "realised + held winning value", unit="USDC", leak="post"), col("redemption_delay_hours_post", FL, "hours from resolution to first redemption (suspected only)", unit="hours", leak="post")]
TABLES["episodes"] = dict(desc="Per (wallet, market, token) episode of documented wallets and their matched controls; pre-news features, then _post outcomes.", cols=EPI)
TABLES["controls"] = dict(desc="Matched controls (A6.10, seed 192) with relaxation flags, per t_news version.", cols=[
    col("t_news_version", S, "A10.2", allowed=VER, pk=True),
    col("control_design", S, "A27/A33 design", allowed="standard;age_matched;winrate_matched;open", pk=True), col("episode_id", S, "documented episode", pk=True), col("wallet", S, "control wallet", pk=True),
    col("relaxed_band", B, "A33: chosen with the adjacent age / win-rate band allowed"),
    col("control_type", S, "same_side or other_side_large_buyer", allowed="same_side;other_side_large_buyer", pk=True),
    col("relaxation", S, "A6.10 relaxation used", allowed="base;window_72h;price_0.10;size_0.25_4x"), col("n_eligible", I, "eligible controls at that step"),
    col("case_id", S, "case"), col("condition_id", S, "market"), col("asset_id", S, "token"), col("outcome_label", S, "token label"),
    col("first_buy_ts", I, "control's first pre-news buy", unit="Unix s", leak="pre"), col("first_buy_price", FL, "its price", leak="pre"),
    col("size_usdc", FL, "its pre-news buy USDC", unit="USDC", leak="pre"), col("n_buys", I, "its pre-news buy legs", leak="pre")])
TABLES["weak_labels"] = dict(desc="Per wallet in Polymarket-v1: ACDC reconstruction and Inca rule (A6.9, E6), and Gate 1/2 counts (A16). Rule outputs, never merged with claims.", cols=[
    col("wallet", S, "address", pk=True), col("n_markets", I, "distinct markets (Polymarket-v1)"), col("n_fills", I, "legs"), col("buy_usdc", FL, "BUY USDC", unit="USDC"),
    col("sell_usdc", FL, "SELL USDC", unit="USDC"), col("first_fill_utc", T, "first Polymarket-v1 fill"), col("last_fill_utc", T, "last Polymarket-v1 fill"),
    col("n_longshots", I, "ACDC longshot bets (reconstruction)"), col("longshot_win_rate", FL, "share of longshots won"), col("n_longshot_types", I, "market types of longshots"),
    col("military_longshot_share", FL, "share on military slugs"), col("acdc_class", S, "reconstruction only: Orca or longshot_wallet; NOT a label (misses the A6.9 5% bar)", allowed="Orca;longshot_wallet", leak="label"),
    col("acdc_military_orca", B, "reconstruction only", leak="label"), col("realised_pnl", FL, "A6.9 realised PnL (no splits, merges, redemptions, fees)", unit="USDC"),
    col("inca_flag", B, "published rule only; broader than Inca's list (9,285 vs 39) (A12.4)", leak="label"),
    col("gate1_n", I, "positions with gate1 (precise version)", leak="label"), col("gate2a_n", I, "positions with gate2a (precise)", leak="label"),
    col("gate2b_n", I, "positions with gate2b (precise)", leak="label"), col("gate1_n_day", I, "gate1 (day version)", leak="label"),
    col("gate2a_n_day", I, "gate2a (day)", leak="label"), col("gate2b_n_day", I, "gate2b (day)", leak="label"),
    col("coordinated_rule_fired", B, "A13 rule fired for this wallet in any case, precise version (rule output; about 1/3 expected by chance; may include copy-traders; not an allegation)", leak="label"),
    col("coordinated_rule_fired_day", B, "same, day version", leak="label"),
    col("triggering_suspect", S, "documented wallet of the earliest trigger (precise version first)", leak="label"),
    col("placebo_rate", FL, "placebo-to-real ratio of that version", leak="label"),
    col("gate_scope", S, "case_placebo_or_twin_markets or not_in_case_placebo_or_twin_markets"),
    col("is_market_maker", B, "A34.1 reporting flag, NOT a label: >= 20 active (market, minute) pairs in case, twin and placebo markets with both tokens traded in > 50% of them"), col("evidence_grade", S, "E6", allowed="E6"), col("data_scope", S, "data window")])
TABLES["market_minutes"] = dict(desc="One row per market, version and UTC minute with fills, cut - 48 h to + 24 h, Yes token (A9.3, A10.2, A14).", cols=[
    col("market_set", S, "case, placebo or twin", allowed="case;placebo;twin", pk=True), col("case_id", S, "case", pk=True), col("condition_id", S, "market", pk=True),
    col("t_news_version", S, "A10.2", allowed=VER, pk=True), col("minute_ts", I, "minute start", unit="Unix s", pk=True), col("minute_utc", T, "minute start"),
    col("minutes_from_cut", I, "minutes relative to the cut (negative = before)", unit="minutes"), col("source", S, "sources in the minute"),
    col("n_fills_hf", I, "HF fills (taker legs)"), col("n_legs_api", I, "Data API legs"), col("usdc", FL, "volume", unit="USDC"), col("vwap", FL, "volume-weighted price"),
    col("last_price", FL, "last price"), col("taker_buy_usdc", FL, "aggressor buy volume (HF)", unit="USDC"), col("taker_sell_usdc", FL, "aggressor sell volume (HF)", unit="USDC"),
    col("n_wallets", I, "distinct wallets"), col("n_new_wallets", I, "wallets with first Polymarket-v1 fill in the previous 7 days"), col("n_wallets_age_unknown", I, "wallets with no Polymarket-v1 history"),
    col("t_news_reliable", B, "A29: the (matched) case's news time is reliable", leak="label")])
TABLES["contradictions"] = dict(desc="Places where the trades disagree with a claim (the claim is never edited), incl. the run-7 amount checks (gap > 10%).", cols=[
    col("contradiction_id", S, "CXnnn", pk=True), col("claim_id", S, "claim (FK claims)"), col("case_id", S, "case"), col("field", S, "claim field"),
    col("claimed_value", S, "value in the claim"), col("observed_value", S, "value observed"), col("evidence", S, "how it was observed"), col("evidence_file", S, "raw file or table"),
    col("phase", S, "run / phase"), col("found_utc", T, "when recorded")])
TABLES["edges"] = dict(desc="Money links between addresses from the seed sources (funding, Relay handoff, Safe owner, cash-out). Not expanded (A12.2).", cols=[
    col("edge_id", S, "row key EDnnnn", pk=True), col("src", S, "sender"), col("dst", S, "receiver"), col("kind", S, "link type"), col("case_id", S, "case"), col("chain", S, "chain or route"),
    col("amount_usd", FL, "amount", unit="USD"), col("tx", S, "transaction hash or evidence"), col("utc", T, "time (NULL where the source gives only a block number)"), col("block_number", I, "Polygon block number where the source gives one instead of a time"),
    col("source", S, "source file"), col("source_url", S, "source URL")])

TABLES["twin_markets"] = dict(desc="One row per twin market (A22): a resolved market of the same category, volume decile, duration band and year as a case market, in no claim; unmatched case-market rows have NULL twin fields.", cols=[
    col("twin_row_id", S, "row key TRnnnnn", pk=True), col("twin_id", S, "TWnnnnn; NULL when unmatched"), col("case_id", S, "matched case (FK cases)"),
    col("case_condition_id", S, "matched case market (FK markets)"), col("twin_condition_id", S, "twin market condition id (unique)"),
    col("category_refined", S, "Polymarket-v1 category shared by case market and twin"), col("twin_slug", S, "twin market slug"), col("twin_token_ids", S, "token ids"),
    col("twin_outcomes", S, "outcome labels"), col("twin_outcome", S, "winning outcome", leak="post"), col("twin_opens_utc", T, "opens_at"),
    col("twin_end_utc", T, "resolved_at else close_at"), col("twin_volume_usdc", FL, "Polymarket-v1 volume", unit="USDC", leak="post"),
    col("volume_decile", I, "case market's volume decile", leak="post"), col("duration_band", S, "case market's duration band"), col("resolution_year", I, "case market's end year"),
    col("twin_duration_band", S, "twin duration band"), col("twin_year", I, "twin end year"), col("relaxation", S, "A22 step or reason unmatched"),
    col("n_eligible", I, "twins eligible at that step"), col("case_tnews_position_day_ratio", FL, "position of t_news in the case market's life (0-1)"),
    col("case_tnews_position_precise_ratio", FL, "same for t_news_precise"), col("t_ref_day_utc", T, "twin cut time, day version", leak="label"),
    col("t_ref_precise_utc", T, "twin cut time, precise version", leak="label"), col("benchmark_split", S, "split of the matched case (A15)", allowed="train;test")])
TABLES["hard_negatives"] = dict(desc="One row per hard negative (A21): a position or wallet that matches the suspect profile but is a negative.", cols=[
    col("hard_negative_id", S, "row key HNnnnnnn", pk=True), col("rule", S, "A21 rule", allowed="lookalike_loser;cleared_case_lookalike;placebo_lookalike_winner;cleared_case_wallet", leak="label"),
    col("market_set", S, "case, twin, placebo, or NULL for wallet-level rows", allowed="case;twin;placebo"), col("case_id", S, "case"), col("condition_id", S, "market (NULL for wallet-level rows)"),
    col("asset_id", S, "token"), col("wallet", S, "wallet"), col("t_news_version", S, "A10.2", allowed=VER), col("pre_buy_usdc", FL, "pre-cut BUY", unit="USDC", leak="pre"),
    col("vwap_price_usdc_pre", FL, "pre-cut BUY VWAP", leak="pre"), col("profile_created_utc", T, "Gamma profile createdAt", leak="pre"),
    col("first_buy_utc", T, "first pre-cut BUY on the token", leak="pre"), col("won_post", B, "token won", leak="post")])
TABLES["claim_wallet_links"] = dict(desc="One row per (claim, wallet, link type): how a claim names a wallet (A20). Used for wallet_grade and label_strict.", cols=[
    col("claim_id", S, "claim (FK claims)", pk=True), col("wallet", S, "wallet", pk=True), col("case_id", S, "case", pk=True),
    col("link_type", S, "A20 link", allowed="address_in_claim;resolved_handle;label_source_handle;source_url;official_figures_match", pk=True),
    col("evidence_grade", S, "the claim's grade", allowed=GR, leak="label"), col("subject_type", S, "the claim's subject type")])


# PROTOCOL A24: build-side name -> released name (units in names). tables.py renames before casting.
RENAME = {'twin_markets': {'case_tnews_fraction_day': 'case_tnews_position_day_ratio', 'case_tnews_fraction_precise': 'case_tnews_position_precise_ratio'}, 'claims': {'run': 'run_number'}, 'markets': {'volume_gamma': 'volume_gamma_usdc'}, 'placebo_markets': {'placebo_volume': 'placebo_volume_usdc', 'case_volume': 'case_volume_usdc', 'case_tnews_fraction_day': 'case_tnews_position_day_ratio', 'case_tnews_fraction_precise': 'case_tnews_position_precise_ratio'}, 'fills': {'ts': 'ts_unix', 'price': 'price_usdc'}, 'positions': {'t_cut_ts': 't_cut_unix', 'first_buy_ts': 'first_buy_unix', 'last_buy_ts': 'last_buy_unix', 'first_buy_price': 'first_buy_price_usdc', 'max_buy_price': 'max_buy_price_usdc', 'vwap_pre': 'vwap_price_usdc_pre', 'first_fill_in_market_ts': 'first_fill_in_market_unix', 'f5_conviction': 'f5_conviction_ratio', 'vol_to_day': 'vol_to_day_usdc', 'lifetime_markets_v1': 'n_lifetime_markets_v1', 'f3_main_vwap': 'f3_main_vwap_price_usdc', 'pnl_post': 'pnl_usdc_post'}, 'episodes': {'prior_markets': 'n_prior_markets', 'first_price': 'first_price_usdc', 'vwap': 'vwap_price_usdc', 'max_price_paid': 'max_price_paid_usdc', 'fill_size_cv': 'fill_size_cv_ratio', 'size_price_slope': 'size_price_slope_usdc', 'follower_wallets_60m': 'n_follower_wallets_60m', 'pnl_post': 'pnl_usdc_post'}, 'controls': {'first_buy_ts': 'first_buy_unix', 'first_buy_price': 'first_buy_price_usdc'}, 'weak_labels': {'realised_pnl': 'realised_pnl_usdc', 'gate1_n': 'n_gate1', 'gate2a_n': 'n_gate2a', 'gate2b_n': 'n_gate2b', 'gate1_n_day': 'n_gate1_day', 'gate2a_n_day': 'n_gate2a_day', 'gate2b_n_day': 'n_gate2b_day'}, 'market_minutes': {'minute_ts': 'minute_unix', 'vwap': 'vwap_price_usdc', 'last_price': 'last_price_usdc'}}

for _t, _m in RENAME.items():
    for _c in TABLES[_t]["cols"]:
        if _c["name"] in _m:
            _c["source_name"] = _c["name"]; _c["name"] = _m[_c["name"]]
