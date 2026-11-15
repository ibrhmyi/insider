# UI review: Insider Signal web app

> **2026-11-15 update.** The app was redesigned into a single page at the owner's request ("one page, concise, tell a story, show not tell"). The review below covers the earlier multi-page version; its fixes (phone nav, chart tab stops, lint, focus handling) carried over. Checks rerun on the one-page version: Quartz lint exit 0 with the same single em-dash warning; 23/23 tests; Playwright interaction check with no console errors (market switch, row click, chart-buy click, cut-off slider 4 to 6 giving 7/7, 5/7, 1/7 named wallets caught, cached live scan on arrival); screenshots `figures/app_onepage*.png` and `figures/app_hero.png`.


The app is ready to demo: every page loads, reads at 390 and 1280 px, and can be used with the keyboard alone. All blocking and should-fix findings from the first pass are fixed.

Ready to ship: yes, with fixes (blocking 0, should-fix 0 open, 3 notes, 3 questions for a person).

## Review record
- Source: local production build (`next build && next start`, port 3100), branch `claude/hopeful-mendel-tado7n`.
- Tools: ui-review skill (design.how), `build-design-system/scripts/capture.mjs` (16 captures with accessibility trees, `--no-backend`, guard blocked 0 requests), a Playwright probe script for full-page 390 captures and measured probes, and the Quartz lint (`npx eslint -c quartz.eslint.config.mjs app components/app lib/*.ts`).
- Widths: 390 and 1280. Theme: light (the app ships no dark theme).
- Date: 2026-11-14. Criteria: `.agents/skills/ui-review/references/criteria.md` plus the Quartz skill's rules, which count as agreed criteria.
- Purpose of each screen (assumed from the brief):
  - Overview: give the headline and the three numbers in one look, and route to a market.
  - Market view: see when high-score wallets bought relative to the news, and find a wallet to review.
  - Wallet alert: judge one wallet: flags against thresholds, what followed, the public record, and what is post-hoc.
  - Live scan: score a live market's largest recent buyers on F1-F5, or show the cached example offline.
  - Method: explain the method, its checks and limits to a non-specialist.
  - Story: a keyboard-driven walkthrough to screen-record.
- Gaps: no dark theme reviewed (none shipped); no screen reader run by a person (accessibility trees were captured and read instead); touch tested by width only, not on a device.

## Commands and exit codes
- `npx eslint -c quartz.eslint.config.mjs app components/app lib/*.ts`: first run exit 1 (13 errors, 1 warning); after fixes, exit 0 with 1 warning (see notes).
- `npx next build`: exit 0 (281 pages generated, including 271 alert pages; 1 server route).
- `npx vitest run`: exit 0, 23 tests passed.
- `node .agents/skills/build-design-system/scripts/capture.mjs --base http://localhost:3100 --kind after --out web/.ui-review/captures --no-backend --routes ...`: 16 of 16 captures, 0 routes not as expected, 0 requests blocked.

## Findings

### Blocking
None.

### Should-fix (all fixed in this session)
1. **Main navigation cut off at 390 px** (criterion 12, `nav 'Main'`, maduro-full-390). "Live scan" was clipped and Method and Story were off-screen with no visible scroll cue. Fixed: brand link hidden under 640 px (Overview is in the nav), tighter link padding and header gutter. Measured after: nav `scrollWidth - clientWidth` = 0 px at 390.
2. **Chart took a Tab stop with a meaningless name** (criterion 5 and quartz-keyboard, `svg[application] "Dec 12Dec 16Dec 21…"`, tab path on /markets/maduro). Recharts' accessibility layer made the SVG focusable and named it from its tick labels. Fixed: `accessibilityLayer={false}` on all three charts. The keyboard path to the values is the chart's table view (segmented control in the chart header), and each chart has a figure label that states what it shows.
3. **Empty Live scan submit reported "Scan failed"** (criteria 7 and 8, `button 'Scan market'`, live-error capture). Nothing had been sent, yet the result area showed a failure, away from the cause. Fixed: the field is marked `aria-invalid` with the message right under it (`role="alert"`). "Scan failed" now appears only for a real request error, with "Retry scan" and "Load cached example".
4. **Quartz lint: 13 errors** (quartz-tokens-only, anti-slop-no-status-dots, quartz-components-first). Stock radii (`rounded-sm/md/xl`) changed to role radii (`rounded-inner/soft/frame`); a restyled Badge for unfired flags replaced by plain text; restyled nav Buttons replaced by links styled with `aria-current`; a shadow on the flat tooltip replaced by the frame utility; hue-only legend dots replaced by the same round mark as the chart, always beside its text; an inline width moved to a custom property; native step buttons replaced by Quartz Buttons.
5. **Alert card flags table overflowed at 1280** (criterion 12, `table 'Flags with this wallet's values and thresholds'`, first alert capture). The value and Fired columns were clipped. Fixed: the rule moved under the flag name in one column.
6. **Story step 5 clipped at the top** (criterion 12, story step 5 at 1280x800). Centring a tall step with `items-center` cut off its top. Fixed: safe centring (`my-auto`), and the story's alert card shows only the flags, the public record and the disclaimer, so it fits one screen for recording.
7. **Story step region drew a focus ring when it received programmatic focus** (criterion 3). Fixed with `data-control`, Quartz's marker for a container that takes focus without being a control. The region still takes focus on every step change, so screen readers announce the new step.

