# Frozen v2 (model v2: outcome-learned detector)

**Frozen:** 2026-11-18 (UTC), committed before any forward-test market was selected or scored.
**Honest status:** the coefficients, N and gamma were fit on the 106 training markets (resolved before 2026-04-01) and then the 49 validation markets were looked at (results in `data/results/v2_summary.md`). Nothing below was changed after seeing validation. The validation set is NOT a clean test of any later tweak; the only clean test is `prereg/forward_test.md`.
Machine-readable copy: `rules/frozen_v2.json`. Code: `src/v2_features.py`, `src/v2_06_analysis.py`, `src/v2_07_forward.py`.

## Unit and sample
Unit = wallet x market x side with a net-long position at decision time (price path leaves 0.05-0.95 for good; for open markets: now). Modelled units: at least USD 100 bought, wallet stats available. n_train_units = 68,982 (106 markets), n_val_units = 33,431 (49 markets).

## Unit model
`logit P(won) = intercept + sum_j coef_j * z_j + logit(price paid)`; z = (feature - mean) / sd (train); the price offset has a fixed coefficient of 1. L2 penalty lambda = 100 (chosen on an inner time split of training), intercept unpenalised.

| feature | coef | 95% CI (bootstrap over training markets, 200) | train mean | train sd |
|---|---|---|---|---|
| log_age | -0.00021 | [-0.040, +0.043] | 4.3136 | 1.8952 |
| share_event | +0.00040 | [-0.088, +0.101] | 0.5876 | 0.3942 |
| log_usd | -0.00199 | [-0.433, +0.432] | 6.5086 | 1.5095 |
| log_rel_size | +0.08310 | [-0.351, +0.470] | 0.3326 | 1.4963 |
| conviction | -0.17674 | [-0.276, -0.092] | 0.4888 | 0.4671 |
| log_hours_to_end | +0.01720 | [-0.115, +0.165] | 6.0533 | 1.9367 |
| log_prior_markets | +0.00403 | [-0.032, +0.045] | 0.7624 | 1.0610 |
| prior_excess | -0.00051 | [-0.048, +0.062] | 0.0020 | 0.0484 |

Feature definitions: log_age = ln(1 + days from join date to first buy); share_event = wallet USD in this event's markets / wallet USD in all dataset markets up to its last pre-decision buy; log_usd = ln(USD bought); log_rel_size = ln(USD / median USD of units in the market); conviction = net shares / gross shares bought, in (0,1]; log_hours_to_end = ln(1 + hours from first buy to scheduled endDate, clipped 0..8760); log_prior_markets = ln(1 + n prior dataset markets resolved before first buy); prior_excess = mean(won - price paid) over those prior units x n/(n+5).
Score s = sum_j coef_j * z_j (no intercept, no offset).

## Market level
At snapshot time t: Z = sum over buys in the last N = 24 hours of sign x USD x s / sum USD (sign +1 Yes, -1 No; wallets without a score count s = 0).
`p_model = sigmoid(logit(p_mkt) + gamma * Z)`, gamma = -5.0421 (fit on training evaluation points, N chosen by training log loss among 1, 3, 6, 12, 24, 48, 72; scores for training units were out-of-fold).
p_mkt = median of the last 10 fills' implied Yes price.
Note the sign: gamma is NEGATIVE. In training, buying by high-score wallets preceded the opposite outcome. Not an interpretation, just the fitted value; given the null at unit level it is probably noise.

## Thresholds
- "Model and market differ" = |p_model - p_mkt| >= 5 percentage points.
- Forward-test success rule: in `prereg/forward_test.md`.
