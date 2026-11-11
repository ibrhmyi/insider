# Blind validation: Maduro out by January 31, 2026?

Frozen rules only (`rules/frozen_v0.md`, frozen 2026-11-09T16:31:34Z); no parameter was changed after seeing this market.
Earliest public news used: 2026-01-03T06:00:00Z (first reports of explosions in Caracas, approximate); Trump post 2026-01-03T09:21:00Z. Resolution 2026-01-03T12:14:07Z.

## Seed quantile 0.95

- seeds: 384; pre-news usable: 249; excluded for news overlap: 66; post-news: 134
- pre-news seeds in the final 24 h before first news: 24
- **alerts (excess wallets > 12.91) before public news: 2**

| seed UTC | hours before first news | direction | notional USD | YES price | observed wallets | expected | excess |
|---|---|---|---|---|---|---|---|
| 2025-12-30T05:48:35Z | 96.2 | toward NO | 2,558 | 0.090 | 24 | 2.5 | 21.5 |
| 2025-12-31T00:32:07Z | 77.5 | toward NO | 1,000 | 0.080 | 51 | 2.8 | 48.2 |

Pre-news seeds in final 24 h (all, alert or not):

| seed UTC | dir | notional USD | YES price | obs | exp | excess | alert |
|---|---|---|---|---|---|---|---|
| 2026-01-02T08:27:31Z | -1 | 2,820 | 0.060 | 8 | 6.4 | 1.6 | False |
| 2026-01-02T09:09:55Z | -1 | 3,000 | 0.060 | 3 | 5.9 | -2.9 | False |
| 2026-01-02T09:48:23Z | +1 | 1,832 | 0.070 | 1 | 1.7 | -0.7 | False |
| 2026-01-02T11:28:21Z | +1 | 1,340 | 0.070 | 2 | 1.2 | 0.8 | False |
| 2026-01-02T12:05:19Z | -1 | 4,700 | 0.060 | 11 | 4.3 | 6.7 | False |
| 2026-01-02T12:25:23Z | -1 | 2,000 | 0.060 | 8 | 3.8 | 4.2 | False |
| 2026-01-02T13:04:53Z | -1 | 2,350 | 0.060 | 7 | 4.1 | 2.9 | False |
| 2026-01-02T13:26:01Z | -1 | 4,700 | 0.060 | 7 | 4.6 | 2.4 | False |
| 2026-01-02T13:49:11Z | -1 | 8,001 | 0.060 | 7 | 4.4 | 2.6 | False |
| 2026-01-02T16:49:29Z | +1 | 6,000 | 0.066 | 3 | 2.1 | 0.9 | False |
| 2026-01-02T19:22:41Z | -1 | 2,000 | 0.060 | 3 | 3.5 | -0.5 | False |
| 2026-01-02T21:44:21Z | +1 | 5,783 | 0.072 | 2 | 2.3 | -0.3 | False |
| 2026-01-02T23:29:35Z | -1 | 1,767 | 0.070 | 5 | 5.8 | -0.8 | False |
| 2026-01-02T23:31:59Z | -1 | 1,674 | 0.070 | 5 | 5.8 | -0.8 | False |
| 2026-01-02T23:58:41Z | -1 | 11,986 | 0.070 | 4 | 5.8 | -1.8 | False |
| 2026-01-03T00:33:21Z | -1 | 5,363 | 0.060 | 2 | 6.5 | -4.5 | False |
| 2026-01-03T01:38:35Z | +1 | 6,000 | 0.073 | 0 | nan | nan | False |
| 2026-01-03T02:15:05Z | +1 | 7,000 | 0.080 | 2 | nan | nan | False |
| 2026-01-03T02:58:25Z | +1 | 7,215 | 0.082 | 11 | nan | nan | False |
| 2026-01-03T03:09:37Z | -1 | 4,094 | 0.080 | 18 | nan | nan | False |
| 2026-01-03T03:41:21Z | -1 | 1,888 | 0.080 | 28 | nan | nan | False |
| 2026-01-03T03:42:01Z | +1 | 10,000 | 0.113 | 25 | nan | nan | False |
| 2026-01-03T03:42:59Z | -1 | 8,416 | 0.110 | 17 | nan | nan | False |
| 2026-01-03T04:41:57Z | -1 | 14,264 | 0.100 | 12 | nan | nan | False |

## Seed quantile 0.99

- seeds: 110; pre-news usable: 78; excluded for news overlap: 12; post-news: 32
- pre-news seeds in the final 24 h before first news: 11
- **alerts (excess wallets > 12.91) before public news: 1**

| seed UTC | hours before first news | direction | notional USD | YES price | observed wallets | expected | excess |
|---|---|---|---|---|---|---|---|
| 2025-12-30T05:48:35Z | 96.2 | toward NO | 2,558 | 0.090 | 24 | 2.6 | 21.4 |

