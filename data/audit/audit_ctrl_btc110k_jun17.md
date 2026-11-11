# Field audit: Bitcoin above $110,000 on June 17? (`ctrl_btc110k_jun17`)

- Source: Polymarket Data API v2 /v2/trades (taker_only=true); condition `0xb65f93ec7a24727c41e0700e73cc67c26c722cd9752a958d5eb7fe5e1bf2be2b`
- Pages fetched: 2 (last page has_more=False)
- Rows raw: **1592**; duplicates removed (composite key transaction_hash, proxy_wallet, token_id, timestamp, size, price): **0**; rows clean: **1592**
- Distinct wallets: 479; sides {'BUY': 1296, 'SELL': 296}; outcomes {'No': 842, 'Yes': 750}
- Timestamp coverage: first 2025-06-10T18:37:30Z -> last 2025-06-17T17:06:41Z (span 166.49 h)
- Market open 2025-06-10T17:20:00Z (first trade 1.29 h after open); resolution 2025-06-17T18:02:27Z
- Trades after resolution (flagged, kept): **0**
- Largest gap between consecutive trades: 5.17 h (starting 2025-06-11T02:50:11Z)
- Batch checks: pages not sorted newest-first = 0; pages overlapping previous page's floor = max 0.0 s; pages with negative gap = 0
- Validity: outcome_index=999: 0; size<=0: 0; price outside [0,1]: 0; wrong condition: 0; token not in market: 0
- Completeness check: taker notional (size x price) $630,339 vs Gamma volume $979,889 -> ratio 0.643 (taker-only; varies with price level because makers on the complementary token pay 1-p)
- Completeness cross-check: maker+taker rows (taker_only=false) = 4009, notional $1,046,142 -> ratio to Gamma volume **1.068** (~1.0 means no missing history)

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
| name | 174 |
| pseudonym | 218 |
| bio | 1384 |
| profile_image | 1329 |
| profile_image_optimized | 1592 |
| transaction_hash | 0 |
