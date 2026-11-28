# Run 2 report (2026-11-26)

Run 2 had three parts: an X sweep under amendment A5, Gamma handle resolution, and a rebuild from the 12 repositories in `logs/repos.csv`, each cloned at its listed commit. Extractor: claude-opus-5.5.

## Totals

| Table | Before | After |
|---|---|---|
| claims.csv | 84 | 92 (+8, CL0085 to CL0092) |
| cases.csv | 58 | 60 (+2) |
| wallet_labels.csv | 239 | 248 (+9 resolved handles; 1 note updated) |
| wallet_edges.csv | 416 | 416 |
| handles_to_resolve.csv | 13 | 17 (+4 handles from new claims) |
| logs/search_log.csv | 40 | 75 (+35 queries) |

Case grades after run 2: E1 = 4, E2 = 3, E3 = 8, **E4 = 13** (was 11), E5 = 24, E6 = 8.

The rebuild reproduced all 84 earlier claims, 416 edges and 238 of 239 wallet rows unchanged. The only changed wallet row is the AlphaRaccoon note.

## How the X sweep went (read this first)

- **The search engine ignored `site:x.com`.** None of the 35 queries returned an x.com post. Every result was a press or aggregator page that quotes the posts.
- **No page could be opened.** Every page fetch failed: the hosts are not allowed by this environment's network.
- **So the 8 run-2 claims come from search-result text.** Each carries the quoting page as `url`, not the post. Its `notes` say `via=search_engine; ... source page not read ...; post URL not recovered`.
- **They are S4 under A5's "pages that quote them" clause, but they do not meet A5's "the post URL as url".** Before verification, each needs its page read and its post URL found. CL0089 (BlueHorseshoe86) is also flagged because its tie to that URL is unverified.
- **Suggestion (not done):** record this as amendment A6 in PROTOCOL.md. I did not change the protocol.

## New claims

| Claim | Case | Grade | Source | What |
|---|---|---|---|---|
| CL0085 | maduro-2026-01 | E5 | Lookonchain via Stocktwits | 3 wallets, $630,484; probably the origin of CL0005 |
| CL0086 | maduro-2026-01 | E5 | Bubblemaps via crypto.news | Counter-claim: disputes the funding-match ownership link |
| CL0087 | us-iran-strike-2026-02-28 | E4 | Bubblemaps via Blockchain.news | Skoobidoobnj linked on-chain to 2 more accounts (post 2026-03-05) |
| CL0088 | us-iran-ceasefire-2026-04-07 | E5 | Lookonchain via Blockchain.news | 4 same-day wallets, about $663k |
| CL0089 | us-iran-ceasefire-2026-04-07 | E5 | Lookonchain via BeInCrypto | BlueHorseshoe86, about $194k (attribution unverified) |
| CL0090 | zachxbt-axiom-2026-02 | E5 | DefiOasis via Cointelegraph | 8 of the top 10 winners, over $1.2M; prefixes 0x054ec2f and 0xe56526b kept as prefixes |
| CL0091 | **world-cup-2026-06** (new) | E4 | Lookonchain via crypto.news | mintblade, GRIMDRIP, endlessFate: $24.25M, one shared Binance deposit address |
| CL0092 | **tweet-count-self-2026-03** (new) | E4 | Euanker via Crypto Times | 7 accounts allegedly tied to the market's own subject, $52,286 (manipulation family) |

The URL of CL0092 has a public figure's name in its slug. No data field names them.

## New cases by grade

- **E4:** world-cup-2026-06 (informed trading, sports), tweet-count-self-2026-03 (manipulation, outcome maker).
- **Existing cases that changed:**
  - zachxbt-axiom-2026-02 now has grades E4 and E5, and its maximum amount rose to $1.2M.
  - maduro-2026-01, us-iran-strike-2026-02-28 and us-iran-ceasefire-2026-04-07 gained claims; no case grade changed.
  - Side effect: `first_claim_date` for the ceasefire case is now `2026-04`, because CL0088 and CL0089 have month-only dates and `build_cases.py` takes a string minimum.

## Leads seen but not recorded

