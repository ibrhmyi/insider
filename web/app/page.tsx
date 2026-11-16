import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {Replay, type ReplayData} from '@/components/product/replay';
import {Watchlist} from '@/components/product/watchlist';
import {ScanBox} from '@/components/product/scan-box';
import {getValidation, getWallets, getMarket} from '@/lib/data';
import {FLAGS, FLAG_PLAIN, FLAG_SHORT, usd} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

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
  const charged = getValidation().find(v => v.label_id === 'MAD-CFTC-1')!;
  const source = charged.source;
  const w = getWallets('maduro').find(x => x.id === charged.wallet_id)!;
  const nMaduro = getMarket('maduro')!.n_wallets;
  const value: Record<FlagId, string> = {
    F1: `${w.f1_days.toFixed(1)} days`, F2: `${Math.round((w.f2_share ?? 0) * 100)}%`, F3: `${Math.round(w.avg_price * 100)}¢`,
    F4: usd(w.usd), F5: `${Math.round(w.f5 * 100)}%`, F6: `${w.hours.toFixed(1)} h`,
  };

  return <div className="bg-page text-text-1" style={{'--title-ch': '30ch'} as React.CSSProperties}>
    <section aria-labelledby="problem-title" className="flex min-h-[70svh] flex-col justify-center gap-6 px-6 py-20 sm:px-12 lg:px-24">
      <h1 id="problem-title" className="type-product-title max-w-(--title-ch)">Some Polymarket bets may be placed by people who already know the answer. Every trade is public.</h1>
      <p className="type-product max-w-measure text-text-2">
        In the days before Jan 3, 2026, a 5-day-old account bet $32,538 on Maduro&apos;s fall at 7¢. The CFTC later charged its alleged owner. Charged, not convicted.{' '}
        <a href={source} target="_blank" rel="noreferrer" className="text-text-1 underline underline-offset-4 focus-visible:focus-ring">Source</a>
      </p>
    </section>

    <Section id="idea" title="Score every wallet on six simple signs.">
      <ul className="grid gap-x-12 gap-y-6 md:grid-cols-2 xl:grid-cols-3" aria-label="The six signs">
        {FLAGS.map(f => <li key={f} className="flex flex-col gap-1">
          <span className="type-product text-text-1">{FLAG_SHORT[f]}</span>
          <span className="type-product text-text-2">{FLAG_PLAIN[f]}</span>
        </li>)}
      </ul>
      <p className="type-product max-w-measure text-text-1">Count the yeses. Four or more: worth a look. Rules based on published research and fixed before testing.</p>
      <div className="flex flex-col gap-4 border-t border-line pt-6">
        <h3 className="type-product text-text-2">Example: the Maduro wallet later charged by the CFTC</h3>
        <ul className="flex flex-wrap gap-x-8 gap-y-3" aria-label="Its six signs">
          {FLAGS.map(f => <li key={f} className="flex items-baseline gap-2">
            <span className="type-product text-text-1" aria-label={w.flags.includes(f) ? 'yes' : 'no'}>{w.flags.includes(f) ? '\u2713' : '\u2717'}</span>
            <span className="type-product text-text-1">{FLAG_SHORT[f]}</span>
            <span className="type-product text-text-2">{value[f]}</span>
          </li>)}
        </ul>
        <p className="type-product text-text-1">{w.score} of 6. Ranked 1st of {nMaduro.toLocaleString('en-US')} wallets.</p>
      </div>
      <p className="type-product max-w-measure text-text-2">While a market is still open, nobody knows when the news will come, so close to the news cannot be checked. Live scans use the other 5: 4 or more of those 5 is worth a look.</p>
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
