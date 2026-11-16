import {describe, expect, it} from 'vitest';
import {computeFeatures, type Fill} from '../lib/flags';

// One wallet, two buys in the last day before T. Account start is what changes between cases.
const T = 1_767_420_000;
const fills: Fill[] = [[T - 20 * 3600, 'BUY', 0, 40_000, 0.07], [T - 10 * 3600, 'BUY', 0, 10_000, 0.08]];
const base = {fills, t: T, n_markets: 7437, vol_to_t: 1_000_000};

describe('F1 (new account) when /v2/user-stats has no join_date', () => {
  it('uses the first /v2/activity row when join_date is missing (old account: not fired)', () => {
    const r = computeFeatures({...base, join_date: null, first_activity: T - 400 * 86400, first_fill_known: false}, false)!;
    expect(r.F1_days).toBeCloseTo(400 - 20 / 24, 6);
    expect(r.flags.F1).toBe(false);
    expect(r.fired).not.toContain('F1');
  });

  it('is unknown, not 0, when join_date, the activity row and the first fill in the market are all unknown (live scan)', () => {
    const r = computeFeatures({...base, join_date: null, first_activity: null, first_fill_known: false}, false)!;
    expect(r.F1_days).toBeNull();
    expect(r.flags.F1).toBeNull();
    expect(r.fired).not.toContain('F1');
    // the other signs still score: cheap (F3), big (F4), one-way (F5); F2 not (7,437 markets, 5% of volume)
    expect(r.fired).toEqual(['F3', 'F4', 'F5']);
    expect(r.score).toBe(3);
  });

  it('matches the frozen Python fallback when the first fill in this market is known (earliest of activity and first fill)', () => {
    // No activity row: account start = first fill in the market, so the account is 0 days old there (src/v1_03_layer1.py).
    const r = computeFeatures({...base, join_date: null, first_activity: null}, false)!;
    expect(r.F1_days).toBe(0);
    expect(r.flags.F1).toBe(true);
    // An activity row after the first fill does not move the start later.
    const r2 = computeFeatures({...base, join_date: null, first_activity: T - 5 * 3600}, false)!;
    expect(r2.F1_days).toBe(0);
  });

  it('ignores first_activity when join_date is present', () => {
    const r = computeFeatures({...base, join_date: T - 3 * 86400, first_activity: T - 400 * 86400, first_fill_known: false}, false)!;
    expect(r.F1_days).toBeCloseTo(3 - 20 / 24, 6);
    expect(r.flags.F1).toBe(true);
  });
});
