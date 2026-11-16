import type {Metadata} from 'next';
import {Story} from '@/components/inv/story';
import {InvestigationChart} from '@/components/inv/chart';
import {STATE_ALL, STATE_MARKET} from '@/lib/chart-state';
import {FlagMark, FLAG_RULE_SHORT, flagValue} from '@/components/inv/flag-marks';
import {ScoreBars} from '@/components/inv/score-bars';
import {chartBase, chartBuys, liveExample, scoreDist} from '@/lib/derive';
import {getLayer2, getMarket, getMarkets, getV0, getValidation, getWallets} from '@/lib/data';
import {DISCLAIMER, FLAGS, NOT_PROOF, usd} from '@/lib/copy';

export const metadata: Metadata = {title: 'Story'};

export default function StoryPage() {
  const {headline: h} = getMarkets();
  const v0 = getV0();
  const ip = v0.pooled['insider-possible'], ctl = v0.pooled['insider-impossible'];
  const charged = getValidation().find(v => v.label_id === 'MAD-CFTC-1')!;
  const w = getWallets('maduro').find(x => x.id === charged.wallet_id)!;
  const vals = {f1: w.f1_days, f2share: w.f2_share, f2markets: w.f2_markets, avg: w.avg_price, usd: w.usd, f5: w.f5, hours: w.hours};
  const nobel = getMarket('nobel')!;
  const l2 = getLayer2().tests.find(t => t.H === 30 && t.outcome === 'wallets' && t.scope === 'nobel')!;
  const {dist, namedTotal} = scoreDist();
  const live = liveExample();
  const liveRows = live.wallets.filter(x => x.score >= 3 && x.F4_buy_usd >= 2500);
  const big = 'type-display max-w-3xl text-balance';

  const slides = [
    {title: 'The problem', body: <>
      <h1 className={big}>Some traders may know how a market ends before anyone else does.</h1>
      <p className="type-heading max-w-3xl text-text-2">Can public trade data alone point to them, before the news breaks? Three Polymarket markets decided by a small group: a US strike on Iran, Maduro out by January 31, and the 2025 Nobel Peace Prize.</p>
    </>},
    {title: 'A first idea that failed', body: <>
      <h1 className={big}>First idea: big trades draw copycats. It found nothing.</h1>
      <div className="flex max-w-3xl flex-col gap-5">
        {[{l: 'Markets where insiders were possible', v: ip}, {l: 'Bitcoin price markets (no insiders possible)', v: ctl}].map(r => <div key={r.l} className="flex flex-col gap-2">
          <span className="flex flex-wrap justify-between gap-x-6 type-heading-sm"><span>{r.l}</span><span className="type-code">+{r.v.mean_excess.toFixed(2)} extra wallets, n = {r.v.n_seeds}</span></span>
          <span aria-hidden className="block h-6 w-(--w) bg-text-3" style={{'--w': `${(r.v.mean_excess / 2.2) * 100}%`} as React.CSSProperties}/>
        </div>)}
        <p className="type-heading-sm text-text-2">No difference: permutation p = {v0.p_value.toFixed(2)}. So score the trader, not the trade.</p>
      </div>
    </>},
    {title: 'Six signs', body: <>
      <h1 className={big}>Six signs from published research, fixed before any result was seen.</h1>
      <ul className="grid max-w-3xl gap-x-12 gap-y-6 sm:grid-cols-2">
        {FLAGS.map(f => <li key={f} className="flex flex-col gap-1"><FlagMark f={f} fired size="lg"/><span className="type-heading-sm text-text-2">{FLAG_RULE_SHORT[f]}</span></li>)}
      </ul>
      <p className="type-heading-sm text-text-2">A wallet showing 4 or more is flagged for review.</p>
    </>},
    {title: 'The Maduro wallet', body: <div className="grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:items-center">
      <div className="flex flex-col gap-5">
        <h1 className="type-title">#{h.rank} of {h.n_in_market.toLocaleString('en-US')} wallets, flagged {h.hours_before} hours before the news.</h1>
        <div className="flex flex-wrap gap-x-5 gap-y-2">{FLAGS.map(f => <FlagMark key={f} f={f} fired={w.flags.includes(f)} value={flagValue(f, vals)} size="lg"/>)}</div>
        <p className="type-heading-sm">In April 2026 the CFTC charged its alleged owner. Charged, not convicted.</p>
        <p className="type-body-sm text-text-2">{DISCLAIMER}</p>
      </div>
      <div className="h-[60svh] min-h-80">
        <InvestigationChart {...chartBase('maduro')} buys={chartBuys('maduro', w.id)} state={STATE_ALL} newsLabel="First news 06:00 UTC"
          firstHighT={chartBase('maduro').tNews - charged.first_high_h * 3600} firstHighLabel={`Crossed 4 signs, ${h.hours_before} h before`}
          callout={<div className="flex flex-col gap-1"><span className="type-code text-accent-text">{charged.identifier}</span><span className="type-body-sm">{usd(w.usd)} at {Math.round(w.avg_price * 100)}¢</span></div>}
          label="Maduro market, last 48 hours: the charged wallet's buys highlighted, news at 06:00 UTC January 3"/>
      </div>
    </div>},
    {title: 'Nobel', body: <div className="grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:items-center">
      <div className="flex flex-col gap-5">
        <h1 className="type-title">Nobel is the one market where the signal holds up.</h1>
        <p className="type-heading-sm text-text-2">Real wallets beat random timing: {nobel.permutation.observed} flagged against {nobel.permutation.null_mean} expected, p = {nobel.permutation.p_value.toFixed(3)}.</p>
        <p className="type-heading-sm text-text-2">After flagged buys, {l2.mean_diff.toFixed(1)} more traders followed within 30 minutes than after matched buys (n = {l2.n_A_seeds}).</p>
        <p className="type-body-sm text-text-2">In Maduro and Iran, neither test shows an effect.</p>
      </div>
      <div className="h-[60svh] min-h-80">
        <InvestigationChart {...chartBase('nobel')} buys={chartBuys('nobel')} state={STATE_MARKET} newsLabel="Announcement 09:00 UTC"
          label="Nobel market, last 48 hours before the announcement: flagged buys in yellow"/>
      </div>
    </div>},
    {title: 'The line and its limits', body: <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
      <div className="flex flex-col gap-5">
        <h1 className="type-title">At 4 signs, all {namedTotal} named wallets are caught. So are {h.n_high_total - namedTotal} others.</h1>
        <ul className="flex flex-col gap-2 type-heading-sm text-text-2">
          <li>{h.n_high_under_1k} of the {h.n_high_total} flagged bought under $1,000.</li>
          <li>Partly circular: reporters found these wallets with similar signs.</li>
          <li>Timing needs the news time, which is unknown live.</li>
          <li>Three markets. A pilot, not a validated model.</li>
        </ul>
      </div>
      <ScoreBars dist={dist} cutoff={4} height={300}/>
    </div>},
    {title: 'Live scan', body: <>
      <h1 className={big}>The same signs run on any market today, minus timing.</h1>
      <p className="type-heading-sm text-text-2">{live.market.question}</p>
      {liveRows.length === 0
        ? <p className="type-heading">No wallet crosses the line in this market right now.</p>
        : <ul className="flex max-w-3xl flex-col gap-3">{liveRows.slice(0, 5).map(r => <li key={r.id} className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-line pb-3">
          <span className="type-code">{r.id}…</span><span className="type-code text-accent-text">{r.score}/5</span>
          <span className="type-code">{usd(r.F4_buy_usd)}</span>
          <span className="flex flex-wrap gap-x-4">{(['F1', 'F2', 'F3', 'F4', 'F5'] as const).map(f => <FlagMark key={f} f={f} fired={r.fired.includes(f)}/>)}</span>
        </li>)}</ul>}
      <p className="type-heading-sm">{NOT_PROOF}</p>
    </>},
  ];
  return <Story slides={slides}/>;
}

