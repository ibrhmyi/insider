import type {Market, MarketId} from '@/lib/types';

/** Neutral SVG charts for the paper, drawn on the server in the site's greys. */

const NAME: Record<MarketId, string> = {maduro: 'Maduro', nobel: 'Nobel', iran: 'Iran'};

/** One row per market: the permutation null as a grey histogram, the observed count as a white line. */
export function PermutationChart({markets}: {markets: Market[]}) {
  const W = 600, rowH = 96, top = 8, left = 74, right = W - 16;
  const all = markets.flatMap(m => [...m.permutation.hist.map(h => h[0]), m.permutation.observed]);
  const lo = Math.floor(Math.min(...all) / 10) * 10, hi = Math.ceil(Math.max(...all) / 10) * 10 + 5;
  const sx = (v: number) => left + ((v - lo) / (hi - lo)) * (right - left);
  const bw = Math.max(2, (right - left) / (hi - lo) - 1);
  const H = top + rowH * markets.length + 34;
  const ticks: number[] = [];
  for (let t = lo; t <= hi; t += 20) ticks.push(t);
  return <svg viewBox={`0 0 ${W} ${H}`} role="img" className="paper-svg"
    aria-label={`Timestamp permutation null for each market. ${markets.map(m => `${NAME[m.id]}: observed ${m.permutation.observed}, null mean ${m.permutation.null_mean.toFixed(1)}`).join('. ')}.`}>
    {ticks.map(t => <g key={t}>
      <line x1={sx(t)} x2={sx(t)} y1={top} y2={H - 30} className="svg-grid"/>
      <text x={sx(t)} y={H - 10} textAnchor="middle" className="svg-axis">{t}</text>
    </g>)}
    {markets.map((m, i) => {
      const y0 = top + i * rowH, base = y0 + rowH - 22;
      const maxC = Math.max(...m.permutation.hist.map(h => h[1]));
      const p = m.permutation;
      return <g key={m.id}>
        <text x={0} y={base - 26} className="svg-label">{NAME[m.id]}</text>
        <text x={0} y={base - 8} className="svg-axis">p = {p.p_value < 0.001 ? '< 0.001' : p.p_value.toFixed(3)}</text>
        {p.hist.map(([v, c]) => {
          const h = (c / maxC) * (rowH - 34);
          return <rect key={v} x={sx(v) - bw / 2} y={base - h} width={bw} height={h} className="svg-bar"/>;
        })}
        <line x1={left} x2={right} y1={base} y2={base} className="svg-base"/>
        <line x1={sx(p.observed)} x2={sx(p.observed)} y1={y0 + 4} y2={base} className="svg-observed"/>
        <text x={sx(p.observed) + 6} y={y0 + 14} className="svg-value">{p.observed}</text>
      </g>;
    })}
  </svg>;
}

/** Follow-on difference (A minus matched B) with 95% intervals, one row per scope. */
export function FollowChart({rows}: {rows: {label: string; diff: number; lo: number; hi: number; main?: boolean}[]}) {
  const W = 600, rowGap = 44, top = 20, left = 150, right = W - 16;
  const lo = Math.floor(Math.min(...rows.map(r => r.lo)) / 5) * 5, hi = Math.ceil(Math.max(...rows.map(r => r.hi)) / 5) * 5;
  const sx = (v: number) => left + ((v - lo) / (hi - lo)) * (right - left);
  const bottom = top + rowGap * (rows.length - 1) + 18;
  const H = bottom + 30;
  const ticks: number[] = [];
  for (let t = lo; t <= hi; t += 5) ticks.push(t);
  return <svg viewBox={`0 0 ${W} ${H}`} role="img" className="paper-svg"
    aria-label={`Extra follower wallets after flagged buys compared with matched ordinary buys, 30 minutes. ${rows.map(r => `${r.label}: ${r.diff.toFixed(1)}`).join(', ')}.`}>
    {ticks.map(t => <g key={t}>
      <line x1={sx(t)} x2={sx(t)} y1={top - 14} y2={bottom} className={t === 0 ? 'svg-zero' : 'svg-grid'}/>
      <text x={sx(t)} y={bottom + 22} textAnchor="middle" className="svg-axis">{t > 0 ? `+${t}` : t}</text>
    </g>)}
    {rows.map((r, i) => {
      const y = top + i * rowGap;
      return <g key={r.label}>
        <text x={0} y={y + 5} className={r.main ? 'svg-label is-main' : 'svg-label'}>{r.label}</text>
        <line x1={sx(r.lo)} x2={sx(r.hi)} y1={y} y2={y} className={r.main ? 'svg-ci is-main' : 'svg-ci'}/>
        <circle cx={sx(r.diff)} cy={y} r={r.main ? 6.5 : 5} className={r.main ? 'svg-dot is-main' : 'svg-dot'}/>
      </g>;
    })}
  </svg>;
}
