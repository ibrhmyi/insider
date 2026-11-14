import type {Metadata} from 'next';
import Link from 'next/link';
import {notFound} from 'next/navigation';
import {PageHeader, PageHeaderContent, PageHeaderDescription, PageHeaderTitle} from '@/components/quartz/ui/page-header';
import {Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator} from '@/components/quartz/ui/breadcrumb';
import {AlertCard} from '@/components/app/alert-card';
import {FlagChips, DocBadge} from '@/components/app/flag-chips';
import {MARKET_IDS, getAlerts, getMarket, getMarkets, getValidation, getWallets, isMarketId} from '@/lib/data';

export const dynamicParams = false;

/** An alert exists for every wallet-market that scores 4 or more (271 pages). */
export function generateStaticParams() {
  return MARKET_IDS.flatMap(id => getWallets(id).filter(w => w.score >= getMarkets().flags.HIGH).map(w => ({id, prefix: w.id})));
}

export async function generateMetadata({params}: {params: Promise<{id: string; prefix: string}>}): Promise<Metadata> {
  const {id, prefix} = await params;
  return {title: `Alert ${prefix}… in ${getMarket(id)?.short ?? id}`};
}

export default async function WalletAlert({params}: {params: Promise<{id: string; prefix: string}>}) {
  const {id, prefix} = await params;
  if (!isMarketId(id)) notFound();
  const w = getWallets(id).find(x => x.id === prefix);
  if (!w) notFound();
  const m = getMarket(id)!;
  const {flags, impact} = getMarkets();
  const labels = getValidation().filter(v => v.market === id && v.wallet_id === w.id);
  const conf = labels.some(l => l.confidence === 'charged') ? 'charged' : 'alleged';

  return <div className="mx-auto flex w-full max-w-(--container) flex-col gap-8 px-(--gutter-sm) py-6 sm:px-(--gutter)">
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem><BreadcrumbLink render={<Link href="/"/>}>Overview</BreadcrumbLink></BreadcrumbItem>
        <BreadcrumbSeparator/>
        <BreadcrumbItem><BreadcrumbLink render={<Link href={`/markets/${id}`}/>}>{m.short}</BreadcrumbLink></BreadcrumbItem>
        <BreadcrumbSeparator/>
        <BreadcrumbItem><BreadcrumbPage>{w.id}…</BreadcrumbPage></BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
    <PageHeader size="sm">
      <PageHeaderContent>
        <PageHeaderTitle>Alert for wallet <span className="font-mono">{w.id}…</span>{labels.length > 0 && <DocBadge confidence={conf}/>}</PageHeaderTitle>
        <PageHeaderDescription>{m.question}</PageHeaderDescription>
        <FlagChips fired={w.flags}/>
      </PageHeaderContent>
    </PageHeader>
    <AlertCard wallet={w} market={m} flags={flags} seeds={getAlerts(id)[w.id] ?? []} labels={labels} impact={impact}/>
  </div>;
}
