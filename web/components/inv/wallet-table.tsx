'use client';

import {useMemo, useState} from 'react';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/sodium/ui/table';
import {Tag} from '@/components/sodium/ui/tag';
import {Switch} from '@/components/sodium/ui/switch';
import {Tooltip, TooltipContent, TooltipTrigger} from '@/components/sodium/ui/tooltip';
import {FlagMark, FLAG_RULE_SHORT, flagValue, type FlagValues} from './flag-marks';
import {FLAGS, FLAG_SHORT, usd} from '@/lib/copy';
import type {FlagId} from '@/lib/types';

export type CaseWallet = FlagValues & {
  id: string; addr: string | null; rank: number; score: number; flags: FlagId[]; side: string; firstHigh: number | null;
  won: boolean; dormant: boolean | null;
  doc?: {handle: string | null; confidence: 'charged' | 'alleged'; publisher: string; source: string; claim: string};
};

/** Six marks with a hover tooltip each: the wallet's value against the frozen rule. One accessible name for the set. */
export function FlagMarksWithTips({w}: {w: CaseWallet}) {
  const fired = new Set(w.flags);
  return <span role="img" aria-label={`${w.score} of 6 signs: ${w.flags.map(f => `${FLAG_SHORT[f]} ${flagValue(f, w)}`).join(', ') || 'none'}`}
    className="inline-flex flex-nowrap gap-x-2.5 whitespace-nowrap">
    {FLAGS.map(f => <Tooltip key={f}>
      <TooltipTrigger render={<span aria-hidden/>}><FlagMark f={f} fired={fired.has(f)}/></TooltipTrigger>
      <TooltipContent>{`${FLAG_SHORT[f]}: ${flagValue(f, w)}. Rule: ${FLAG_RULE_SHORT[f]}.`}</TooltipContent>
    </Tooltip>)}
  </span>;
}

export function DocTag({doc}: {doc: NonNullable<CaseWallet['doc']>}) {
  return <span className="inline-flex flex-wrap items-center gap-2">
    <Tag size="sm" variant={doc.confidence === 'charged' ? 'neutral' : 'outline'}>{doc.confidence === 'charged' ? 'Charged' : 'Alleged'}</Tag>
    <a href={doc.source} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
      className="type-micro text-text-2 underline underline-offset-4 hover:text-text-1 focus-visible:focus-ring">
      {doc.confidence === 'charged' ? 'CFTC complaint' : doc.publisher.split(' (')[0].split(' via ')[0]}
    </a>
  </span>;
}

export function WalletTable({rows, flaggedMin, selected, onSelect, market}: {
  rows: CaseWallet[]; flaggedMin: number; selected?: string; onSelect: (id: string) => void; market: string;
}) {
  const [showSmall, setShowSmall] = useState(false);
  const small = rows.filter(r => r.usd < flaggedMin);
  const shown = useMemo(() => rows.filter(r => showSmall || r.usd >= flaggedMin), [rows, showSmall, flaggedMin]);

  return <div className="flex min-w-0 flex-col gap-3">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="type-body-sm text-text-2">Wallets with 4 or more signs that bought {usd(flaggedMin)} or more before the news, ranked by score, then by money. Hover a sign for its value.</p>
      <label className="flex items-center gap-2 type-label-sm text-text-2">
        <Switch checked={showSmall} onCheckedChange={setShowSmall}/>
        Show small wallets (under {usd(flaggedMin)}) <span className="type-code-sm text-text-3">{showSmall ? `${small.length} shown` : `+${small.length} hidden`}</span>
      </label>
    </div>
    <Table aria-label={`Flagged wallets, ${market}`} size="sm" stickyHeader maxHeight={520}>
      <TableHeader><TableRow>
        <TableHead numeric>Rank</TableHead><TableHead>Wallet</TableHead><TableHead>Signs</TableHead>
        <TableHead numeric>Bought</TableHead><TableHead numeric>Hours to news</TableHead>
      </TableRow></TableHeader>
      <TableBody>
        {shown.map(r => <TableRow key={r.id} selected={r.id === selected} tabIndex={0} aria-selected={r.id === selected}
          onClick={() => onSelect(r.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(r.id); } }}
          className="cursor-pointer focus-visible:focus-ring-inset">
          <TableCell numeric>{r.rank}</TableCell>
          <TableCell><span className="flex flex-wrap items-center gap-x-3 gap-y-1"><span className="type-code-sm">{r.id}…</span>{r.doc?.handle && <span className="type-body-sm text-text-2">{r.doc.handle}</span>}{r.doc && <DocTag doc={r.doc}/>}</span></TableCell>
          <TableCell><FlagMarksWithTips w={r}/></TableCell>
          <TableCell numeric className={r.usd >= flaggedMin ? '' : 'text-text-3'}>{usd(r.usd)}</TableCell>
          <TableCell numeric>{r.hours === null ? 'n/a' : r.hours.toFixed(1)}</TableCell>
        </TableRow>)}
      </TableBody>
    </Table>
  </div>;
}
