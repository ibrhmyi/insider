# Gate 1 result

Frozen test: `rules/frozen_gate1.md` (freeze commit b7b8d636d90834ba14803eedf23c5b03c97e2ce4 2026-11-25T21:58:30+00:00). Input hashes checked: match. Run by `src/gate1_run.py`, once.

## Primary

Core universe, main definition ($2,500 within 24 h at a buy VWAP <= 0.35, p_a < 0.50, t_a < T_dec), event as the unit.

- Events: 443; markets: 556; episodes: 2,083.
- Mean excess (outcome - p_a), averaged within event and then across events: **-0.0079**. 95% bootstrap CI -0.0381 to +0.0231; t-test p = 0.612.
- Episode level: alert side won 0.231 of the time vs mean p_a 0.206.
- **Decision: NULL.** No excess detectable at this sample size (the feasibility MDE was about 0.04 to 0.05). This is a null result, stated plainly.

## Secondary (they decide nothing)

| analysis | units | markets | episodes | mean excess | 95% CI | t-test p |
|---|---|---|---|---|---|---|
| market unit | 556 | 556 | 2,083 | -0.019 | -0.046 to +0.008 | 0.157 |
| series unit | 312 | 556 | 2,083 | -0.008 | -0.044 to +0.028 | 0.645 |
| t_a < T_dec - 24 h | 371 | 467 | 1,882 | +0.011 | -0.025 to +0.049 | 0.555 |
| $1,000, cap 0.35 | 692 | 891 | 3,661 | -0.009 | -0.031 to +0.014 | 0.446 |
| $10,000, cap 0.35 | 203 | 246 | 701 | +0.007 | -0.040 to +0.058 | 0.771 |
| $2,500, cap 0.20 | 313 | 390 | 1,179 | -0.003 | -0.034 to +0.030 | 0.872 |
| category: military/government | 411 | 517 | 1,903 | -0.007 | -0.038 to +0.025 | 0.660 |
| category: company | 23 | 26 | 130 | +0.004 | -0.104 to +0.127 | 0.953 |
| category: appointment | 7 | 10 | 36 | -0.108 | -0.225 to +0.034 | 0.181 |
| category: award | 2 | 3 | 14 | +0.067 | -0.067 to +0.202 | 0.705 |
| category: central bank | 0 | 0 | 0 | n/a | n/a to n/a | n/a |
| period P1 | 373 | 446 | 1,595 | -0.009 | -0.043 to +0.025 | 0.589 |
| period P2 | 77 | 110 | 488 | -0.009 | -0.074 to +0.063 | 0.791 |
| v2's 165 markets (seen in v2 work) | 114 | 139 | 784 | +0.034 | -0.022 to +0.093 | 0.246 |
| markets new in v3 (out of sample) | 350 | 417 | 1,299 | -0.021 | -0.055 to +0.014 | 0.231 |


Unit is the event unless the row says otherwise.

## Calibration (episode level, primary set)

| p_a band | episodes | mean p_a | share won | excess |
|---|---|---|---|---|
| 0.0-0.1 | 401 | 0.062 | 0.075 | +0.012 |
| 0.1-0.2 | 581 | 0.149 | 0.141 | -0.008 |
| 0.2-0.3 | 641 | 0.249 | 0.296 | +0.047 |
| 0.3-0.4 | 433 | 0.335 | 0.390 | +0.056 |
| 0.4-0.5 | 27 | 0.441 | 0.407 | -0.034 |


## FFIC markets (descriptive only)

Main definition, kept episodes, markets not excluded. FFIC markets outside v2's candidate list have no outcome in this data, because only the candidate list carries outcomes; those episodes show n/a.

| case | markets | episodes | with outcome | mean excess |
|---|---|---|---|---|
| fficd-001 2024 U.S. Presidential Election | 3 | 44 | 0 | n/a |
| fficd-002 October 2024 Iran strike on Israel | 1 | 2 | 0 | n/a |
| fficd-003 2026 U.S.-Iran Conflict Cluster | 5 | 35 | 33 | +0.691 |
| fficd-004 January 2026 U.S.–Venezuela / Maduro operation cluster | 9 | 42 | 30 | -0.115 |
| fficd-005 Bitcoin ETF SEC approval | 1 | 1 | 0 | n/a |
| fficd-007 FTX / SBF case cluster | 3 | 12 | 9 | -0.049 |
| fficd-008 Romanian presidential election 2024-2025 | 1 | 3 | 0 | n/a |


## Notes

- The 165 v2 markets were used, with their outcomes, in the v2 model work on 2026-11-18. The 'markets new in v3' row is the clean out-of-sample check.
- Excess is before fees and spread. One episode can involve several wallets; no wallet is named.
