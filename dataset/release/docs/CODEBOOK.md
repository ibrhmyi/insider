# PMITC v1.0 codebook

Generated from `build/v1/schema.py`. Every released column is listed with its type, unit, allowed values, source and a
leakage note. Missing values are NULL (never empty strings). Timestamps are UTC (`timestamp[s, tz=UTC]` in parquet, ISO-8601 `...Z` in CSV).
Addresses are lower-case `0x` + 40 hex. `PK` marks primary-key columns.

Leakage notes: `pre` = computed only from data before the row's cut time; `post` = outcome column; `label` = label or target; `static` = known at creation; `meta` = id/provenance.

## cases

One row per case (underlying event). Derived from claims (build/build_cases.py) plus market and wallet counts.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `case_id` | string (PK) |  |  | claims | meta | case key |
| `title` | string |  |  | hand-written | meta | short title; no names of alleged traders |
| `category` | string |  |  | hand-written | meta | topic category |
| `platform` | string |  | polymarket, kalshi, both |  | meta | platforms in the case's claims, ';'-joined |
| `family` | string |  |  |  | meta | families in the case's claims, ';'-joined (PROTOCOL 2) |
| `case_grade` | string |  | E1, E2, E3, E4, E5, E6 |  | label | strongest evidence grade among the case's claims |
| `grades_present` | string |  |  |  | meta | all grades present, ';'-joined |
| `investigation_outcome` | string |  | sanctioned, charged, cleared_official, cleared_analyst, disputed, under_investigation, unresolved |  | label | PROTOCOL A9.2 |
| `event_date` | string |  |  |  | meta | earliest event_date as written (partial dates allowed, A6.3) |
| `event_date_earliest` | date |  |  |  | meta | earliest possible day of event_date |
| `event_date_precision` | string |  | day, month, quarter, year, range |  | meta | precision of event_date |
| `first_claim_date` | string |  |  |  | meta | earliest claim_date as written |
| `first_claim_date_earliest` | date |  |  |  | meta | earliest possible day of the first claim (used for the A15 time split) |
| `first_claim_date_precision` | string |  | day, month, quarter, year, range |  | meta | precision of first_claim_date |
| `n_claims` | int64 |  |  |  | meta | number of claims |
| `n_sources` | int64 |  |  |  | meta | distinct source URLs |
| `n_markets` | int64 |  |  |  | meta | case markets in markets |
| `n_wallets_suspected` | int64 |  |  |  | meta | suspected wallets (any trade confirmation) |
| `n_wallets_documented` | int64 |  |  |  | meta | suspected and trade_confirmed wallets (is_documented) |
| `n_wallets_candidate` | int64 |  |  |  | meta | A13 coordinated-buyer candidates |
| `max_amount_claimed_usd` | float64 | USD |  |  | meta | largest amount any claim states |
| `amounts_disagree` | bool |  |  |  | meta | claims state different amounts |
| `benchmark_split` | string |  | train, test |  | meta | PROTOCOL A15 split |
| `status_note` | string |  |  |  | meta | free note |

## claims

