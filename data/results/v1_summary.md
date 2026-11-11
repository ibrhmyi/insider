# v1 results: wallet-market suspicion screen and follow-on test (PILOT)

Rules: `rules/frozen_v1.md` (frozen and committed before any v1 feature was computed). 3 insider-possible markets; this is a pilot, not a validated model.
A high score means **consistent with informed trading / unusual activity for review**. It never identifies an owner or proves insider trading.

## Finding #1 (v0, unchanged)
Ripple after large trades did not differ between insider-possible markets and BTC controls: +1.98 vs +1.58 extra wallets (n = 147 vs 50 seeds, permutation p = 0.72). See `data/results/comparison_summary.md`. BTC controls are kept only as an appendix.

## Layer 1: screen and timestamp-permutation null

| market | pre-news buyers (wallets) | score >= 4 observed | null mean | null 95th pct | null range | p (1,000 perms) |
|---|---|---|---|---|---|---|
| iran | 977 | 95 | 95.5 | 97 | 91-98 | 0.814 |
| maduro | 2608 | 39 | 43.0 | 51 | 27-61 | 0.829 |
| nobel | 3554 | 137 | 88.2 | 99 | 68-110 | 0.001 |

Only **Nobel** has more high-score wallets than random timing produces. Iran and Maduro are at or below the null: their high scores come mostly from flags that do not depend on timing.

Score distribution (wallets per score 0-6): iran: {'1': 75, '2': 503, '3': 304, '4': 82, '5': 12, '6': 1}; maduro: {'0': 256, '1': 1247, '2': 850, '3': 216, '4': 28, '5': 9, '6': 2}; nobel: {'0': 1797, '1': 557, '2': 595, '3': 468, '4': 93, '5': 42, '6': 2}

**F4 sensitivity** (high-score wallets per market): $1,000: iran 108, maduro 42, nobel 147; $2,500: iran 95, maduro 39, nobel 137; $10,000: iran 88, maduro 33, nobel 129

**Scorable trades vs v0:** v0 could compare iran 27, maduro 73, nobel 47 seeds (Nobel 38 unmatched). v1 scores every pre-news buyer: iran 977 wallets / 4308 buy fills (1275 in the last 6 h), maduro 2608 wallets / 9362 buy fills (640 in the last 6 h), nobel 3554 wallets / 9252 buy fills (3236 in the last 6 h). Run-up hours are now included.

**Flag firing rates** (share of pre-news buyers): iran: F1 26%, F2 3%, F3 33%, F4 10%, F5 71%, F6 100%; maduro: F1 14%, F2 2%, F3 28%, F4 5%, F5 73%, F6 23%; nobel: F1 9%, F2 2%, F3 23%, F4 3%, F5 31%, F6 38%.
- **F6 fires for 100% of Iran buyers**: the market lived ~49 h before T_news, so the 72 h timing flag is uninformative there and the Iran permutation null cannot test timing.
- **F5 (conviction) fires for 71-73%** of buyers in Iran and Maduro (most small wallets buy one side only), so it adds little discrimination.

## Validation against publicly documented wallets

| label | market | identifier | confidence | score | flags fired | rank / n | first score >= 4 (h before T_news) | F7 won | F8 dormant |
|---|---|---|---|---|---|---|---|---|---|
| MAD-CFTC-1 | maduro | Burdensome-Mix | charged | 6 | F1,F2,F3,F4,F5,F6 | 1 / 2608 | 30.0 | True | no |
| MAD-LOOK-1 | maduro | 0x31a5 | alleged | 6 | F1,F2,F3,F4,F5,F6 | 1 / 2608 | 30.0 | True | no |
| MAD-LOOK-2 | maduro | 0xa72d | alleged | 5 | F2,F3,F4,F5,F6 | 5 / 2608 | 8.3 | True | yes |
| MAD-LOOK-3 | maduro | SBet365 | alleged | 5 | F1,F3,F4,F5,F6 | 3 / 2608 | 2.3 | True | no |
| NOB-BLM-1 | nobel | dirtycup | alleged | 5 | F1,F2,F4,F5,F6 | 3 / 3554 | 5.5 | True | yes |
| NOB-WSJ-1 | nobel | 6741 | alleged | 4 | F1,F3,F4,F6 | 45 / 3554 | 10.3 | True | yes |
| IRN-ACDC-1 | iran | Skoobidoobnj | alleged | 4 | F3,F4,F5,F6 | 15 / 977 | 28.3 | True | yes |
| IRN-ACDC-2 | iran | 0xoracle | alleged | 5 | F2,F3,F4,F5,F6 | 3 / 977 | 1.2 | True | no |

