import {readFileSync, readdirSync, statSync} from 'node:fs';
import {join} from 'node:path';
import {describe, expect, it} from 'vitest';
import {clean, DISCLAIMER, NOT_PROOF, FLAG_SHORT, FLAG_NAMES, FLAG_RULE} from '../lib/copy';

/** Owner rule (2026-11-17): no em dash anywhere in the UI, metadata or alt text. */
const EM = '—';
const root = join(__dirname, '..');
const walk = (dir: string): string[] => readdirSync(dir).flatMap(f => { const p = join(dir, f); return statSync(p).isDirectory() ? walk(p) : [p]; });
const offending = (files: string[]) => files.filter(f => readFileSync(f, 'utf8').includes(EM)).map(f => f.replace(root + '/', ''));

describe('no em dash in rendered copy', () => {
  it('page source, components and shared copy contain none', () => {
    const files = [...walk(join(root, 'app')), ...walk(join(root, 'components', 'product')), ...['copy.ts', 'scan.ts', 'watchlist.ts', 'flags.ts'].map(f => join(root, 'lib', f))]
      .filter(f => /\.(tsx?|css)$/.test(f));
    expect(offending(files)).toEqual([]);
  });

  it('shared strings contain none', () => {
    const strings = [DISCLAIMER, NOT_PROOF, ...Object.values(FLAG_SHORT), ...Object.values(FLAG_NAMES), ...Object.values(FLAG_RULE)];
    expect(strings.filter(s => s.includes(EM))).toEqual([]);
  });

  it('text shown from data files contains none after cleaning (market titles come from Polymarket)', () => {
    const shown: string[] = [];
    const pick = (v: unknown, key = ''): void => {
      if (typeof v === 'string') { if (['question', 'who', 'choice', 'error'].includes(key)) shown.push(clean(v)); return; }
      if (Array.isArray(v)) v.forEach(x => pick(x, key));
      else if (v && typeof v === 'object') Object.entries(v).forEach(([k, x]) => pick(x, k));
    };
    for (const f of ['watchlist.json', 'live_example.json', 'maduro_replay.json']) pick(JSON.parse(readFileSync(join(root, 'public', 'data', f), 'utf8')));
    expect(shown.length).toBeGreaterThan(0);
    expect(shown.filter(s => s.includes(EM))).toEqual([]);
  });

  it('clean() turns an em dash into a colon or comma', () => {
    expect(clean('Bitcoin — up or down')).toBe('Bitcoin: up or down');
    expect(clean('a—b')).toBe('a, b');
  });
});
