import Link from 'next/link';
import {Hero} from '@/components/inv/hero';
import {MaduroInvestigation, type MaduroData} from '@/components/inv/maduro';
import {getBuys, getMarket, getMarkets, getTimeline, getValidation, getWallets} from '@/lib/data';
import {NOT_PROOF} from '@/lib/copy';

const CHARGED = 'MAD-CFTC-1';

export default function Investigation() {
  const {headline: h, flags} = getMarkets();
  const m = getMarket('maduro')!;
  const tl = getTimeline('maduro');
  const bf = getBuys('maduro');
  const label = getValidation().find(v => v.label_id === CHARGED)!;
  const w = getWallets('maduro').find(x => x.id === label.wallet_id)!;
  const isFlagged = (i: number) => bf.wallets[i].score >= flags.HIGH && bf.wallets[i].usd >= flags.F4_usd;
  const in48 = bf.buys.filter(b => b[0] >= m.t_news - 48 * 3600);
  const pre48 = tl.price.filter(([t]) => t >= m.t_news - 48 * 3600 && t < m.t_news).map(([, p]) => p).sort((a, b) => a - b);

  const d: MaduroData = {
    price: tl.price, tNews: m.t_news, resolution: tl.resolution_epoch, firstHighH: label.first_high_h,
    buys: bf.buys.map(([t, y, usd, i]) => ({t, y, usd, flagged: isFlagged(i), focus: bf.wallets[i].id === w.id})),
    wallet: {id: w.id, handle: label.identifier, fired: w.flags, nWallets: m.n_wallets, f1: w.f1_days, f2share: w.f2_share, f2markets: w.f2_markets, avg: w.avg_price, usd: w.usd, f5: w.f5, hours: w.hours},
    counts: {buys48: in48.length, wallets48: new Set(in48.map(b => b[3])).size, flaggedWallets48: new Set(in48.filter(b => isFlagged(b[3])).map(b => b[3])).size},
    priceStats: {median: pre48[Math.floor(pre48.length / 2)], max: pre48[pre48.length - 1]},
    source: {url: label.source, publisher: 'Baker Botts'},
  };

  return <>
    <Hero n={h.n_in_market} hoursBefore={h.hours_before} named={h.documented_flagged} namedTotal={h.documented_total}/>
    <MaduroInvestigation d={d}/>
    <section aria-labelledby="next-title" className="flex w-full flex-col gap-6 border-t border-line px-4 py-16 sm:px-6">
      <h2 id="next-title" className="type-heading max-w-2xl">One case is a story, not a result. The same screen, run on three markets, flagged {h.n_high_total} wallets, and {h.n_high_under_1k} of them bought under $1,000.</h2>
      <nav aria-label="Continue" className="flex flex-wrap gap-x-8 gap-y-3">
        <Link href="/cases" className="type-label text-text-1 underline underline-offset-4 focus-visible:focus-ring">See the three markets</Link>
        <Link href="/method" className="type-label text-text-1 underline underline-offset-4 focus-visible:focus-ring">Read the method and its limits</Link>
        <Link href="/live" className="type-label text-text-1 underline underline-offset-4 focus-visible:focus-ring">Scan a live market</Link>
      </nav>
      <p className="type-body text-text-2">{NOT_PROOF}</p>
    </section>
  </>;
}
