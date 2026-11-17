import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {Replay, type ReplayData} from '@/components/product/replay';
import {Watchlist} from '@/components/product/watchlist';
import {ScanBox} from '@/components/product/scan-box';
import {How, Source, Where, Who, Why} from '@/components/product/research';
import {getLayer2, getValidation, getWallets, getMarket, getMarkets, getV0, MARKET_IDS} from '@/lib/data';
import {FLAGS, FLAG_PLAIN, FLAG_SHORT, NOT_PROOF, usd} from '@/lib/copy';
import {SOURCES} from '@/lib/research';
import type {FlagId} from '@/lib/types';

const REPO = 'https://github.com/ibrhmyi/insider';
// One centred reading column, the same width as the research articles on iyildiz.me/research.
const pad = 'mx-auto w-full max-w-[680px] px-6';

function Section({id, title, children, className = ''}: {id: string; title: string; children: React.ReactNode; className?: string}) {
  return <section aria-labelledby={`${id}-title`} id={id} className={`flex flex-col gap-8 border-t border-line py-16 ${pad} ${className}`}>
    <h2 id={`${id}-title`} className="type-product-title max-w-(--title-ch)">{title}</h2>
    {children}
  </section>;
}

/** How often each sign fires: among the wallets named in public reporting, and among every pre-news buyer. */
function signRates() {
  const all = MARKET_IDS.flatMap(m => getWallets(m));
  const named = [...new Map(getValidation().map(v => [v.addr, v])).values()];
  return {
    nAll: all.length, nNamed: named.length,
    rows: FLAGS.map(f => ({f, named: named.filter(v => v.flags.includes(f)).length, all: all.filter(w => w.flags.includes(f)).length / all.length})),
  };
}

