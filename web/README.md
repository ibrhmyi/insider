# Insider Signal (web app)

The frozen v1 wallet screen from this repository as a web product: an overview, one page per market, an alert card per high-score wallet, a live scan of any Polymarket market, a plain-language method page and a keyboard-driven story mode for the course video.

Everything shown is unusual activity for review, not proof of insider trading. No rule or result is changed here: the app only reads the frozen outputs.

## Run it

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000. Pages:

| Route | What it shows |
|---|---|
| `/` | Headline and the three numbers, one card per market |
| `/markets/[id]` | Price from fills with the first-news marker and high-score buys sized by USD; ranked wallet table (`maduro`, `nobel`, `iran`) |
| `/markets/[id]/wallet/[prefix]` | Alert card for each wallet-market scoring 4 or more (271 pages) |
| `/live` | Live scan of a Polymarket link or slug, F1-F5 only; "Load cached example" works offline |
| `/method` | Attempt 1, the six flags, the permutation null, validation, Layer 2, limits |
| `/story` | Six steps for screen recording: arrow keys, PageUp/PageDown, Home/End; `?step=3` opens a step |

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

The app is static pages plus one server route (`/api/scan`, which calls `gamma-api.polymarket.com` and `data-api.polymarket.com`).

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
