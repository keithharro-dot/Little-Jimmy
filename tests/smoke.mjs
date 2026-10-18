// Smoke test for both games. Needs Node 18+ and Playwright:  npm i -D playwright && npx playwright install chromium
// Run from the repo root:  node tests/smoke.mjs
// It serves the repo itself, swaps PeerJS for a local stand-in (tests/mockpeer.js) so two pages can play together
// without a network, and blocks Three.js so 3D falls back to 2D (that fallback is part of what it checks).
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const TYPES = {'.html':'text/html', '.js':'text/javascript', '.mp3':'audio/mpeg', '.jpg':'image/jpeg'};
const server = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, {'content-type': TYPES[path.extname(f)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(res);
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}`;
const FACE = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
const b = await chromium.launch(); const errs = []; let failed = 0;
const check = (ok, what) => { console.log((ok ? '  ✓ ' : '  ✗ ') + what); if (!ok) failed++; };
const ctx = await b.newContext({viewport:{width:390, height:844}, hasTouch:true});
await ctx.route('**/peerjs.min.js', r => r.fulfill({path:path.join(ROOT, 'tests/mockpeer.js'), contentType:'text/javascript'}));
await ctx.route('**/qrcode.min.js', r => r.fulfill({path:path.join(ROOT, 'tests/qrstub.js'), contentType:'text/javascript'}));
await ctx.route(/cdn\.jsdelivr\.net|fonts\.g/, r => r.abort());
const page = async (url, name) => { const p = await ctx.newPage(); p.on('pageerror', e => errs.push(`${name}: ${e.message}`));
  if (name) await p.addInitScript(([n, f]) => localStorage.setItem('ps_profile', JSON.stringify({name:n, faces:[f]})), [name, FACE]);
  await p.goto(url); return p; };

console.log('Pocket Soccer');
const h = await page(BASE + '/soccer.html', 'Host');
await h.tap('#goHost'); await h.waitForFunction(() => !!inviteToken);
await h.waitForTimeout(500); if (await h.isVisible('#pinPad')) await h.tap('#pinPad .no');   // headless has no share sheet or clipboard, so the link box opens: close it
const link = (await h.evaluate(() => joinUrl())).replace(/^https:\/\/[^#]+/, BASE + '/soccer.html');
const g = await page(link, 'Guest'); await g.waitForTimeout(400);
check(await g.isVisible('#joinGo') && (await g.textContent('#joinTitle')).includes('Host invited you'), 'the link opens a Join game screen');
await g.tap('#joinGo'); await h.waitForTimeout(1000);
check(await g.isVisible('#lobby'), 'guest joins by tapping Join game');
check(await h.locator('#plist .prow').count() === 2, 'host lobby shows 2 players');
await h.tap('#btnStart'); await h.waitForTimeout(3000);
check(await g.isVisible('#game') && await g.evaluate(() => !!view), 'match starts on both phones');
await h.evaluate(() => { game.t = game.len - .2; }); await h.waitForFunction(() => game.status === 'duel' || game.status === 'over', null, {timeout:15000});
check(true, 'a timed match reaches its end (duel if level)');
// the lobby's Send button shares that same link; a made-up pass is turned away
const h2 = await page(BASE + '/soccer.html', 'Sender');
await h2.evaluate(() => { window.shared = null; navigator.share = d => { window.shared = d; return Promise.resolve(); }; });
await h2.tap('#goHost'); await h2.waitForFunction(() => !!inviteToken); await h2.tap('#btnInvite'); await h2.waitForFunction(() => !!window.shared);
check(await h2.evaluate(() => window.shared.url === joinUrl()), 'Send the link shares the same link as the QR code');
const g3 = await page(BASE + '/soccer.html#join=' + await h2.evaluate(() => hostCode) + '.ABCDEFGHJK', 'Stranger');
await g3.tap('#joinGo'); await g3.waitForTimeout(1200);
check(!(await g3.isVisible('#lobby')) && await h2.locator('#plist .prow').count() === 1, 'a made-up link is turned away');
for (const p of [h2, g3]) await p.close();
const p1 = await page(BASE + '/soccer.html', 'Solo'); await p1.tap('#goPractice'); await p1.waitForTimeout(2500);
check(await p1.evaluate(() => game.status !== undefined && !G3.on), 'practice runs, in 2D when 3D can\'t load');

console.log('Tower Defence');
const t = await page(BASE + '/tower-defence.html'); await t.tap('#goMulti'); await t.tap('#goLocal'); await t.waitForTimeout(1500);
await t.evaluate(() => { game.status = 'play'; game.gold = 9999; applyCmd(game, 'def', {type:'place', x:5, y:3, spec:PRESETS[0]}); spawnEnemy(game, 'zombie', 1, 1); });
await t.waitForTimeout(2500);
check(await t.evaluate(() => game.towers.length === 1), 'a tower can be built');
check(await t.evaluate(() => game.t > 1), 'the game clock runs');

check(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.join(' | ') : ''));
await b.close(); server.close();
console.log(failed ? `${failed} check(s) failed` : 'All checks passed'); process.exit(failed ? 1 : 0);