- **Recall:** 7 of 7 distinct documented wallets (8 labels; the CFTC handle and Lookonchain's 0x31a5 resolve to the same wallet) score >= 4 at the frozen $2,500 F4 threshold. Sensitivity: $1,000: 7/7; $2,500: 7/7; $10,000: 6/7 (below 4 at $10,000: Skoobidoobnj).
- Chance check (if the high-score set were random within each market): iran P = 0.0094; maduro P = 3.1e-06; nobel P = 0.0015.
- **Circularity caveat:** journalists and Lookonchain found these wallets with similar cues (new, focused, large longshot bets before news), so high recall is partly by construction. It shows the screen reproduces public reporting, not that it finds hidden cases.
- 'Hours early' is retrospective: F6 uses T_news, which is not known in real time.

### Precision proxy (post-hoc F7/F8; never in the score)

| size band | group | n | win rate (F7) | dormant 30 d (F8) |
|---|---|---|---|---|
| <1k | other | 6337 | 0.27 | 0.39 |
| <1k | score >= 4 | 213 | 0.52 | 0.39 |
| 1k-2.5k | other | 261 | 0.25 | 0.14 |
| 1k-2.5k | score >= 4 | 5 | 0.40 | 0.40 |
| 2.5k-10k | other | 173 | 0.29 | 0.06 |
| 2.5k-10k | score >= 4 | 31 | 0.48 | 0.42 |
| >=10k | other | 97 | 0.17 | 0.12 |
| >=10k | score >= 4 | 22 | 0.68 | 0.55 |

**Confound:** all three markets resolved in favour of the side that was the longshot for most of their life, so any longshot screen 'wins' more. Holding longshot buying fixed (F3 flagged), high-score wallets win **less** often than other longshot buyers: <1k 0.55 (n=180) vs 0.79 (n=1572); 1k-2.5k 0.50 (n=4) vs 0.68 (n=50); 2.5k-10k 0.58 (n=26) vs 0.75 (n=24); >=10k 0.45 (n=11) vs 0.71 (n=7). So F7 does **not** support precision here.
**Dormancy among winners** (same outcome held fixed): <1k: high 0.27 (n=110) vs other 0.26 (n=1727); 1k-2.5k: high 0.00 (n=2) vs other 0.15 (n=66); 2.5k-10k: high 0.47 (n=15) vs other 0.08 (n=51); >=10k: high 0.73 (n=15) vs other 0.12 (n=16). Larger high-score winners go dormant far more often, consistent with single-use accounts; partly mechanical because F1/F2 already select new, focused accounts.

### Price impact per $1,000 (taker buys; YES price of last fill as mid-price proxy; windows crossing T_news dropped)

| window | high-score median (n) | all others median (n) | p | others >= $2.5k median (n) | p |
|---|---|---|---|---|---|
| 5m | 0.0001 (251) | 0.0000 (5138) | 0.300 | 0.0017 (215) | 0.862 |
| 60m | 0.0023 (220) | 0.0000 (4974) | 0.009 | 0.0013 (208) | 0.170 |

Against similarly sized other wallets there is **no significant difference** in price impact per dollar. We do not reproduce Gomez-Cram et al.'s larger impact for suspected insider accounts (different proxy, 3 markets).

## Layer 2: do others follow high-score wallets more than matched established-wallet buys?

Follower types: whales = top 1% lifetime volume (>= $22,488,082; 84 wallets), bots = >= 50 trades/day since join (282 wallets).
A seeds without any B match dropped: 79 (30 min), 71 (120 min). Windows overlapping T_news +-15 min excluded: A 30 min: 38, A 120 min: 95, B 30 min: 143, B 120 min: 257 (listed in `v1_layer2_excluded_windows.csv`).

| window | outcome | scope | A seeds (wallets) | mean A | mean B | A - B [95% CI] | p (sign-flip) | wallet-clustered A - B (p) |
|---|---|---|---|---|---|---|---|---|
| 30 | wallets | pooled | 273 (211) | 26.81 | 28.69 | -1.88 [-3.56, -0.12] | 0.033 | -1.31 (0.197) |
| 30 | wallets | iran | 117 (88) | 10.24 | 20.73 | -10.49 [-12.22, -8.81] | 0.000 | -10.57 (0.000) |
| 30 | wallets | maduro | 47 (31) | 3.55 | 9.05 | -5.50 [-7.21, -3.83] | 0.000 | -4.48 (0.000) |
| 30 | wallets | nobel | 109 (92) | 54.63 | 45.71 | 8.93 [6.18, 11.80] | 0.000 | 8.61 (0.000) |
| 30 | usd | pooled | 273 (211) | 12812 | 16651 | -3839 [-5129, -2588] | 0.000 | -3401 (0.000) |
| 30 | price_move | pooled | 273 (211) | 0.001 | -0.003 | 0.004 [-0.003, 0.011] | 0.240 | 0.002 (0.593) |
| 30 | whales | pooled | 273 (211) | 1.91 | 1.92 | -0.01 [-0.19, 0.18] | 0.945 | -0.02 (0.829) |
| 30 | bots | pooled | 273 (211) | 2.91 | 2.92 | -0.01 [-0.24, 0.22] | 0.931 | -0.00 (0.989) |
| 120 | wallets | pooled | 224 (177) | 79.79 | 89.53 | -9.73 [-14.40, -5.34] | 0.000 | -8.25 (0.002) |
| 120 | wallets | iran | 104 (77) | 37.23 | 68.67 | -31.44 [-37.09, -25.83] | 0.000 | -31.05 (0.000) |
| 120 | wallets | maduro | 40 (31) | 11.50 | 21.33 | -9.83 [-13.33, -6.57] | 0.000 | -9.14 (0.000) |
| 120 | wallets | nobel | 80 (69) | 169.28 | 150.73 | 18.54 [11.73, 25.02] | 0.000 | 17.60 (0.000) |
| 120 | usd | pooled | 224 (177) | 48526 | 63640 | -15115 [-18313, -11976] | 0.000 | -13355 (0.000) |
| 120 | price_move | pooled | 224 (177) | -0.001 | 0.001 | -0.002 [-0.010, 0.006] | 0.677 | 0.002 (0.699) |
| 120 | whales | pooled | 224 (177) | 3.88 | 4.60 | -0.73 [-1.06, -0.41] | 0.000 | -0.68 (0.000) |
| 120 | bots | pooled | 224 (177) | 7.53 | 7.56 | -0.04 [-0.47, 0.40] | 0.867 | 0.06 (0.814) |

**Result:** pooled, high-score buys attract **fewer** same-direction followers than matched established-wallet buys, with no difference in whale or bot followers at 30 min and slightly fewer whales at 120 min. This does **not** support the claim that whales and bots piggyback on suspicious wallets in general. **Nobel is the exception** (more followers after high-score buys), consistent with the publicly reported pre-announcement spike, where many traders bought the same side within minutes.
**Limitation:** B seeds are matched on market, size (+-30%) and time (+-6 h), not on local activity; within 6 h activity varies a lot, so part of the differences can reflect busier or quieter moments rather than trader type. Seeds from the same wallet are not independent (see wallet-clustered column).

## What could not be computed, and why
- **On-chain funding sources:** not done. Polygonscan, Dune and Bitquery are not reachable from this session and no API key is available.
- **Additional markets (2-3 more):** not added in this session; time went to the frozen screen, permutation null and validation.
- **Mid-price impact:** no historical order-book mid-price for these dates (price history is 12-hour grain); last-fill price used as proxy.
- **Threshold sources:** the Bock & Guenthoer PDF and ACDC figures could not be opened from this session; thresholds follow the brief as cited.
- **Documented wallets:** only 7 public cases (1 charged, 6 alleged); Bloomberg's two other Nobel accounts were not named in the coverage found.
- **F2 'event cluster':** measured on the single market, not sibling markets in the same event (e.g. other Maduro dates), which can understate focus.
- **Duplicates:** with maker rows, the composite key removed 199 / 420 / 14 rows (Iran / Maduro / Nobel); some may be genuine repeated fills (no log index in the API).

All high-score wallets that are not in public reporting are **unusual activity for review, not insiders**. No wallet addresses are listed in this summary except those already published.