One row per claim: one statement by one source at one time (PROTOCOL 2, 6). Claims are never edited; contradictions go to contradictions.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `claim_id` | string (PK) |  |  |  | meta | CLnnnn, stable |
| `case_id` | string |  |  |  | meta | case (FK cases) |
| `platform` | string |  | polymarket, kalshi, both |  | meta | platform |
| `family` | string |  |  |  | meta | family (PROTOCOL 2) |
| `subject_type` | string |  | address, handle, account, cluster, market, aggregate, notice |  | meta | what the claim points at |
| `subject` | string |  |  |  | meta | subject as the source gives it (prefixes kept as prefixes); notice or release ID for official notices; never a personal name |
| `claim_text` | string |  |  |  | meta | our paraphrase, under 30 words |
| `evidence_grade` | string |  | E1, E2, E3, E4, E5, E6 |  | label | PROTOCOL 5 (A12.1 for employer findings) |
| `stance` | string |  | alleges, disputes, clears, context |  | meta | PROTOCOL A9.1 |
| `verified` | string |  | true, pending, false |  | meta | A6.1: true = page text read and supports the claim |
| `run` | int64 |  |  |  | meta | collection run that added the row (A6.2) |
| `amount_claimed_usd` | float64 | USD |  |  | meta | amount the source states |
| `n_accounts_claimed` | int64 |  |  |  | meta | accounts the source names |
| `event_date` | string |  |  |  | meta | event date as written (A6.3) |
| `claim_date` | string |  |  |  | meta | claim date as written (A6.3) |
| `source_class` | string |  | S1, S2, S3, S4, S5 |  | meta | PROTOCOL 3 |
| `source_name` | string |  |  |  | meta | outlet or author ('X via Y') |
| `url` | string |  |  |  | meta | source URL; may contain names chosen by the source (official file names, article slugs) |
| `post_url` | string |  |  |  | meta | X post URL recovered from the page (from notes) |
| `accessed_date` | date |  |  |  | meta | date accessed |
| `extractor` | string |  |  |  | meta | who extracted the row |
| `notes` | string |  |  |  | meta | free notes |

## wallets

One row per (wallet, case) label. Labels are allegations by the named source, not findings.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `wallet` | string (PK) |  |  |  | meta | Polymarket proxy (or owner key) address, lower-case 0x + 40 hex |
| `case_id` | string (PK) |  |  |  | meta | case (FK cases) |
| `handle` | string |  |  |  | meta | public username or label as the source gives it |
| `role` | string |  |  |  | meta | trader, owner_key, ... |
| `label_tier` | string |  |  |  | meta | L2 official-case wallet, L3 analyst full address / resolved handle, L4 cluster member, L4_coordinated (A13 rule), A ambiguous, NC negative control, M manipulation |
| `polarity` | string |  | suspected, ambiguous, negative_control, manipulation, context, candidate |  | label | label polarity |
| `trade_confirmed` | bool |  |  |  | label | A12.5: >= 1 fill in a market of its case (from fills) |
| `is_documented` | bool |  |  |  | label | polarity = suspected and trade_confirmed (default positive label) |
| `is_candidate_coordinated` | bool |  |  |  | label | A13 coordinated-buyer candidate (never documented) |
| `doc_grade` | string |  | E1, E2, E3, E4, E5, E6 |  | label | strongest grade among the case's claims about accounts, addresses, handles or clusters (not aggregates or markets) |
| `source` | string |  |  |  | meta | file or method the row came from |
| `source_url` | string |  |  |  | meta | source URL |
| `verification` | string |  |  |  | meta | how the address was obtained |
| `first_case_fill_utc` | timestamp |  |  | fills | post | first fill in a case market |
| `case_buy_usdc` | float64 | USD |  |  | post | BUY USDC in case markets, all time |
| `case_redeem_usdc` | float64 | USD |  |  | post | redemptions in case markets (Data API) |
| `notes` | string |  |  |  | meta | free notes |

## markets

