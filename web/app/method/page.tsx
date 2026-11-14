import type {Metadata} from 'next';
import Link from 'next/link';
import {PageHeader, PageHeaderContent, PageHeaderDescription, PageHeaderTitle} from '@/components/quartz/ui/page-header';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/quartz/ui/table';
import {NullHist} from '@/components/app/null-hist';
import {DocBadge, FlagChips} from '@/components/app/flag-chips';
import {MARKET_IDS, getLayer2, getMarket, getMarkets, getV0, getValidation} from '@/lib/data';
import {FLAGS, FLAG_NAMES, FLAG_RULE, FLAG_SOURCE, NOT_PROOF, pct} from '@/lib/copy';

export const metadata: Metadata = {title: 'Method'};

const TOC = [
  ['attempt-1', 'Attempt 1: ripples'], ['screen', 'The v1 screen'], ['null', 'Random timing'], ['validation', 'Validation'], ['layer-2', 'Do others follow?'], ['limits', 'Limits'],
] as const;

function H2({id, n, children}: {id: string; n: number; children: React.ReactNode}) {
  return <h2 id={id} className="type-heading scroll-mt-20"><span className="text-text-3">{n}. </span>{children}</h2>;
}
const P = ({children}: {children: React.ReactNode}) => <p className="type-body-lg text-text-2 max-w-(--measure)">{children}</p>;

