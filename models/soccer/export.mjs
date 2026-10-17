import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import fs from 'node:fs';
// node models/soccer/export.mjs <dir with three-pkg/ (npm pack three@0.147.0, unpacked)>
// Needs the game served at http://127.0.0.1:8765 (python3 -m http.server 8765 in the repo root).
const SP = process.argv[2], OUT = new URL('.', import.meta.url).pathname;
const b = await chromium.launch({args:['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']}); const errs = [];
const ctx = await b.newContext({viewport:{width:1400, height:900}, deviceScaleFactor:1});
await ctx.route(/peerjs|qrcode|fonts\.g/, r => r.abort());
await ctx.route('https://cdn.jsdelivr.net/npm/three@0.147.0/**', r => { const f = r.request().url().split('three@0.147.0/')[1]; r.fulfill({path:SP + '/three-pkg/package/' + f, contentType:'text/javascript'}); });
const p = await ctx.newPage(); p.on('pageerror', e => errs.push(e.message));
await p.addInitScript(() => { localStorage.setItem('ps_gfx', '3d'); localStorage.setItem('ps_music', '0'); localStorage.setItem('ps_profile', JSON.stringify({name:'Ref', faces:[]}));
  Math.random = (s => () => (s = (s*16807) % 2147483647)/2147483647)(7); });
await p.goto('http://127.0.0.1:8765/soccer.html'); await p.waitForFunction(() => G3.ready, null, {timeout:30000});
await p.addScriptTag({content: fs.readFileSync(OUT + 'stage.js', 'utf8')});
await p.addScriptTag({path: SP + '/three-pkg/package/examples/js/exporters/GLTFExporter.js'});
console.log(await p.evaluate(() => stageSoccer()));
await p.waitForTimeout(1500); await p.evaluate(() => chaos());
await p.waitForTimeout(700);
await p.screenshot({path: OUT + 'boss-freeze.png'});
const r = await p.evaluate(() => freezeSoccer());
if (r.error) console.log('export error', r.error);
else { fs.writeFileSync(OUT + 'boss.glb', Buffer.from(r.glb, 'base64')); fs.writeFileSync(OUT + 'boss.json', JSON.stringify(r.info));
  console.log('glb', (fs.statSync(OUT + 'boss.glb').size/1e6).toFixed(1) + 'MB', 'parts', r.info.parts.length, 'bosses', JSON.stringify(r.info.bosses), 'ball', JSON.stringify(r.info.ball)); }
console.log('errors', errs); await b.close();
