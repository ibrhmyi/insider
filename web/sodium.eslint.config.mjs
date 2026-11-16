import {existsSync, readFileSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import tsParser from '@typescript-eslint/parser';

function pluginPath() {
  const here = dirname(fileURLToPath(import.meta.url));
  const dirs = [here, join(here, 'lib/sodium/lint'), join(here, 'src/lib/sodium/lint')];
  try {
    const alias = JSON.parse(readFileSync(join(here, 'components.json'), 'utf8')).aliases?.lib;
    if (alias) dirs.push(...['', 'src'].map(base => join(here, base, alias.replace(/^[@~]\//, ''), 'sodium/lint')));
  } catch {}
  const found = dirs.map(dir => join(dir, 'plugin.mjs')).find(existsSync);
  if (!found) throw new Error('Sodium lint: lib/sodium/lint/plugin.mjs is missing. Run npx shadcn@latest add https://design.how/r/sodium/lint.json');
  return found;
}

const plugin = pluginPath();
const sodium = (await import(pathToFileURL(plugin).href)).default;
const {LINT_IGNORES} = await import(pathToFileURL(join(dirname(plugin), 'value-rules.mjs')).href);

export default [
  {ignores: [...LINT_IGNORES, '**/lib/sodium/lint/**']},
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    languageOptions: {parser: tsParser, parserOptions: {ecmaFeatures: {jsx: true}}},
    linterOptions: {reportUnusedDisableDirectives: 'off'},
    plugins: {sodium},
    processor: 'sodium/standalone',
    rules: sodium.configs.app.rules,
  },
  {files: ['**/components/sodium/{ui,ai}/**', '**/components/sodium/icon.tsx', '**/lib/sodium/**'], rules: sodium.configs.source.rules},
  // Project exception: the watchlist card is a multi-line native <button> (Sodium's Button has a fixed control height).
  // It keeps the focus ring and aria-expanded. Logged in log/process_log.md, 2026-11-17.
  {files: ['**/components/product/watchlist.tsx'], rules: {'sodium/no-native-control': 'off'}},
];
