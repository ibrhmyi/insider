import {Badge} from '@/components/quartz/ui/badge';
import {FLAGS, FLAG_NAMES} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

/** All six flag slots in a fixed order so columns line up; fired flags read as a framed tag, others are dimmed. */
export function FlagChips({fired, only = false, of = FLAGS}: {fired: FlagId[]; only?: boolean; of?: FlagId[]}) {
  const set = new Set(fired);
  const shown = only ? of.filter(f => set.has(f)) : of;
  return <span className="inline-flex flex-wrap gap-1" aria-label={fired.length ? `Flags fired: ${fired.map(f => `${f} ${FLAG_NAMES[f]}`).join(', ')}` : 'No flags fired'} role="img">
    {shown.map(f => set.has(f)
      ? <Badge key={f} variant="outline" title={FLAG_NAMES[f]} aria-hidden>{f}</Badge>
      : <Badge key={f} variant="ghost" className="text-text-disabled" title={`${FLAG_NAMES[f]}: not fired`} aria-hidden>{f}</Badge>)}
  </span>;
}

export function DocBadge({confidence}: {confidence: 'charged' | 'alleged'}) {
  return <Badge kind="model" label={confidence === 'charged' ? 'Charged' : 'Alleged'}/>;
}
