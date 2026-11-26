# Gate 2 result

Frozen test: `rules/frozen_gate2.md` (freeze commit 48fa175ed2e2dcee7cd3e9d5485e1e6613f7ebc5 2026-11-26T03:29:07+00:00). Input hashes: match. Run once by `src/gate2_run.py`. Excess = outcome - p_a, before fees and spread. Unit = Gamma event, equal weight. Intervals: two-sided 97.5% bootstrap (10,000 resamples, seed 192), Bonferroni for two signals.

## 1. Verdict

| signal | verdict | mean excess | 97.5% interval | events | markets | episodes | won | mean p_a |
|---|---|---|---|---|---|---|---|---|
| A (price-insensitive accumulation) | **NULL** | -0.005 | -0.064 to +0.054 | 242 | 286 | 537 | 0.300 | 0.292 |
| B (deadline choice) | **NULL** | -0.009 | -0.091 to +0.079 | 110 | 124 | 645 | 0.191 | 0.218 |


## 2. Counts

Primary: $2,500, std mode, core markets. Blind counts and power for every threshold and mode are in `data/results/gate2_power.md`. Ladders: 73 (311 markets). Share of primary episodes that overlap a Gate 1 episode (same market and side, within 24 h): A 51.2%, B 78.8%.


## 3. Robustness (decides nothing)


**Signal A**

| analysis | units | markets | episodes | mean excess | 97.5% interval |
|---|---|---|---|---|---|
| market unit | 286 | 286 | 537 | -0.009 | -0.063 to +0.047 |
| series unit | 171 | 286 | 537 | -0.001 | -0.067 to +0.067 |
| live-realistic (no T_dec rule or exclusion) | 248 | 293 | 544 | -0.009 | -0.067 to +0.049 |
| $1,000 | 370 | 447 | 872 | +0.001 | -0.045 to +0.046 |
| $10,000 | 109 | 124 | 190 | +0.030 | -0.059 to +0.125 |
| overlaps a Gate 1 episode | 168 | 192 | 275 | -0.000 | -0.071 to +0.073 |
| does not overlap Gate 1 | 138 | 161 | 262 | +0.005 | -0.073 to +0.086 |
| v2's 165 markets (seen in v2 work) | 83 | 99 | 195 | +0.056 | -0.047 to +0.161 |
| markets new in v3 | 171 | 187 | 342 | -0.027 | -0.096 to +0.044 |
| category: appointment | 4 | 4 | 8 | -0.039 | -0.357 to +0.390 |
| category: award | 2 | 3 | 5 | +0.215 | -0.267 to +0.697 |
| category: company | 17 | 20 | 32 | -0.042 | -0.209 to +0.149 |
| category: military/government | 219 | 259 | 492 | -0.004 | -0.065 to +0.060 |
| period P1 | 196 | 224 | 407 | -0.018 | -0.081 to +0.048 |
| period P2 | 48 | 62 | 130 | +0.045 | -0.077 to +0.178 |


**Signal B**

| analysis | units | markets | episodes | mean excess | 97.5% interval |
|---|---|---|---|---|---|
| market unit | 124 | 124 | 645 | -0.013 | -0.093 to +0.069 |
| series unit | 43 | 124 | 645 | -0.018 | -0.140 to +0.118 |
| live-realistic (no T_dec rule or exclusion) | 116 | 130 | 686 | -0.010 | -0.089 to +0.072 |
| $1,000 | 134 | 157 | 892 | -0.006 | -0.074 to +0.067 |
| $10,000 | 71 | 79 | 283 | +0.018 | -0.098 to +0.142 |
| overlaps a Gate 1 episode | 101 | 114 | 508 | +0.013 | -0.069 to +0.106 |
| does not overlap Gate 1 | 53 | 56 | 137 | -0.124 | -0.244 to +0.014 |
| v2's 165 markets (seen in v2 work) | 33 | 37 | 255 | +0.051 | -0.097 to +0.222 |
| markets new in v3 | 81 | 87 | 390 | -0.038 | -0.128 to +0.062 |
| category: military/government | 110 | 124 | 645 | -0.009 | -0.091 to +0.079 |
| period P1 | 79 | 86 | 435 | -0.003 | -0.103 to +0.105 |
| period P2 | 31 | 38 | 210 | -0.023 | -0.157 to +0.133 |
| B_last comparison (last deadline, descriptive) | 26 | 26 | 148 | +0.102 | -0.079 to +0.301 |
| B_last, live-realistic | 27 | 27 | 152 | +0.098 | -0.081 to +0.289 |


Units are events unless the row says otherwise.

## 4. Calibration by p_a band (episode level, primary sets)


**A**

| p_a band | episodes | mean p_a | share won | excess |
|---|---|---|---|---|
| 0.0-0.1 | 39 | 0.078 | 0.256 | +0.179 |
| 0.1-0.2 | 109 | 0.155 | 0.119 | -0.036 |
| 0.2-0.3 | 123 | 0.250 | 0.236 | -0.015 |
| 0.3-0.4 | 136 | 0.349 | 0.375 | +0.026 |
| 0.4-0.5 | 130 | 0.450 | 0.446 | -0.004 |