One row per (case, market). Ladders are full Gamma events (A6.5). Titles withheld where they name the alleged trader (A12.6).

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `case_id` | string (PK) |  |  |  | meta | case (FK cases) |
| `condition_id` | string (PK) |  |  |  | meta | market condition id, lower-case hex |
| `question` | string |  |  |  | static | market question; NULL when title_withheld |
| `slug` | string |  |  |  | meta | market slug; NULL when title_withheld |
| `event_id` | string |  |  |  | meta | Gamma event id (or withheld-week-<date>) |
| `event_slug` | string |  |  |  | meta | Gamma event slug; NULL when title_withheld |
| `selected_as` | string |  |  |  | meta | how the market was selected |
| `found_via` | string |  |  |  | meta | A6.5 method |
| `reason` | string |  |  |  | meta | why the market belongs to the case |
| `selection_level` | string |  | event, market, ladder |  | meta | event, market or ladder |
| `created_utc` | timestamp |  |  |  | static | market creation |
| `deadline_utc` | timestamp |  |  |  | static | market end date |
| `resolved_utc` | timestamp |  |  |  | post | resolution / close time |
| `outcome` | string |  |  |  | post | winning outcome label |
| `outcomes` | string |  |  |  | meta | outcome labels, ';'-joined |
| `token_ids` | string |  |  |  | meta | outcome token ids, ';'-joined |
| `neg_risk` | bool |  |  |  | meta | Gamma negRisk |
| `volume_gamma` | float64 | USD |  |  | post | Gamma volume |
| `volume_hf_usdc` | float64 | USD |  |  | post | Polymarket-v1 USDC volume |
| `in_hf` | bool |  |  |  | meta | market has fills in Polymarket-v1 |
| `ladder_rank` | int64 |  |  |  | static | deadline rank within the event (1 = earliest) |
| `t_news_utc` | timestamp |  |  |  | label | day-level news time (A6.6, A7) |
| `t_news_method` | string |  |  |  | meta | claim_min, ff_tier1, ff_tier3 |
| `t_news_precision` | string |  | day, month, quarter, year, range, timestamp |  | meta | precision of t_news_utc |
| `t_news_precise_utc` | timestamp |  |  |  | label | exact news time (A10); equals t_news_utc where no exact time is sourced |
| `t_news_precise_precision` | string |  | minute, quarter_hour, hour, window, day_fallback |  | meta | A10.1 |
| `t_news_precise_source` | string |  |  |  | meta | URL of the event_times row, or day_fallback |
| `t_news_precise_verified` | string |  |  |  | meta | verified flag of the event_times row |
| `title_withheld` | bool |  |  |  | meta | A12.6 |
| `is_placebo_market` | bool |  |  |  | meta | always false here |
| `ff_tier` | string |  |  |  | meta | ForesightFlow tier if listed |
| `ff_tier2_tnews` | timestamp |  |  |  | meta | ForesightFlow tier-2 proxy (stored, not used) |

## placebo_markets

One row per placebo market (A14) with its matched case market; case-market rows that could not be matched appear with NULL placebo fields.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `placebo_id` | string |  |  |  | meta | PLnnnnn; NULL for unmatched case-market rows |
| `case_id` | string |  |  |  | meta | matched case (FK cases) |
| `case_condition_id` | string |  |  |  | meta | matched case market (FK markets) |
| `placebo_condition_id` | string |  |  |  | meta | placebo market condition id (unique) |
| `placebo_category` | string |  | crypto_price, weather_reading |  | meta | A14 category |
| `placebo_slug` | string |  |  |  | meta | placebo market slug |
| `placebo_token_ids` | string |  |  |  | meta | outcome token ids |
| `placebo_outcomes` | string |  |  |  | meta | outcome labels |
| `placebo_outcome` | string |  |  |  | post | winning outcome |
| `placebo_opens_utc` | timestamp |  |  |  | meta | opens_at |
| `placebo_close_utc` | timestamp |  |  |  | meta | close_at |
| `placebo_resolved_utc` | timestamp |  |  |  | post | resolved_at (often NULL for weather) |
| `placebo_end_utc` | timestamp |  |  |  | meta | resolved_at else close_at (A14.1) |
| `placebo_volume` | float64 | USD |  |  | post | Polymarket-v1 USDC volume |
| `case_volume` | float64 | USD |  |  | post | case-market volume used for matching |
| `case_volume_basis` | string |  | hf, gamma |  | meta | hf or gamma |
| `volume_decile` | int64 |  |  |  | post | case market's volume decile (1-10) |
| `duration_band` | string |  |  |  | meta | case market's duration band |
| `resolution_month` | string |  |  |  | meta | case market's end month YYYY-MM |
| `placebo_duration_band` | string |  |  |  | meta | placebo duration band |
| `placebo_resolution_month` | string |  |  |  | meta | placebo end month |
| `relaxation` | string |  |  |  | meta | A14 relaxation step or reason unmatched |
| `n_eligible` | int64 |  |  |  | meta | placebos eligible at that step |
| `case_tnews_fraction_day` | float64 |  |  |  | meta | position of t_news in the case market's life (0-1) |
| `case_tnews_fraction_precise` | float64 |  |  |  | meta | same for t_news_precise |
| `t_ref_day_utc` | timestamp |  |  |  | label | placebo cut time, day version (A14) |
| `t_ref_precise_utc` | timestamp |  |  |  | label | placebo cut time, precise version |
| `benchmark_split` | string |  | train, test |  | meta | split of the matched case (A15) |

