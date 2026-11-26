# Run 5 report (2026-11-26)

Run 5 hunted for more insider wallets, mainly Polymarket usernames named in the press that can be resolved to addresses, and started executing the backlog. New rules (A9) were committed before the fields they govern were computed. Every new claim is `verified=pending` (search-result text).

## New wallets and claims

9 claims (CL0098–CL0106) and 3 new cases.

| Case | What was added |
|---|---|
| fed-chair-nomination-2026 (new) | `HD2`, a new account that bet nearly $100k on one candidate's nomination; Polymarket's own X account highlighted it (Barron's). Gamma exact match `0x1138c6c1…`. Its fills confirm the claim: 703 Yes buys, $96,621, 2025-12-19 to 2026-01-21; profile created 2025-11-28. A second new account ($68k) is unnamed. |
| nobel-peace-2025 | `dirtycup` (Bloomberg via Cointelegraph) resolves exactly to `0x234cc49e…`, an address the seed already held from a repo list. Two independent sources agree. Also Norway's espionage suspicion (E3). |
| super-bowl-halftime-2026 (new) | A new account that traded only halftime markets made $16,995, plus a setlist wallet. No addresses published. |
| openai-gpt52-2025-12 | OpenAI fired an employee for using confidential information on prediction markets (WIRED via TechCrunch), plus a secondary report of $16,872 made Dec 10–13. |
| openai-markets-aggregate (new) | Unusual Whales flagged 60 wallets / 77 positions on OpenAI markets. |

**Leads closed:** `Fernandoinfante` and `NOTHINGEVERFRICKINHAPPENS` (no traceable source). No account names are published for the Zelenskyy, Israel-election, Biden-pardon or OpenAI four-account cases.

## Executed ideas

- **Stance (A9.1).** 7 claims marked: 3 `clears`, 3 `disputes`, 1 `context`.
- **Investigation outcome (A9.2).** Applied to `cases.csv`:

  | Outcome | Cases |
  |---|---|
  | sanctioned | 4 |
  | charged | 3 |
  | cleared_official | 1 (survivor-50-2026) |
  | cleared_analyst | 2 (ballon-dor-2026, railgun-venezuela-control) |
  | disputed | 2 (election-2024, nyt-siena-polls-2026) |
  | under_investigation | 10 |
  | unresolved | 43 |

- **Minute paths (A9.3).** `out/market_minutes.parquet`: 216,552 market-minutes, 40 cases, 508 markets, 48 h before to 24 h after t_news.
- **Markets and fills for the new cases.** 112 new market rows; 1.97 M Data API rows pulled. Case-market legs now 22.6 M. Episodes 409 (+1: `HD2`), controls 7,686.

## Fixes

- The fill assembler was killed for memory with about 4 M API rows held at once. It now writes per-market parquet files.
- Wallets labelled after the HF pass (e.g. `HD2`) were missing their pre-April fills. They now come from the Data API for all time; HF legs are kept only for the address list the pass used (`logs/hf_pass_label_addresses.txt`), so nothing is counted twice.

## Decisions needed (new)

1. **Employer findings.** PROTOCOL 5 has no grade for them (OpenAI firing an employee); E3 is used provisionally.
2. **CL0049.** It may describe Super Bowl LX (2026), not LIX (2025). Added to `needs_page_read`; fix by new claim or contradiction, never by editing.
3. **Exact news times.** `data/event_times.csv` is still unused. With day-start t_news, the Maduro buys at 02:58 UTC on the event day, and the Nobel buys, count as post-news. This needs an amendment.
