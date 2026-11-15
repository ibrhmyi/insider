/** Wallets by number of signs (log scale). Bars at or above the cut-off are flagged activity, so they take the yellow. */
export function ScoreBars({dist, cutoff, height = 220}: {dist: {score: number; wallets: number; documented: number}[]; cutoff: number; height?: number}) {
  const W = 560, H = height, pb = 28, pt = 22, bw = W / dist.length;
  const y = (n: number) => pt + (1 - Math.log10(Math.max(1, n)) / Math.log10(4000)) * (H - pt - pb);
  return <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" role="img"
    aria-label={`Wallets by number of signs, log scale: ${dist.map(d => `${d.score} signs ${d.wallets.toLocaleString('en-US')}`).join(', ')}. Flagged at ${cutoff} or more.`}>
    {[1, 10, 100, 1000].map(t => <line key={t} x1={0} x2={W} y1={y(t)} y2={y(t)} className="stroke-line" strokeWidth={1}/>)}
    {dist.map((d, i) => {
      const on = d.score >= cutoff;
      return <g key={d.score}>
        <rect x={i * bw + 6} y={y(d.wallets)} width={bw - 12} height={H - pb - y(d.wallets)}
          className={`transition-[fill] duration-(--dur-state) motion-reduce:transition-none ${on ? 'fill-accent-fill' : 'fill-well stroke-line'}`} strokeWidth={1}/>
        <text x={i * bw + bw / 2} y={y(d.wallets) - 6} textAnchor="middle" className={`type-micro ${on ? 'fill-text-1' : 'fill-text-3'}`}>{d.wallets.toLocaleString('en-US')}</text>
        <text x={i * bw + bw / 2} y={H - 8} textAnchor="middle" className="fill-text-3 type-micro">{d.score} signs</text>
      </g>;
    })}
  </svg>;
}
