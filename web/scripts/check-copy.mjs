// Fails the build if an em dash reaches the rendered HTML (page copy, metadata, alt text). Owner rule, 2026-11-17.
import {readFileSync, readdirSync, statSync, existsSync} from 'node:fs';
import {join} from 'node:path';
const dir = join(process.cwd(), '.next', 'server', 'app');
if (!existsSync(dir)) { console.error('check-copy: no build output at .next/server/app'); process.exit(1); }
const walk = d => readdirSync(d).flatMap(f => { const p = join(d, f); return statSync(p).isDirectory() ? walk(p) : [p]; });
const files = walk(dir).filter(f => /\.(html|meta|rsc|body)$/.test(f));
const bad = files.filter(f => readFileSync(f, 'utf8').includes('—'));
if (bad.length) { console.error('Em dash found in rendered output:\n' + bad.join('\n')); process.exit(1); }
console.log(`check-copy: no em dash in ${files.length} rendered files`);
