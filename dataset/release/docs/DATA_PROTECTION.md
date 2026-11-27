# Data protection

PMITC records allegations about pseudonymous blockchain wallets. A wallet address is not a name, but where it can be linked to a person it can be **personal data** (for example under the EU and UK GDPR). This note says how the dataset treats it.

## What is stored
- Public Polymarket proxy addresses (lower-case hex) and their public trades on Polygon, as published by Polymarket-v1 and the Polymarket Data API.
- Public usernames as quoted by the sources (for example "flagged by Lookonchain: BlueHorseshoe86"), and the source URL.
- Claims: a paraphrase under 30 words, the evidence grade, the source and its URL.
- For rule-based look-ups (coordinated-buyer rule, hard negatives), only the Gamma profile **creation time** is kept.

## What is not stored
- No personal names in any data field (checked by a hashed name list and a reviewed "Name Surname" scan, `dataset/tests/`). Official records are referenced by URL and notice or docket number; a source's own URL may contain a name.
- No profile text, bios, display names chosen by users beyond the handles quoted by sources, profile pictures, or social-media content.
- No identity work: no attempt is made to link a wallet to a person; wallet-to-person mappings made by official sources are referenced by URL only.
- Market titles that name a person alleged, charged or sanctioned in the sources are withheld (PROTOCOL A12.6, A12.7).

## Lawful basis and principles
- **Purpose:** public-interest research on market integrity: how suspected informed trading on prediction markets looks in public trade data, and how well detection methods find it.
- **Lawful basis (where the GDPR applies):** legitimate interests / public-interest research (Art. 6(1)(f), with the research safeguards of Art. 89). The data are already public (on-chain trades, published allegations), the subjects are pseudonymous, and the dataset adds no identifying information.
- **Data minimisation:** only the columns needed for the analysis; profile data reduced to a creation time; rule outputs (coordinated-buyer rule, Gate 1, ACDC, Inca) kept separate from source labels and described as rule outputs, not allegations.
- **Accuracy:** claims are never edited; contradictions with the trades are recorded in `contradictions`; every label shows its source and grade, and the label sets (`label_strict`, `label_standard`, `label_broad`) let users choose how strict to be.

## Retention
- Kept while the dataset is maintained. A row whose only source is retracted is removed (PROTOCOL 9). Raw API responses that are not needed for a released table are not published.

## Your rights: removal, correction, right of reply
- **Removal or correction:** open an issue with the template "Request removal" or "Correct a row" (see `CONTRIBUTING.md`) giving the row id (`claim_id`, or `wallet` + `case_id`) and the reason, or write to the owner (contact below). Requests are answered within 30 days.
- **Right of reply:** a subject may send a reply to a claim. It is recorded, with its date, in the `right_of_reply` column of `claims` (the claim itself is not edited).
- **Contact:** `<owner contact e-mail: to be filled in by the owner before publication>`.
