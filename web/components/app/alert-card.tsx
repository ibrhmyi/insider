import {Alert, AlertDescription, AlertTitle} from '@/components/quartz/ui/alert';
import {Badge} from '@/components/quartz/ui/badge';
import {DataList, DataListItem, DataListLabel, DataListValue} from '@/components/quartz/ui/data-list';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/quartz/ui/table';
import {CopyButton} from '@/components/quartz/ui/copy-button';
import {DocBadge} from './flag-chips';
import {DISCLAIMER, FLAGS, FLAG_NAMES, FLAG_RULE, hours, usd, utc} from '@/lib/copy';
import type {FlagId, Market, MarketsFile, Seed, Thresholds, Validation, WalletRow} from '@/lib/types';

export type AlertCardProps = {
  wallet: WalletRow;
  market: Market;
  flags: Thresholds;
  seeds: Seed[];
  labels: Validation[];
  impact: MarketsFile['impact'];
  compact?: boolean;
};

function value(f: FlagId, w: WalletRow): string {
  switch (f) {
    case 'F1': return `${w.f1_days.toFixed(1)} days${w.acct_src === 'join_date' ? '' : ' (account start estimated)'}`;
    case 'F2': return [w.f2_share !== null ? `${Math.round(w.f2_share * 100)}% of its volume` : 'share unknown', w.f2_markets !== null ? `${w.f2_markets} markets lifetime` : null].filter(Boolean).join(', ');
    case 'F3': return w.avg_price.toFixed(3);
    case 'F4': return usd(w.usd);
    case 'F5': return `${Math.round(w.f5 * 100)}% one direction`;
    case 'F6': return hours(w.hours);
  }
}

const vs = (s?: Seed) => !s ? 'Overlaps the news' : s.n_B === 0 || s.B_wallets === null ? `${s.A_wallets} vs no match` : `${s.A_wallets} vs ${s.B_wallets.toFixed(1)} (${s.n_B})`;
const n2 = (v: number | null | undefined, d = 4) => (v === null || v === undefined ? 'Not measured' : v.toFixed(d));

function Section({title, id, children, description}: {title: string; id: string; description?: React.ReactNode; children: React.ReactNode}) {
  return <section aria-labelledby={id} className="flex min-w-0 flex-col gap-3">
    <div className="flex flex-col gap-1">
      <h2 id={id} className="type-heading-sm">{title}</h2>
      {description && <p className="type-body-sm text-text-2 max-w-(--measure)">{description}</p>}
    </div>
    {children}
  </section>;
}

