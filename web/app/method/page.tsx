import type {Metadata} from 'next';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/sodium/ui/table';
import {FlagMark, FLAG_RULE_SHORT} from '@/components/inv/flag-marks';
import {NullHist} from '@/components/inv/null-hist';
import {Threshold} from '@/components/inv/threshold';
import {MARKET_IDS, getMarket, getMarkets, getV0} from '@/lib/data';
import {scoreDist} from '@/lib/derive';
import {FLAGS, FLAG_SOURCE, NOT_PROOF, pct} from '@/lib/copy';

export const metadata: Metadata = {title: 'Method and limits'};

function Section({id, n, title, children}: {id: string; n: number; title: string; children: React.ReactNode}) {
  return <section aria-labelledby={id} className="flex flex-col gap-5 border-t border-line pt-10">
    <h2 id={id} className="type-heading"><span className="type-code text-text-3">{String(n).padStart(2, '0')} </span>{title}</h2>
    {children}
  </section>;
}

export default function Method() {
  const v0 = getV0();
  const ip = v0.pooled['insider-possible'], ctl = v0.pooled['insider-impossible'];
  const {headline: h, flags} = getMarkets();
  const markets = MARKET_IDS.map(id => getMarket(id)!);
  const {dist, namedTotal} = scoreDist();

  return <div className="mx-auto flex w-full max-w-7xl flex-col gap-12 px-4 py-12 sm:px-6">
    <h1 className="type-title max-w-3xl">How the screen works, and what it cannot tell you.</h1>

    <Section id="v0" n={1} title="The first idea failed">
      <p className="type-body max-w-measure text-text-2">If someone trades on inside knowledge, others might copy them. So we counted extra same-side wallets in the 30 minutes after unusually large trades, in these markets and in Bitcoin price markets where nobody can know the answer early. Rules were tuned on Bitcoin only and frozen first.</p>
      <div className="flex max-w-2xl flex-col gap-4">
        {[{l: 'Insider-possible markets', v: ip}, {l: 'Bitcoin controls', v: ctl}].map(r => <div key={r.l} className="flex flex-col gap-1.5">
          <span className="flex justify-between gap-4 type-label-sm text-text-2"><span>{r.l}</span><span className="type-code-sm">+{r.v.mean_excess.toFixed(2)} wallets, n = {r.v.n_seeds}</span></span>
          <span aria-hidden className="block h-3 w-(--w) bg-text-3" style={{'--w': `${(r.v.mean_excess / 2.2) * 100}%`} as React.CSSProperties}/>
        </div>)}
      </div>
      <p className="type-body text-text-1">No difference: permutation p = {v0.p_value.toFixed(2)}. A blind run on Maduro raised one alert, 96 hours early and pointing the wrong way.</p>
    </Section>

    <Section id="signs" n={2} title="Six signs, frozen before any result">
      <Table aria-label="The six signs, their frozen rules, sources and how often each fired" size="sm">
        <TableHeader><TableRow>
          <TableHead>Sign</TableHead><TableHead>Fires when</TableHead><TableHead>Source</TableHead>
          {markets.map(m => <TableHead key={m.id} numeric>{m.short}</TableHead>)}
        </TableRow></TableHeader>
        <TableBody>{FLAGS.map(f => <TableRow key={f}>
          <TableCell><FlagMark f={f} fired/></TableCell>
          <TableCell className="whitespace-normal">{FLAG_RULE_SHORT[f]}</TableCell>
          <TableCell className="whitespace-normal text-text-2">{FLAG_SOURCE[f]}</TableCell>
          {markets.map(m => <TableCell key={m.id} numeric>{pct(m.firing_rates[f])}</TableCell>)}
        </TableRow>)}</TableBody>
      </Table>
      <p className="type-body-sm max-w-measure text-text-2">Share of pre-news buyers each sign fires for. Thresholds were committed to git before any feature existed, and could not be checked against the source papers from this project. Near news fires for every Iran buyer (that market lived about 49 hours) and One-sided for about 7 in 10 buyers in Iran and Maduro, so both separate little.</p>
    </Section>

    <Section id="shuffle" n={3} title="Would random timing do as well?">
      <p className="type-body max-w-measure text-text-2">Each wallet&apos;s buy times were redrawn at random from the market&apos;s own activity, 1,000 times, keeping sizes and sides. If the real count of flagged wallets sits inside that spread, timing adds nothing.</p>
      <div className="grid gap-8 md:grid-cols-3">
        {markets.map(m => <NullHist key={m.id} hist={m.permutation.hist} observed={m.permutation.observed} title={m.short}
          verdict={m.permutation.p_value < 0.05
            ? `Beats random timing: ${m.permutation.observed} against ${m.permutation.null_mean} expected, p = ${m.permutation.p_value.toFixed(3)}.`
            : `No better than random timing: ${m.permutation.observed} against ${m.permutation.null_mean} expected, p = ${m.permutation.p_value.toFixed(2)}.`}/>)}
      </div>
    </Section>

    <Section id="line" n={4} title="Where to draw the line">
      <Threshold dist={dist} namedTotal={namedTotal} frozen={flags.HIGH}/>
    </Section>

    <Section id="limits" n={5} title="What it cannot say">
      <ul className="grid gap-x-10 gap-y-5 md:grid-cols-2">
        <li className="flex flex-col gap-1"><span className="type-label">Circular validation</span><span className="type-body text-text-2">Reporters and Lookonchain found the named wallets with cues like these signs. Catching them shows the screen reproduces public reporting, not that it finds hidden cases.</span></li>
        <li className="flex flex-col gap-1"><span className="type-label">Precision unproven</span><span className="type-body text-text-2">{h.n_high_total} wallet-markets score 4 or more; {h.n_high_under_1k} of them bought under $1,000. How many were informed is unknown.</span></li>
        <li className="flex flex-col gap-1"><span className="type-label">Three markets</span><span className="type-body text-text-2">One military strike, one regime change, one award. A pilot, not a validated model.</span></li>
        <li className="flex flex-col gap-1"><span className="type-label">Timing needs the news time</span><span className="type-body text-text-2">Near news, and every hours-before figure, use a news time only known afterwards. Live, the score is out of 5.</span></li>
      </ul>
      <p className="type-heading-sm">{NOT_PROOF}</p>
    </Section>
  </div>;
}