## fills

Every leg of every fill in case and placebo markets, plus every leg of labelled wallets elsewhere. Parquet only (split into parts).

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `market_set` | string |  | case, placebo, label_other |  | meta | which part of the fills table |
| `leg_id` | string (PK) |  |  |  | meta | unique leg id: <fill_id>:t/m (HF) or the API row id |
| `source` | string |  | hf_polymarket_v1, data_api_v2 |  | meta | A6.4 |
| `fill_id` | string |  |  |  | meta | HF <day file>:<row>; API <tx hash>:<row index> |
| `tx_hash` | string |  |  |  | meta | transaction hash (Data API rows only) |
| `ts` | int64 | Unix seconds UTC |  |  | meta | block time |
| `ts_utc` | timestamp |  |  |  | meta | block time |
| `condition_id` | string |  |  |  | meta | market |
| `asset_id` | string |  |  |  | meta | outcome token id |
| `outcome_label` | string |  |  |  | meta | label of the traded token |
| `outcome_seq` | int64 |  |  |  | meta | outcome position (HF 1/2; API 0/1) |
| `price` | float64 | USDC |  |  | meta | price per share |
| `usdc` | float64 | USDC |  |  | meta | notional |
| `shares` | float64 | shares |  |  | meta | shares (HF: usdc / price) |
| `fee_usdc` | float64 | USDC |  |  | meta | fee (HF only) |
| `wallet` | string |  |  |  | meta | wallet this leg belongs to |
| `wallet_role` | string |  | maker, taker, unknown |  | meta | maker, taker, unknown (API) |
| `wallet_side` | string |  | BUY, SELL |  | meta | BUY or SELL of this token by this wallet (A6.4) |
| `aggressor_side` | string |  | BUY, SELL |  | meta | taker_direction (HF only) |
| `maker` | string |  |  |  | meta | maker address (HF only) |
| `taker` | string |  |  |  | meta | taker address (HF only) |
| `market_slug` | string |  |  |  | meta | market slug; NULL for withheld markets |

## positions

