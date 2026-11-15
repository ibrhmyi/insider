import type {Metadata} from 'next';
import Link from 'next/link';
import {Tag} from '@/components/sodium/ui/tag';
import {Sparkline} from '@/components/inv/sparkline';
import {NobelStory, type NobelData} from '@/components/inv/nobel';
import {MARKET_IDS, getBuys, getLayer2, getMarket, getTimeline, getValidation, getWallets} from '@/lib/data';
import {chartBuys, isFlagged} from '@/lib/derive';
import {NOT_PROOF} from '@/lib/copy';

export const metadata: Metadata = {title: 'Cases'};

export default function Cases() {
  const val = getValidation();
  const l2 = getLayer2().tests.filter(t => t.H === 30 && t.outcome === 'wallets');
  const cards = MARKET_IDS.map(id => {
    const m = getMarket(id)!;
    const named = [...new Map(val.filter(v => v.market === id).map(v => [v.wallet_id, v])).values()]
      .map(v => ({id: v.wallet_id, rank: v.rank, confidence: val.some(x => x.wallet_id === v.wallet_id && x.confidence === 'charged') ? 'charged' : 'alleged', name: val.find(x => x.wallet_id === v.wallet_id && x.identifier_type === 'handle')?.identifier ?? `${v.wallet_id}…`}))
      .sort((a, b) => a.rank - b.rank);
    const flagged = getWallets(id).filter(w => isFlagged(w.score, w.usd)).length;
    const follow = l2.find(t => t.scope === id)!;
    return {m, named, flagged, follow, price: getTimeline(id).price};
  });

  const nb = getMarket('nobel')!, tl = getTimeline('nobel');
  const buys = chartBuys('nobel');
  const fl48 = buys.filter(b => b.flagged && b.t >= nb.t_news - 48 * 3600);
  const jump = tl.price.find(([t, p]) => p >= 0.3 && t > nb.t_news - 72 * 3600)!;
  const f = l2.find(t => t.scope === 'nobel')!;
  const nobel: NobelData = {
    price: tl.price, buys, tNews: nb.t_news, resolution: tl.resolution_epoch,
    jumpH: (nb.t_news - jump[0]) / 3600,
    flaggedWallets: new Set(getBuys('nobel').buys.filter(([t, , , i]) => t >= nb.t_news - 48 * 3600 && isFlagged(getBuys('nobel').wallets[i].score, getBuys('nobel').wallets[i].usd)).map(b => b[3])).size,
    earliestFlaggedH: (nb.t_news - Math.min(...fl48.map(b => b.t))) / 3600,
    perm: {observed: nb.permutation.observed, nullMean: nb.permutation.null_mean, p: nb.permutation.p_value},
    follow: {diff: f.mean_diff, n: f.n_A_seeds, ci: f.ci95},
  };

  return <div className="flex flex-col">
    <section aria-labelledby="cases-title" className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-12 sm:px-6">
      <h1 id="cases-title" className="type-title max-w-3xl">Three markets, one screen. Only one of them shows a signal beyond chance.</h1>
      <ul className="grid gap-6 lg:grid-cols-3">
        {cards.map(({m, named, flagged, follow, price}) => {
          const beats = m.permutation.p_value < 0.05;
          return <li key={m.id} className="frame flex flex-col">
            <div className="panel-head"><h2 className="type-label">{m.short}</h2><span className="type-code-sm text-text-3">{flagged} flagged of {m.n_wallets.toLocaleString('en-US')}</span></div>
            <div className="flex flex-1 flex-col gap-4 p-4">
              <p className="type-body text-text-2">{m.question}</p>
              <Sparkline price={price} tNews={m.t_news} label={`${m.short}: Yes price over the whole market; dashed line at the first news`}/>
              <div className="flex flex-col gap-1">
                <span className="type-micro text-text-3">Named in public reporting</span>
                <ul className="flex flex-col gap-1">{named.map(n => <li key={n.id} className="flex items-center justify-between gap-3">
                  <span className="type-code-sm">{n.name}</span>
                  <span className="flex items-center gap-2"><span className="type-code-sm text-text-2">rank {n.rank}</span><Tag size="sm" variant={n.confidence === 'charged' ? 'neutral' : 'outline'}>{n.confidence === 'charged' ? 'Charged' : 'Alleged'}</Tag></span>
                </li>)}</ul>
              </div>
              <p className="type-body"><span className={beats ? 'text-text-1' : 'text-text-2'}>{beats ? 'Beats random timing' : "Doesn't beat random timing"}</span> <span className="type-code-sm text-text-3">p = {m.permutation.p_value.toFixed(3)}</span></p>
              <p className="type-body-sm text-text-2">Followers after flagged buys: {follow.mean_diff > 0 ? 'more' : 'fewer'} than after matched buys ({follow.mean_diff > 0 ? '+' : ''}{follow.mean_diff.toFixed(1)}, n = {follow.n_A_seeds}).</p>
              <Link href={`/cases/${m.id}`} className="mt-auto type-label text-text-1 underline underline-offset-4 focus-visible:focus-ring">Open {m.short} wallets</Link>
            </div>
          </li>;
        })}
      </ul>
      <p className="type-body-sm text-text-2">{NOT_PROOF}</p>
    </section>
    <section aria-labelledby="nobel-title" className="border-t border-line">
      <h2 id="nobel-title" className="mx-auto w-full max-w-7xl px-4 pt-12 type-heading sm:px-6">The second story: Nobel</h2>
      <NobelStory d={nobel}/>
    </section>
  </div>;
}
