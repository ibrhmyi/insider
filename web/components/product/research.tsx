import {BEHAVIOURS, CASES, SRC, WHERE} from '@/lib/research';

const link = 'underline underline-offset-4 focus-visible:focus-ring';

export function Source({href, children = 'Source'}: {href: string; children?: React.ReactNode}) {
  return <a href={href} target="_blank" rel="noreferrer" className={`type-label-lg text-text-3 hover:text-text-1 ${link}`}>{children}</a>;
}

/** Who: the definition, then four cases as ruled rows. */
export function Who() {
  return <>
    <p className="type-product max-w-measure text-text-2">
      US regulators call it misappropriation: using confidential information, in breach of a duty of trust, to trade. <Source href={SRC.cftcAdvisory}>CFTC</Source>
    </p>
    <ul aria-label="Four cases" className="flex flex-col border-t border-line">
      {CASES.map(c => <li key={c.who} className="grid items-baseline gap-x-8 gap-y-1 border-b border-line py-4 md:grid-cols-[minmax(0,5fr)_minmax(0,5fr)_minmax(0,2fr)_minmax(0,5fr)_auto]">
        <span className="type-product text-text-1">{c.who}</span>
        <span className="type-product text-text-2">{c.secret}</span>
        <span className="type-product text-text-1">{c.made}</span>
        <span className="type-product text-text-2">{c.status}, {c.venue}</span>
        <Source href={c.source}/>
      </li>)}
    </ul>
    <p className="type-product text-text-3">Amounts are alleged profits. Charged or indicted is not convicted.</p>
  </>;
}

/** Where: share of long-shot bets that win, by market type. */
export function Where() {
  return <>
    <div role="img" aria-label={`Share of long-shot bets that won: ${WHERE.map(w => `${w.label} ${w.pct}%`).join(', ')}.`}
      className="type-product grid max-w-measure grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-8 gap-y-5">
      {WHERE.map(w => <div key={w.label} className="contents">
        <span className={`type-product ${w.lead ? 'text-text-1' : 'text-text-2'}`}>{w.label}</span>
        <span className="h-8 bg-well"><span className={`block h-full w-(--pct) ${w.lead ? 'bg-text-1' : 'bg-text-3'}`} style={{'--pct': `${w.pct}%`} as React.CSSProperties}/></span>
        <span className={`type-product-title text-end ${w.lead ? 'text-text-1' : 'text-text-2'}`}>{w.pct}%</span>
      </div>)}
    </div>
    <p className="type-product max-w-measure text-text-2">
      Share of long-shot bets that won. A long shot is $2,500 or more at 35¢ or less. Markets decided by the public, like elections, show the least. <Source href={SRC.acdcMarkets}>ACDC</Source>
    </p>
  </>;
}

/** How: six behaviours, one line of evidence each. */
export function How() {
  return <>
    <ul aria-label="Six behaviours" className="grid gap-x-12 border-t border-line md:grid-cols-2">
      {BEHAVIOURS.map(b => <li key={b.name} className="flex flex-col gap-1 border-b border-line py-5">
        <span className="type-product text-text-1">{b.name}</span>
        <span className="type-product text-text-2">{b.evidence}</span>
        <span className="flex flex-wrap gap-x-4"><Source href={b.source}>{b.by}</Source>{b.source2 && <Source href={b.source2}>{b.by2}</Source>}</span>
      </li>)}
    </ul>
    <p className="type-product max-w-measure text-text-2">
      Not every case fits. The Google engineer used an account opened in May 2024 and bet on 23 markets. <Source href={SRC.googleAccount}/>
    </p>
  </>;
}