export function AlertCard({wallet: w, market: m, flags: th, seeds, labels, impact, compact = false}: AlertCardProps) {
  const fired = new Set(w.flags);
  const byT = new Map<number, {t: number; usd: number; s30?: Seed; s120?: Seed}>();
  for (const s of seeds) {
    const b = byT.get(s.t) ?? {t: s.t, usd: s.usd};
    if (s.H === 30) b.s30 = s; else b.s120 = s;
    byT.set(s.t, b);
  }
  const buys = [...byT.values()].sort((a, b) => a.t - b.t);
  const doc = labels.length > 0;
  const conf = labels.some(l => l.confidence === 'charged') ? 'charged' : 'alleged';
  const imp = impact.impact_60m_per_1k;
  const k = `alert-${w.id}`;

  return <div className="flex flex-col gap-8">
    <Alert>
      <AlertTitle>Score {w.score} of 6 in {m.short}, rank {w.rank} of {m.n_wallets.toLocaleString('en-US')}</AlertTitle>
      <AlertDescription>{DISCLAIMER}</AlertDescription>
    </Alert>

    <div className="grid gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <div className="flex min-w-0 flex-col gap-8">
        <Section id={`${k}-flags`} title="Flags, value against the frozen threshold" description={w.first_high_h !== null ? `Recomputed with only its own fills so far, this wallet first reached 4 flags ${hours(w.first_high_h)} before the first news. That figure is retrospective: F6 needs the news time.` : undefined}>
          <Table aria-label="Flags with this wallet's values and thresholds" size="sm">
            <TableHeader><TableRow><TableHead>Flag and frozen rule</TableHead><TableHead>This wallet</TableHead><TableHead className="text-end">Fired</TableHead></TableRow></TableHeader>
            <TableBody>{FLAGS.map(f => <TableRow key={f}>
              <TableCell className="whitespace-normal"><span className="flex flex-col gap-0.5"><span><span className="type-label">{f}</span> {FLAG_NAMES[f]}</span><span className="type-body-sm text-text-2">{FLAG_RULE[f]}</span></span></TableCell>
              <TableCell className="data whitespace-normal">{value(f, w)}</TableCell>
              <TableCell className="text-end">{fired.has(f) ? <Badge variant="outline">Fired</Badge> : <span className="text-text-3">No</span>}</TableCell>
            </TableRow>)}</TableBody>
          </Table>
          <p className="type-body-sm text-text-2">High score means {th.HIGH} or more of 6. Thresholds were committed to git before any v1 feature was computed.</p>
        </Section>

        {!compact && <Section id={`${k}-follow`} title="Did others follow its buys?" description="Distinct taker wallets buying the same direction after each of its buys, against size- and time-matched buys by established wallets in the same market (Layer 2).">
          {seeds.length === 0
            ? <p className="type-body text-text-2">No usable buy: every window overlapped the news, or no matched buy existed.</p>
            : <><Table aria-label="Followers after this wallet's buys versus matched buys" size="sm">
              <TableHeader><TableRow>
                <TableHead>Buy (UTC)</TableHead><TableHead className="text-end">USD</TableHead>
                <TableHead className="text-end">Followers, 30 min</TableHead><TableHead className="text-end">Followers, 120 min</TableHead>
              </TableRow></TableHeader>
              <TableBody>{buys.map(b => <TableRow key={b.t}>
                <TableCell className="data">{utc(b.t)}</TableCell><TableCell className="text-end data">{usd(b.usd)}</TableCell>
                <TableCell className="text-end data">{vs(b.s30)}</TableCell><TableCell className="text-end data">{vs(b.s120)}</TableCell>
              </TableRow>)}</TableBody>
            </Table>
            <p className="type-body-sm text-text-2">Each cell: followers after its buy, then the mean for matched buys by established wallets (n matched). No match means no comparable buy within 30% in size and 6 hours; those were left out of the test.</p></>}
          <p className="type-body-sm text-text-2">Across all markets, high-score buys drew fewer followers than matched buys (30 min: 1.9 fewer, n = 273). Nobel is the exception.</p>
        </Section>}

        {!compact && <Section id={`${k}-impact`} title="Price impact per $1,000" description="Change in the YES price after its taker buys, toward the side it bought; the last fill stands in for the mid-price.">
          <DataList size="sm">
            <DataListItem><DataListLabel>This wallet, 5 min</DataListLabel><DataListValue numeric>{n2(w.imp5)}</DataListValue></DataListItem>
            <DataListItem><DataListLabel>This wallet, 60 min</DataListLabel><DataListValue numeric>{n2(w.imp60)}</DataListValue></DataListItem>
            <DataListItem><DataListLabel>All high-score wallets, 60 min median</DataListLabel><DataListValue numeric>{imp.high_median.toFixed(4)} (n = {imp.high_n})</DataListValue></DataListItem>
            <DataListItem><DataListLabel>Other wallets of $2,500 or more, 60 min median</DataListLabel><DataListValue numeric>{imp.other_ge2500_median.toFixed(4)} (n = {imp.other_ge2500_n}, p = {imp.p_mwu_vs_ge2500.toFixed(2)})</DataListValue></DataListItem>
          </DataList>
          <p className="type-body-sm text-text-2">No significant difference from similarly sized wallets.</p>
        </Section>}
      </div>

      <div className="flex min-w-0 flex-col gap-8">
        <Section id={`${k}-wallet`} title="Wallet">
          <DataList size="sm">
            <DataListItem><DataListLabel>Address</DataListLabel><DataListValue mono>
              {w.addr ? <span className="flex min-w-0 items-center gap-1"><span className="break-all">{w.addr}</span><CopyButton value={w.addr} label="Copy address" size="icon-xs"/></span> : `${w.id}…`}
            </DataListValue></DataListItem>
            {w.handle && <DataListItem><DataListLabel>Reported handle</DataListLabel><DataListValue>{w.handle}</DataListValue></DataListItem>}
            <DataListItem><DataListLabel>Main side bought</DataListLabel><DataListValue>{w.side}</DataListValue></DataListItem>
            <DataListItem><DataListLabel>Buys before the news</DataListLabel><DataListValue numeric>{w.n_buys}</DataListValue></DataListItem>
            <DataListItem><DataListLabel>First fill in this market</DataListLabel><DataListValue numeric>{w.first_fill.replace('T', ' ').replace('Z', ' UTC').slice(0, 20)}</DataListValue></DataListItem>
          </DataList>
          {!w.addr && <p className="type-body-sm text-text-2">Only a prefix is shown: this wallet is not named in public reporting.</p>}
        </Section>

        <Section id={`${k}-news`} title="News context">
          <ol className="flex flex-col gap-3">
            {m.news_events.map(e => <li key={e.epoch} className="flex flex-col gap-0.5">
              <span className="type-label data">{utc(e.epoch)}</span>
              <span className="type-body-sm text-text-2">{e.description}</span>
              <a href={e.source.split(' ')[0]} target="_blank" rel="noreferrer" className="type-body-sm underline underline-offset-4 w-fit">Source: {new URL(e.source.split(' ')[0]).hostname.replace('www.', '')}</a>
            </li>)}
          </ol>
          <p className="type-body-sm text-text-2">Its USD-weighted median buy came {hours(w.hours)} before the first news.</p>
        </Section>

        <Section id={`${k}-record`} title="Public record">
          {doc ? <div className="flex flex-col gap-4">
            <span className="flex items-center gap-2"><DocBadge confidence={conf}/><span className="type-body-sm text-text-2">{conf === 'charged' ? 'Charged, not adjudicated' : 'Alleged in reporting'}</span></span>
            {labels.map(l => <div key={l.label_id} className="flex flex-col gap-1">
              <p className="type-body-sm">{l.claim}</p>
              <p className="type-body-sm text-text-2">Reported amount: {l.amount}. Matched by {l.identifier_type === 'handle' ? `handle "${l.identifier}"` : `address prefix ${l.identifier}`}.</p>
              <a href={l.source} target="_blank" rel="noreferrer" className="type-body-sm underline underline-offset-4 w-fit">{l.publisher}, {l.date}</a>
            </div>)}
          </div> : <p className="type-body text-text-2">No public reporting names this wallet. It appears here only because the frozen screen scored it {th.HIGH} or more; that is a reason to look, not a finding.</p>}
        </Section>

        <section aria-labelledby={`${k}-post`} className="flex flex-col gap-3 bg-well rounded-xl p-4">
          <div className="flex flex-col gap-1">
            <h2 id={`${k}-post`} className="type-heading-sm">After the fact, never in the score</h2>
            <p className="type-body-sm text-text-2">Measured after resolution, so a live screen could not have seen them. Shown only to judge the screen.</p>
          </div>
          <DataList size="sm">
            <DataListItem><DataListLabel>F7 Main side won</DataListLabel><DataListValue>{w.post.f7_won ? 'Yes' : 'No'}</DataListValue></DataListItem>
            <DataListItem><DataListLabel>F8 Dormant for 30 days after</DataListLabel><DataListValue>{w.post.f8_dormant === null ? 'Unknown' : w.post.f8_dormant ? 'Yes' : `No, ${w.post.f8_trades_30d} trades`}</DataListValue></DataListItem>
            <DataListItem><DataListLabel>Score with F4 at $1,000 / $2,500 / $10,000</DataListLabel><DataListValue numeric>{w.sens['1000']} / {w.sens['2500']} / {w.sens['10000']}</DataListValue></DataListItem>
          </DataList>
          <p className="type-body-sm text-text-2">All three markets resolved toward the long-time longshot, so winning says little here.</p>
        </section>
      </div>
    </div>
  </div>;
}
