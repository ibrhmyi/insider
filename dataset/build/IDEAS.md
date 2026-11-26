# Backlog: making PMITC useful for behaviour analysis and model training

Written 2026-11-26 after run 3, as a critiqued backlog. Items marked **(keep)** survived the critique. Nothing here is a rule: any change to how labels, t_news or features are computed needs a dated amendment in PROTOCOL.md first.

## Core constraint

- Labels, not rows, limit learning: 123 suspected wallets, 408 episodes, and 311 of those episodes come from one case (us-iran-strike-2026-02-28).
- Report the number of **independent cases** as the sample size, and split train and test by case.

## Data organisation (keep)

| Table | One row is | Notes |
|---|---|---|
| `episodes_master` | wallet × market × side | features before t_news only; one column per label source (documented grade, ACDC, Inca, graph link, human review), never merged into one "insider" flag |
| `wallets_master` | wallet | wallet history, funding, all labels |
| `trades` | fill | Parquet only |

Treat the task as positive-unlabeled learning. Unflagged winners are unlabeled, not negative.

## Data to add, in priority order

1. **(keep) Event / news timestamps per case**, with a source URL.
   - Needs a per-case rule for which moment counts: first wire report, official post, or the outcome-maker's own announcement.
   - Store it as `data/event_times.csv`. Using it for t_news needs a new amendment (it changes A7).
   - Motivation: the Nobel 2025 wallets traded 00:44 to 03:29 UTC, before the announcement, but day-start t_news labels them post-news.
2. **(keep) Placebo markets** where insiders are implausible: weather, and 5- and 15-minute crypto up/down.
   - Match the same behaviours there to estimate the luck base rate.
   - Caveat: bots and market makers dominate these markets, so match on wallet type as well. Sports markets are not clean (injury news).
3. **(keep) Hard unlabeled set:** winning fresh-wallet longshots on insider-possible markets that nobody flagged. They are not negatives.
4. **(keep) More independent cases** (largest gain per unit of effort): deeper GitHub, Dune, Kaggle and Hugging Face sweep; read the pages in `logs/needs_page_read.csv`; Polymarket's own flag posts. Kalshi notices are case-level only (no trades).
5. **(keep, slow) Money graph:** needs an archive Polygon RPC key. Expect few new candidates, because exchange hubs hide most links.
6. **(medium) "Who could know" market tag:** none, crowd, small group, or single person, plus the outcome-maker. An LLM tag needs a hand-checked sample and is not ground truth.
7. **(keep, needs a human) Review queue:** show the top-scoring unlabelled episodes to a person. Claude must not fill it.

## Features (all computed before t_news)

- **(keep) Entry context:** price and volume trend over 1, 6 and 24 h before the first buy; first-large-buyer flag; share of market volume.
- **(keep) Coordination:** other fresh wallets buying the same token within N minutes; co-timed clusters.
- **(keep) Deadline choice:** buying the shortest deadline that still pays.
- **(keep) Wallet history:** category specialisation; earlier longshot win rate; dormancy before the bet.
- **(blocked)** Bet as a share of deposit, and funding-to-trade time: both need the money graph.
- **(not available)** Order-book depth and spread: Polymarket-v1 has fills only.
- **Post-news (`_post`), analysis and targets only:** exits, redemption speed, PnL. Never use them as features.

## Drop from modelling tables

- Full trades for markets with no suspected wallet (election-2024 alone is 10M legs): keep aggregates only.
- Aggregate and Kalshi cases: they stay in the casebook.
- Placeholder markets, text fields, and transfers with Polymarket contracts.

## Evaluation (decide before training)

- Grouped cross-validation by case.
- Forward test on the cases reported last.
- Results with and without the dominant case.
