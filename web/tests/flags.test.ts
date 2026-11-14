import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {describe, expect, it} from 'vitest';
import {computeFeatures, FROZEN, type Fill} from '../lib/flags';

type Case = {
  id: string; t_news: number; fills: Fill[]; join_date: number | null; n_markets: number | null; vol_to_tnews: number | null; first_activity: number | null;
  expected: {score: number; flags: string[]; F1_days: number; F2_share: number | null; F3_vwap: number; F4_buy_usd: number; F5_conviction: number; F6_hours: number};
};
const fx = JSON.parse(readFileSync(join(__dirname, 'fixtures', 'flags_20.json'), 'utf8')) as {flags: Record<string, number>; cases: Case[]};

describe('TypeScript port of the frozen v1 flags', () => {
  it('uses the frozen thresholds', () => {
    expect(FROZEN).toEqual(fx.flags);
  });

  it('has 20 wallets to check', () => {
    expect(fx.cases).toHaveLength(20);
  });

  for (const c of fx.cases) {
    it(`reproduces the Python score for ${c.id}`, () => {
      const r = computeFeatures({fills: c.fills, t: c.t_news, join_date: c.join_date, n_markets: c.n_markets, vol_to_t: c.vol_to_tnews, first_activity: c.first_activity})!;
      expect(r).not.toBeNull();
      expect(r.score).toBe(c.expected.score);
      expect(r.fired).toEqual(c.expected.flags);
      // Python rounds the stored features (F1 to 3 dp, F3 to 4, F4 to 2, F5 to 4, F6 to 2)
      expect(r.F1_days).toBeCloseTo(c.expected.F1_days, 3);
      expect(r.F3_vwap).toBeCloseTo(c.expected.F3_vwap, 4);
      expect(r.F4_buy_usd).toBeCloseTo(c.expected.F4_buy_usd, 2);
      expect(r.F5_conviction).toBeCloseTo(c.expected.F5_conviction, 4);
      expect(r.F6_hours!).toBeCloseTo(c.expected.F6_hours, 2);
      if (c.expected.F2_share === null) expect(r.F2_share).toBeNull();
      else expect(r.F2_share!).toBeCloseTo(c.expected.F2_share, 6);
    });
  }

  it('leaves F6 unevaluated live and scores out of 5', () => {
    const c = fx.cases[0];
    const r = computeFeatures({fills: c.fills, t: c.t_news, join_date: c.join_date, n_markets: c.n_markets, vol_to_t: c.vol_to_tnews, first_activity: c.first_activity}, false)!;
    expect(r.flags.F6).toBeNull();
    expect(r.out_of).toBe(5);
    expect(r.score).toBe(c.expected.flags.filter(f => f !== 'F6').length);
  });
});
