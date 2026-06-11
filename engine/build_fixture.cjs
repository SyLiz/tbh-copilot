// Regenerate engine/fixtures/save_fixture.json from runtime/save_snapshot.json.
// The fixture carries ONLY PlayerSaveData (pure game state, same data already public
// via demo.js). SystemInfo and AccountSaveData (ownerSteamId) are deliberately dropped.
// Run after refreshing the snapshot so CI tests the same save the expectations target.
const fs = require('fs'), p = require('path');
const snap = JSON.parse(fs.readFileSync(p.join(__dirname, '..', 'runtime', 'save_snapshot.json'), 'utf8'));
const fixture = { PlayerSaveData: { value: snap.PlayerSaveData.value } };
const dir = p.join(__dirname, 'fixtures');
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(p.join(dir, 'save_fixture.json'), JSON.stringify(fixture));
console.log('regenerated engine/fixtures/save_fixture.json (' + (JSON.stringify(fixture).length / 1024).toFixed(0) + ' KB, PlayerSaveData only)');
