import Link from 'next/link';
import {PageHeader, PageHeaderContent, PageHeaderDescription, PageHeaderStat, PageHeaderStats, PageHeaderTitle} from '@/components/quartz/ui/page-header';
import {Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle} from '@/components/quartz/ui/card';
import {DataList, DataListItem, DataListLabel, DataListValue} from '@/components/quartz/ui/data-list';
import {Button} from '@/components/quartz/ui/button';
import {Badge} from '@/components/quartz/ui/badge';
import {getMarkets, MARKET_IDS} from '@/lib/data';
import {NOT_PROOF, compactUsd, utc} from '@/lib/copy';

export default function Overview() {
  const {headline: h, markets} = getMarkets();
  const ordered = MARKET_IDS.map(id => markets.find(m => m.id === id)!);
  return <div className="mx-auto flex w-full max-w-(--container) flex-col gap-10 px-(--gutter-sm) py-8 sm:px-(--gutter)">
    <PageHeader>
      <PageHeaderContent>
        <PageHeaderTitle>A screen frozen before any result ranks the CFTC-charged Maduro wallet first of {h.n_in_market.toLocaleString('en-US')}, flagged {h.hours_before} hours before the news</PageHeaderTitle>
        <PageHeaderDescription>
          Six flags from the research literature, frozen in git before any result existed, score every wallet that bought before the first public news in three Polymarket markets.
          The wallet named in the CFTC complaint over the Maduro market ranks first of {h.n_in_market.toLocaleString('en-US')}.
        </PageHeaderDescription>
      </PageHeaderContent>
      <PageHeaderStats aria-label="Headline results">
        <PageHeaderStat label="CFTC-charged wallet, Maduro market" value={`Rank ${h.rank}`} detail={`of ${h.n_in_market.toLocaleString('en-US')}`}/>
        <PageHeaderStat label="Score reached 4 of 6" value={`${h.hours_before} h`} detail="before the news"/>
        <PageHeaderStat label="Wallets named in public reporting" value={`${h.documented_flagged}/${h.documented_total}`} detail="flagged"/>
      </PageHeaderStats>
      <p className="type-body text-text-1">{NOT_PROOF}</p>
    </PageHeader>

    <section aria-labelledby="markets-heading" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 id="markets-heading" className="type-heading">Three markets</h2>
        <p className="type-body text-text-2 max-w-(--measure)">Each resolved on a decision a small group knew before the public. n is every wallet that bought before the news.</p>
      </div>
      <ul className="grid gap-4 md:grid-cols-3">
        {ordered.map(m => <li key={m.id} className="flex">
          <Card className="w-full">
            <CardHeader>
              <CardTitle className="type-heading-xs">{m.short}</CardTitle>
              <CardDescription>{m.question}</CardDescription>
            </CardHeader>
            <CardContent>
              <DataList size="sm">
                <DataListItem><DataListLabel>First news</DataListLabel><DataListValue numeric>{utc(m.t_news)}</DataListValue></DataListItem>
                <DataListItem><DataListLabel>Wallets scored</DataListLabel><DataListValue numeric>{m.n_wallets.toLocaleString('en-US')}</DataListValue></DataListItem>
                <DataListItem><DataListLabel>Score 4 or more</DataListLabel><DataListValue numeric>{m.n_high}</DataListValue></DataListItem>
                <DataListItem><DataListLabel>Beats random timing</DataListLabel><DataListValue>
                  {m.permutation.p_value < 0.05 ? <Badge kind="model" label={`Yes, p = ${m.permutation.p_value.toFixed(3)}`}/> : <span className="data">No, p = {m.permutation.p_value.toFixed(2)}</span>}
                </DataListValue></DataListItem>
                <DataListItem><DataListLabel>Documented wallets</DataListLabel><DataListValue numeric>{m.n_documented}</DataListValue></DataListItem>
                <DataListItem><DataListLabel>Volume</DataListLabel><DataListValue numeric>{compactUsd(m.volume_usd)}</DataListValue></DataListItem>
              </DataList>
            </CardContent>
            <CardFooter>
              <Button variant="secondary" size="sm" nativeButton={false} render={<Link href={`/markets/${m.id}`}/>}>Open {m.short} market</Button>
            </CardFooter>
          </Card>
        </li>)}
      </ul>
    </section>

    <section aria-labelledby="caveat-heading" className="flex flex-col gap-2 max-w-(--measure)">
      <h2 id="caveat-heading" className="type-heading-sm">What this is not</h2>
      <p className="type-body text-text-2">
        A pilot on 3 markets, not a validated model. The documented wallets were found by journalists using similar cues, so catching them is partly by construction.
        Of the {h.n_high_total} wallet-markets that score 4 or more, {h.n_high_under_1k} bought under $1,000, and how many are truly informed is unknown.
        Read the <Link href="/method" className="underline underline-offset-4">method and its limits</Link>.
      </p>
    </section>
  </div>;
}