All-buyer positions before the cut (C2): the full population a detector must search, case and placebo markets.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `market_set` | string (PK) |  | case, placebo |  | meta | case or placebo |
| `case_id` | string (PK) |  |  |  | meta | case (placebo: matched case) |
| `condition_id` | string (PK) |  |  |  | meta | market |
| `asset_id` | string (PK) |  |  |  | meta | outcome token |
| `wallet` | string (PK) |  |  |  | meta | buyer |
| `t_news_version` | string (PK) |  | day, precise |  | meta | A10.2 |
| `outcome_label` | string |  |  |  | meta | token label |
| `t_cut_ts` | int64 | Unix s |  |  | label | cut time: t_news / t_news_precise (case) or t_ref (placebo) |
| `is_shortest_sufficient` | bool |  |  |  | post | this market is its event's shortest deadline that resolved Yes |
| `n_buy_fills_pre` | int64 |  |  |  | pre | BUY legs before the cut |
| `buy_usdc_pre` | float64 | USDC |  |  | pre | BUY USDC before the cut |
| `buy_shares_pre` | float64 |  |  |  | pre | BUY shares before the cut |
| `first_buy_ts` | int64 | Unix s |  |  | pre | first pre-cut BUY |
| `last_buy_ts` | int64 | Unix s |  |  | pre | last pre-cut BUY |
| `first_buy_price` | float64 |  |  |  | pre | price of the first pre-cut BUY |
| `max_buy_price` | float64 |  |  |  | pre | highest pre-cut BUY price |
| `median_buy_fill_usdc` | float64 | USDC |  |  | pre | median pre-cut BUY leg |
| `sell_usdc_pre` | float64 | USDC |  |  | pre | SELL USDC before the cut |
| `sell_shares_pre` | float64 |  |  |  | pre | SELL shares before the cut |
| `taker_share_pre` | float64 |  |  |  | pre | share of pre-cut BUY legs as taker (HF only) |
| `source_pre` | string |  |  |  | pre | sources of pre-cut legs |
| `vwap_pre` | float64 |  |  |  | pre | pre-cut BUY VWAP |
| `is_main_side` | bool |  |  |  | pre | token with the wallet's largest pre-cut BUY in this market |
| `account_age_days_at_first_buy` | float64 | days |  |  | pre | days from first Polymarket-v1 fill to first pre-cut BUY (NULL if no v1 history) |
| `first_fill_in_market_ts` | int64 | Unix s |  |  | pre | first pre-cut fill in this market (any side) |
| `market_usdc_pre` | float64 | USDC |  |  | pre | all pre-cut USDC in this market (both sides, both tokens) |
| `market_buy_usdc_pre` | float64 | USDC |  |  | pre | pre-cut BUY USDC in this market, both tokens (F4) |
| `f5_conviction` | float64 |  |  |  | pre | F5 /net YES USDC/ / gross USDC, pre-cut |
| `vol_to_day` | float64 | USDC |  |  | pre | Polymarket-v1 volume, all markets, up to the end of the cut's UTC day (A16 F2 denominator; includes the rest of that day as frozen v1 does) |
| `lifetime_markets_v1` | int64 |  |  |  | pre | lifetime distinct Polymarket-v1 markets (F2 market branch, as frozen v1; A16.1: ex-post count that can only understate the flag) |
| `f1_days_account_to_first_fill` | float64 | days |  |  | pre | F1 freshness (A16 substitution) |
| `f2_share` | float64 |  |  |  | pre | F2 focus share |
| `f3_main_vwap` | float64 |  |  |  | pre | F3 main-side VWAP |
| `f6_hours_median_buy_to_tnews` | float64 | hours |  |  | pre | F6 hours from USD-weighted median main-side buy to the cut |
| `flag_f1` | bool |  |  |  | pre | F1 <= 7 days |
| `flag_f2` | bool |  |  |  | pre | F2 share >= 0.8 or markets <= 2 |
| `flag_f3` | bool |  |  |  | pre | F3 <= 0.35 |
| `flag_f4` | bool |  |  |  | pre | F4 >= $2,500 |
| `flag_f5` | bool |  |  |  | pre | F5 >= 0.8 |
| `flag_f6` | bool |  |  |  | pre | F6 <= 72 h |
| `gate1_score` | int64 |  |  |  | pre | number of F1-F6 flags (NULL outside Polymarket-v1) |
| `gate1` | bool |  |  |  | label | gate1_score >= 4 (A16) |
| `gate2a` | bool |  |  |  | pre | Signal A: a later pre-cut BUY at >= 1.5x the first price |
| `gate2b` | bool |  |  |  | post | Signal B: largest pre-cut BUY in the event is on the shortest Yes deadline, Yes token (uses resolution: label only) |
| `is_documented` | bool |  |  |  | label | wallet is documented for this case |
| `doc_grade` | string |  | E1, E2, E3, E4, E5, E6 |  | label | wallet's doc_grade |
| `is_candidate_coordinated` | bool |  |  |  | label | A13 candidate for this case |
| `is_control` | bool |  |  |  | label | selected as a matched control in this market, version |
| `is_placebo_market` | bool |  |  |  | label | market_set = placebo |
| `buy_usdc_post` | float64 | USDC |  |  | post | BUY USDC at or after the cut |
| `buy_shares_post` | float64 |  |  |  | post | BUY shares at or after the cut |
| `sell_usdc_post` | float64 | USDC |  |  | post | SELL USDC at or after the cut |
| `sell_shares_post` | float64 |  |  |  | post | SELL shares at or after the cut |
| `won_post` | bool |  |  |  | post | token won |
| `pnl_post` | float64 | USDC |  |  | post | sells - buys + winning shares held (no redemptions, fees) |

