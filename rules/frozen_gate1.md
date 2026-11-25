# Gate 1: frozen test (written before any outcome was loaded)

**Frozen:** 2026-11-25 (UTC). Committed and pushed BEFORE `src/gate1_run.py` loads any outcome.
Up to this commit, no outcome, resolution value, payout, PnL or win rate of any market in this universe has been loaded,
printed or computed in the Gate 1 work (see the 2026-11-24 and 2026-11-25 log entries). The v2 model work (2026-11-18) did use outcomes
of the 165 v2 markets. Those markets are part of this universe; this is stated, not hidden.
Machine-readable copy: `rules/frozen_gate1.json`. Nothing below may change after the run. A bug fix is allowed only if it is
logged with the result before and after the fix.

## Question
When a wallet builds a large, cheap position on one side of a market decided by a small group, does that side win more often
than the market price right after the alert implies? (Informed flow worth a look, not proof of insider trading.)

## Data (fixed by hash)
- Episodes: `data/v3/episodes.csv.gz` (sha256 `8bb99391...e1b1c`), made by `src/feasibility_gate1.py` (sha256 `be30a8bf...bc8a`) from the
  fill cache listed in `data/v2/fills_manifest.csv`.
- Markets: `data/v3/market_info.csv` (sha256 `6e97cd77...62c5`).
- Outcomes (loaded only by `src/gate1_run.py`): `yes_won` in `data/v2/markets_candidates.csv`. It is set by the v2 rule: Gamma outcome prices
  exactly [1, 0] or [0, 1] after close; everything else was excluded before any trade pull. All 1,821 usable core markets have it.

## Episode (as in the feasibility report)
On one token side, a wallet's net buys (buy USD - sell USD of that token, same wallet) within a rolling 24 h window reach >= $2,500
at a buy VWAP <= 0.35. A trigger is the buy fill where this first becomes true (rising edge). Same-side triggers <= 24 h apart chain
into one episode, and t_a = its first trigger. p_a = size-weighted price of the episode's token over all fills in (t_a, t_a + 10 min];
else the last fill strictly before t_a; else the trigger fill. Keep the episode if p_a < 0.50 and t_a < T_dec.
T_dec is the v2 price-path rule, or the first news time for the v1 markets.

## Universe (primary)
Core markets: v2's 165, v2's 1,835 unfetched military/government markets, the 58 over-$12M military/government markets, and v1
Maduro, Nobel and Iran. Each is counted once. Excluded: T_dec within 24 h of the first fill (238). FFIC-only markets are not in the
primary universe.

## Primary test (the only one that decides)
- y = 1 if the episode's side won (side Yes: `yes_won`; side No: 1 - `yes_won`). Excess e = y - p_a.
- Unit = Gamma event (`event_id`; a market without one is its own unit). Event value = the mean of e over all kept main-definition
  episodes in the event's core markets. Estimate = the unweighted mean of event values over events with at least one episode.
- 95% CI: percentile bootstrap over events, 10,000 resamples, numpy seed 20261125. Also reported: a one-sample t-test on the event values (two-sided).
- **Decision.**
  - **POSITIVE** if the CI lower bound > 0: alert sides win more often than p_a implies.
  - **NEGATIVE** if the CI upper bound < 0.
  - **NULL** otherwise: no excess detectable at this size. The feasibility MDE for this cell was 0.039 to 0.052.
- Excess is before fees and spread; a POSITIVE result is not a trading profit.

## Secondary (reported with CIs; they decide nothing, and no claim rests on them)
Same estimator for each of these:
1. Market unit.
2. Series unit (Gamma series, else event).
3. t_a < T_dec - 24 h.
4. Variants $1,000 / $10,000 at cap 0.35, and $2,500 at cap 0.20.
5. By category.
6. By period (P1: resolved up to 2026-05-05; P2: 2026-05-06 to 2026-10-31).
7. Calibration table: mean y vs mean p_a by p_a band (0-0.1, 0.1-0.2, 0.2-0.3, 0.3-0.4, 0.4-0.5), episode level.
8. The 165 v2 markets alone vs the markets new in v3. The first set was seen in the v2 work; the second is clean out-of-sample.
9. FFIC markets: counts and mean excess by case, descriptive only.

## Reporting rules
Results go to `data/results/gate1_result.md` and `.json`. The null is reported plainly if it is null, with n events, n markets and n episodes.
No wallet is called an insider; no full wallet address appears.
