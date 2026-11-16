'use client';

import {useEffect, useRef, useState, type ReactNode} from 'react';
import {StoryChart, type StoryChartData} from './story-chart';
import {TryIt} from './try-it';
import {DISCLAIMER, NOT_PROOF} from '@/lib/copy';

export type StoryData = {
  chart: StoryChartData;
  signs: {word: string; value: string}[];
  source: string;
  rank: number; n: number; hoursEarly: number; named: number; namedTotal: number; othersFlagged: number;
  repo: string;
};

/** A full-screen step: lots of empty space, content left-aligned, never hidden on scroll. */
function Screen({id, children, className = ''}: {id?: string; children: ReactNode; className?: string}) {
  return <section id={id} className={`flex min-h-svh flex-col justify-center gap-8 px-6 py-24 sm:px-12 lg:px-24 ${className}`}>{children}</section>;
}

/** Wide screen with motion allowed: sticky chart driven by scroll. Otherwise: steps stacked, chart in its end state. */
function useScrolly() {
  const [on, set] = useState(true);
  useEffect(() => {
    const wide = window.matchMedia('(min-width: 1024px)'), calm = window.matchMedia('(prefers-reduced-motion: reduce)');
    const upd = () => set(wide.matches && !calm.matches);
    upd(); wide.addEventListener('change', upd); calm.addEventListener('change', upd);
    return () => { wide.removeEventListener('change', upd); calm.removeEventListener('change', upd); };
  }, []);
  return on;
}

function Signs({signs, lit}: {signs: StoryData['signs']; lit: boolean}) {
  return <ul className="flex flex-col gap-4" aria-label="Six signs, all present for this wallet">
    {signs.map((s, i) => <li key={s.word} className="flex items-baseline gap-4" style={{'--sign-delay': lit ? `${i * 280}ms` : '0ms'} as React.CSSProperties}>
      <span aria-hidden className={`size-5 shrink-0 translate-y-0.5 border-2 transition-colors delay-(--sign-delay) duration-(--dur-wipe) motion-reduce:transition-none ${lit ? 'border-accent-edge bg-accent-fill' : 'border-text-3'}`}/>
      <span className={`type-story-sign transition-colors delay-(--sign-delay) duration-(--dur-wipe) motion-reduce:transition-none ${lit ? 'text-text-1' : 'text-text-3'}`}>{s.word}</span>
      <span className={`type-story-sign transition-colors delay-(--sign-delay) duration-(--dur-wipe) motion-reduce:transition-none ${lit ? 'text-accent-text' : 'text-text-3'}`}>{s.value}</span>
    </li>)}
  </ul>;
}

const RULES_LINE = 'Rules based on published research, and fixed before I looked at any result.';