export default function MethodPage() {
  const v0 = getV0();
  const {headline: h} = getMarkets();
  const markets = MARKET_IDS.map(id => getMarket(id)!);
  const val = getValidation();
  const l2 = getLayer2().tests.filter(t => t.outcome === 'wallets');
  const ip = v0.pooled['insider-possible'], ctl = v0.pooled['insider-impossible'];
  const distinct = [...new Map(val.map(v => [`${v.market}:${v.wallet_id}`, v])).values()];
  const at10k = distinct.filter(v => v.sens['10000'] >= 4).length;

  return <div className="mx-auto flex w-full max-w-(--container) flex-col gap-12 px-(--gutter-sm) py-8 sm:px-(--gutter)">
    <PageHeader>
      <PageHeaderContent>
        <PageHeaderTitle>How the screen works, and what it cannot tell you</PageHeaderTitle>
        <PageHeaderDescription>A plain-language account of the pilot: one attempt that failed, the method that replaced it, how it was checked, and where it stops. Every number states its n.</PageHeaderDescription>
      </PageHeaderContent>
      <nav aria-label="On this page"><ol className="flex flex-wrap gap-x-4 gap-y-1">
        {TOC.map(([id, t], i) => <li key={id}><a href={`#${id}`} className="type-label text-text-2 underline-offset-4 hover:underline">{i + 1}. {t}</a></li>)}
      </ol></nav>
    </PageHeader>

    <section aria-labelledby="attempt-1" className="flex flex-col gap-4">
      <H2 id="attempt-1" n={1}>Attempt 1: ripples after large trades (it failed)</H2>
      <P>The first idea: if someone trades on inside knowledge, others might notice and pile in. So after every unusually large trade (above the 99th percentile of size), count how many extra wallets trade the same way in the next 30 minutes, compared with quiet moments. Do this in the three insider-possible markets and in Bitcoin price markets, where nobody can know the answer early. The rules were tuned on the Bitcoin markets only and frozen before the real markets were scored.</P>
      <Table aria-label="Attempt 1 results" size="sm" className="max-w-2xl">
        <TableHeader><TableRow><TableHead>Group</TableHead><TableHead className="text-end">Large trades compared</TableHead><TableHead className="text-end">Extra wallets after each</TableHead></TableRow></TableHeader>
        <TableBody>
          <TableRow><TableCell>Insider-possible, {ip.n_markets} markets</TableCell><TableCell className="text-end data">{ip.n_seeds}</TableCell><TableCell className="text-end data">+{ip.mean_excess.toFixed(2)}</TableCell></TableRow>
          <TableRow><TableCell>Bitcoin controls, {ctl.n_markets} markets</TableCell><TableCell className="text-end data">{ctl.n_seeds}</TableCell><TableCell className="text-end data">+{ctl.mean_excess.toFixed(2)}</TableCell></TableRow>
        </TableBody>
      </Table>
      <P>The difference is not distinguishable from chance (permutation p = {v0.p_value.toFixed(2)}), and the baseline itself added +{v0.placebo_bias.toFixed(2)} wallets on the controls. A blind run on Maduro raised {v0.maduro_blind.alerts_pre_news} alert before the news, {v0.maduro_blind.hours_before_news} hours early and {v0.maduro_blind.direction}; the final hours before the news could not be scored because they were too busy to match. Why it failed: it judged trades, not traders; size alone picks whales and market makers; and it was blind exactly when it mattered.</P>
    </section>

    <section aria-labelledby="screen" className="flex flex-col gap-4">
      <H2 id="screen" n={2}>The v1 screen: score the wallet, not the trade</H2>
      <P>For every wallet that bought before the first public news, six yes-or-no flags are computed from its trading up to that moment. The score is how many fired. Four or more is a high score. The thresholds come from published work, were written to <code className="type-code">rules/frozen_v1.md</code> and committed to git before any feature existed, and were never changed after.</P>
      <Table aria-label="The six flags with firing rates per market" size="sm">
        <TableHeader><TableRow>
          <TableHead>Flag</TableHead><TableHead>Fires when</TableHead><TableHead>Source</TableHead>
          {markets.map(m => <TableHead key={m.id} className="text-end">{m.short}</TableHead>)}
        </TableRow></TableHeader>
        <TableBody>{FLAGS.map(f => <TableRow key={f}>
          <TableCell className="whitespace-normal"><span className="type-label">{f}</span> {FLAG_NAMES[f]}</TableCell>
          <TableCell className="whitespace-normal text-text-2">{FLAG_RULE[f]}</TableCell>
          <TableCell className="whitespace-normal text-text-2">{FLAG_SOURCE[f]}</TableCell>
          {markets.map(m => <TableCell key={m.id} className="text-end data">{pct(m.firing_rates[f])}</TableCell>)}
        </TableRow>)}</TableBody>
      </Table>
      <p className="type-body-sm text-text-2 max-w-(--measure)">Share of pre-news buyers for whom each flag fires (n = {markets.map(m => `${m.n_wallets.toLocaleString('en-US')} ${m.short}`).join(', ')}). F6 fires for every Iran buyer because that market lived only about 49 hours; F5 fires for about 7 in 10 buyers in Iran and Maduro. Both separate little. The thresholds could not be checked against the source papers from this project&apos;s environment.</p>
      <P>Two more measures are kept apart and never enter the score, because they are only known afterwards: F7, whether the wallet&apos;s side won, and F8, whether it went quiet for 30 days after resolution.</P>
    </section>

    <section aria-labelledby="null" className="flex flex-col gap-4">
      <H2 id="null" n={3}>Would random timing do as well?</H2>
      <P>Some flags fire for reasons that have nothing to do with knowing early. To check, every wallet&apos;s buy times were shuffled at random within the market&apos;s own activity, 1,000 times, keeping sizes and sides, and the high scores were counted again. If the real count sits inside that spread, timing adds nothing.</P>
      <div className="grid gap-6 md:grid-cols-3">
        {markets.map(m => <NullHist key={m.id} hist={m.permutation.hist} observed={m.permutation.observed}
          label={`${m.short}: observed ${m.permutation.observed}, random ${m.permutation.null_min} to ${m.permutation.null_max} (mean ${m.permutation.null_mean}), p = ${m.permutation.p_value.toFixed(3)}`}/>)}
      </div>
      <P>Only Nobel has more high scores than random timing produces. In Iran and Maduro the high scores come from flags that do not depend on timing.</P>
    </section>

    <section aria-labelledby="validation" className="flex flex-col gap-4">
      <H2 id="validation" n={4}>Validation against wallets named in public reporting</H2>
      <P>Labels come only from public reporting: a CFTC complaint, Lookonchain, Bloomberg, the WSJ via secondary coverage, and the Anti-Corruption Data Collective. They were matched to wallets by a frozen rule before scoring. No wallet was ever added because the screen flagged it.</P>
      <Table aria-label="Documented wallets and their scores" size="sm">
        <TableHeader><TableRow>
          <TableHead>Label</TableHead><TableHead>Reported as</TableHead><TableHead>Status</TableHead><TableHead className="text-end">Score</TableHead><TableHead>Flags</TableHead>
          <TableHead className="text-end">Rank</TableHead><TableHead className="text-end">Score 4 reached</TableHead><TableHead>Source</TableHead>
        </TableRow></TableHeader>
        <TableBody>{val.map(v => <TableRow key={v.label_id}>
          <TableCell className="type-code-sm">{v.label_id}</TableCell>
          <TableCell>{v.identifier}</TableCell>
          <TableCell><DocBadge confidence={v.confidence}/></TableCell>
          <TableCell className="text-end data">{v.score}</TableCell>
          <TableCell><FlagChips fired={v.flags}/></TableCell>
          <TableCell className="text-end data">{v.rank} of {v.n.toLocaleString('en-US')}</TableCell>
          <TableCell className="text-end data">{v.first_high_h.toFixed(1)} h before</TableCell>
          <TableCell><a href={v.source} target="_blank" rel="noreferrer" className="underline underline-offset-4">{v.publisher.split(' (')[0].split(' via ')[0]}</a></TableCell>
        </TableRow>)}</TableBody>
      </Table>
      <P>{h.documented_flagged} of {h.documented_total} distinct wallets (8 labels; the CFTC handle and Lookonchain&apos;s 0x31a5 are the same wallet) score 4 or more. With the size flag at $10,000 instead of $2,500, {at10k} of {distinct.length} still do. The wallets in the CFTC complaint and in Lookonchain&apos;s report crossed the line 30, 8 and 2 hours before the news.</P>
      <P><Link href="/markets/maduro/wallet/0x31a5" className="underline underline-offset-4">Open the alert for the CFTC-charged wallet</Link>.</P>
    </section>

    <section aria-labelledby="layer-2" className="flex flex-col gap-4">
      <H2 id="layer-2" n={5}>Do other traders follow high-score wallets? Mostly no</H2>
      <P>Each buy by a high-score wallet was compared with buys of similar size, within 6 hours, by established wallets (10 or more markets, score 1 or less). The question: do more traders buy the same side right after?</P>
      <Table aria-label="Followers after high-score buys versus matched buys" size="sm">
        <TableHeader><TableRow>
          <TableHead>Window</TableHead><TableHead>Scope</TableHead><TableHead className="text-end">High-score buys (wallets)</TableHead>
          <TableHead className="text-end">Followers after them</TableHead><TableHead className="text-end">After matched buys</TableHead><TableHead className="text-end">Difference [95% CI]</TableHead><TableHead className="text-end">p</TableHead>
        </TableRow></TableHeader>
        <TableBody>{l2.map(t => <TableRow key={`${t.H}-${t.scope}`}>
          <TableCell className="data">{t.H} min</TableCell><TableCell>{t.scope === 'pooled' ? 'All markets' : getMarket(t.scope)?.short}</TableCell>
          <TableCell className="text-end data">{t.n_A_seeds} ({t.n_A_wallets})</TableCell>
          <TableCell className="text-end data">{t.mean_A.toFixed(1)}</TableCell><TableCell className="text-end data">{t.mean_B.toFixed(1)}</TableCell>
          <TableCell className="text-end data">{t.mean_diff > 0 ? '+' : ''}{t.mean_diff.toFixed(1)} [{t.ci95[0].toFixed(1)}, {t.ci95[1].toFixed(1)}]</TableCell>
          <TableCell className="text-end data">{t.p_signflip < 0.001 ? '< 0.001' : t.p_signflip.toFixed(3)}</TableCell>
        </TableRow>)}</TableBody>
      </Table>
      <P>Pooled, high-score buys draw fewer followers, not more, and no more whales or bots. Nobel is the exception: after high-score buys there, more traders bought the same side, consistent with the publicly reported spike before the announcement. Matched buys were not matched on how busy the market was at the time, which can explain part of the gap.</P>
    </section>

    <section aria-labelledby="limits" className="flex flex-col gap-4">
      <H2 id="limits" n={6}>Limits</H2>
      <ul className="grid gap-x-8 gap-y-5 md:grid-cols-2">
        <li className="flex flex-col gap-1"><span className="type-heading-xs">Circular validation</span><span className="type-body text-text-2">Journalists and Lookonchain found these wallets with cues like the flags: new, focused, large longshot bets before news. Catching them shows the screen reproduces public reporting, not that it finds hidden cases.</span></li>
        <li className="flex flex-col gap-1"><span className="type-heading-xs">Precision unproven</span><span className="type-body text-text-2">{h.n_high_total} of {h.n_wallet_markets.toLocaleString('en-US')} wallet-markets score 4 or more; {h.n_high_under_1k} of them bought under $1,000. Winning does not help tell them apart: all three markets resolved to the long-time longshot, and among longshot buyers, high scorers won less often.</span></li>
        <li className="flex flex-col gap-1"><span className="type-heading-xs">F6 needs the news time</span><span className="type-body text-text-2">The timing flag and every hours-before figure use a news time that is only known afterwards. The live scan therefore scores out of 5, and no live threshold is validated.</span></li>
        <li className="flex flex-col gap-1"><span className="type-heading-xs">Three markets only</span><span className="type-body text-text-2">One military, one regime change, one award. Adding two or three more markets under the same frozen rules is the main path to statistical power.</span></li>
      </ul>
      <p className="type-heading-sm">{NOT_PROOF}</p>
    </section>
  </div>;
}
