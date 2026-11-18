# Model v2 summary (2026-11-18)

**Verdict: the model does not beat the market price.** At unit level it is no better than price (log loss +0.0014 worse, CI spans zero). At market level the point estimate is slightly better (Brier -0.008) but the interval spans zero (n = 47 markets). No demonstrated edge, and no clear persistence of past winners. Wording: any wallet-level output here is "informed flow" or "worth a look", never an identification; this is not evidence of insider trading by anyone.

## 1. Data (sample sizes)
- Universe rule: `rules/model_v2_universe.md` (written before any pull; two dated amendments, both before trade pulls). 254,832 closed Gamma markets pulled for 2025-01 to 2026-10 (after repairing the 2,000-row cap on 95 windows); 4,309 pass the text screen, 4,192 are <= $12M volume; the 165 highest-volume of those were fetched (so all have $3.7M-$11.9M volume, which is a selection bias: no small markets, and the biggest markets such as Fed meetings and the Iran strikes above $12M are out).
- 165 markets, 5,798,770 fills (maker+taker), 306,168 wallets, 590,721 wallet x market x side positions at close - 1 h. Categories: 108 military/government, 35 company, 16 appointment, 3 award, 3 central bank.
- Wallet stats (join date, markets, lifetime volume) fetched for the 59,074 wallets with >= $100 in a unit (0 errors); the other 247,094 wallets are not in the model.
- **Gamma `closedTime` lags the real event** (median market already at 0.001/0.999 one hour before close). So the model uses a decision time T_dec (price leaves 0.05-0.95 for good) instead of close - 1 h; both position sets are stored.
- Modelled units: 102,413 (>= $100, wallet stats available, net long at decision), 44,859 wallets, 155 markets. Train: 106 markets resolved before 2026-04-01 (68,982 units). Validation: 49 markets (33,431 units).
- Every exclusion with a reason: `data/v2/exclusions.csv.gz`; fetch log `data/v2/fetch_log.csv`.

## 2. Persistence (step 2)
Top 5% by mean excess win rate (won - price paid) on markets resolved in 2025, min 5 markets: 89 of 1778 wallets (cutoff +0.221; mean +0.302 in 2025).
On 2026 markets, mean excess per wallet (bootstrap over wallets, 95%):
- top group: +0.037 [-0.047, +0.115], n = 57 wallets (377 units)
- all other wallets: -0.016 [-0.020, -0.011], n = 25,782
- other wallets that also had >= 5 markets in 2025: -0.002 [-0.015, +0.010], n = 1,151
- difference top minus all others: +0.053 [-0.030, +0.128]; minus eligible others: +0.040 [-0.043, +0.118].
Reading: the 2025 winners fell from +0.30 to about +0.04 in 2026, i.e. almost all of it was luck or regression to the mean. The point estimate is above the others, but the interval includes zero, so I cannot claim persistence and cannot rule out a small amount. Excess here is measured against the price paid, with positions as at decision time.

