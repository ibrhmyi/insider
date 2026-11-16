# Insider Signal (web app)

One page, one story (Maduro), seven full-screen steps: the hook, the question, a sticky price chart where one wallet's bet lights up, its six signs, the result, the catch, and a live scan to try. It only reads the frozen outputs; no rule or result is changed here. Earlier multi-page versions are in `archive/` (not built).

## Run it

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000. The only other route is `/api/scan` (the live scan). On a wide screen with motion allowed the chart is sticky and changes as you scroll; on phones or with reduced motion the steps are stacked and the chart shows its end state.

Tests (the TypeScript flag port against the Python scores for 20 wallets):

```bash
npm test
```

Sodium's lint on the app code:

```bash
npx eslint -c sodium.eslint.config.mjs app components/one lib/*.ts
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
- The page is `components/one/` (story, chart, live scan). The chart is hand-drawn SVG with a linear price axis; yellow marks only the one wallet. Three page-level type roles in `app/globals.css` extend Sodium's scale (22px+ body, 96px+ numbers) for a 1920x1080 recording.
- `lib/flags.ts` is the TypeScript port of the frozen F1-F6 features; `lib/scan.ts` is the live scan.
- `REVIEW.md` holds the UI review.

Privacy: full wallet addresses appear only for wallets named in public reporting (`data/labels/documented_wallets.csv`); every other wallet is shown by its shortest unique prefix.