## episodes

Per (wallet, market, token) episode of documented wallets and their matched controls; pre-news features, then _post outcomes.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `row_id` | string |  |  |  | meta | row id within version |
| `episode_id` | string |  |  |  | meta | stable id of a documented episode (hash of case, wallet, market, token); NULL on control rows |
| `t_news_version` | string |  | day, precise |  | meta | A10.2 |
| `role` | string |  |  |  | label | suspected, control_same_side, control_other_side_large_buyer |
| `control_of` | string |  |  |  | meta | row_id... of the episode this control is matched to (its episode_id via controls) |
| `case_id` | string |  |  |  | meta | case |
| `condition_id` | string |  |  |  | meta | market |
| `event_slug` | string |  |  |  | meta | Gamma event |
| `asset_id` | string |  |  |  | meta | token |
| `outcome_label` | string |  |  |  | meta | token label |
| `wallet` | string |  |  |  | meta | wallet |
| `source_pre` | string |  |  |  | pre | source of pre-news legs |
| `account_age_days_at_first_buy` | float64 | days |  |  | pre | days from first Polymarket-v1 fill to first pre-news buy |
| `prior_markets` | int64 |  |  |  | pre | distinct Polymarket-v1 markets before the first buy |
| `prior_net_long_win_rate` | float64 |  |  |  | pre | win rate on earlier resolved net-long positions |
| `case_share_of_lifetime_volume` | float64 |  |  |  | post | case volume / lifetime Polymarket-v1 volume (uses lifetime: ex-post denominator) |
| `first_price` | float64 |  |  |  | pre | first pre-news buy price |
| `vwap` | float64 |  |  |  | pre | pre-news buy VWAP |
| `max_price_paid` | float64 |  |  |  | pre | max pre-news price |
| `n_buy_fills` | int64 |  |  |  | pre | pre-news buy legs |
| `median_fill_usdc` | float64 | USDC |  |  | pre | median pre-news buy leg |
| `fill_size_cv` | float64 |  |  |  | pre | coefficient of variation of pre-news buy legs |
| `taker_share` | float64 |  |  |  | pre | share of pre-news buys as taker |
| `hour_of_day_first_buy` | int64 |  |  |  | pre | UTC hour of first buy |
| `pre_buy_usdc` | float64 | USDC |  |  | pre | pre-news buy USDC |
| `pre_buy_shares` | float64 |  |  |  | pre | pre-news buy shares |
| `signal_a_rebuy_1_5x` | bool |  |  |  | pre | Signal A |
| `size_price_slope` | float64 |  |  |  | pre | slope of buy size on price |
| `hours_last_buy_to_tnews` | float64 | hours |  |  | pre | hours from last pre-news buy to t_news |
| `ladder_rank` | int64 |  |  |  | static | deadline rank |
| `is_shortest_sufficient` | bool |  |  |  | post | market is the event's shortest deadline that resolved Yes |
| `share_on_this_ladder_market` | float64 |  |  |  | label | share of event buys on this market. LEAKY for suspected-vs-control tasks: controls are matched one market at a time, so it is 1 for every control |
| `hours_first_buy_to_tnews` | float64 | hours |  |  | pre | hours from first buy to t_news |
| `hours_funding_to_first_trade` | float64 |  |  |  | pre | empty: money graph not run (A12.2) |
| `funding_source_type` | string |  |  |  | pre | empty (A12.2) |
| `funder_shared_with_labelled` | bool |  |  |  | pre | empty (A12.2) |
| `follower_wallets_60m` | int64 |  |  |  | post | other wallets buying the token within 60 min after a pre-news buy (may extend past t_news) |
| `follower_buy_usdc_60m` | float64 | USDC |  |  | post | their buy USDC (may extend past t_news) |
| `share_sold_before_resolution_post` | float64 |  |  |  | post | share of shares sold before resolution |
| `won_post` | bool |  |  |  | post | token won |
| `pnl_post` | float64 | USDC |  |  | post | realised + held winning value |
| `redemption_delay_hours_post` | float64 | hours |  |  | post | hours from resolution to first redemption (suspected only) |

