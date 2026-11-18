# Model v2 universe: inclusion rule

**Written:** 2026-11-18 (UTC), BEFORE any v2 market list or trade was pulled.
Basis: market question and resolution text only. No price, volume-pattern, wallet or outcome information is used to include or exclude a market, except the two practical limits in section 4.

## 1. Include
Resolved Polymarket markets (binary Yes/No) with resolution date from 2025-01-01 to 2026-10-31, whose outcome is decided by a small group or a single identifiable actor, so that people close to that group could know it early. Categories:
- military and government actions (strikes, ceasefires, sanctions, executive orders, resignations/removals of officials)
- awards (Nobel, Oscars-style committee prizes)
- appointments and nominations (cabinet, agency heads, central-bank chairs, court nominees)
- central-bank rate decisions (Fed, ECB, BoE, BoJ and similar), because the committee decides
- company announcements decided by the company (product launches, model releases, mergers, filings, CEO changes)

## 2. Exclude
- sports and esports
- crypto and other asset-price markets (threshold, up/down)
- elections, polls, vote shares
- weather and natural events
- scheduled statistics releases, TV/entertainment ratings, social-media counts (tweet counts), mention-markets
- markets whose rule depends on subjective judgement not made by a small group
- non-binary markets or markets with no clear Yes/No resolution (voided, 50/50)

## 3. How the list is built
1. Pull closed markets from Gamma (`closed=true`) in date windows, collect question, slug, event, description, dates, volume, outcome prices, condition id, token ids.
2. Apply the category screen by keyword on question/event title/description (keyword lists saved in `src/v2_01_markets.py` and committed with the output). Every excluded market and its reason goes to `data/v2/exclusions.csv`.
3. Resolution = outcome price of exactly 1/0 after close. Anything else is excluded and logged.

## 4. Practical limits (not outcome-based)
- Minimum lifetime volume USD 20,000 (below that there are almost no wallets to learn from).
- Maximum 400 fill pages (400,000 fill rows) per market, because the Data API serves fills newest-first in 1,000-row pages. Markets above that are excluded and logged as a data gap, not truncated.
- If more than 150 markets qualify and the time budget is short, the 150 with the most volume (within these limits) are taken, and this is stated in the summary. If fewer than 150 qualify, the shortfall is reported.

## 5. Unit and timing
Unit = wallet x market x side. "Close" = the market's `closedTime` (else `endDate`). Position "before" = fills with timestamp <= close minus 1 hour. Prices paid are volume-weighted prices of that wallet's buys on that side.
