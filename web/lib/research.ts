/**
 * Research shown on the page: who insiders are, where they trade, how they behave. Every line is a paraphrase of the
 * source it links to; checked 2026-11-16. People are described by role and are charged or indicted, not convicted.
 */

export const SRC = {
  cftcAdvisory: 'https://www.cftc.gov/PressRoom/PressReleases/9158-26',
  cftcSoldier: 'https://www.cftc.gov/PressRoom/PressReleases/9217-26',
  google: 'https://techcrunch.com/2026/05/27/google-engineer-charged-with-insider-trading-after-making-1-2m-on-polymarket/',
  googleAccount: 'https://finance.yahoo.com/markets/options/articles/google-employee-lands-trouble-over-210151989.html',
  googleHide: 'https://amp.insurancejournal.com/news/national/2026/05/29/871768.htm',
  israel: 'https://www.jns.org/news/israel-news/after-secret-briefing-iaf-reservist-allegedly-told-friend-to-bet-on-preemptive-iran-strike',
  acdcMarkets: 'https://acdatacollective.org/?p=1495',
  acdcOrcas: 'https://acdatacollective.org/?p=1688',
  gomezCram: 'https://www.theblock.co/amp/post/398902/skilled-polymarket-traders-are-a-3-minority-and-everyone-else-funds-their-gains-study',
  mittsOfir: 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6426778',
  bock: 'http://www.vernimmen.com/ftp/mif2026_rp_bock_guenthoer.pdf',
  polymarketDocs: 'https://docs.polymarket.com/concepts/order-lifecycle',
  nechepurenko: 'https://arxiv.org/pdf/2605.00459',
};

export type Case = {who: string; secret: string; venue: string; made: string; status: string; source: string};

export const CASES: Case[] = [
  {who: 'US Army soldier', secret: 'The raid on Maduro', venue: 'Polymarket', made: '$404k', status: 'Charged, Apr 2026', source: SRC.cftcSoldier},
  {who: 'Google engineer', secret: 'Year in Search results', venue: 'Polymarket', made: '$1.2M', status: 'Charged, May 2026', source: SRC.google},
  {who: 'Israeli air force reservist and a friend', secret: 'The strike on Iran', venue: 'Polymarket', made: '$152k', status: 'Indicted, Feb 2026', source: SRC.israel},
  {who: 'YouTube channel editor', secret: 'Videos before they aired', venue: 'Kalshi', made: '$5.4k', status: 'Fined and suspended, Feb 2026', source: SRC.cftcAdvisory},
];

/** Share of long-shot bets ($2,500 or more at 35 cents or less) that won, by market type. ACDC, all settled Polymarket markets. */
export const WHERE: {label: string; pct: number; lead?: boolean}[] = [
  {label: 'All markets', pct: 14},
  {label: 'Political markets', pct: 25},
  {label: 'Military and defense', pct: 52, lead: true},
];

export type Behaviour = {name: string; evidence: string; by: string; source: string; by2?: string; source2?: string};

export const BEHAVIOURS: Behaviour[] = [
  {name: 'New account', evidence: 'Over half of the top long-shot winners in military markets first bet within 2 days of joining.', by: 'ACDC', source: SRC.acdcOrcas},
  {name: 'One event, then silence', evidence: '1,950 accounts opened just before a single event and went quiet after it.', by: 'Gomez-Cram et al.', source: SRC.gomezCram},
  {name: 'Long shots, bought big', evidence: 'They buy the unlikely side at 35¢ or less, with $2,500 or more.', by: 'ACDC', source: SRC.acdcMarkets},
  {name: 'Right before the news', evidence: 'Winning long shots cluster in the last hours before a market resolves.', by: 'ACDC', source: SRC.acdcMarkets},
  {name: 'Moves the price', evidence: 'Each dollar moves the price 7 to 12 times more than a skilled trader does.', by: 'Gomez-Cram et al.', source: SRC.gomezCram},
  {name: 'Covers their tracks', evidence: 'One changed his handle after online suspicion. Another had a friend place the bets.', by: 'Google case', source: SRC.googleHide, by2: 'Israel case', source2: SRC.israel},
];

/** Why this project: who loses, what is public, what is missing. Each row links its sources. */
export type WhyRow = {label: string; text: string; sources: {by: string; href: string}[]};

export const WHY: WhyRow[] = [
  {label: 'Why it matters', text: 'Whoever takes the other side of an informed bet loses. In 2026 US regulators brought their first insider trading cases on prediction markets.', sources: [{by: 'CFTC', href: SRC.cftcSoldier}]},
  {label: 'What is public', text: 'Every Polymarket trade settles on a public blockchain and is served by a public API: time, wallet, side, size and price. Who owns a wallet is not public, and neither are orders that never filled.', sources: [{by: 'Polymarket docs', href: SRC.polymarketDocs}]},
  {label: 'What is missing', text: 'Published screens work after a market resolves, and their flagged lists are not released. This project tests a simple check that can run while a market is open and shows its evidence.', sources: [{by: 'Bock and Guenthoer', href: SRC.bock}, {by: 'Nechepurenko', href: SRC.nechepurenko}]},
];

export const SOURCES: {name: string; what: string; href: string}[] = [
  {name: 'CFTC, Feb 2026', what: 'Enforcement advisory on prediction markets', href: SRC.cftcAdvisory},
  {name: 'CFTC, Apr 2026', what: 'Complaint against a US service member', href: SRC.cftcSoldier},
  {name: 'ACDC, Apr 2026', what: 'Insider risks in Polymarket political markets', href: SRC.acdcMarkets},
  {name: 'ACDC, Aug 2026', what: 'The long-shot betting ecosystem', href: SRC.acdcOrcas},
  {name: 'Gomez-Cram, Guo, Jensen, Kung, 2026', what: 'Crowd wisdom or informed minority', href: SRC.gomezCram},
  {name: 'Mitts and Ofir, 2026', what: 'Informed trading in prediction markets', href: SRC.mittsOfir},
  {name: 'Bock and Guenthoer, 2026', what: 'An ex-ante screen for insider activity', href: SRC.bock},
  {name: 'Polymarket docs', what: 'How orders and trades settle', href: SRC.polymarketDocs},
  {name: 'Nechepurenko, 2026', what: 'Information leakage at population scale', href: SRC.nechepurenko},
];
