// Structural smoke test for the dashboard — pure Node, zero dependencies, so it runs in
// CI alongside test.cjs without a browser or node_modules. It does NOT render in a real
// DOM (that stays a manual browser pass); it catches the regression classes this project
// has actually hit: a partial/forgotten cache bump, a tab wired without its pane, a
// missing script asset, a syntax error in the inline script, and i18n keys that exist in
// en-US but were never translated in one of the 10 main locales (the Shop/History tab-
// label bug). Exit 1 on any failure so CI goes red.
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'dashboard.html'), 'utf8');

let pass = 0, fail = 0;
const ok = (cond, label) => { console.log(`${cond ? 'PASS' : 'FAIL'} ${label}`); cond ? pass++ : fail++; };

console.log('=== dashboard structural smoke ===\n');

// 1. inline script parses (syntax)
const inline = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/);
ok(!!inline, 'found the inline dashboard script');
if (inline) {
  let parsed = true;
  try { new vm.Script(inline[1]); } catch (e) { parsed = false; console.log('   ' + e.message); }
  ok(parsed, 'inline dashboard script parses without syntax error');
}

// 2. cache-buster: every ?v=NN reference is identical (no partial bump), matches the
// recorded version, and — crucially — the shipped assets haven't changed since the last
// bump. The hash guard is what makes "forgot to bump" a hard CI failure (the v50 bug).
const vers = [...html.matchAll(/\?v=(\d+)/g)].map(m => m[1]);
ok(vers.length > 0, `cache-buster refs present (${vers.length})`);
ok(new Set(vers).size === 1, `all ?v= refs identical (found ${[...new Set(vers)].join(', ')})`);
const cver = JSON.parse(fs.readFileSync(path.join(__dirname, 'cachever.json'), 'utf8'));
ok(vers[0] === String(cver.version), `?v=${vers[0]} matches cachever.json version ${cver.version}`);
const { assetHash } = require('./bump.cjs');
ok(assetHash() === cver.hash, 'shipped assets unchanged since last bump — else run: node engine/bump.cjs');

// 3. every <script src="engine/X?v=.."> file exists on disk
const srcs = [...html.matchAll(/<script src="([^"?]+)(?:\?v=\d+)?"><\/script>/g)].map(m => m[1]);
ok(srcs.length >= 5, `script srcs found (${srcs.length})`);
for (const s of srcs) ok(fs.existsSync(path.join(ROOT, s)), `asset exists: ${s}`);

// 4. every TABS entry has a matching pane-<id> element and a resolvable label key
const I18N = require('./i18n.js');
const tabsBlock = html.match(/const TABS=\[([\s\S]*?)\];/);
ok(!!tabsBlock, 'found the TABS array');
const tabPairs = tabsBlock ? [...tabsBlock[1].matchAll(/\['([^']+)','([^']+)'\]/g)].map(m => [m[1], m[2]]) : [];
ok(tabPairs.length >= 6, `TABS parsed (${tabPairs.length} tabs)`);
for (const [id, key] of tabPairs) {
  ok(html.includes(`id="pane-${id}"`), `tab '${id}' has a pane-${id} element`);
  ok(I18N.UI['en-US'][key] != null, `tab '${id}' label key '${key}' exists in en-US`);
}

// 5. i18n coverage: every en-US key must exist (raw, not via fallback) in all 10 main
// locales. The 6 smaller locales intentionally fall back to English for UI chrome, so
// they're reported as info only, never a failure.
const MAIN = ['en-US', 'pt-BR', 'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ko-KR', 'zh-Hans', 'zh-Hant', 'ru-RU'];
const SMALL = ['pl-PL', 'tr-TR', 'uk-UA', 'id-ID', 'th-TH', 'vi-VN'];
const enKeys = Object.keys(I18N.UI['en-US']);
console.log(`\n-- i18n coverage: ${enKeys.length} keys × ${MAIN.length} main locales --`);
let gaps = 0;
for (const loc of MAIN) {
  if (loc === 'en-US') continue;
  const missing = enKeys.filter(k => I18N.UI[loc][k] == null);
  if (missing.length) { gaps += missing.length; console.log(`   ${loc} missing ${missing.length}: ${missing.slice(0, 12).join(', ')}${missing.length > 12 ? '…' : ''}`); }
}
ok(gaps === 0, `no missing i18n keys across the 10 main locales (${gaps} gaps)`);
const smallCov = SMALL.map(loc => `${loc}:${enKeys.filter(k => I18N.UI[loc] && I18N.UI[loc][k] != null).length}/${enKeys.length}`).join('  ');
console.log(`   (info) smaller locales fall back to English by design — ${smallCov}`);

console.log(`\n=== ${pass} passed, ${fail} failed ===`);
process.exit(fail ? 1 : 0);
