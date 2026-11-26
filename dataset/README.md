# Prediction-Market Informed-Trading Casebook (PMITC)

An open, source-traced register of every publicly documented case of suspected informed trading on prediction markets: court and regulator actions, platform sanctions, analyst investigations, press reports, and rule-based screens. Each claim keeps its own source and evidence grade, so a researcher can choose how strict to be.

**Version:** 0.2 (2026-11-26). Collected under [PROTOCOL.md](PROTOCOL.md) v1.0 and its amendments.

## Contents

| File | Rows | One row is |
|---|---|---|
| `data/claims.csv` | 84 | One claim by one source: subject, paraphrase, evidence grade, amount, dates, URL |
| `data/cases.csv` | 58 | One underlying event, derived from its claims: strongest grade, number of sources, whether amounts disagree |
| `data/wallet_labels.csv` | 239 | One wallet address in one case, with role, label tier, polarity and the source file it came from |
| `data/wallet_edges.csv` | 416 | One money link between addresses (funding, Relay handoff, Safe owner, cash-out, transfer) |
| `data/handles_to_resolve.csv` | 13 | A public username whose wallet address still needs an API lookup |
| `logs/search_log.csv` | 40 | Every search query run, its source class, and what it produced |
| `logs/repos.csv` | 12 | Every code repository used, with the exact commit |
| `build/*.py` | | Scripts that rebuild every table from the cloned sources |

### Coverage (v0.2)

- **Platforms:** Polymarket (most cases), Kalshi (official enforcement), both (pre-taped TV).
- **Families:** informed trading; manipulation by the outcome maker or odds support; oracle and resolution attacks; public-data leaks; pre-taped show leaks; negative controls; rule-based screens.
- **Topics:** military and geopolitical (Venezuela, the June 2025 and February 2026 Iran strikes, Khamenei, ceasefires), elections (US 2024 VP picks, 2026 midterms, Israel 2026), executive decisions (pardons, tariffs, a Trump–Zelenskyy meeting), awards (Nobel, Ballon d'Or, papal conclave), technology (Google, Gemini, OpenAI), corporate (earnings, MicroStrategy, DraftKings, Spotify), crypto (Arbitrum airdrop, the ZachXBT exposé), culture (Taylor Swift, Super Bowl halftime, Survivor, MrBeast), and speech mention markets.
- **Case grades:** E1 = 4, E2 = 3, E3 = 8, E4 = 11, E5 = 24, E6 = 8.

## Evidence grades (per claim; a case takes its strongest)

| Grade | Meaning |
|---|---|
| E1 | Adjudicated or final sanction (conviction, settlement order, final platform discipline) |
| E2 | Charged (indictment or complaint) |
| E3 | Official inquiry or referral reported |
| E4 | Analyst with transaction-level evidence (funding paths, transfers, fills) |
| E5 | Pattern claim (timing, account age, win rate) without transaction-level links |
| E6 | Rule-based flag from a published screen |

Wallet label tiers (`L2` to `L4`, `A`, `NC`, `M`) are explained in `build/build_seed.py`.

## Rules for use

1. **A label is an allegation, not a finding.** Only E1 is a final outcome, and E1 is mostly platform discipline on Kalshi.
2. **One case is one event.** A cohort of 38 wallets on one market is one observation.
3. **The collection is biased toward what was noticed.** Almost every case is a fresh wallet making a big, cheap, well-timed bet on a viral market. Do not estimate prevalence from it, and do not train a detector only on it.
4. **Freeze before you test.** These cases were public before you built your method. Report results on cases added after your freeze date separately.
5. **No identity work.** The tables contain no personal names. Official records are referenced by URL. Do not use the data to identify people behind wallets.

## Known gaps

- X was not searched directly (protocol amendment A1). X posts appear only through press, reports and repositories.
- The 20% blind re-extraction is not done yet (A4).
- Several large lists exist but are private: the ~100 Polymarket referrals, the ~34,000 Polysights flags, the NYT's 80+ accounts, ACDC's 556 Orcas, Inca Digital's 39. Rule-based lists can be rebuilt from trades (see `build/PIPELINE.md`).
- AlphaRaccoon's address conflicts between sources (`0xee50…` in a repository vs `0xafEe…` in the press).

## How to cite

Yildiz, I. (2026). *Prediction-Market Informed-Trading Casebook (PMITC)*, version 0.2. Collected under protocol v1.0. https://github.com/ibrhmyi/insider (dataset folder).

## License

Tables written for this dataset: CC-BY-4.0. Third-party sources keep their own licenses: searadacunha's research text is CC BY-NC-ND 4.0, and ForesightFlow is CC-BY-4.0. Only public blockchain facts and short paraphrases are copied, with links. To correct or remove a row, open an issue with the row ID and the reason.
