import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {Replay, type ReplayData} from '@/components/product/replay';
import {Watchlist} from '@/components/product/watchlist';
import {ScanBox} from '@/components/product/scan-box';
import {getValidation} from '@/lib/data';
import {FLAGS, FLAG_SHORT} from '@/lib/copy';

const REPO = 'https://github.com/ibrhmyi/insider';

function Section({id, title, children, className = ''}: {id: string; title?: string; children: React.ReactNode; className?: string}) {
  return <section aria-labelledby={title ? `${id}-title` : undefined} aria-label={title ? undefined : id} id={id}
    className={`flex flex-col gap-8 px-6 py-20 sm:px-12 lg:px-24 ${className}`}>
    {title && <h2 id={`${id}-title`} className="type-product-title max-w-(--title-ch)">{title}</h2>}
    {children}
  </section>;
}

export default function Home() {
  const replay: ReplayData = JSON.parse(readFileSync(join(process.cwd(), 'public', 'data', 'maduro_replay.json'), 'utf8'));
  const source = getValidation().find(v => v.label_id === 'MAD-CFTC-1')!.source;

  return <div className="bg-page text-text-1" style={{'--title-ch': '30ch'} as React.CSSProperties}>
    <section aria-labelledby="problem-title" className="flex min-h-[70svh] flex-col justify-center gap-6 px-6 py-20 sm:px-12 lg:px-24">
      <h1 id="problem-title" className="type-product-title max-w-(--title-ch)">Some Polymarket bets may be placed by people who already know the answer. Every trade is public, but nobody is watching.</h1>
      <p className="type-product max-w-measure text-text-2">
        In the days before Jan 3, 2026, a 5-day-old account bet $32,538 on Maduro&apos;s fall at 7¢. The CFTC later charged its alleged owner. Charged, not convicted.{' '}
        <a href={source} target="_blank" rel="noreferrer" className="text-text-1 underline underline-offset-4 focus-visible:focus-ring">Source</a>
      </p>
    </section>

    <Section id="idea" title="Score every wallet on six simple signs.">
      <ul className="flex flex-wrap gap-x-10 gap-y-4" aria-label="The six signs">
        {FLAGS.map(f => <li key={f} className="flex items-center gap-3"><span aria-hidden className="size-3 border border-text-2"/><span className="type-product text-text-1">{FLAG_SHORT[f]}</span></li>)}
      </ul>
      <p className="type-product max-w-measure text-text-2">Four or more: worth a look. Rules based on published research and fixed before testing.</p>
    </Section>

    <Section id="replay" title="Replay: Maduro market, Jan 1 to Jan 3, 2026." className="border-t border-line">
      <Replay d={replay}/>
    </Section>

    <Section id="watchlist" title="Open markets decided by small groups, scanned today." className="border-t border-line">
      <Watchlist/>
    </Section>

    <Section id="scan" title="Scan any market." className="border-t border-line">
      <ScanBox/>
    </Section>

    <footer className="flex flex-wrap items-baseline gap-x-8 gap-y-2 border-t border-line px-6 py-10 sm:px-12 lg:px-24">
      <p className="type-product text-text-2">Finds bets worth checking, not criminals. Also flags accounts nobody has accused. Tested on 3 past markets.</p>
      <a href={REPO} target="_blank" rel="noreferrer" className="type-product text-text-1 underline underline-offset-4 focus-visible:focus-ring">Code and data on GitHub</a>
    </footer>
  </div>;
}
