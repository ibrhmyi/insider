# UI review: Insider Signal

## 2026-11-17: product page (replay, watchlist, scan)

Ready to ship: yes. One page: problem, idea, replay, watchlist, scan, one-line limits. Blocking 0, should-fix 0 open.

| check | result |
|---|---|
| `npm run build` | runs `vitest run` (31 tests, including the no-em-dash test), `next build`, then `scripts/check-copy.mjs` on the rendered HTML; exit 0. With an em dash planted in page copy the build fails (exit 1), checked |
| Sodium lint (`app components/product lib/*.ts`) | exit 0, no warnings; one project exception in `sodium.eslint.config.mjs`: the multi-line watchlist card is a native button |
| capture.mjs | `/` at 390 and 1920 (dark), accessibility trees saved, 0 routes not as expected |
| Lighthouse | mobile 98 / 100 / 96, desktop 96 / 98 to 100 / 96 (performance / accessibility / best practices) |
| Replay at 1920x1080, 10x | plays Jan 1 to resolution in about 24 s; four alerts slide in (30.0 h, 8.3 h, 2.3 h, 0.4 h before the news); news line at 06:00 UTC; closing line "Alert fired 30 hours before the news. Ranked 1st of 2,608 buyers." |
| Keyboard | Play, Next and Previous event, speed and the time slider (End jumps to the end) all work by keyboard; watchlist cards open with Enter (`aria-expanded`) |
| Reduced motion | no Play button and no animation; Next and Previous event step through alerts, news and resolution; the slider scrubs |
| Phone (390) | 0 px overflow; controls wrap, chart above, alerts and feed stacked; replay usable with the step buttons |
| Yellow | only alerts: alert cards and markers, "worth a look" verdicts, scores of wallets over the line. Sodium's yellow selected and checked controls are mapped to neutral roles inside `neutral-controls` (token remap, no raw values) |
| Type | body 20px or more (`type-product`), headings calmer than before (`type-product-title`) |

Fixed during the review: alert cards scrolled the first (30 h) alert out of view at the end (now one-line rows with the relevant card expanded); the alert's own buy could be cut from the feed when several fills shared a minute; yellow on the slider and selected speed; the time slider had no accessible name on its thumb; heading order (h4 under h2).

Notes: chart axis labels scale down with the SVG on phones (about 12px at 390); the em dash in HANDOFF's disclaimer is shown as a colon on the page (same words); market titles from Polymarket pass through `clean()` so an em dash in a title is shown as a colon or comma.

---


## 2026-11-17: one-page version

The site is now one page (`/`) with seven full-screen steps; the review below this section covers the archived multi-page version.

