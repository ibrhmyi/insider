# Field audit: Will María Corina Machado win the Nobel Peace Prize in 2025? (`nobel`)

- Source: Polymarket Data API v2 /v2/trades (taker_only=true); condition `0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d`
- Pages fetched: 7 (last page has_more=False)
- Rows raw: **6143**; duplicates removed (composite key transaction_hash, proxy_wallet, token_id, timestamp, size, price): **0**; rows clean: **6143**
- Distinct wallets: 3028; sides {'BUY': 3960, 'SELL': 2183}; outcomes {'No': 3997, 'Yes': 2146}
- Timestamp coverage: first 2025-07-08T18:41:57Z -> last 2025-10-10T12:05:56Z (span 2249.4 h)
- Market open 2025-07-08T15:43:10Z (first trade 2.98 h after open); resolution 2025-10-10T11:03:30Z
- Trades after resolution (flagged, kept): **16**
- Largest gap between consecutive trades: 108.21 h (starting 2025-07-23T03:34:09Z)
- Batch checks: pages not sorted newest-first = 0; pages overlapping previous page's floor = max 0.0 s; pages with negative gap = 0
- Validity: outcome_index=999: 0; size<=0: 0; price outside [0,1]: 0; wrong condition: 0; token not in market: 0
- Completeness check: taker notional (size x price) $1,102,032 vs Gamma volume $2,243,006 -> ratio 0.491 (taker-only; varies with price level because makers on the complementary token pay 1-p)
- Completeness cross-check: maker+taker rows (taker_only=false) = 15598, notional $2,156,470 -> ratio to Gamma volume **0.961** (~1.0 means no missing history)

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
| name | 286 |
| pseudonym | 407 |
| bio | 5430 |
| profile_image | 5119 |
| profile_image_optimized | 6143 |
| transaction_hash | 0 |
