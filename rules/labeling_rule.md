# Labeling rule: insider-possible vs. insider-impossible

**Written:** 2026-11-09T16:11:20Z (UTC). Frozen before any trade-level analysis.
**Basis:** the market's own resolution criteria (Polymarket market description + stated resolution source) only. No price, volume, or trade data may be used to assign a label.

## Rule

A market is labelled **insider-possible** when its outcome is fixed by a discrete decision, action, or deliberation of an identifiable small group (for example, a government or military chain of command, a prize committee, or an appointing authority) and that group, or people close to it, can know the outcome before the resolution source makes it public. A market is labelled **insider-impossible** when its outcome is set mechanically by a public, continuously observed data source at a pre-specified reference time (for example, an exchange or oracle price of BTC/ETH/SOL "above $X on date Y at time T"), so that nobody can know the resolving value before that reference time and no single small group decides it. A market that fits neither description is labelled **excluded** and not used in this pilot. Examples: sports results, elections, scheduled statistics releases (embargoed figures are known early by agency staff), and markets whose rules depend on subjective judgement. The label is assigned by reading the rules text and is recorded with a one-line justification in `data/markets.csv` (column `label_justification`).

## Known limitations of the rule (stated in advance)
- "Insider-impossible" means *no advance knowledge of the outcome*. It does **not** mean no informed trading: crypto-threshold markets still respond to public price moves and can be moved by large spot or derivatives traders. Controls therefore measure the baseline "ripple" that public information and herding produce.
- "Insider-possible" means *advance knowledge was structurally possible*. It does **not** mean anyone had it or traded on it.
- Process note: while testing API connectivity, one page (1,000 rows) of the Iran development market's trades was retrieved before this rule was written. The rule uses only resolution mechanics, so that page could not inform it, but the order of events is recorded in `log/process_log.md`.