| check | result |
|---|---|
| Sodium lint (`app components/one lib/*.ts`) | exit 0 errors, 1 warning: the em dash in "a second look — not criminals", kept as the owner wrote it |
| Tests | 23/23 |
| Lighthouse | mobile 96 / 100 / 96, desktop 100 / 100 / 96 (performance / accessibility / best practices) |
| 1920x1080 screen recording (Playwright video, wheel scrolling top to bottom, then the cached example) | every step lands; chart states change in order (line, yellow dot, news line, jump); signs light one by one; no blank screens |
| Page overflow | 0 px at 1920 and 390 |
| Phone (390) | steps stacked, chart static in its end state, news label shortened to fit, all six signs lit |
| Reduced motion (1920) | no sticky chart, chart in end state, all six signs lit, no transitions |
| Yellow | only the one wallet: the amount in the hook and caption, its chart dot and label, its six signs. The primary button was yellow (Sodium's slab) and was changed to the secondary style |
| Type | body 22px or more, numbers 96px or more, via three page-level roles (Sodium's scale stops at 56px and 15px body) |
| Words per step | at most about 25, except the catch (31, the owner's wording) |

Wording changes from the brief, to stay inside the data and HANDOFF's wording rules: the hook says "a wallet" and "hours later" (its money went in mostly in the final hours; the 30 h is when it crossed the line); the CFTC line says "its alleged owner, a US soldier"; "Early" shows 4.4 h (median buy before the news), not 30 h; "suspects" became "publicly named wallets"; "271 wallets nobody has accused" became 264 (271 includes the 7 named).

---


The redesign is ready to record and demo. The investigation lands, the chart shows the key trade, flagged means flagged, and every page works by keyboard, at phone width and under reduced motion. All findings ranked high are fixed.

Ready to ship: yes, with fixes (blocking 0, should-fix 0 open, 4 notes, 3 questions for a person).

## Review record
- Source: local production build (`next build && next start`), branch `claude/hopeful-mendel-tado7n`, 2026-11-16.
- Tools: design.how ui-review skill; `build-design-system/scripts/capture.mjs` (24 captures with accessibility trees, routes `/`, `/cases`, `/cases/maduro`, `/cases/nobel`, `/cases/iran`, `/method`, `/live`, `/story`; widths 390, 1440, 1920; theme dark; `--no-backend`); Playwright probe scripts; Lighthouse 12; Sodium lint (`npx eslint -c sodium.eslint.config.mjs app components/inv components/site-nav.tsx lib/*.ts`).
- Criteria: `.agents/skills/ui-review/references/criteria.md` plus the Sodium skill's global rules and anti-slop list, which count as agreed criteria.
- Purpose of each screen (given by the brief): `/` tell the Maduro case as an investigation; `/cases` compare three markets and tell Nobel; `/cases/[id]` review flagged wallets; `/method` state the method and its limits; `/live` score an open market; `/story` record the video.
- Gaps: no screen reader run by a person (accessibility trees and Lighthouse instead); no real touch device (390 px emulation); light theme not reviewed (the brief asks for dark only).

## Commands and results
| check | result |
|---|---|
| Sodium lint | first run exit 1 (17 errors); after fixes exit 0, no warnings |
| `npx vitest run` | 23/23 pass (TypeScript flags vs Python scores for 20 wallets) |
| `npx next build` | exit 0 |
| capture.mjs | 24 of 24 captures, 0 routes not as expected; 48 requests blocked (Sodium's font URLs on design.how, unreachable from this sandbox) |
| Lighthouse, mobile profile (performance / accessibility / best practices) | `/` 98/100/96, `/cases` 96/100/96, `/cases/maduro` 96/100/96, `/method` 98/100/96, `/live` 93/100/96, `/story` 99/100/96; desktop `/` 100/100 |
| Blank-section probe (scroll in 0.8-viewport steps, flag frames with under 1% non-background pixels) | 0 blank frames on `/` and `/cases` at 1440x900, 1920x1080 and 390x844; the lowest frame is the intentionally dark hero (1.4 to 2.1%) |
| Page overflow, 7 routes x 3 widths | 0 px everywhere after fix |
| Console errors (excluding blocked font URLs and prefetches) | none |

## Findings (all fixed)

### Should-fix
1. **The blank-section bug: step text disappeared behind the sticky chart on phones** (criterion 12, `/` at 390, step 4). The sticky chart is drawn above the steps, and a step centred on screen sat underneath it, so the screen showed the chart and empty background. Fixed: on phones the step cards sit in the lower part of the screen and the active zone moves there (`-70% 0px -12% 0px`); measured by the blank-section probe above.
2. **Nobel chart drew no flagged buys and no announcement line** (criterion 7, `/story` slide 5). A server page spread a constant exported from a `'use client'` module and got an empty reference. Fixed by moving chart states to `lib/chart-state.ts`; probe counted 59 yellow buys after the fix.
3. **Wallet table pushed the page 409 to 457 px wide at 390** (criterion 12, `/cases/maduro`, `/cases/nobel`). Grid children lacked `min-w-0`. Fixed; overflow 0 px.
4. **Sticky chart covered the site header and its navigation** when the scrolly section ended (criterion 6, `/` at 1440, step 7). Header moved to Sodium's overlay layer; the last step is a full screen tall so the chart never scrolls away mid-read.
5. **Story mode drew a yellow focus ring around the whole slide** (criterion 3, `/story`). The slide region received programmatic focus. It no longer takes focus; the live region announces each slide.
6. **17 Sodium lint errors**, including a real layout bug: `max-w-7xl` does not exist in Sodium's theme, so containers had no limit. Sodium has no page-width token, so pages run full width with gutters (Sodium's tool layout) and prose is capped at `max-w-measure` or `max-w-3xl`. Also fixed: `z-[1]` to `z-(--z-raised)`, the callout's inline position to custom properties.
7. **Heading order** (Lighthouse, `/cases/maduro`): wallet detail `h3` under the page `h1`; now `h2`.

### Notes
1. **Em dash in the mandated disclaimer.** Sodium bans em dashes; HANDOFF rule 1 fixes the wording "Unusual activity for review — this does not identify an owner or prove insider trading." It is kept verbatim, as is the brief's "n/a — needs news time" spirit (shown as "Near news n/a" in the live table).
2. **Yellow use.** The brief reserves yellow for flagged activity and the charged wallet; Sodium reserves it for the one primary action, the selection and a chart series. Both hold: chart dots, fired signs, flagged counts, the charged wallet and the one primary button per view. The selected table row uses Sodium's selection wash, which is yellow-tinted in dark mode; rows that can be selected are all flagged wallets.
3. **Stat tiles.** Sodium bans rows of equal stat cards, so the hero's three numbers are one ruled status strip at Sodium's largest type role (`type-display`); there is no larger token.
4. **Scroll reveal.** Sodium bans content that fades in on scroll. Step text is always visible; only the sticky chart changes state. Under reduced motion every state change is instant (measured: dot and line `transition-property: none`, hero numbers show final values at once).

## Probes (measured)
| probe | result |
|---|---|
| Tab path on `/` | skip link, brand, 5 nav links, scroll link, CFTC source link, 3 closing links; every stop shows a ring |
| Table by keyboard (`/cases/maduro`) | 12 rows by default (score >= 4 and >= $2,500); Enter on row 3 opens `0x6baf…`; Space on the switch shows 39 rows (+27 small) |
| Slider by keyboard (`/method`) | ArrowRight to 5: 5 of 7 named caught, 68 flagged, 43 under $1,000 |
| Story keys | 3 x ArrowRight to slide 4; End to 7; Home to 1; `?slide=N` opens a slide |
| Live scan states | cached example on arrival; empty submit marks the field; unknown slug gives "Scan failed" with retry; a real market with no hits (TIME Person of the Year, Pope Leo XIV) shows "No wallet crosses the line in this market right now." |
| Press latency (Event Timing) | switch click 32 ms |

## Edge cases
- Empty: shown (live scan with no wallet over the line). Loading: shown (live skeleton). Error: shown (unknown market).
- Long content: market questions wrap; addresses only as prefixes except documented wallets.
- Widths: 390, 1440, 1920 captured; the scrolly layout switches at 1024.
- Offline: the cached live example; all other pages are static.
- Reduced motion: shown. Touch: no hover-only content that carries meaning (sign tooltips repeat values that the detail panel shows).

## For a person to decide
1. The square-root price scale makes the 5 to 11 cent run readable and is labelled on the chart. Keep it, or show a linear scale with the zoom alone?
2. Sodium's real fonts load from design.how on the deployed site when that host allows it; locally the open stand-ins (Inter, Commit Mono) are used. Fine for the video?
3. The live example (TIME Person of the Year, Mamdani) will age. Refresh it before recording with the command in `web/README.md`?

Coverage: routes `/`, `/cases`, `/cases/maduro`, `/cases/nobel`, `/cases/iran`, `/method`, `/live`, `/story` (7 slides); widths 390, 1440, 1920; theme dark; probes: blank sections, overflow, console, tab path, table keyboard, switch, slider, story keys, live states, reduced motion, event timing, Lighthouse. Not measured: screen reader by a person, real touch device, throttled CPU beyond Lighthouse's mobile profile.
