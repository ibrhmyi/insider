/** Open markets decided by a small group of people, scanned for the watchlist. Display labels only. */
export const WATCHLIST: {slug: string; who: string}[] = [
  {slug: 'will-zohran-mamdani-be-time-person-of-the-year-2026', who: 'Decided by TIME editors'},
  {slug: 'will-donald-trump-be-time-person-of-the-year-2026', who: 'Decided by TIME editors'},
  {slug: 'will-grand-theft-auto-vi-win-game-of-the-year-at-the-2026-game-awards-20260804145651075', who: 'Decided by a jury and fan vote'},
  {slug: 'will-dune-part-three-be-nominated-for-best-picture-at-the-99th-academy-awards', who: 'Decided by Academy voters'},
  {slug: 'will-the-us-invade-iran-before-2027', who: 'Decided by the US government'},
  {slug: 'israel-military-action-against-lebanon-on-november-26', who: 'Decided by the Israeli government'},
];

/** The live line: at least 3 of the 5 live signs and at least $2,500 bought (display filter, not a rule). */
export const LIVE_MIN_SCORE = 3;
export const LIVE_MIN_USD = 2500;
