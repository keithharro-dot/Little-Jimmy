import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import fs from 'node:fs';
// node models/battle/export.mjs <dir with three-pkg/ (npm pack three@0.147.0, unpacked)> [ms to let the battle run]
// Needs the game served at http://127.0.0.1:8765 (python3 -m http.server 8765 in the repo root).
const SP = process.argv[2], OUT = new URL('.', import.meta.url).pathname; const b = await chromium.launch({args:['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']}); const errs = [];
const ctx = await b.newContext({viewport:{width:1400, height:900}, deviceScaleFactor:1});
await ctx.route(/peerjs|qrcode/, r => r.abort());
await ctx.route('https://cdn.jsdelivr.net/npm/three@0.147.0/**', r => { const f = r.request().url().split('three@0.147.0/')[1]; r.fulfill({path:SP + '/three-pkg/package/' + f, contentType:'text/javascript'}); });
const p = await ctx.newPage(); p.on('pageerror', e => errs.push(e.message));
await p.addInitScript(() => { localStorage.setItem('tc_gfx', '3d'); localStorage.setItem('tc_map', 'grass'); localStorage.setItem('tc_mute', '1'); Math.random = (s => () => (s = (s*16807) % 2147483647)/2147483647)(42); });
await p.goto('http://127.0.0.1:8765/tower-defence.html'); await p.waitForFunction(() => G3.ready, null, {timeout:30000});
await p.click('#goLocal'); await p.waitForTimeout(1000);
await p.addScriptTag({content: fs.readFileSync(OUT + 'stage.js', 'utf8')});
await p.addScriptTag({path: SP + '/three-pkg/package/examples/js/exporters/GLTFExporter.js'});
await p.evaluate(() => hiResGround());
console.log(await p.evaluate(() => stageBattle()));
const wait = +(process.argv[3] || 2600);
for (let t = 0; t < wait; t += 100) { await p.waitForTimeout(100); await p.evaluate(() => keepAlive()); }
await p.screenshot({path: OUT + 'freeze.png'});
const r = await p.evaluate(() => freezeAndExport());
if (r.error) console.log('export error', r.error);
else { fs.writeFileSync(OUT + 'battle.glb', Buffer.from(r.glb, 'base64')); fs.writeFileSync(OUT + 'battle.json', JSON.stringify(r.info));
  const i = r.info; console.log('glb', (fs.statSync(OUT + 'battle.glb').size/1e6).toFixed(1) + 'MB', 'parts', i.parts.length, 'missiles', i.missiles.length, 'beams', i.beams.length, 'fx', i.fx.map(f => f.k).join(','), 'proj', i.proj.length, 'enemies', i.enemies.length, 'towers', i.towers.length); }
console.log('errors', errs); await b.close();
