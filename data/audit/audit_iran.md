# Field audit: US military action against Iran by Sunday? (`iran`)

- Source: Polymarket Data API v2 /v2/trades (taker_only=true); condition `0x4ec4d0c92654ccfed5b161c3ca1b4e3664608581b9d21d80939ce792a3a3b94f`
- Pages fetched: 3 (last page has_more=False)
- Rows raw: **2291**; duplicates removed (composite key transaction_hash, proxy_wallet, token_id, timestamp, size, price): **0**; rows clean: **2291**
- Distinct wallets: 914; sides {'BUY': 1714, 'SELL': 577}; outcomes {'No': 1376, 'Yes': 915}
- Timestamp coverage: first 2025-06-19T23:06:46Z -> last 2025-06-22T02:43:24Z (span 51.61 h)
- Market open 2025-06-19T22:45:31Z (first trade 0.35 h after open); resolution 2025-06-22T02:41:50Z
- Trades after resolution (flagged, kept): **1**
- Largest gap between consecutive trades: 0.49 h (starting 2025-06-20T22:41:04Z)
- Batch checks: pages not sorted newest-first = 0; pages overlapping previous page's floor = max 0.0 s; pages with negative gap = 0
- Validity: outcome_index=999: 0; size<=0: 0; price outside [0,1]: 0; wrong condition: 0; token not in market: 0
- Completeness check: taker notional (size x price) $1,392,584 vs Gamma volume $3,733,050 -> ratio 0.373 (taker-only; varies with price level because makers on the complementary token pay 1-p)
- Completeness cross-check: maker+taker rows (taker_only=false) = 6845, notional $3,773,242 -> ratio to Gamma volume **1.011** (~1.0 means no missing history)

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
| name | 69 |
| pseudonym | 109 |
| bio | 1832 |
| profile_image | 1604 |
| profile_image_optimized | 2291 |
| transaction_hash | 0 |
