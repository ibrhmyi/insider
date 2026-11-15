# Insider Signal (web app)

The frozen v1 wallet screen from this repository as one page that shows rather than tells.

Everything shown is unusual activity for review, not proof of insider trading. No rule or result is changed here: the app only reads the frozen outputs.

## Run it

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000. It is one page that tells the story with working parts:

1. The hook: the CFTC-charged Maduro wallet, ranked first of 2,608 by the frozen screen, 30 hours before the news.
2. Six signs, every wallet: switch market, see every buy by a flagged wallet on the price chart, click a buy or a row to see that wallet's six flags against their thresholds.
3. Where do you draw the line: a slider over the cut-off shows how many wallets are flagged and how many of the 7 publicly named ones are caught (the frozen line is 4).
4. Is it just timing: the 1,000-run timestamp shuffle per market, with the observed count marked.
5. Run it on a market today: live scan of any Polymarket link (F1-F5); the cached example is shown on arrival and works offline.
6. What it cannot say: four limits.

The only other route is `/api/scan`.

Tests (the TypeScript flag port against the Python scores for 20 wallets):

```bash
npm test
```

Quartz's lint on the app code:

```bash
npx eslint -c quartz.eslint.config.mjs app components/app lib/*.ts
```

## Regenerate the data

The JSON in `public/data/` is written from the frozen outputs, without re-analysis:

```bash
python3 src/export_web.py      # from the repository root
```

It is also the last step of `./run_all.sh`. It writes `public/data/*.json` and `tests/fixtures/flags_20.json`. `public/data/live_example.json` is the cached live scan; to refresh it, run the app and save the route's answer:

```bash
curl -s "http://localhost:3000/api/scan?q=israel-x-iran-ceasefire-continues-through-november-15" > public/data/live_example.json
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
- Design system: Quartz from design.how. Its source is in `components/quartz/` and its lint in `lib/quartz/lint/`. The design.how skills (`quartz`, `build-design-system`, `ui-review`) are in `.agents/skills/` at the repository root.
- Charts: Recharts inside Quartz's `ChartFrame`, colored only with Quartz tokens; each chart has a table view.
- `lib/flags.ts` is the TypeScript port of the frozen F1-F6 features; `lib/scan.ts` is the live scan.
- `REVIEW.md` holds the UI review.

Privacy: full wallet addresses appear only for wallets named in public reporting (`data/labels/documented_wallets.csv`); every other wallet is shown by its shortest unique prefix.
