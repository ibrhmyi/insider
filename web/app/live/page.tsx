import type {Metadata} from 'next';
import {PageHeader, PageHeaderContent, PageHeaderDescription, PageHeaderTitle} from '@/components/quartz/ui/page-header';
import {LiveScan} from './live-scan';

export const metadata: Metadata = {title: 'Live scan'};

export default function LivePage() {
  return <div className="mx-auto flex w-full max-w-(--container) flex-col gap-8 px-(--gutter-sm) py-8 sm:px-(--gutter)">
    <PageHeader size="sm">
      <PageHeaderContent>
        <PageHeaderTitle>Live scan</PageHeaderTitle>
        <PageHeaderDescription>
          Score a market&apos;s largest recent buyers with the same frozen flags, F1 to F5. F6 compares a buy with the time of the first public news, which nobody knows while a market is open, so the live score is out of 5.
        </PageHeaderDescription>
      </PageHeaderContent>
    </PageHeader>
    <LiveScan/>
  </div>;
}
