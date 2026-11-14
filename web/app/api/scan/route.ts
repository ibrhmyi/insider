import {NextResponse} from 'next/server';
import {scan, ScanError} from '@/lib/scan';

export const maxDuration = 60;
export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const q = new URL(req.url).searchParams.get('q') ?? '';
  try {
    return NextResponse.json(await scan(q));
  } catch (e) {
    const status = e instanceof ScanError ? e.status : 502;
    const msg = e instanceof ScanError ? e.message : 'Could not reach the Polymarket API. Try again, or load the cached example.';
    return NextResponse.json({error: msg}, {status});
  }
}