### Notes
1. **Em dash in mandated copy.** Quartz bans em dashes (anti-slop-no-em-dash; the lint warns once). The disclaimer ("Unusual activity for review — this does not identify an owner or prove insider trading.") is fixed wording under HANDOFF rule 1, and "n/a — needs news time" is the wording the brief asked for. Both kept on purpose.
2. **Wide tables scroll inside their frame at 390** (alert follow-on table, market wallet table). Columns are reachable by horizontal scroll inside the table, and lower-priority columns hide below set widths. Page-level overflow is 0 px on every route at 390 and 1280.
3. **Press feedback is close to the 100 ms limit on Nobel** (criterion 13, measured with the Event Timing API). Toggling the F4 filter re-filters 3,554 rows: click durations 88 ms and 80 ms. Passes today; a bigger market would need memoised filtering per flag.

## Probes (measured)
| probe | result |
|---|---|
| Horizontal overflow, 6 routes x 2 widths | 0 px everywhere |
| Console errors on load, 6 routes x 2 widths | none (prefetch 404s for unbuilt routes disappeared once all routes existed) |
| Tab path, /markets/maduro, 40 stops | skip link, brand, nav, breadcrumb, news source, market links, range control, view control, search, 8 filter toggles, table region, sort and column menus, rows, source links. Every stop draws a ring; the search field draws it on its container (checked in a capture) |
| Enter on a focused table row | opens `/markets/maduro/wallet/0x31a5` |
| Story keys | 2 x ArrowRight to `?step=3`; End to `?step=6`; ArrowLeft to `?step=5` |
| Reduced motion | story step animation `none` under `prefers-reduced-motion: reduce`, `story-in` otherwise |
| Press latency (Event Timing) | 80-88 ms for a filter toggle on the largest table |
| Live scan states | empty, field error, loading (skeleton rows, pending button), request error with retry, success, cached example offline: all shown in captures |
| Live scan against the real API | `/api/scan` for an open market answered in about 3 s with 25 scored wallets |

## Edge cases
- Empty: shown (live scan before a scan; wallet table with no match says which filter to turn off).
- Loading and slow loading: shown (live scan skeleton). Static pages have no loading state.
- Error: shown (live scan field error and request error). Failed save: not applicable, the app writes nothing.
- Partial data: shown (alert follow-on rows with "No match" or "Overlaps the news"; price impact "Not measured").
- Long content: shown (long market questions wrap; full addresses break; handles never truncate).
- Narrowest and widest width: shown. Layout switch widths (640, 768, 1024): not captured separately.
- Offline: shown for live scan via the cached example; the other pages are static.
- No permission or read-only role: not applicable.
- Touch: hover-only content is the chart tooltip; the same values are in the table view.

## For a person to decide
1. Quartz is light by default and the app ships no dark theme. Add one before the demo, or keep light for the recording?
2. The live score is out of 5 and no live threshold has been validated, so the page calls it a ranking, not an alert. Is that the framing you want in the video?
3. Story step 4 uses a log scale so the 5 wallets at score 6 are visible next to 2,054 at score 0. Keep it, or switch to a linear scale with labels?

## Dismissed and left out
- The flag toggles take two rows at 1280. They are the main filter; collapsing them into a menu would hide F1-F6, which the brief asks to show. Left as is.
- Market cards on the overview use a vertical label/value list. A matter of taste; no criterion is broken.

Coverage: routes /, /markets/maduro, /markets/nobel, /markets/iran, /markets/maduro/wallet/0x31a5, /live, /method, /story (steps 1-6); widths 390 and 1280; theme light; probes: overflow, console, tab path, row Enter, story keys, reduced motion, event timing, live API. Not measured: screen reader by a person, a real touch device, a throttled CPU, dark theme.