## controls

Matched controls (A6.10, seed 192) with relaxation flags, per t_news version.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `t_news_version` | string (PK) |  | day, precise |  | meta | A10.2 |
| `episode_id` | string (PK) |  |  |  | meta | documented episode |
| `wallet` | string (PK) |  |  |  | meta | control wallet |
| `control_type` | string (PK) |  | same_side, other_side_large_buyer |  | meta | same_side or other_side_large_buyer |
| `relaxation` | string |  | base, window_72h, price_0.10, size_0.25_4x |  | meta | A6.10 relaxation used |
| `n_eligible` | int64 |  |  |  | meta | eligible controls at that step |
| `case_id` | string |  |  |  | meta | case |
| `condition_id` | string |  |  |  | meta | market |
| `asset_id` | string |  |  |  | meta | token |
| `outcome_label` | string |  |  |  | meta | token label |
| `first_buy_ts` | int64 | Unix s |  |  | pre | control's first pre-news buy |
| `first_buy_price` | float64 |  |  |  | pre | its price |
| `size_usdc` | float64 | USDC |  |  | pre | its pre-news buy USDC |
| `n_buys` | int64 |  |  |  | pre | its pre-news buy legs |

## weak_labels

Per wallet in Polymarket-v1: ACDC reconstruction and Inca rule (A6.9, E6), and Gate 1/2 counts (A16). Rule outputs, never merged with claims.

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `wallet` | string (PK) |  |  |  | meta | address |
| `n_markets` | int64 |  |  |  | meta | distinct markets (Polymarket-v1) |
| `n_fills` | int64 |  |  |  | meta | legs |
| `buy_usdc` | float64 | USDC |  |  | meta | BUY USDC |
| `sell_usdc` | float64 | USDC |  |  | meta | SELL USDC |
| `first_fill_utc` | timestamp |  |  |  | meta | first Polymarket-v1 fill |
| `last_fill_utc` | timestamp |  |  |  | meta | last Polymarket-v1 fill |
| `n_longshots` | int64 |  |  |  | meta | ACDC longshot bets (reconstruction) |
| `longshot_win_rate` | float64 |  |  |  | meta | share of longshots won |
| `n_longshot_types` | int64 |  |  |  | meta | market types of longshots |
| `military_longshot_share` | float64 |  |  |  | meta | share on military slugs |
| `acdc_class` | string |  | Orca, longshot_wallet |  | label | reconstruction only: Orca or longshot_wallet; NOT a label (misses the A6.9 5% bar) |
| `acdc_military_orca` | bool |  |  |  | label | reconstruction only |
| `realised_pnl` | float64 | USDC |  |  | meta | A6.9 realised PnL (no splits, merges, redemptions, fees) |
| `inca_flag` | bool |  |  |  | label | published rule only; broader than Inca's list (9,285 vs 39) (A12.4) |
| `gate1_n` | int64 |  |  |  | label | positions with gate1 (precise version) |
| `gate2a_n` | int64 |  |  |  | label | positions with gate2a (precise) |
| `gate2b_n` | int64 |  |  |  | label | positions with gate2b (precise) |
| `gate1_n_day` | int64 |  |  |  | label | gate1 (day version) |
| `gate2a_n_day` | int64 |  |  |  | label | gate2a (day) |
| `gate2b_n_day` | int64 |  |  |  | label | gate2b (day) |
| `gate_scope` | string |  |  |  | meta | case_or_placebo_markets or not_in_case_or_placebo_markets |
| `evidence_grade` | string |  | E6 |  | meta | E6 |
| `data_scope` | string |  |  |  | meta | data window |

