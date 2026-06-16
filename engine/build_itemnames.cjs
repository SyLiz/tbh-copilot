// Generate engine/itemnames.js — localized names for NON-gear items (materials, boxes,
// stones, scrolls…). Gear (5760 items) is already named in gearnames.js (English, since
// those double as Steam market hashes), so this only fills the rest, keeping it ~48KB.
// Lets the Items tab show real, localized names and makes name-search work per locale.
const fs = require('fs'), path = require('path');
const GAME_LOCALES = ['en-US', 'pt-BR', 'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ko-KR', 'zh-Hans', 'zh-Hant', 'ru-RU', 'pl-PL', 'tr-TR', 'uk-UA', 'id-ID', 'th-TH', 'vi-VN'];
const items = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'wiki', 'items.json'), 'utf8'));
const map = {};
for (const it of items) {
  if (it.gear != null || !it.name) continue; // gear handled by gearnames.js
  const o = {};
  for (const l of GAME_LOCALES) if (it.name[l]) o[l] = it.name[l];
  if (o['en-US']) map[it.id] = o;
}
const payload = JSON.stringify(map);
const out = ';(function(g){g.TBH_ITEMNAMES=' + payload + ';if(typeof module!=="undefined"&&module.exports)module.exports=g.TBH_ITEMNAMES;})(typeof globalThis!=="undefined"?globalThis:this);\n';
fs.writeFileSync(path.join(__dirname, 'itemnames.js'), out);
console.log('wrote engine/itemnames.js: ' + Object.keys(map).length + ' non-gear item names, ' + (out.length / 1024).toFixed(0) + 'KB');