| Lead | Reason not recorded |
|---|---|
| A Polymarket-run X account with 25 insider-signal posts (via Barron's) | No claim date recoverable (inclusion rule 4) |
| A ZachXBT note on a $70k deposit into a new account | Source URL not identified |
| Ceasefire handles Fernandoinfante and NOTHINGEVERFRICKINHAPPENS | Analyst attribution unclear |
| Lookonchain "clear case" remark on the Maduro bet | URL not identified |
| An analyst's naming of a person behind the Maduro wallet | Personal-name speculation, excluded |
| A Polymarket top-up wallet exploit | Security incident, out of scope |

## Handle resolution

Method: Gamma `public-search?q=<handle>&search_profiles=true`. A handle counts as resolved only if exactly one profile's `name` equals it exactly, case included. Raw responses are in `logs/gamma_raw/<handle>.json`. For each resolved address, Data API v2 activity was pulled (`build/run2_fill_check.py`, saved as `logs/gamma_raw/activity_<address>.json.gz`) to check it traded its case's markets.

**Resolved (10)**, each added to `wallet_labels.csv` as `L3_handle_resolved`, polarity suspected:

| Handle | Address |
|---|---|
| djijaij83jdo4jdlwjflsg | 0xa4eb52229991c074bc560f825bf2776d77acd010 |
| Skoobidoobnj | 0xfe6eee00d36717359578ddb4d6e091d56bc9074e |
| Magamyman | 0x4dfd481c16d9995b809780fd8a9808e8689f6e4a |
| romanticpaul | 0xf5cfe6f998d597085e366f915b140e82e0869fc6 |
| whopperlover | 0x607fec58640fcea5cb837adb09d658747720592c |
| aenews0 | 0x4bac00c61a02275d681f3857cdc5ae315f1f7075 |
| mintblade | 0x96cfcb0c30942cfcd1cdf76c7d408794d66b1acb |
| GRIMDRIP | 0x3f87d51f27ba6e19ec52aaeebb68559a839c742c |
| endlessFate | 0x5e4c3b5b81171e2ca4ab776ac0d6bba787f9dba2 |
| BlueHorseshoe86 | 0x44de2a52d8d2d3ddcf39d58e315a10df53ba9c08 |

All 10 have trades on their case's markets; the World Cup three traded `fifwc-*` match markets from 2026-06-03 to 06-18. romanticpaul's engagement market was not matched by keyword: only Taylor Swift Spotify and Google-search markets showed up, so that one needs a manual check.

**Failed lookups (7):**

| Handle | Result |
|---|---|
| Elonfax89678 | Only `ElonfaX89678` (case differs); not accepted |
| rundeep | Only `Rundeep`, which is 0x0afc7ce5…, already in the seed for this case; not accepted as a lookup result |
| Bama124 | Only `bama124` (case differs); not accepted |
| ricosuave666 | Exact match 0x0002682d… has **zero activity** (the name was reused after the account was deleted); rejected. The trader is the seed's 0x0afc7ce5…, now shown as "Rundeep", which has the Israel–Iran strike buys |
| AlphaRaccoon | No exact match (the account was renamed); settled from fills instead, below |
| Burdensome-Mix | One unrelated profile returned |
| OnlyBibi2026 | No profiles returned |

## AlphaRaccoon conflict: settled

- Data API v2 shows that proxy `0xee50a31c3f5a7c77824b12a941a54388a2827ed6` now uses the display name **`0xafEe`** (pseudonym Limping-Semicolon). The press "0xafEe" is that renamed username, not an address prefix.
- Its Yes buys on "Will d4vd be the #1 searched person on Google this year?" total **$10,650.04 over 125 fills** (2025-11-24 to 12-02). That matches the reported ~$10.6k, and CL0011's $10,647.
- It redeemed $205,108 on that market and $25,423 on the d4vd Top-5 market.
- It also traded the Gemini 3.0 release markets.
- Result: keep `0xee50…`. No second address exists.

## Not done

- The Maduro check from PIPELINE step 1 (is 0x31a56e9e… the account in the CFTC complaint?) was not in this run's scope.
- The 20% blind re-extraction (A4) is still open.
- The Data API v1 endpoints that PIPELINE step 3 names now return 410; v2 works and is what was used.
