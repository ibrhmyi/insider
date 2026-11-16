/** Shuffle test: wallets flagged in each of 1,000 random-timing runs, with the real count marked. Neutral bars; the observed line is text-1. */
export function NullHist({hist, observed, title, verdict}: {hist: [number, number][]; observed: number; title: string; verdict: string}) {
  const lo = Math.min(hist[0][0], observed) - 2, hi = Math.max(hist[hist.length - 1][0], observed) + 2;
  const max = Math.max(...hist.map(h => h[1]));
  const W = 320, H = 140, pb = 20, pt = 22;
  const x = (v: number) => ((v - lo) / (hi - lo)) * W, bw = Math.max(1, W / (hi - lo + 1) - 1);
  const ox = x(observed), right = ox > W * 0.6;
  return <figure className="flex flex-col gap-2">
    <figcaption className="type-label">{title}</figcaption>
    <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full overflow-visible" role="img"
      aria-label={`${title}: random timing gives ${hist[0][0]} to ${hist[hist.length - 1][0]} flagged wallets; observed ${observed}.`}>
      <line x1={0} x2={W} y1={H - pb} y2={H - pb} className="stroke-line" strokeWidth={1}/>
      {hist.map(([v, n]) => <rect key={v} x={x(v) - bw / 2} y={H - pb - (n / max) * (H - pb - pt)} width={bw} height={(n / max) * (H - pb - pt)} className="fill-text-3"/>)}
      <line x1={ox} x2={ox} y1={pt - 6} y2={H - pb} className="stroke-text-1" strokeWidth={2}/>
      <text x={right ? ox - 6 : ox + 6} y={pt - 8} textAnchor={right ? 'end' : 'start'} className="fill-text-1 type-micro">Observed {observed}</text>
      {[lo + 2, Math.round((lo + hi) / 2), hi - 2].map(v => <text key={v} x={x(v)} y={H - 4} textAnchor="middle" className="fill-text-3 type-micro">{v}</text>)}
    </svg>
    <p className="type-body-sm text-text-2">{verdict}</p>
  </figure>;
}