## market_minutes

One row per market, version and UTC minute with fills, cut - 48 h to + 24 h, Yes token (A9.3, A10.2, A14).

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `market_set` | string (PK) |  | case, placebo |  | meta | case or placebo |
| `case_id` | string (PK) |  |  |  | meta | case |
| `condition_id` | string (PK) |  |  |  | meta | market |
| `t_news_version` | string (PK) |  | day, precise |  | meta | A10.2 |
| `minute_ts` | int64 (PK) | Unix s |  |  | meta | minute start |
| `minute_utc` | timestamp |  |  |  | meta | minute start |
| `minutes_from_cut` | int64 | minutes |  |  | meta | minutes relative to the cut (negative = before) |
| `source` | string |  |  |  | meta | sources in the minute |
| `n_fills_hf` | int64 |  |  |  | meta | HF fills (taker legs) |
| `n_legs_api` | int64 |  |  |  | meta | Data API legs |
| `usdc` | float64 | USDC |  |  | meta | volume |
| `vwap` | float64 |  |  |  | meta | volume-weighted price |
| `last_price` | float64 |  |  |  | meta | last price |
| `taker_buy_usdc` | float64 | USDC |  |  | meta | aggressor buy volume (HF) |
| `taker_sell_usdc` | float64 | USDC |  |  | meta | aggressor sell volume (HF) |
| `n_wallets` | int64 |  |  |  | meta | distinct wallets |
| `n_new_wallets` | int64 |  |  |  | meta | wallets with first Polymarket-v1 fill in the previous 7 days |
| `n_wallets_age_unknown` | int64 |  |  |  | meta | wallets with no Polymarket-v1 history |

## contradictions

Places where the trades disagree with a claim (the claim is never edited), incl. the run-7 amount checks (gap > 10%).

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `contradiction_id` | string (PK) |  |  |  | meta | CXnnn |
| `claim_id` | string |  |  |  | meta | claim (FK claims) |
| `case_id` | string |  |  |  | meta | case |
| `field` | string |  |  |  | meta | claim field |
| `claimed_value` | string |  |  |  | meta | value in the claim |
| `observed_value` | string |  |  |  | meta | value observed |
| `evidence` | string |  |  |  | meta | how it was observed |
| `evidence_file` | string |  |  |  | meta | raw file or table |
| `phase` | string |  |  |  | meta | run / phase |
| `found_utc` | timestamp |  |  |  | meta | when recorded |

## edges

Money links between addresses from the seed sources (funding, Relay handoff, Safe owner, cash-out). Not expanded (A12.2).

| column | type | unit | allowed values | source | leakage | description |
|---|---|---|---|---|---|---|
| `src` | string |  |  |  | meta | sender |
| `dst` | string |  |  |  | meta | receiver |
| `kind` | string |  |  |  | meta | link type |
| `case_id` | string |  |  |  | meta | case |
| `chain` | string |  |  |  | meta | chain or route |
| `amount_usd` | float64 | USD |  |  | meta | amount |
| `tx` | string |  |  |  | meta | transaction hash or evidence |
| `utc` | timestamp |  |  |  | meta | time (NULL where the source gives only a block number) |
| `block_number` | int64 |  |  |  | meta | Polygon block number where the source gives one instead of a time |
| `source` | string |  |  |  | meta | source file |
| `source_url` | string |  |  |  | meta | source URL |

