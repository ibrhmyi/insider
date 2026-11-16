# Insider Signal (web app)

A scrollytelling investigation of the frozen v1 wallet screen, in the Sodium design system (dark). It only reads the frozen outputs; no rule or result is changed here.

## Run it

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000.

| Route | What it is |
|---|---|
| `/` | The investigation: hero numbers, then a sticky chart beside seven steps for the Maduro case (price, every pre-news buy, flagged wallets in yellow, the charged wallet, the news, its six signs, the public record) |
| `/cases` | Maduro, Nobel and Iran side by side, then the Nobel story |
| `/cases/[id]` | Zoomed chart and the wallet table for one market (default: score >= 4 and >= $2,500; switch for small wallets) |
| `/method` | The failed first idea, the six signs and sources, the shuffle test, the cut-off slider, the limits |
| `/live` | Scan an open Polymarket market on 5 signs; the cached example works offline |
| `/story` | Recording mode: 7 full-screen slides, arrow keys, `?slide=N` |

Tests (the TypeScript flag port against the Python scores for 20 wallets):

```bash
npm test
```

Sodium's lint on the app code:

```bash
npx eslint -c sodium.eslint.config.mjs app components/inv components/site-nav.tsx lib/*.ts
```

## Regenerate the data

The JSON in `public/data/` is written from the frozen outputs, without re-analysis:

```bash
python3 src/export_web.py      # from the repository root
```

It is also the last step of `./run_all.sh`. It writes `public/data/*.json` and `tests/fixtures/flags_20.json`. `public/data/live_example.json` is the cached live scan; to refresh it, run the app and save the route's answer:

```bash
curl -s "http://localhost:3000/api/scan?q=will-zohran-mamdani-be-time-person-of-the-year-2026" > public/data/live_example.json
```

## Deploy (Vercel)

Deployed 2026-11-14 as the Vercel project `insider-signal`: https://insider-signal-rho.vercel.app (production). To redeploy from `web/`: `npx vercel deploy --prod`.

The app is one static page plus one server route (`/api/scan`, which calls `gamma-api.polymarket.com` and `data-api.polymarket.com`).

1. Push the branch to GitHub.
2. In Vercel, choose Add New, then Project, and import the repository.
3. Set Root Directory to `web`. The framework preset is detected as Next.js; keep the default build command (`next build`).
4. Deploy. No environment variables are needed.

With the Vercel CLI instead:

```bash
cd web
npx vercel --prod
```

`/api/scan` sets `maxDuration = 60` seconds; a scan usually takes about 3 seconds.

## How it is built

- Next.js 15 (App Router, TypeScript), Tailwind CSS 4.
- Design system: Sodium from design.how, dark theme. Its source is in `components/sodium/` (installed from the design.how GitHub repository; the design.how registry is blocked from the build environment) and its lint in `lib/sodium/lint/`. Skills (`sodium`, `build-design-system`, `ui-review`) are in `.agents/skills/` at the repository root.
- Charts are hand-drawn SVG (`components/inv/chart.tsx`) driven by a scroll step or a story slide; colour comes only from Sodium roles, and yellow only marks flagged activity (score >= 4 and >= $2,500) and the charged wallet.
- `lib/flags.ts` is the TypeScript port of the frozen F1-F6 features; `lib/scan.ts` is the live scan.
- `REVIEW.md` holds the UI review.

Privacy: full wallet addresses appear only for wallets named in public reporting (`data/labels/documented_wallets.csv`); every other wallet is shown by its shortest unique prefix.
