# Field audit: Will the price of Solana be above $280 on October 10? (`ctrl_sol280_oct10`)

- Source: Polymarket Data API v2 /v2/trades (taker_only=true); condition `0x488494df640f0323aa8211f9771927f89969b795c8fa3f4422c28553414e7e3b`
- Pages fetched: 1 (last page has_more=False)
- Rows raw: **399**; duplicates removed (composite key transaction_hash, proxy_wallet, token_id, timestamp, size, price): **0**; rows clean: **399**
- Distinct wallets: 129; sides {'BUY': 318, 'SELL': 81}; outcomes {'No': 394, 'Yes': 5}
- Timestamp coverage: first 2025-10-09T05:03:01Z -> last 2025-10-10T14:50:44Z (span 33.8 h)
- Market open 2025-10-03T16:11:12Z (first trade 132.86 h after open); resolution 2025-10-10T18:08:34Z
- Trades after resolution (flagged, kept): **0**
- Largest gap between consecutive trades: 7.96 h (starting 2025-10-10T14:50:44Z)
- Batch checks: pages not sorted newest-first = 0; pages overlapping previous page's floor = max 0.0 s; pages with negative gap = 0
- Validity: outcome_index=999: 0; size<=0: 0; price outside [0,1]: 0; wrong condition: 0; token not in market: 0
- Completeness check: taker notional (size x price) $2,355,660 vs Gamma volume $2,367,013 -> ratio 0.995 (taker-only; varies with price level because makers on the complementary token pay 1-p)
- Completeness cross-check: maker+taker rows (taker_only=false) = 804, notional $4,695,234 -> ratio to Gamma volume **1.984** (~1.0 means no missing history)

## Missing values per field (null or empty string)

| field | missing |
|---|---|
| proxy_wallet | 0 |
| side | 0 |
| token_id | 0 |
| condition_id | 0 |
| size | 0 |
| price | 0 |
| timestamp | 0 |
| title | 0 |
| slug | 0 |
| icon | 0 |
| event_slug | 0 |
| outcome | 0 |
| outcome_index | 0 |
| name | 2 |
| pseudonym | 2 |
| bio | 383 |
| profile_image | 394 |
| profile_image_optimized | 399 |
| transaction_hash | 0 |