Pre-news seeds in final 24 h (all, alert or not):

| seed UTC | dir | notional USD | YES price | obs | exp | excess | alert |
|---|---|---|---|---|---|---|---|
| 2026-01-02T12:05:19Z | -1 | 4,700 | 0.060 | 11 | 6.0 | 5.0 | False |
| 2026-01-02T13:49:11Z | -1 | 8,001 | 0.060 | 7 | 5.0 | 2.0 | False |
| 2026-01-02T21:44:21Z | +1 | 5,783 | 0.072 | 2 | 2.7 | -0.7 | False |
| 2026-01-02T23:58:41Z | -1 | 11,986 | 0.070 | 4 | 4.9 | -0.9 | False |
| 2026-01-03T01:38:35Z | +1 | 6,000 | 0.073 | 0 | 1.6 | -1.6 | False |
| 2026-01-03T02:15:05Z | +1 | 7,000 | 0.080 | 2 | 1.6 | 0.4 | False |
| 2026-01-03T02:58:25Z | +1 | 7,215 | 0.082 | 11 | nan | nan | False |
| 2026-01-03T03:42:01Z | +1 | 10,000 | 0.113 | 25 | nan | nan | False |
| 2026-01-03T03:42:59Z | -1 | 8,416 | 0.110 | 17 | nan | nan | False |
| 2026-01-03T03:59:31Z | -1 | 8,655 | 0.080 | 15 | nan | nan | False |
| 2026-01-03T04:41:57Z | -1 | 14,264 | 0.100 | 12 | nan | nan | False |

## Seed quantile 0.995

- seeds: 77; pre-news usable: 54; excluded for news overlap: 8; post-news: 23
- pre-news seeds in the final 24 h before first news: 7
- **alerts (excess wallets > 12.91) before public news: 0**

Pre-news seeds in final 24 h (all, alert or not):

| seed UTC | dir | notional USD | YES price | obs | exp | excess | alert |
|---|---|---|---|---|---|---|---|
| 2026-01-02T23:58:41Z | -1 | 11,986 | 0.070 | 4 | 3.8 | 0.2 | False |
| 2026-01-03T02:15:05Z | +1 | 7,000 | 0.080 | 2 | 1.3 | 0.7 | False |
| 2026-01-03T02:58:25Z | +1 | 7,215 | 0.082 | 11 | 1.3 | 9.7 | False |
| 2026-01-03T03:42:01Z | +1 | 10,000 | 0.113 | 25 | nan | nan | False |
| 2026-01-03T03:42:59Z | -1 | 8,416 | 0.110 | 17 | nan | nan | False |
| 2026-01-03T03:59:31Z | -1 | 8,655 | 0.080 | 15 | nan | nan | False |
| 2026-01-03T04:41:57Z | -1 | 14,264 | 0.100 | 12 | nan | nan | False |

All flags are **unusual activity for review, not proof of insider trading**. Wallet addresses are deliberately not listed in this report.

## Descriptive context (NOT detector output; added after the frozen run, rules unchanged)

15-minute profile of taker trades, 2026-01-02 22:00 to 2026-01-03 07:00 UTC (script snippet in `log/process_log.md`):
- 22:00-01:15: 1-6 trades per 15 min; YES price 0.06-0.08; flow mostly toward NO.
- 01:30, 02:15, 02:45: single trades of $6,000, $7,000 and $7,215 toward YES (these are the seeds at 01:38, 02:15, 02:58). Price stays 0.06-0.08. The frozen detector scored 01:38 at -1.6 and 02:15 at +0.4 excess wallets; 02:58 could not be scored (no matched baseline within +-2 h).
- 03:30-04:00: activity rises (45 then 24 trades per 15 min) with flow in BOTH directions (~$10k toward YES, ~$12k toward NO at 03:30). Seeds 03:42 (toward YES, 25 same-direction wallets) and 03:42/03:59/04:41 (toward NO) could not be scored (unmatched).
- 05:30-06:15: YES price 0.10 -> 0.14, YES-direction flow increases.
- 06:15-06:45: YES price 0.12 -> 0.51 with 137-242 trades per 15 min, i.e. AFTER the approximate first public reports of explosions (~06:00 UTC).

**Factual answer to the validation question:** using only the frozen v0 rules, the detector raised **one** pre-news alert in this market at the primary 99th-percentile setting (2025-12-30 05:48 UTC, 96 h before the news, direction toward NO, i.e. against the eventual outcome) and **no alert in the final 24 h before the news**. The pre-news YES-direction seeds in the last ~4 h before news either did not exceed the alert threshold or could not be scored because the frozen baseline found no matched no-seed window within +-2 h. Whether those hours contain informed trading is therefore **not answered** by v0. This is a limitation of the detector, not a negative finding.
