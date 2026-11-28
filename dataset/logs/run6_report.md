# Run 6 report (2026-11-26)

Run 6 read the source pages behind the claims, after you approved 20 press, ACDC and CFTC/DOJ hosts for the environment. The goal was to recover full wallet addresses and X post URLs that search snippets could not give. The page log is `logs/page_reads_run6.csv`.

## Pages

- 39 URLs fetched; 29 were read.
- 10 were refused by the sites' own bot blocks (HTTP 403): beincrypto, gizmodo, The Block, cryptotimes.
- Third-party page text is not committed; only the facts extracted from it are.

## New insider wallets: 9, all confirmed by their own fills

- **8 Axiom-market wallets** (zachxbt-axiom-2026-02). KuCoin's copy of Lookonchain's list prints 9 of the 12 addresses; 1 was already labelled.
  - `0x054ec2f0…` and `0xe56526b2…` match the address prefixes DefiOasis gave in a separate source (CL0090).
  - All 8 first bought on Feb 25–26, before ZachXBT's release at 14:16 UTC on Feb 26.
  - Combined buys about $737k. The largest: `0x054ec2f0…` bought $503,575 and redeemed $224,479.
- **1 Super Bowl LX account** (`0x40d9ac81…`, super-bowl-halftime-2026). Futurism and Covers both link its profile.
  - Day-old account; it traded only halftime markets.
  - It bought $69,355 and redeemed $48,847, against "about $70,000 wagered" in Covers.
- Totals: 260 labelled addresses, 133 suspected; 120 of them traded their case market.

## Claims verified by reading the page

- **Verified:** CL0085, CL0086, CL0087, CL0091, CL0093, CL0095, CL0098, CL0099, CL0100, CL0102, CL0103.
- **X post URLs recovered** (in `notes` as `post_url=`): 4 Lookonchain posts and 2 Bubblemaps posts.
- **Still pending:** CL0088 and CL0090. Their pages were read and their post URLs found, but part of the claim text is not in the page.
- **Not reachable:** CL0089, CL0092, CL0094 (403); CL0096, CL0097, CL0101, CL0104, CL0105 (hosts not added).

## New claim

CL0107 (run 6, verified): the Futurism report on super-bowl-halftime-2026, with the account's address.

## Contradictions (claims never edited)

- **CX002, CL0049.** Dated 2025 and filed under super-bowl-halftime-2025, but the source (Futurism, 2026-02-11) describes Super Bowl LX, the Bad Bunny show of 2026. Re-recorded correctly as CL0107.
- **CX003, CL0099.** The $68k Fed-chair bet was placed on 2025-12-16, not in January 2026.

## Effect

| Measure | Before run 6 | After run 6 |
|---|---|---|
| Episodes | 409 | 425 |
| Controls | 7,686 | 7,898 |
| Pre-news buys by suspected wallets in their case markets | 10,334 | 10,626 (68 wallets, 17 cases, $6.42M) |

Day-start t_news still hides most of the Axiom and Super Bowl buys made on the event day (see run 5, decision 3).
