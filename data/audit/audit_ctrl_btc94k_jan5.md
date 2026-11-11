# Field audit: Will the price of Bitcoin be above $94,000 on January 5? (`ctrl_btc94k_jan5`)

- Source: Polymarket Data API v2 /v2/trades (taker_only=true); condition `0xe4a7020ebf8d1b55246fff86b10351a4bbced6e394ba4a4ffd8438f1771e58fc`
- Pages fetched: 5 (last page has_more=False)
- Rows raw: **4376**; duplicates removed (composite key transaction_hash, proxy_wallet, token_id, timestamp, size, price): **0**; rows clean: **4376**
- Distinct wallets: 869; sides {'BUY': 2747, 'SELL': 1629}; outcomes {'Yes': 2781, 'No': 1595}
- Timestamp coverage: first 2025-12-29T19:02:05Z -> last 2026-01-05T19:17:01Z (span 168.25 h)
- Market open 2025-12-29T17:01:12Z (first trade 2.01 h after open); resolution 2026-01-05T19:17:25Z
- Trades after resolution (flagged, kept): **0**
- Largest gap between consecutive trades: 17.52 h (starting 2025-12-31T23:32:25Z)
- Batch checks: pages not sorted newest-first = 0; pages overlapping previous page's floor = max 0.0 s; pages with negative gap = 0
- Validity: outcome_index=999: 0; size<=0: 0; price outside [0,1]: 0; wrong condition: 0; token not in market: 0
- Completeness check: taker notional (size x price) $406,741 vs Gamma volume $1,165,857 -> ratio 0.349 (taker-only; varies with price level because makers on the complementary token pay 1-p)
- Completeness cross-check: maker+taker rows (taker_only=false) = 10292, notional $1,158,375 -> ratio to Gamma volume **0.994** (~1.0 means no missing history)

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
| name | 189 |
| pseudonym | 219 |
| bio | 4104 |
| profile_image | 4012 |
| profile_image_optimized | 4376 |
| transaction_hash | 0 |
