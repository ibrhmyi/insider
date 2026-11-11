# Control match table

Score = |ln(vol_control/vol_target)| + 5*|median_pre_price_control - median_pre_price_target| + 0.1*days_between_closes.
Pre-resolution price = YES-token price-history points (12h grain, the only grain still available for these dates) excluding the final 3h before close.
Candidate pool: Gamma crypto 'X above $Y' markets closing within +-7 days of the target, volume > $200k, top-40 by volume. Lowest score chosen.

Added screen (after the first Nobel control failed): control must have maker+taker notional / Gamma volume ~1 (feed complete) and a meaningful share of taker notional at contested prices 0.02-0.98.

| Insider-possible market | Vol | Pre-res YES median [min,max] | Matched control | Vol | Pre-res YES median [min,max] | Days apart | Score | Feed ratio | Contested share | Match quality / caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| US military action against Iran by Sunday? | $3.73M | 0.145 [0.105,0.165] | Bitcoin above $110,000 on June 17? | $0.98M | 0.090 [0.000,0.525] | 4.4 | 2.05 | 1.068 | 0.956 | WEAK: control 3.8x smaller volume, closes 4.4 days earlier; no crypto-threshold market in Jun 15-29 2025 matched the 10-17% price band with similar volume. |
| Will María Corina Machado win the Nobel Peace Prize in 2025? | $2.24M | 0.018 [0.005,0.728] | Bitcoin Up or Down - October 14, 5PM ET | $0.92M | 0.500 [0.500,1.000] | 4.5 | 3.75 | 1.003 | 0.992 | SUBSTITUTE: first choice (Solana >$280 Oct 10, score 0.09) rejected - 0% contested trading, incomplete-looking feed. All Oct-2025 'price above' markets failed the same screen. This hourly Up/Down market passes the screen but trades near 0.5, not Machado's low band, and is 0.41x the volume. |
| Maduro out by January 31, 2026? | $10.97M | 0.145 [0.055,0.245] | Will the price of Bitcoin be above $94,000 on January 5? | $1.17M | 0.080 [0.000,0.195] | 2.3 | 2.80 | 0.994 | 0.689 | WEAK on volume: control 9.4x smaller (largest crypto-threshold market that week was ~$1.2M). Price band and calendar close. |

Runner-up candidates are stored in `data/raw/control_match_candidates.json`.