**B**

| p_a band | episodes | mean p_a | share won | excess |
|---|---|---|---|---|
| 0.0-0.1 | 150 | 0.063 | 0.100 | +0.037 |
| 0.1-0.2 | 175 | 0.147 | 0.206 | +0.058 |
| 0.2-0.3 | 141 | 0.245 | 0.234 | -0.011 |
| 0.3-0.4 | 97 | 0.350 | 0.258 | -0.092 |
| 0.4-0.5 | 82 | 0.446 | 0.171 | -0.275 |


**B_last**

| p_a band | episodes | mean p_a | share won | excess |
|---|---|---|---|---|
| 0.0-0.1 | 14 | 0.073 | 0.214 | +0.141 |
| 0.1-0.2 | 33 | 0.143 | 0.364 | +0.221 |
| 0.2-0.3 | 45 | 0.248 | 0.622 | +0.374 |
| 0.3-0.4 | 28 | 0.342 | 0.571 | +0.229 |
| 0.4-0.5 | 28 | 0.454 | 0.607 | +0.153 |


## 5. FFIC cases (descriptive only; hindsight-selected cases)

FFIC markets outside v2's candidate list have no outcome in this data (n/a).

| signal | case | markets | episodes | with outcome | mean excess |
|---|---|---|---|---|---|
| A | fficd-001 2024 U.S. Presidential Election | 3 | 28 | 0 | n/a |
| A | fficd-003 2026 U.S.-Iran Conflict Cluster | 5 | 17 | 16 | +0.516 |
| A | fficd-004 January 2026 U.S.–Venezuela / Maduro operation cluster | 3 | 10 | 9 | -0.302 |
| A | fficd-005 Bitcoin ETF SEC approval | 1 | 2 | 0 | n/a |
| A | fficd-007 FTX / SBF case cluster | 2 | 2 | 1 | -0.042 |
| A | fficd-008 Romanian presidential election 2024-2025 | 1 | 2 | 0 | n/a |
| B | fficd-003 2026 U.S.-Iran Conflict Cluster | 3 | 29 | 29 | +0.843 |
| B | fficd-004 January 2026 U.S.–Venezuela / Maduro operation cluster | 1 | 14 | 14 | -0.327 |


## 6. Example episodes (chosen without outcomes: the most wallets, then earliest)

*Unusual activity for review: this does not identify an owner or prove insider trading.*


**Signal A**

| market | side | t_a | p_a | wallets | outcome |
|---|---|---|---|---|---|
| US strikes Iran by February 28, 2026? | Yes | 2026-02-27 12:36 UTC | 0.200 | 50: 0x1270fc…, 0x1caa6a…, 0x1e5540…, 0x1fa1be… … | won |
| US x Iran permanent peace deal by June 15, 2026? | Yes | 2026-06-13 11:57 UTC | 0.259 | 49: 0x0619da…, 0x06ac70…, 0x076ba1…, 0x0e7ae1… … | won |
| US x Iran ceasefire by April 7? | Yes | 2026-04-07 19:53 UTC | 0.114 | 46: 0x011f2d…, 0x0484ce…, 0x08458f…, 0x162f6f… … | won |
| Khamenei out as Supreme Leader of Iran by February 28? | Yes | 2026-02-28 09:53 UTC | 0.174 | 41: 0x00425c…, 0x0a6d26…, 0x17ed7d…, 0x183a2a… … | won |
| US government shutdown Saturday? | Yes | 2026-01-24 18:46 UTC | 0.383 | 35: 0x090a0d…, 0x0c4f5b…, 0x17ce7c…, 0x21ff16… … | won |


**Signal B**

| market | side | t_a | p_a | wallets | outcome |
|---|---|---|---|---|---|
| Khamenei out as Supreme Leader of Iran by March 31? | Yes | 2026-02-14 22:40 UTC | 0.145 | 351: 0x00425c…, 0x00be7c…, 0x011f2d…, 0x031d98… … | won |
| US x Iran ceasefire by April 7? | Yes | 2026-04-06 01:59 UTC | 0.037 | 326: 0x00090e…, 0x000d25…, 0x002dcd…, 0x00425c… … | won |
| Khamenei out as Supreme Leader of Iran by February 28? | Yes | 2026-02-28 06:41 UTC | 0.106 | 323: 0x000d25…, 0x002cbc…, 0x00425c…, 0x026036… … | won |
| US military action against Iran before July? | Yes | 2025-06-11 09:11 UTC | 0.109 | 263: 0x00a611…, 0x010395…, 0x011f2d…, 0x039401… … | won |
| Khamenei out as Supreme Leader of Iran by January 31? | Yes | 2026-01-07 17:22 UTC | 0.120 | 169: 0x005a19…, 0x00e1e8…, 0x011f2d…, 0x019761… … | lost |


## Notes

- Gate 2 was proposed after the Gate 1 NULL, on the same markets. The 'markets new in v3' rows are the cleanest check for v2's earlier look at 165 markets; no clean holdout exists for Gate 1.
- Signal B only sees cached ladder rungs; v2's 3-markets-per-event cap hides some later deadlines.