## 3. Validation against market price (step 3)
Logistic regression of won with logit(price paid) as a fixed offset, L2 (lambda = 100, chosen on an inner time split). Features known at trade time (approximations in the process log).
- **Unit level, validation (n = 33,431 units, 49 markets):** log loss market 0.4309 vs model 0.4323 (diff +0.0014, CI -0.0020 to +0.0043); Brier 0.1418 vs 0.1421 (diff CI -0.0012 to +0.0016). Bootstrap over markets. The model is not better than price.
- **Market level** (price adjusted by USD-weighted score of net buying in the last N hours; N = 24 chosen on training only; evaluation points at 25/50/75% of a market's life where price was still 0.03-0.97; train 250 points / 100 markets; validation 114 points / 47 markets): Brier market 0.1740 (CI 0.106-0.248) vs model 0.1656 (CI 0.110-0.228); difference -0.0083, CI -0.031 to +0.011. Log loss 0.5162 vs 0.4973 (diff CI -0.085 to +0.034). Not distinguishable from zero. Fitted gamma is negative (-5.04): in training, buying by high-score wallets preceded the opposite outcome, which makes no story and is most likely noise. Calibration table: `data/results/v2_calibration.csv` (8 bins, 3 to 29 points per bin; too sparse to read much into).
- **The 7 documented wallets** (`data/labels/documented_wallets.csv`; sanity check, not evaluation): only the Maduro market is in this universe. The three Maduro wallets that traded it (0x31a5.., 0xa72d.., 0x6baf..) rank 330, 427 and 386 of 1,187 units (percentile 72, 64, 67 within that market). That is above the middle but nowhere near the top; the model does not single them out. The Nobel and Iran markets of v1 are not among the 165, so the other four are not tested here (those wallets also appear in other markets: details in `data/results/v2_analysis.json`, not meaningful as a check).

## 4. Coefficients in plain words
Per 1 standard deviation of the feature, change in log-odds of winning beyond what the price already says (95% bootstrap over training markets, 200):

| feature | coefficient | 95% CI |
|---|---|---|
| log_age | -0.0002 | -0.040 to +0.043 |
| share_event | +0.0004 | -0.088 to +0.101 |
| log_usd | -0.0020 | -0.433 to +0.432 |
| log_rel_size | +0.0831 | -0.351 to +0.470 |
| conviction | -0.1767 | -0.276 to -0.092 |
| log_hours_to_end | +0.0172 | -0.115 to +0.165 |
| log_prior_markets | +0.0040 | -0.032 to +0.045 |
| prior_excess | -0.0005 | -0.048 to +0.062 |

Only conviction has an interval that excludes zero: positions that were closer to gross (the wallet did not sell part of it) won slightly less than their price implied. That is small and I would not read it as a mechanism. Account age, size, share of volume, time to deadline, number of prior markets and track record are indistinguishable from zero. Several are collinear (USD size and relative size), which is why those intervals are wide. The point estimates are tiny: the data say these features add almost nothing beyond price.

## 5. The 10 locked forward-test predictions
Snapshot 2026-11-18T00:58:42Z; file `prereg/forward_test_locked.csv`, SHA-256 `b0c2eec27373b5021df4a7268bdd78ac59263d758ea821e2d6d15e7211e480fb` (in `prereg/forward_test.md`). Success rule: model Brier < market Brier over the 10, plus hit rate where |diff| >= 5 points (n = 3 such markets). Not to be scored until after 2026-12-10 (`scripts/score_forward_test.py`, not run).

| # | question | market | model | diff (pts) | direction | wallets driving |
|---|---|---|---|---|---|---|
| 1 | Will the Fed increase interest rates by 25 bps after the December 2026 meeting? | 0.930 | 0.752 | -17.8 | model below market | 101 |
| 2 | US announces end of Iranian blockade by November 30, 2026? | 0.047 | 0.101 | +5.4 | model above market | 47 |
| 3 | Israel x Iran ceasefire continues through November 30? | 0.850 | 0.737 | -11.3 | model below market | 70 |
| 4 | Will Pedro Sánchez be the next Prime Minister of Spain? | 0.145 | 0.245 | +10.1 | model above market | 49 |
| 5 | Pete Hegseth out as Secretary of Defense by November 30? | 0.037 | 0.065 | +2.8 | model above market | 14 |
| 6 | Next White House Press Secretary announced by November 30, 2026? | 0.180 | 0.182 | +0.2 | model above market | 8 |
| 7 | Will Predict.fun launch a token by November 30, 2026? | 0.126 | 0.170 | +4.4 | model above market | 76 |
| 8 | US x Iran Effective Ceasefire by November 22? | 0.410 | 0.436 | +2.6 | model above market | 65 |
| 9 | Will Anthropic have the best AI model at the end of November 2026? | 0.090 | 0.099 | +0.9 | model above market | 25 |
| 10 | Russia x Ukraine ceasefire agreement by November 30, 2026? | 0.030 | 0.060 | +2.9 | model above market | 11 |

Note: the Fed row shows the model 17.8 points below a 0.93 market; given the null at validation I would expect that to be noise. One selected market (Spanish prime minister) is election-like and slipped through the keyword screen; it stays in because the rule was fixed first.

## 6. What failed or was skipped
- The model has no demonstrated edge; the forward test has n = 10 and cannot validate it.
- Coefficients, N and gamma were frozen after validation was seen (stated in `rules/frozen_v2.md`); validation is therefore not a clean test of anything tuned later. Only the forward test is clean.
- Selection bias: only the highest-volume small-group markets ($3.7M-$11.9M); the keyword screen is imperfect in both directions (not read market by market).
- Wallets under $100 and wallets without stats are excluded (247,094 wallets; 3,361 units with no stats).
- "Share of volume in event", "prior markets" and prior track record are computed from the 165-market dataset only, not lifetime. "Hours before close" is hours to the scheduled end date. Unit features use positions up to T_dec, so market-level scoring at earlier evaluation points leaks a little future position building.
- T_dec uses the market's price path (post hoc); fine for building units, not usable as a live feature.
- Dedup on a composite key (as in v1) may remove some real fills (dupes in `fetch_log.csv`). Positions from splits/merges or neg-risk conversions are not visible in fills.
- One Gamma day (2025-12-31) still hit the 2,000-row cap; possible small gap.
- Not done: separate sensitivity on the close - 1 h positions, event-cluster features, on-chain funding, the 400-page limit never bound, so no market was dropped for it.
- Git: a 1.6 GB raw dump was committed by mistake locally and removed from the unpushed history before the first push; no effect on content.
