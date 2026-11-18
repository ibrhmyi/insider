# Forward test of model v2: pre-registration

**Written:** 2026-11-18 (UTC), before any forward-test market was selected or scored. Model is frozen in `rules/frozen_v2.md` / `.json` (committed earlier).
Wording: the model output is "informed flow"/"worth a look" signal at best; it does not identify anyone.

## Selection rule for the 10 markets
From Gamma, take markets that are: open (`closed=false`, accepting orders), binary Yes/No, with scheduled `endDate` from 2026-11-19 to 2026-12-09 (so they can resolve before 2026-12-10); lifetime volume at least USD 50,000; passing the same text screen as `rules/model_v2_universe.md` (small-group decision: military/government action, award, appointment, central-bank decision, company announcement; excluding sports, crypto prices, elections, weather, statistics releases, mention-markets), implemented by `src/v2_01_markets.py` functions; and with market price (median of last 10 fills) between 0.03 and 0.97 at the snapshot. At most 1 market per event. Rank by lifetime volume, descending, and take the top 10. No model output is used in selection. Order of events: this file is committed first; then the markets are selected and the model is run at ONE timestamp; then `prereg/forward_test_locked.csv` is written, hashed and pushed.

## Recorded at the snapshot (one UTC timestamp)
question, slug, market price (Yes), model probability (Yes), direction of difference (model above / below / same), difference in points, number of wallets driving it (wallets with a scored buy in the last 24 h), snapshot timestamp. Computation exactly as `rules/frozen_v2.md`, code `src/v2_07_forward.py`.

## Scoring (run later with `scripts/score_forward_test.py`, not run now)
Resolution = Gamma outcome prices exactly 1/0 for Yes by 2026-12-20. Markets still open then, voided or 50/50 are reported as missing and left out of every metric (the count is reported).
1. **Primary success criterion:** mean squared error (Brier) of model probability < Brier of market price, over the resolved markets of the 10.
2. **Secondary:** among markets where |model - market| >= 5 percentage points, hit rate = share where the model moved toward the realised outcome (model above market and outcome Yes, or model below market and outcome No). Reported with n.
3. Reported plainly whatever the result. With n = 10, one market can flip either metric: this test can only show an obvious failure or give weak support, and cannot validate the model. No metric, threshold or market may be changed after the snapshot.

## SHA-256 of prereg/forward_test_locked.csv
(filled in after the file is written; see below)
