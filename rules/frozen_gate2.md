# Gate 2: two behavioural signals, frozen test (written before any Gate 2 outcome was loaded)

**Frozen:** 2026-11-26 (UTC). Committed and pushed BEFORE `src/gate2_run.py` loads any outcome. Machine-readable copy:
`rules/frozen_gate2.json`. Nothing below may change after the run. A bug fix is allowed only if it is logged with the result
before and after the fix.

**Stated, not hidden.** These signals were proposed after the Gate 1 NULL was known (2026-11-25), and Gate 1 used the outcomes of
the same markets. The v2 model work (2026-11-18) also saw the outcomes of v2's 165 markets. No Gate 2 episode was matched to an
outcome before this freeze. The blind counts and power are in `data/results/gate2_power.md`.

## Universe and data (fixed by hash)
- Gate 1 universe and exclusions (`rules/frozen_gate1.md`). Core = v2's 165, v2's unfetched military/government markets (1,835), the
  over-$12M military/government markets (58) and v1 Maduro/Nobel/Iran. A market is excluded if T_dec is within 24 h of its first fill.
  T_dec = the v2 price-path rule (first news time for v1).
- Fills: the local cache (`data/v2/fills_manifest.csv`). Episodes: `data/v3/gate2_episodes.csv.gz` (sha256 `8f998d6b...42bcf`),
  ladders: `data/v3/gate2_ladders.csv` (sha256 `c82530ff...0fe5`), both made by `src/gate2_signals.py` (sha256 `406dc96c...9f05`).
- Outcomes (loaded only by `src/gate2_run.py`): `yes_won` in `data/v2/markets_candidates.csv`.

## Signal A: price-insensitive accumulation
Per wallet x market x side, using only fills before T_dec:
- p0 = the price of the wallet's first buy on that side; it must be <= 0.35.
- The trigger is the wallet's first later buy fill (timestamp strictly after the first buy) at a price >= max(1.5 x p0, p0 + 0.03). At that point:
  - its net buys (buy USD - sell USD on that side) over fills with a strictly earlier timestamp must be >= $2,500;
  - its sell USD over those fills must be < 10% of its buy USD over them.
- t_a = the trigger time. p_a = the size-weighted price of the side's token over all fills in (t_a, t_a + 10 min]. If there are none, the
  last fill strictly before t_a; failing that, the trigger fill (as in Gate 1). Keep if p_a < 0.50 and t_a < T_dec. Direction = that side.
- Triggers on the same market side chain into one episode while consecutive triggers are <= 24 h apart; t_a = the first.

## Signal B: deadline choice
- **Ladder.** Markets in one Gamma series (else event) whose question, with its final "by ..." / "before ..." phrase removed, is
  identical; whose lives (Gamma start to min(end, resolution)) overlap; and that have >= 3 distinct deadlines (Gamma endDate).
  Only "by/before" questions are cumulative deadlines; "in <month>", "on <day>" and "between" questions ask about separate periods
  and are not ladders. 73 ladders, 311 markets; all listed in `data/v3/gate2_ladders.csv`.
- **Limitation.** Only cached markets can be ladder rungs. v2 capped each event at 3 markets, so later-deadline rungs outside the
  universe are not seen, and buys there are not counted.
- **Trigger.** At a Yes buy fill on ladder market m, which is not the ladder's last deadline:
  - the wallet's net Yes USD on m over (t - 24 h, t] must be >= $2,500;
  - its net Yes USD on all later-deadline cached rungs over the same window must be < 10% of that amount.
  The trigger is a rising edge; fills before T_dec of m only; m not excluded.
- t_a, p_a (Yes price), episode chaining and the keep rule are as in Signal A. Direction = Yes on m.
- **Comparison group B_last (descriptive only).** The same rule on the last deadline: net Yes on it >= $2,500 in 24 h, with < 10% on
  earlier rungs.

## Test (one per signal)
- y = 1 if the episode's direction won. Excess e = y - p_a.
- Unit = Gamma event (`event_id`, else the market). Event value = the mean e over the event's kept episodes. Estimate = the
  unweighted mean over events.
- Bootstrap over events: 10,000 resamples, numpy `default_rng(192)`, a separate generator per analysis.
- **PASS** if the estimate > 0 AND the lower bound of the two-sided 97.5% interval (percentiles 1.25 and 98.75) > 0. This is
  Bonferroni for the two signals at 5%. Otherwise **NULL**; a significant negative is reported as NULL (negative).
- Primary per signal: threshold $2,500, std mode (Gate 1 exclusions, t_a < T_dec), core markets only.

## Robustness (reported, not deciding)
Each is reported with the same estimator and 97.5% interval:
1. Market unit.
2. Series unit (Gamma series, else event).
3. Live-realistic: fills up to resolution - 1 h, no T_dec exclusion and no t_a < T_dec rule.
4. $1,000 and $10,000 thresholds.
5. Gate 1 overlap. A Gate 2 episode overlaps if a kept Gate 1 main-definition episode exists on the same market and side with
   |Δt_a| <= 24 h. Report the share that overlaps, and the excess for episodes that do and do not overlap.
6. B_last vs B.
7. By category and by period (P1 up to 2026-05-05; P2 2026-05-06 to 2026-10-31).
8. Calibration by p_a band (0.1 wide).
9. FFIC markets, descriptive only.
10. Five example episodes per signal, chosen without outcomes: the five kept primary episodes with the most wallets (ties: earliest
    t_a). Each shows market, time, p_a, outcome and wallet prefixes only.

## Reporting
`data/results/gate2_result.md`; `data/v3/gate2_episodes_scored.csv.gz` (episodes with outcome and excess). Nulls are reported
plainly with n. No wallet is called an insider; wallet prefixes only.
