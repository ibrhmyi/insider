# Upstream sources and their licences (checked 2026-11-26, run 7)

| Source | What PMITC uses | Licence found | Redistributed in v1.0? |
|---|---|---|---|
| Polymarket-v1 on Hugging Face (`TimeSeventeen/Polymarket-v1` @ 6d1bcd52) | fills (`source = hf_polymarket_v1`), market catalog, rule labels | **CC-BY-4.0** (dataset card) | Yes, with attribution |
| Polymarket Data API v2 / Gamma API | fills after 2026-04-28 and for markets/wallets not in Polymarket-v1 (`source = data_api_v2`), profiles, market metadata | **Not verified.** Polymarket's terms page could not be reached from the build environment; docs.polymarket.com lists no data licence. The rows are public on-chain trades. | Yes, in separate files (`fills_part*_data_api_v2.parquet`) so they can be withheld; see "Decisions needed" |
| ForesightFlow/datasets @ 5ba41274 | FFIC market prefixes, t_news tiers | **CC-BY-4.0** (LICENSE.md) | Facts only (market ids, tier labels), with attribution |
| Kalshi regulatory notices (public bucket `kalshi-public-docs`) | one claim per notice: ID, date, rule, sanction | No licence stated; official public notices | Facts and short paraphrases only, with URL |
| CFTC, DOJ press releases | claims | US federal government works (public domain in the US) | Facts and paraphrases, with URL |
| Press and analyst pages | claims (paraphrase under 30 words), event times | Copyright of each outlet | Facts and short paraphrases only, with URL (no page text is shipped) |
| Ha1o/PolyShadow @ f00ca247 | seed wallet labels | MIT | Facts (addresses), with attribution |
| pselamy/polymarket-insider-tracker @ 49f8770c | seed wallet labels | MIT | Facts, with attribution |
| searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS @ acc5e422 | seed wallet labels, money links (`edges`) | MIT (repository); its research text is described as CC BY-NC-ND 4.0 in the README of v0.3 | Facts only (addresses, transaction hashes, amounts), no text |
| 1712n/dn-institute @ 8a3b6dd5 | seed claims | Unlicense (public domain) | Yes |
| Vedant-29/Insider-Trading-Detection-Fireplace, Vedant-29/polymarket-insider-detection, aidensandler/polyInsider, corbettbw/prediction-market-insider, dipsylala/polymarket-monitor, gabrielseow/polymarket-insider-tracker, klixq/polymarket-insider-analysis | seed wallet labels | **No licence file** (all rights reserved by default) | Only public blockchain facts (addresses) and their source URL; none of their files or text. `build/build_seed.py` rebuilds the seed rows from the clones. |

No upstream source was found that explicitly forbids redistribution of a released table or column. Where a licence is missing or not verified, PMITC ships only uncopyrightable facts (addresses, transaction ids, times, amounts) with a link, and the scripts that rebuild them.
