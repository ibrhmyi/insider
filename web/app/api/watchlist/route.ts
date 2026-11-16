/**
 * Watchlist: the fixed list of open markets in lib/watchlist.ts, each scanned with the live scan (lib/scan.ts).
 * The response is cached and regenerated at most every 6 hours (Next.js incremental regeneration), so the page
 * loads fast and the scans refresh on their own. A committed snapshot (public/data/watchlist.json) is the fallback.
 */
import {NextResponse} from 'next/server';
import {scan} from '@/lib/scan';
import {WATCHLIST} from '@/lib/watchlist';

export const dynamic = 'force-static';
export const revalidate = 21600;
export const maxDuration = 60;

export async function GET() {
  const markets = [];
  for (const m of WATCHLIST) {
    try { markets.push({slug: m.slug, who: m.who, ...(await scan(m.slug))}); }
    catch (e) { markets.push({slug: m.slug, who: m.who, error: e instanceof Error ? e.message : 'Scan failed'}); }
  }
  return NextResponse.json({scanned_at: Math.floor(Date.now() / 1000), markets});
}