export default function Home() {
  const replay: ReplayData = JSON.parse(readFileSync(join(process.cwd(), 'public', 'data', 'maduro_replay.json'), 'utf8'));
  const charged = getValidation().find(v => v.label_id === 'MAD-CFTC-1')!;
  const w = getWallets('maduro').find(x => x.id === charged.wallet_id)!;
  const nMaduro = getMarket('maduro')!.n_wallets;
  const head = getMarkets().headline;
  const v0 = getV0();
  const rates = signRates();
  // Four checks, every number read from the frozen result files.
  const perm = Object.fromEntries(MARKET_IDS.map(m => [m, getMarket(m)!.permutation]));
  const l2 = (scope: string) => getLayer2().tests.find(t => t.outcome === 'wallets' && t.H === 30 && t.scope === scope)!;
  const pooledL2 = l2('pooled').mean_diff;
  const nobelL2 = l2('nobel').mean_diff;
  const chanceOnly = MARKET_IDS.filter(m => m !== 'nobel' && perm[m].p_value >= 0.05).map(m => ({maduro: 'Maduro', iran: 'Iran', nobel: 'Nobel'})[m]);
  const checks: {check: string; result: string; verdict: string}[] = [
    {check: 'Do big bets draw more copycats where insiders are possible?',
      result: `${v0.pooled['insider-possible'].mean_excess} against ${v0.pooled['insider-impossible'].mean_excess} extra wallets, p\u00a0=\u00a0${v0.p_value.toFixed(2)}.`,
      verdict: v0.p_value < 0.05 ? 'Yes' : 'No'},
    {check: 'Do the six signs find the wallets named in public reporting?',
      result: `${head.documented_flagged} of ${head.documented_total} flagged. The wallet later charged ranks ${head.rank === 1 ? '1st' : `#${head.rank}`} of ${head.n_in_market.toLocaleString('en-US')}.`,
      verdict: 'Yes, partly circular'},
    {check: 'Could random timing explain the flags?',
      result: `${perm.nobel.n_perm.toLocaleString('en-US')} shuffles per market. Nobel: ${perm.nobel.observed} flagged against ${Math.round(perm.nobel.null_mean)} expected, p\u00a0=\u00a0${perm.nobel.p_value.toFixed(3)}. ${chanceOnly.join(' and ')}: no better than chance.`,
      verdict: 'Nobel only'},
    {check: 'Do other traders follow flagged wallets?',
      result: pooledL2 < 0 && nobelL2 > 0
        ? 'Fewer followers than after ordinary bets of the same size, except in the Nobel market.'
        : `Followers after flagged bets, against ordinary bets of the same size: ${pooledL2.toFixed(1)} pooled, ${nobelL2.toFixed(1)} in the Nobel market.`,
      verdict: pooledL2 < 0 && nobelL2 > 0 ? 'Nobel only' : 'See result'},
  ];
  const value: Record<FlagId, string> = {
    F1: `${w.f1_days.toFixed(1)} days`, F2: `${Math.round((w.f2_share ?? 0) * 100)}%`, F3: `${Math.round(w.avg_price * 100)}¢`,
    F4: usd(w.usd), F5: `${Math.round(w.f5 * 100)}%`, F6: `${w.hours.toFixed(1)} h`,
  };
  const results: {figure: string; label: string}[] = [
    {figure: `1st of ${nMaduro.toLocaleString('en-US')}`, label: 'Rank of the wallet later charged, Maduro market'},
    {figure: `${head.hours_before} h`, label: 'Flagged before the news broke'},
    {figure: `${head.documented_flagged} of ${head.documented_total}`, label: 'Publicly named wallets flagged, 3 markets'},
    {figure: `${head.n_high_total - head.documented_flagged}`, label: 'Other wallets flagged, never accused'},
  ];

  return <div id="top" className="text-text-1" style={{'--title-ch': '30ch'} as React.CSSProperties}>
    <header aria-labelledby="question-title" className={`flex flex-col gap-5 pt-[12vh] pb-14 ${pad}`}>
      <a href="/research/" className="research-label w-fit text-text-3 transition-colors duration-(--dur-state) hover:text-text-1 focus-visible:focus-ring">← Research</a>
      <p className="research-label mt-12 text-text-3"><time dateTime="2026-11-14">11.2026</time> · Capstone</p>
      <h1 id="question-title" className="type-story-title max-w-(--title-ch)">Can public trades reveal an insider before the news breaks?</h1>
      <p className="type-product max-w-measure text-text-2">On Polymarket every trade is public. This page asks who insiders are, where they trade and how they behave, then tests a model that looks for them.</p>
      <p className="type-product max-w-measure text-text-3">For journalists, researchers and traders who watch these markets.</p>
    </header>

    <Section id="why" title="The trades are public. The check is missing."><Why/></Section>
    <Section id="who" title="An insider trades on a secret they were trusted with."><Who/></Section>
    <Section id="where" title="They trade where a few people know the answer first."><Where/></Section>
    <Section id="how" title="They leave a pattern."><How/></Section>

    <Section id="model" title="The model turns that pattern into six signs per wallet.">
      <ul className="grid gap-x-12 gap-y-6 sm:grid-cols-2" aria-label="The six signs">
        {FLAGS.map(f => <li key={f} className="flex flex-col gap-1">
          <span className="type-product text-text-1">{FLAG_SHORT[f]}</span>
          <span className="type-product text-text-2">{FLAG_PLAIN[f]}</span>
        </li>)}
      </ul>
      <p className="type-product max-w-measure text-text-1">Count the yeses. Four or more: worth a look. Thresholds come from the research above and were fixed before testing.</p>
      <div className="flex flex-col gap-4 border-t border-line pt-6">
        <h3 className="type-product text-text-2">Example: the Maduro wallet later charged by the CFTC</h3>
        <ul className="flex flex-wrap gap-x-8 gap-y-3" aria-label="Its six signs">
          {FLAGS.map(f => <li key={f} className="flex items-baseline gap-2">
            <span className="type-product text-text-1" aria-label={w.flags.includes(f) ? 'yes' : 'no'}>{w.flags.includes(f) ? '✓' : '✗'}</span>
            <span className="type-product text-text-1">{FLAG_SHORT[f]}</span>
            <span className="type-product text-text-2">{value[f]}</span>
          </li>)}
        </ul>
        <p className="type-product text-text-1">{w.score} of 6.</p>
      </div>
    </Section>

    <Section id="findings" title="Tested on three past markets: Maduro, the Nobel Peace Prize, the Iran strike.">
      <dl className="grid border-t border-line sm:grid-cols-2">
        {results.map(r => <div key={r.label} className="flex flex-col-reverse justify-end gap-2 border-b border-line py-6 md:pe-8">
          <dt className="type-product text-text-2">{r.label}</dt>
          <dd className="type-product-title text-text-1">{r.figure}</dd>
        </div>)}
      </dl>
      <div className="flex flex-col gap-4">
        <h3 className="type-product text-text-1">How often each sign shows up</h3>
        <div role="table" aria-label="Share of wallets showing each sign" className="type-product grid max-w-measure grid-cols-[auto_minmax(0,1fr)_auto_minmax(0,1fr)_auto] items-center gap-x-5 gap-y-3">
          <div role="row" className="contents">
            <span role="columnheader" className="type-label-lg text-text-3">Sign</span>
            <span role="columnheader" className="type-label-lg col-span-2 text-text-1">Named wallets, {rates.nNamed}</span>
            <span role="columnheader" className="type-label-lg col-span-2 text-text-3">All buyers, {rates.nAll.toLocaleString('en-US')}</span>
          </div>
          {rates.rows.map(r => <div key={r.f} role="row" className="contents">
            <span role="rowheader" className="type-product text-text-1">{FLAG_SHORT[r.f]}</span>
            <span aria-hidden className="h-4 bg-well"><span className="block h-full w-(--pct) bg-text-1" style={{'--pct': `${(r.named / rates.nNamed) * 100}%`} as React.CSSProperties}/></span>
            <span role="cell" className="type-product text-text-1">{r.named} of {rates.nNamed}</span>
            <span aria-hidden className="h-4 bg-well"><span className="block h-full w-(--pct) bg-text-3" style={{'--pct': `${r.all * 100}%`} as React.CSSProperties}/></span>
            <span role="cell" className="type-product text-end text-text-2">{Math.round(r.all * 100)}%</span>
          </div>)}
        </div>
        <p className="type-product max-w-measure text-text-2">Wallets named in public reporting, against every buyer before the news. Big bets and all-in accounts separate them most.</p>
      </div>
      <div className="flex flex-col gap-4">
        <h3 className="type-product text-text-1">Four checks, one that held up</h3>
        <ul aria-label="Four checks" className="flex flex-col border-t border-line">
          {checks.map(c => <li key={c.check} className="grid grid-cols-1 gap-x-6 gap-y-1 border-b border-line py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-baseline">
            <span className="type-product text-text-1 sm:col-start-1">{c.check}</span>
            <span className="type-product text-text-2 sm:col-start-1">{c.result}</span>
            <span className="type-label-lg text-text-2 sm:col-start-2 sm:row-start-1 sm:text-end">{c.verdict}</span>
          </li>)}
        </ul>
      </div>
    </Section>

    <Section id="demo" title="Demo: replay the Maduro market, Jan 1 to Jan 3, 2026.">
      <Replay d={replay}/>
    </Section>

    <Section id="watchlist" title="Open markets decided by small groups, scanned today.">
      <Watchlist/>
    </Section>

    <Section id="scan" title="Scan any market.">
      <ScanBox/>
    </Section>

    <Section id="next" title="What it cannot say, and what comes next.">
      <ul className="type-product flex max-w-measure flex-col border-t border-line" aria-label="Limits">
        {[
          'A flag is a reason to look, not proof. Most flagged wallets have never been accused.',
          'Journalists found the named wallets with similar signs, so 7 of 7 is partly circular.',
          'It misses insiders who use an old account, as in the Google case.',
        ].map(t => <li key={t} className="type-product border-b border-line py-4 text-text-1">{t}</li>)}
      </ul>
      <p className="type-product max-w-measure text-text-2">Planned next: learn the weight of each sign from resolved markets, then lock predictions on 10 open markets and score them when they resolve.</p>
    </Section>

    <footer className={`flex flex-col gap-6 border-t border-line py-10 ${pad}`}>
      <ul aria-label="Sources" className="grid gap-x-12 gap-y-2 md:grid-cols-2">
        {SOURCES.map(s => <li key={s.href} className="flex flex-wrap items-baseline gap-x-3">
          <Source href={s.href}>{s.name}</Source>
          <span className="type-product text-text-3">{s.what}</span>
        </li>)}
      </ul>
      <div className="flex flex-wrap items-baseline gap-x-8 gap-y-2">
        <p className="type-product text-text-2">{NOT_PROOF}</p>
        <a href={REPO} target="_blank" rel="noreferrer" className="type-product text-text-1 underline underline-offset-4 focus-visible:focus-ring">Code and data on GitHub</a>
      </div>
    </footer>
  </div>;
}
