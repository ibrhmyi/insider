import type {Metadata} from 'next';
import {LiveScan} from '@/components/inv/live-scan';

export const metadata: Metadata = {title: 'Live scan'};

export default function LivePage() {
  return <div className="flex w-full flex-col gap-8 px-4 py-12 sm:px-6">
    <div className="flex flex-col gap-3">
      <h1 className="type-title max-w-3xl">Run the screen on a market that is still open.</h1>
      <p className="type-body max-w-measure text-text-2">The same frozen signs, scored on the largest recent buyers. Timing is left out because nobody knows when the news will break, so the score is out of 5.</p>
    </div>
    <LiveScan/>
  </div>;
}
