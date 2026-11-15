import {FLAGS, FLAG_SHORT} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

/** Wallet values as the six flags read them, with the frozen rule for each. */
export type FlagValues = {f1: number; f2share: number | null; f2markets: number | null; avg: number; usd: number; f5: number; hours: number | null};

export function flagValue(f: FlagId, v: FlagValues): string {
  switch (f) {
    case 'F1': return `${v.f1.toFixed(1)} d`;
    case 'F2': return v.f2share !== null ? `${Math.round(v.f2share * 100)}%` : `${v.f2markets ?? '?'} mkts`;
    case 'F3': return `${Math.round(v.avg * 100)}¢`;
    case 'F4': return v.usd >= 1000 ? `$${(v.usd / 1000).toFixed(1)}k` : `$${Math.round(v.usd)}`;
    case 'F5': return `${Math.round(v.f5 * 100)}%`;
    case 'F6': return v.hours === null ? 'n/a' : `${v.hours.toFixed(1)} h`;
  }
}

export const FLAG_RULE_SHORT: Record<FlagId, string> = {
  F1: 'account 7 days old or less',
  F2: '80% of its money here, or 2 markets ever',
  F3: 'average price 35¢ or less',
  F4: '$2,500 or more bought',
  F5: '80% or more in one direction',
  F6: 'median buy 72 h or less before the news',
};

/** Colour change with an optional per-flag delay (set --flag-delay on a parent); none under reduced motion. */
const T = 'transition-[background-color,border-color,color] duration-(--dur-wipe) delay-(--flag-delay) ease-out motion-reduce:transition-none';

/** One flag: a square mark (solid yellow when fired, outline when not) and its word. */
export function FlagMark({f, fired, value, size = 'sm'}: {f: FlagId; fired: boolean | null; value?: string; size?: 'sm' | 'lg'}) {
  const box = size === 'lg' ? 'size-3' : 'size-2';
  return <span className="inline-flex items-center gap-1.5">
    <span aria-hidden className={`${box} shrink-0 border ${T} ${fired ? 'border-accent-edge bg-accent-fill' : 'border-text-3 bg-transparent'}`}/>
    <span className={`${size === 'lg' ? 'type-label' : 'type-micro'} ${T} ${fired ? 'text-text-1' : 'text-text-3'}`}>{FLAG_SHORT[f]}</span>
    {value && <span className={`${size === 'lg' ? 'type-code' : 'type-code-sm'} ${T} ${fired ? 'text-accent-text' : 'text-text-3'}`}>{value}</span>}
  </span>;
}

/** All six marks in a fixed order; the accessible name lists what fired. */
export function FlagRow({fired, values, of = FLAGS}: {fired: FlagId[]; values?: FlagValues; of?: FlagId[]}) {
  const set = new Set(fired);
  return <span role="img" aria-label={fired.length ? `${fired.length} of ${of.length} signs: ${fired.map(f => FLAG_SHORT[f]).join(', ')}` : 'No signs'}
    className="inline-flex flex-wrap gap-x-3 gap-y-1">
    {of.map(f => <span key={f} aria-hidden><FlagMark f={f} fired={set.has(f)} value={values ? flagValue(f, values) : undefined}/></span>)}
  </span>;
}
