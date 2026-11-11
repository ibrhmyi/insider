# Field audit: Bitcoin Up or Down - October 14, 5PM ET (`ctrl_btcupdown_oct14`)

- Source: Polymarket Data API v2 /v2/trades (taker_only=true); condition `0xe0999c0d75900f3d80ed22b976b4ba1e95dce3efd58397ac7d368e02e2617036`
- Pages fetched: 3 (last page has_more=False)
- Rows raw: **2682**; duplicates removed (composite key transaction_hash, proxy_wallet, token_id, timestamp, size, price): **0**; rows clean: **2682**
- Distinct wallets: 196; sides {'BUY': 1749, 'SELL': 933}; outcomes {'Up': 1366, 'Down': 1316}
- Timestamp coverage: first 2025-10-14T12:12:13Z -> last 2025-10-14T23:08:49Z (span 10.94 h)
- Market open 2025-10-12T21:01:09Z (first trade 39.18 h after open); resolution 2025-10-14T23:11:39Z
- Trades after resolution (flagged, kept): **0**
- Largest gap between consecutive trades: 2.36 h (starting 2025-10-14T14:54:51Z)
- Batch checks: pages not sorted newest-first = 0; pages overlapping previous page's floor = max 0.0 s; pages with negative gap = 0
- Validity: outcome_index=999: 0; size<=0: 0; price outside [0,1]: 0; wrong condition: 0; token not in market: 0
- Completeness check: taker notional (size x price) $462,746 vs Gamma volume $920,452 -> ratio 0.503 (taker-only; varies with price level because makers on the complementary token pay 1-p)
- Completeness cross-check: maker+taker rows (taker_only=false) = 7187, notional $923,510 -> ratio to Gamma volume **1.003** (~1.0 means no missing history)

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
| name | 101 |
| pseudonym | 103 |
| bio | 1518 |
| profile_image | 1779 |
| profile_image_optimized | 2682 |
| transaction_hash | 0 |
