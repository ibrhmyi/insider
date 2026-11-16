/** Whole-market Yes price as a small step line, with the first-news time marked. Neutral only. */
export function Sparkline({price, tNews, label}: {price: [number, number][]; tNews: number; label: string}) {
  const W = 300, H = 72, a = price[0][0], b = price[price.length - 1][0];
  const x = (t: number) => ((t - a) / (b - a)) * W, y = (p: number) => 4 + (1 - Math.sqrt(p)) * (H - 8);
  let d = `M${x(price[0][0]).toFixed(1)},${y(price[0][1]).toFixed(1)}`;
  for (const [t, p] of price.slice(1)) d += `H${x(t).toFixed(1)}V${y(p).toFixed(1)}`;
  return <svg viewBox={`0 0 ${W} ${H}`} className="block h-18 w-full" role="img" aria-label={label} preserveAspectRatio="none">
    <line x1={x(tNews)} x2={x(tNews)} y1={0} y2={H} className="stroke-text-3" strokeWidth={1} strokeDasharray="2 3" vectorEffect="non-scaling-stroke"/>
    <path d={d} className="fill-none stroke-text-1" strokeWidth={1.25} vectorEffect="non-scaling-stroke"/>
  </svg>;
}
