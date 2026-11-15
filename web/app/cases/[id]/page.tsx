import type {Metadata} from 'next';
import Link from 'next/link';
import {notFound} from 'next/navigation';
import {StatusStrip, StatusStripCell, StatusStripLabel, StatusStripValue} from '@/components/sodium/ui/status-strip';
import {CaseExplorer} from '@/components/inv/case-explorer';
import type {CaseWallet} from '@/components/inv/wallet-table';
import {MARKET_IDS, getBuys, getMarket, getMarkets, getTimeline, getValidation, getWallets, isMarketId} from '@/lib/data';
import {isFlagged} from '@/lib/derive';
import {utc} from '@/lib/copy';

export const dynamicParams = false;
export const generateStaticParams = () => MARKET_IDS.map(id => ({id}));

export async function generateMetadata({params}: {params: Promise<{id: string}>}): Promise<Metadata> {
  return {title: `${getMarket((await params).id)?.short ?? 'Market'} wallets`};
}

export default async function CasePage({params}: {params: Promise<{id: string}>}) {
  const {id} = await params;
  if (!isMarketId(id)) notFound();
  const m = getMarket(id)!;
  const {flags} = getMarkets();
  const tl = getTimeline(id), bf = getBuys(id);
  const val = getValidation().filter(v => v.market === id);
  const docs = new Map<string, CaseWallet['doc']>();
  for (const v of val) {
    const prev = docs.get(v.wallet_id);
    if (!prev || v.confidence === 'charged') docs.set(v.wallet_id, {handle: v.identifier_type === 'handle' ? v.identifier : prev?.handle ?? null, confidence: v.confidence, publisher: v.publisher, source: v.source, claim: v.claim});
    else if (!prev.handle && v.identifier_type === 'handle') prev.handle = v.identifier;
  }
  const rows: CaseWallet[] = getWallets(id).filter(w => w.score >= flags.HIGH).map(w => ({
    id: w.id, addr: w.addr, rank: w.rank, score: w.score, flags: w.flags, side: w.side, firstHigh: w.first_high_h,
    f1: w.f1_days, f2share: w.f2_share, f2markets: w.f2_markets, avg: w.avg_price, usd: w.usd, f5: w.f5, hours: w.hours,
    won: w.post.f7_won, dormant: w.post.f8_dormant, doc: docs.get(w.id),
  }));
  const buys = bf.buys.map(([t, y, usd, i]) => ({t, y, usd, flagged: isFlagged(bf.wallets[i].score, bf.wallets[i].usd), focus: false, w: bf.wallets[i].id}));
  const flagged = rows.filter(r => isFlagged(r.score, r.usd)).length;
  const beats = m.permutation.p_value < 0.05;

  return <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-10 sm:px-6">
    <nav aria-label="Breadcrumb" className="type-label text-text-3"><Link href="/cases" className="hover:text-text-1 focus-visible:focus-ring">Cases</Link> <span aria-hidden>/</span> <span className="text-text-1">{m.short}</span></nav>
    <h1 className="type-title max-w-4xl">{m.question}</h1>
    <StatusStrip label={`${m.short} results`}>
      <StatusStripCell><StatusStripLabel>Pre-news buyers</StatusStripLabel><StatusStripValue>{m.n_wallets.toLocaleString('en-US')}</StatusStripValue></StatusStripCell>
      <StatusStripCell><StatusStripLabel>Flagged, $2,500 or more</StatusStripLabel><StatusStripValue className="text-accent-text">{flagged}</StatusStripValue></StatusStripCell>
      <StatusStripCell><StatusStripLabel>Shuffle test</StatusStripLabel><StatusStripValue>{beats ? 'Beats random timing' : 'No better than random'} <span className="text-text-3">p {m.permutation.p_value.toFixed(3)}</span></StatusStripValue></StatusStripCell>
      <StatusStripCell><StatusStripLabel>First news</StatusStripLabel><StatusStripValue>{utc(m.t_news)}</StatusStripValue></StatusStripCell>
    </StatusStrip>
    <CaseExplorer chart={{price: tl.price, tNews: m.t_news, x0: m.t_news - 48 * 3600, x1: tl.resolution_epoch, newsLabel: 'First news'}}
      buys={buys} rows={rows} nWallets={m.n_wallets} flaggedMin={flags.F4_usd} market={m.short}/>
  </div>;
}
