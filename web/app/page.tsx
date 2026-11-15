import {Explorer, type XMarket, type XWallet} from '@/components/app/explorer';
import {Threshold} from '@/components/app/threshold';
import {NullHist} from '@/components/app/null-hist';
import {LiveScan} from '@/components/app/live-scan';
import {MARKET_IDS, getMarket, getMarkets, getTimeline, getV0, getValidation, getWallets} from '@/lib/data';
import {NOT_PROOF} from '@/lib/copy';

function Section({id, title, lede, children}: {id: string; title: string; lede?: string; children: React.ReactNode}) {
  return <section aria-labelledby={id} className="flex flex-col gap-5">
    <div className="flex flex-col gap-1">
      <h2 id={id} className="type-heading">{title}</h2>
      {lede && <p className="type-body-lg text-text-2 max-w-(--measure)">{lede}</p>}
    </div>
    {children}
  </section>;
}

export default function Home() {
  const {flags, headline: h, markets} = getMarkets();
  const val = getValidation();

  const xmarkets: XMarket[] = MARKET_IDS.map(id => {
    const m = getMarket(id)!;
    const docs = new Map<string, XWallet['doc']>();
    for (const v of val.filter(v => v.market === id)) {
      const prev = docs.get(v.wallet_id);
      if (!prev || v.confidence === 'charged') docs.set(v.wallet_id, {handle: v.identifier_type === 'handle' ? v.identifier : prev?.handle ?? null, confidence: v.confidence, publisher: v.publisher, source: v.source, claim: v.claim});
    }
    const wallets = getWallets(id).filter(w => w.score >= flags.HIGH).map(w => ({
      id: w.id, addr: w.addr, rank: w.rank, score: w.score, flags: w.flags, usd: w.usd, avg: w.avg_price, hours: w.hours, firstHigh: w.first_high_h,
      f1: w.f1_days, f2share: w.f2_share, f2markets: w.f2_markets, f5: w.f5, side: w.side, won: w.post.f7_won, dormant: w.post.f8_dormant, doc: docs.get(w.id),
    }));
    return {id, short: m.short, question: m.question, t_news: m.t_news, n_wallets: m.n_wallets, n_high: m.n_high, timeline: getTimeline(id), wallets};
  });

  const docScores = [...new Map(val.map(v => [`${v.market}:${v.wallet_id}`, v.score])).values()];
  const all = MARKET_IDS.flatMap(id => getWallets(id));
  const dist = Array.from({length: 7}, (_, s) => ({
    score: s,
    wallets: all.filter(w => w.score === s).length,
    documented: docScores.filter(x => x === s).length,
    under1k: all.filter(w => w.score === s && w.usd < 1000).length,
  }));
  const v0 = getV0();
  const ordered = MARKET_IDS.map(id => markets.find(m => m.id === id)!);

  return <div className="mx-auto flex w-full max-w-(--container) flex-col gap-16 px-(--gutter-sm) pt-8 pb-20 sm:px-(--gutter)">
    <header className="flex flex-col gap-4">
      <h1 className="type-display max-w-4xl text-balance">Hours before Maduro fell, an account opened days earlier had bet $32,538 at 7¢ that he would.</h1>
      <p className="type-body-lg text-text-2 max-w-(--measure)">
        From public trades alone, a screen written before we looked at any result ranked it first of {h.n_in_market.toLocaleString('en-US')} wallets, {h.hours_before} hours before the news. In April the CFTC charged its alleged owner. Here is the screen, run on three markets.
      </p>
    </header>

    <Section id="explore" title="Six signs, every wallet"
      lede="A fresh account, all-in on one market, a longshot price, a big bet, one direction only, and timing close to the news. A wallet showing 4 of the 6 is flagged. Pick a market, then a buy or a row.">
      <Explorer markets={xmarkets}/>
    </Section>

    <Section id="line" title="Where do you draw the line?"
      lede="Every wallet named in public reporting shows 4 or more signs. So do hundreds that nobody has named.">
      <Threshold dist={dist} total={all.length} documentedTotal={docScores.length} frozen={flags.HIGH}/>
    </Section>

    <Section id="luck" title="Is it just timing?"
      lede="We shuffled every buy to a random time in the same market, 1,000 times. Only on Nobel do the real wallets beat the shuffle.">
      <div className="grid gap-6 md:grid-cols-3">
        {ordered.map(m => <NullHist key={m.id} hist={m.permutation.hist} observed={m.permutation.observed}
          label={`${m.short}: ${m.permutation.observed} flagged vs ${m.permutation.null_min} to ${m.permutation.null_max} shuffled, p = ${m.permutation.p_value.toFixed(3)}`}/>)}
      </div>
    </Section>

    <Section id="live" title="Run it on a market today"
      lede="Paste any Polymarket link. Live, nobody knows when the news will break, so timing is left out and the score is out of 5.">
      <LiveScan/>
    </Section>

    <Section id="limits" title="What it cannot say">
      <ul className="grid gap-x-8 gap-y-4 md:grid-cols-2 max-w-5xl">
        <li className="type-body text-text-2"><span className="text-text-1">Partly circular.</span> Journalists found the named wallets with similar signs.</li>
        <li className="type-body text-text-2"><span className="text-text-1">Precision unproven.</span> {h.n_high_total} wallets flagged, {h.n_high_under_1k} of them under $1,000.</li>
        <li className="type-body text-text-2"><span className="text-text-1">Three markets.</span> A pilot, not a validated model.</li>
        <li className="type-body text-text-2"><span className="text-text-1">The first idea failed.</span> Counting copycat trades after big bets found nothing (p = {v0.p_value.toFixed(2)}).</li>
      </ul>
      <p className="type-heading-sm">{NOT_PROOF}</p>
    </Section>
  </div>;
}
