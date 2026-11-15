'use client';

import {useEffect, useRef, useState, type ReactNode} from 'react';
import {InvestigationChart, type ChartBuy, type ChartState} from './chart';

export type Step = {id: string; title: string; body: ReactNode; state: ChartState};

/**
 * Sticky chart beside short text steps. The step nearest the middle of the screen sets the chart's state.
 * Step text is always visible (no scroll reveal); only the chart changes. The first step's state shows on load,
 * so the chart is never blank.
 */
export function Scrolly({steps, chart, aside, label}: {
  steps: Step[];
  chart: {price: [number, number][]; buys: ChartBuy[]; tNews: number; x0: number; x1: number; newsLabel: string; firstHighT?: number | null; firstHighLabel?: string; callout?: ReactNode; inset?: {price: [number, number][]; label: string}};
  aside?: (active: number) => ReactNode;
  label: string;
}) {
  const [active, setActive] = useState(0);
  const refs = useRef<(HTMLElement | null)[]>([]);
  useEffect(() => {
    // On wide screens the step at mid-screen is active; on phones the chart fills the top, so the zone sits low.
    const wide = window.matchMedia('(min-width: 1024px)').matches;
    const io = new IntersectionObserver(entries => {
      for (const e of entries) if (e.isIntersecting) setActive(Number((e.target as HTMLElement).dataset.index));
    }, {rootMargin: wide ? '-45% 0px -45% 0px' : '-70% 0px -12% 0px'});
    refs.current.forEach(el => el && io.observe(el));
    return () => io.disconnect();
  }, [steps.length]);
  const s = steps[active];

  return <div className="mx-auto grid w-full max-w-7xl gap-x-10 px-4 sm:px-6 lg:grid-cols-[minmax(0,4fr)_minmax(0,8fr)]">
    <div className="sticky top-(--head) z-[1] -mx-4 h-[58svh] border-b border-line bg-page px-4 py-3 sm:-mx-6 sm:px-6 lg:order-2 lg:mx-0 lg:h-[calc(100svh-var(--head))] lg:border-b-0 lg:px-0 lg:py-6">
      <div className="flex h-full flex-col gap-3">
        <InvestigationChart {...chart} state={s.state} label={`${label}. ${s.title}`} className="flex-1"/>
        {aside?.(active)}
      </div>
    </div>
    <ol className="relative flex flex-col lg:order-1">
      {steps.map((st, i) => <li key={st.id} id={st.id} data-index={i} ref={el => { refs.current[i] = el; }}
        className="flex min-h-[75svh] items-end pb-6 last:min-h-[90svh] lg:min-h-[85svh] lg:items-center lg:py-10 lg:first:pt-16">
        <article aria-current={i === active ? 'step' : undefined}
          className={`flex flex-col gap-3 border bg-panel p-5 ${i === active ? 'border-text-3' : 'border-line'}`}>
          <h2 className="type-heading-sm">{st.title}</h2>
          <div className="flex flex-col gap-2 type-body text-text-2">{st.body}</div>
        </article>
      </li>)}
    </ol>
  </div>;
}
