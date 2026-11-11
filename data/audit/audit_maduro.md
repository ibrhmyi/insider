# Field audit: Maduro out by January 31, 2026? (`maduro`)

- Source: Polymarket Data API v2 /v2/trades (taker_only=true); condition `0x580adc1327de9bf7c179ef5aaffa3377bb5cb252b7d6390b027172d43fd6f993`
- Pages fetched: 10 (last page has_more=False)
- Rows raw: **9367**; duplicates removed (composite key transaction_hash, proxy_wallet, token_id, timestamp, size, price): **0**; rows clean: **9367**
- Distinct wallets: 3533; sides {'BUY': 6709, 'SELL': 2658}; outcomes {'No': 5351, 'Yes': 4016}
- Timestamp coverage: first 2025-12-12T01:20:24Z -> last 2026-01-03T12:13:39Z (span 538.89 h)
- Market open 2025-12-12T00:27:56Z (first trade 0.87 h after open); resolution 2026-01-03T12:14:07Z
- Trades after resolution (flagged, kept): **0**
- Largest gap between consecutive trades: 3.48 h (starting 2025-12-12T05:40:46Z)
- Batch checks: pages not sorted newest-first = 0; pages overlapping previous page's floor = max 0.0 s; pages with negative gap = 0
- Validity: outcome_index=999: 0; size<=0: 0; price outside [0,1]: 0; wrong condition: 0; token not in market: 0
- Completeness check: taker notional (size x price) $4,540,177 vs Gamma volume $10,966,929 -> ratio 0.414 (taker-only; varies with price level because makers on the complementary token pay 1-p)
- Completeness cross-check: maker+taker rows (taker_only=false) = 26404, notional $9,706,735 -> ratio to Gamma volume **0.885** (~1.0 means no missing history)

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
| name | 1011 |
| pseudonym | 1217 |
| bio | 8296 |
| profile_image | 7427 |
| profile_image_optimized | 9367 |
| transaction_hash | 0 |
