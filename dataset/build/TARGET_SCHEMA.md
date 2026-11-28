# Target schema (planning note, run 4)

v0.1 is a list of known cases. v1 covers the whole universe: every position anyone has taken on Polymarket, scored against a null distribution built from markets where inside information is impossible. Known cases become one label column among many, not the whole dataset.

## The idea that makes it different

Every public list of "insiders" has the same problem: there is no denominator. A wallet that bet 8¢ and won could be an insider or could be lucky, and nobody measures how often luck alone produces that pattern.

Polymarket answers this itself. It runs millions of markets where **nobody can know the outcome in advance**: 5- and 15-minute crypto up/down markets, weather readings, many sports results. In those markets every early, cheap, winning bet is luck or skill. That gives an empirical null for every behaviour we measure, at the same platform, same fees, same users.

So for any position in an insider-possible market (military, award, corporate release, political decision), the dataset reports how unusual that position is compared with the same behaviour in insider-impossible markets. It is a difference-in-differences: (behaviour → win) in insider-possible markets minus (behaviour → win) in placebo markets, at the same price.

## Layer 1. Universe (every market, every position)

| Table | Grain | Source |
|---|---|---|
| `markets` | every Polymarket market ever (v1 + v2 exchanges) | Gamma API, Polymarket-v1, Data API |
| `fills` | every fill with true aggressor side | Polymarket-v1 to 2026-04-28; Data API / chain logs after |
| `positions` | one row per (wallet, market, side): entry path, exit path, PnL | built from fills |
| `wallets` | every proxy: creation time, owner key, lifetime stats | Polygon logs, Gamma profiles |
| `kalshi_markets`, `kalshi_trades` | every Kalshi market and trade (no account IDs) | Kalshi public API |
| `manifold_bets` | every Manifold bet with user ID (play money) | Manifold public API |

## Layer 2. Information timing (for every market, not 2,052)

| Column | How |
|---|---|
| `t_event` | when the thing happened (strike time, decision time) |
| `t_news` | first public report |
| `t_scheduled` | official release time when scheduled (Nobel, earnings SEC acceptance, Google Year in Search, FOMC, CPI) |
| `tnews_method` | ForesightFlow tier where it exists; else GDELT first mention; else LLM reading of the resolution source; confidence score |

Scheduled releases are the cleanest experiments: the release time is known to the second, so any flow before it can be measured exactly.

## Layer 3. Who could know (every market)

An LLM classifier with a frozen rubric and a 500-market hand-checked validation sample tags each market:
- `insider_possible`: `none` (random or physical: crypto 5-min, weather, dice-like), `crowd` (many observers: sports live), `small_group` (committee, company, military unit, one decision-maker), `single_person` (a person's own action: candidate, creator, speaker)
- `outcome_maker`: who decides the outcome (ACDC's "group outcome maker" idea)
- `category`, `deadline_type` (deadline vs event resolution, as FFIC uses)

`none` markets are the placebo pool. `small_group` and `single_person` markets are where insiders can exist.

## Layer 4. Labels (many, each with its own column, never merged)

| Column | Type | Source |
|---|---|---|
| `doc_case_id`, `doc_tier` | documented | court, regulator, platform, analyst (v0.1 seed, then the harvest below) |
| `acdc_class` | rule | ACDC longshot and Orca definitions, rerun |
| `inca_flag` | rule | Inca Digital rule |
| `mitts_ofir_flag` | rule | their composite screen, if reproducible from the paper |
| `skilled_gc` | rule | Gómez-Cram et al. skilled-trader test, rerun |
| `gate1`, `gate2a`, `gate2b` | rule | our frozen gates |
| `graph_link` | network | shares a funder, bridge order, or cash-out address with a documented wallet |
| `excess_vs_placebo` | continuous | position's win minus price, minus the placebo-pool rate for the same price band, behaviour bucket and horizon |
| `informed_score` | continuous | hierarchical Bayesian posterior that the position was informed (PyMC; wallet and event random effects) |

The last two make every one of the positions labelled, with an honest uncertainty, instead of 218 wallets.

## Layer 5. Money graph (every wallet that matters, not just seeds)

For every wallet with a pre-news position in an insider-possible market above $1,000, plus every documented wallet:
- Polygon USDC/USDC.e in and out; Relay orders across Polygon, Ethereum, Base, Arbitrum, Solana; Safe owner keys; exchange deposit addresses (common deposit address = same exchange customer account)
- connected components after removing hubs (over 500 counterparties)
- this is how "same money, new account" works at scale

## Layer 6. Documented-case harvest (target: every public allegation)

Systematic, not ad hoc. For each source, pull everything since 2024, keep the post URL, time and every address or handle:
- X accounts: Bubblemaps, Lookonchain, Polysights, PolymarketStory, Unusual Whales, DefiOasis, ZachXBT, and accounts that repost them (search terms: "insider", "fresh wallet", "suspicious" + "polymarket")
- Press: Bloomberg, Reuters, AP, WSJ, Guardian, Block, CoinDesk, Decrypt, Cointelegraph, Times of Israel
- Official: DOJ, CFTC, Kalshi notices page, Israeli courts, Polymarket integrity announcements, WIRED FOIA files
- Research: ACDC, Inca Digital, Solidus Labs, Mitts and Ofir, ForesightFlow, GitHub repos (the 30-plus already reviewed)
Each harvested claim becomes a row in `claims.csv` (one claim, one source), then is joined to cases, markets and wallets. Claims that contradict each other stay as separate rows.

## Release

- GitHub: tables under 50 MB, code, README, DATASHEET, label rules, validation sample.
- Hugging Face: fills, positions, features as parquet, versioned.
- Zenodo DOI per release.
- Terminology: "flagged by", never "insider". No personal names. Removal process in README.

## Checks before any release

1. ACDC reconstruction within 5% of their published counts.
2. Placebo test: `excess_vs_placebo` averages zero on a held-out half of the placebo pool.
3. Known-case recall: share of documented cases where the top-scored positions include the documented wallets, reported with the selection-bias warning.
4. Hand check of 200 random rows across tables.