export function Story({d}: {d: StoryData}) {
  const scrolly = useScrolly();
  const [stage, setStage] = useState(0);
  const refs = useRef<(HTMLElement | null)[]>([]);
  useEffect(() => {
    if (!scrolly) return;
    const io = new IntersectionObserver(es => { for (const e of es) if (e.isIntersecting) setStage(Number((e.target as HTMLElement).dataset.stage)); }, {rootMargin: '-45% 0px -45% 0px'});
    refs.current.forEach(el => el && io.observe(el));
    return () => io.disconnect();
  }, [scrolly]);

  const captions: ReactNode[] = [
    <>For two days the market priced Maduro&apos;s fall at about <span className="text-text-1">7¢</span>. Almost nobody believed it.</>,
    <>One wallet bought <span className="text-accent-text">$32,538</span> of &ldquo;Yes&rdquo;, at about 7¢. Grey dots are everyone else.</>,
    <>06:00 UTC, January 3: first reports of explosions in Caracas.</>,
    <>The price jumps to 100¢. Each 7¢ share now pays $1.</>,
  ];

  return <div className="bg-page text-text-1" style={{'--title-ch': '20ch', '--prose-ch': '40ch'} as React.CSSProperties}>
    <Screen>
      <h1 className="type-story-title max-w-(--title-ch)">A wallet bet <span className="text-accent-text">$32,538</span> that Maduro would fall. Hours later, he did.</h1>
      <p className="type-story max-w-3xl text-text-2">In April 2026 the CFTC charged its alleged owner, a US soldier. Charged, not convicted. <a href={d.source} target="_blank" rel="noreferrer" className="text-text-1 underline underline-offset-4 focus-visible:focus-ring">Source</a></p>
    </Screen>

    <Screen><h2 className="type-story-title max-w-(--title-ch)">Could you have spotted this wallet from public data alone?</h2></Screen>

    {scrolly
      ? <div className="grid grid-cols-[minmax(0,5fr)_minmax(0,8fr)] gap-12 px-24">
        <ol className="flex flex-col">
          {captions.map((c, i) => <li key={i} data-stage={i} ref={el => { refs.current[i] = el; }} className="flex min-h-svh items-center">
            <p className="type-story max-w-xl text-text-2">{c}</p>
          </li>)}
          <li data-stage={4} ref={el => { refs.current[4] = el; }} className="flex min-h-svh flex-col justify-center gap-6 py-12">
            <h2 className="type-story text-text-2">Six signs. This wallet shows all of them.</h2>
            <Signs signs={d.signs} lit={stage >= 4}/>
            <p className="type-story max-w-xl text-text-2">{RULES_LINE}</p>
          </li>
        </ol>
        <div className="sticky top-0 flex h-svh flex-col justify-center gap-4 py-16">
          <div className="min-h-0 flex-1"><StoryChart d={d.chart} stage={Math.min(stage, 3)}/></div>
          <p className="type-story text-text-3">{DISCLAIMER}</p>
        </div>
      </div>
      : <Screen>
        <div className="h-[60svh] min-h-80"><StoryChart d={d.chart} stage={3} still/></div>
        <div className="flex flex-col gap-6">{captions.map((c, i) => <p key={i} className="type-story text-text-2">{c}</p>)}</div>
        <h2 className="type-story text-text-2">Six signs. This wallet shows all of them.</h2>
        <Signs signs={d.signs} lit/>
        <p className="type-story text-text-2">{RULES_LINE}</p>
        <p className="type-story text-text-3">{DISCLAIMER}</p>
      </Screen>}

    <Screen>
      <h2 className="sr-only">Result</h2>
      <dl className="flex flex-col gap-10">
        {[[`#${d.rank}`, `of ${d.n.toLocaleString('en-US')} wallets`], [`${d.hoursEarly} h`, 'early'], [`${d.named} of ${d.namedTotal}`, 'publicly named wallets flagged']].map(([num, label]) =>
          <div key={label} className="flex flex-wrap items-baseline gap-x-8 gap-y-2"><dt className="sr-only">{label}</dt>
            <dd className="type-story-number">{num}</dd><dd className="type-story-sign text-text-2">{label}</dd></div>)}
      </dl>
    </Screen>

    <Screen>
      <h2 className="type-story-title max-w-(--title-ch)">The catch</h2>
      <p className="type-story-sign max-w-(--prose-ch) text-text-2">It also flags {d.othersFlagged} other wallets nobody has accused. Journalists found the named ones with similar signs. So this finds bets worth a second look — not criminals.</p>
    </Screen>

    <Screen id="try">
      <h2 className="type-story-title max-w-(--title-ch)">Try it on a market that is still open.</h2>
      <TryIt/>
      <p className="type-story text-text-2">{NOT_PROOF}</p>
    </Screen>

    <footer className="flex flex-wrap gap-x-10 gap-y-3 border-t border-line px-6 py-10 sm:px-12 lg:px-24">
      <a href={d.repo} target="_blank" rel="noreferrer" className="type-story text-text-1 underline underline-offset-4 focus-visible:focus-ring">Code and data on GitHub</a>
      <span className="type-story text-text-2">Method and limits in the written report.</span>
    </footer>
  </div>;
}
