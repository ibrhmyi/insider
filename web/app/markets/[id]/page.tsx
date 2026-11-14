import type {Metadata} from 'next';
import Link from 'next/link';
import {notFound} from 'next/navigation';
import {PageHeader, PageHeaderContent, PageHeaderDescription, PageHeaderRow, PageHeaderStat, PageHeaderStats, PageHeaderTitle} from '@/components/quartz/ui/page-header';
import {Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator} from '@/components/quartz/ui/breadcrumb';
import {Button} from '@/components/quartz/ui/button';
import {PriceTimeline} from '@/components/app/price-timeline';
import {WalletTable, type TableRow} from '@/components/app/wallet-table';
import {MARKET_IDS, getMarket, getMarkets, getTimeline, getValidation, getWallets, isMarketId} from '@/lib/data';
import {DISCLAIMER, utc} from '@/lib/copy';

export const dynamicParams = false;
export const generateStaticParams = () => MARKET_IDS.map(id => ({id}));

export async function generateMetadata({params}: {params: Promise<{id: string}>}): Promise<Metadata> {
  const m = getMarket((await params).id);
  return {title: m ? `${m.short} market` : 'Market'};
}

export default async function MarketPage({params}: {params: Promise<{id: string}>}) {
  const {id} = await params;
  if (!isMarketId(id)) notFound();
  const m = getMarket(id)!;
  const val = getValidation().filter(v => v.market === id);
  const docBy = new Map<string, TableRow['doc']>();
  for (const v of val) {
    const prev = docBy.get(v.wallet_id);
    if (!prev || v.confidence === 'charged') docBy.set(v.wallet_id, {
      handle: v.identifier_type === 'handle' ? v.identifier : prev?.handle ?? null,
      confidence: v.confidence, publisher: v.publisher, source: v.source,
    });
    else if (!prev.handle && v.identifier_type === 'handle') prev.handle = v.identifier;
  }
  const rows: TableRow[] = getWallets(id).map(w => ({
    id: w.id, rank: w.rank, score: w.score, flags: w.flags, usd: w.usd, avg: w.avg_price, hours: w.hours, side: w.side,
    won: w.post.f7_won, dormant: w.post.f8_dormant, doc: docBy.get(w.id),
  }));
  const p = m.permutation;
  const others = getMarkets().markets.filter(x => x.id !== id);

  return <div className="mx-auto flex w-full max-w-(--container) flex-col gap-8 px-(--gutter-sm) py-6 sm:px-(--gutter)">
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem><BreadcrumbLink render={<Link href="/"/>}>Overview</BreadcrumbLink></BreadcrumbItem>
        <BreadcrumbSeparator/>
        <BreadcrumbItem><BreadcrumbPage>{m.short}</BreadcrumbPage></BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
    <PageHeader>
      <PageHeaderRow>
        <PageHeaderContent>
          <PageHeaderTitle>{m.question}</PageHeaderTitle>
          <PageHeaderDescription>{m.why_insider_possible} First public news: {utc(m.t_news)}, {m.t_news_basis.charAt(0).toLowerCase() + m.t_news_basis.slice(1)} (<a className="underline underline-offset-4" href={m.t_news_source.split(' ')[0]} target="_blank" rel="noreferrer">news source</a>).</PageHeaderDescription>
        </PageHeaderContent>
        <nav aria-label="Other markets" className="flex flex-wrap gap-2">
          {others.map(o => <Button key={o.id} variant="secondary" size="sm" nativeButton={false} render={<Link href={`/markets/${o.id}`}/>}>{o.short} market</Button>)}
        </nav>
      </PageHeaderRow>
      <PageHeaderStats aria-label="Market results">
        <PageHeaderStat label="Pre-news buyers scored" value={m.n_wallets.toLocaleString('en-US')}/>
        <PageHeaderStat label="Score 4 or more" value={p.observed} detail={`random timing gives ${p.null_mean}`}/>
        <PageHeaderStat label="Permutation p, 1,000 runs" value={p.p_value.toFixed(3)} detail={p.p_value < 0.05 ? 'beats random timing' : 'no better than random timing'}/>
        <PageHeaderStat label="Named in public reporting" value={m.n_documented}/>
      </PageHeaderStats>
    </PageHeader>

    <PriceTimeline data={getTimeline(id)} title={m.short}/>

    <section aria-labelledby="wallets-heading" className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <h2 id="wallets-heading" className="type-heading">Ranked wallets</h2>
        <p className="type-body text-text-2 max-w-(--measure)">Every wallet that bought before the news, ranked by score, then by USD bought. The list starts filtered to F4, wallets that bought $2,500 or more.</p>
      </div>
      <WalletTable rows={rows} market={id} marketName={m.short}/>
      <p className="type-body text-text-1">{DISCLAIMER}</p>
    </section>
  </div>;
}
