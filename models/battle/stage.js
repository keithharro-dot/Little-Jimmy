// Stages an epic mid-battle moment in the running game (local game, 3D on). Runs inside the page.
window.stageBattle = function () {
  G3.ft = -1e9; game.status = 'play'; game.gold = 1e7; game.energy = 1e7; game.waveT = 1e9; game.wave = 21;
  const LP = PRESETS.find(d => d.role === 'launcher'), P = n => PRESETS.find(d => d.name === n);
  // tiles near the road, with where along the road they sit
  const tiles = [];
  for (let x = 0; x < COLS; x++) for (let y = 0; y < ROWS; y++) {
    if (PATH.has(x + ',' + y)) continue; let near = 99, at = 0;
    for (let d = 0; d < PATHLEN; d += .1) { const [px, py] = posAt(d), r = Math.hypot(px - x - .5, py - y - .5); if (r < near) { near = r; at = d / PATHLEN; } }
    tiles.push({x, y, near, at});
  }
  const used = new Set(), put = (spec, lvl, pred) => {
    const t = tiles.filter(t => !used.has(t.x + ',' + t.y) && pred(t)).sort((a, b) => a.near - b.near)[0]; if (!t) return;
    used.add(t.x + ',' + t.y); applyCmd(game, 'def', {type:'place', x:t.x, y:t.y, spec});
    const tw = game.towers[game.towers.length - 1]; for (let l = 1; l < lvl; l++) applyCmd(game, 'def', {type:'upgrade', id:tw.id});
  };
  // the defence: launchers of every level along the road, the ANNIHILATOR at the heart of it, plus a mixed army
  put(LP, 1, t => t.at > .05 && t.at < .15 && t.near > 1);
  put(LP, 2, t => t.at > .18 && t.at < .28 && t.near > 1);
  put(LP, 3, t => t.at > .33 && t.at < .43 && t.near > 1);
  put(LP, 5, t => t.at > .48 && t.at < .6 && t.near > 2.2);
  put(LP, 4, t => t.at > .62 && t.at < .72 && t.near > 1);
  put(LP, 5, t => t.at > .8 && t.at < .92 && t.near > 1.5);
  const army = [['Sniper', 4], ['Boomer', 4], ['Frost', 3], ['Trooper', 4], ['Boomer', 3], ['Sniper', 3], ['Trooper', 2], ['Frost', 2], ['DJ', 3], ['Reviver', 2], ['Trooper', 3], ['Boomer', 2], ['Sniper', 2], ['Trooper', 1]];
  army.forEach(([n, l], i) => put(P(n), l, t => t.near < 1.6 && Math.abs(t.at - (i + .5)/army.length) < .12));
  // the attack: bosses spread down the road, a horde between them, bats overhead
  const at = (k, f, mul = 1) => { spawnEnemy(game, k, mul, false); const e = game.enemies[game.enemies.length - 1]; e.d = f*routeLen(e); return e; };
  const m1 = at('erad', .3, 40), m2 = at('erad2', .52, 40), vd = at('void', .76, 40);
  m2.hp = m2.m*.4;   // raging
  const horde = ['zombie', 'brute', 'riot', 'speedy', 'medic', 'zombie', 'phantom', 'zombie', 'brute', 'avatar', 'zombie', 'speedy'];
  for (let i = 0; i < 70; i++) { const f = .03 + i*.86/70 + (Math.random() - .5)*.01; if (Math.abs(f - .3) < .025 || Math.abs(f - .52) < .03 || Math.abs(f - .76) < .025) continue; at(horde[i % horde.length], f, 40); }
  for (let i = 0; i < 7; i++) at('bat', .15 + i*.11, 40);
  for (const e of game.enemies) e.hp = Math.max(e.hp, e.m*.3);
  return {towers: game.towers.length, enemies: game.enemies.length};
};
// keep everyone alive while the battle runs, so the freeze-frame is crowded
window.keepAlive = () => {
  for (const e of game.enemies) { if (e.hp < e.m*.25) e.hp = e.m*.5; if (e.d > routeLen(e)*.92) e.d = routeLen(e)*.92; }
  for (const t of game.towers) { t.stuns = 0; t.stun = 0; t.mc = 0; }
};
// Freeze the moment: clone the 3D world (so nothing moves while it's written out) and note every effect in the air.
window.freezeAndExport = function () {
  game.paused = true;
  const W = G3.world.clone(true), T = THREE;
  const drop = [];
  W.traverse(o => {
    if (o.isSprite || o.isLineSegments || o.isLine || !o.visible) drop.push(o);
    else if (o.isMesh && o.geometry && o.geometry.parameters && o.geometry.parameters.width === 80) drop.push(o);   // the endless grass around the board
    else if (o.isMesh && o.geometry && o.geometry.type === 'RingGeometry') drop.push(o);                           // flat effect rings
    else if (o.isMesh && o.geometry && o.geometry.type === 'CircleGeometry' && o.material && o.material.opacity < .5) drop.push(o);
  });
  for (const o of drop) if (o.parent) o.parent.remove(o);
  const v3 = o => { const p = new T.Vector3(); o.getWorldPosition(p); return [p.x, p.y, p.z].map(n => +n.toFixed(3)); };
  const info = {
    cols: COLS, rows: ROWS,
    parts: G3.parts.filter(q => q.life > 0 && q.sp.visible).map(q => ({p: v3(q.sp), s: +q.sp.scale.x.toFixed(3), c: '#' + q.sp.material.color.getHexString(), a: +q.sp.material.opacity.toFixed(2)})),
    missiles: G3.missiles.filter(m => m.userData.live).map(m => { const u = m.userData; return {p: v3(m), a: u.a, b: u.b, t: u.t, dur: u.dur, arc: u.arc, shell: !!u.shell}; }),
    beams: G3.beams.filter(m => m.visible).map(m => { const c = new T.Vector3(); m.getWorldPosition(c); const dir = new T.Vector3(0, 1, 0).applyQuaternion(m.quaternion).multiplyScalar(m.scale.y/2);
      return {a: [c.x - dir.x, c.y - dir.y, c.z - dir.z].map(n => +n.toFixed(3)), b: [c.x + dir.x, c.y + dir.y, c.z + dir.z].map(n => +n.toFixed(3)), w: +m.scale.x.toFixed(2), c: '#' + m.material.color.getHexString()}; }),
    fx: game.fx.map(f => ({k: f.k, x: f.x - COLS/2, z: f.y - ROWS/2, ttl: f.ttl, x2: f.x2 === undefined ? null : f.x2 - COLS/2, z2: f.y2 === undefined ? null : f.y2 - ROWS/2})),
    proj: game.proj.map(q => ({x: q.x - COLS/2, z: q.y - ROWS/2, t: q.t, blast: q.blast})),
    shots: game.shots.map(s => ({a: [s.x1 - COLS/2, s.y1 - ROWS/2], b: [s.x2 - COLS/2, s.y2 - ROWS/2], sp: s.sp, c: s.c})),
    enemies: game.enemies.map(e => ({k: e.k, x: e.x - COLS/2, z: e.y - ROWS/2, fury: !!e.fury, boss: !!ENEMIES[e.k].boss, fly: !!ENEMIES[e.k].fly, r: ENEMIES[e.k].r})),
    towers: game.towers.map(t => ({x: t.x + .5 - COLS/2, z: t.y + .5 - ROWS/2, role: t.spec.role, lvl: t.lvl, name: t.spec.name})),
    way: WAY.map(([x, y]) => [x - COLS/2, y - ROWS/2]),
    extra: window.EXTRA || {},
  };
  return new Promise(res => new T.GLTFExporter().parse(W, glb => {
    let bin = ''; const u8 = new Uint8Array(glb); for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    res({glb: btoa(bin), info});
  }, err => res({error: String(err)}), {binary: true, onlyVisible: true, maxTextureSize: 4096}));
};
// sharper ground: redraw the board texture at 160 px per tile instead of 64
window.hiResGround = function () {
  window.groundTex = (0, eval)('(' + groundTex.toString().replace('const ts = 64', 'const ts = 160') + ')');
  buildWorld();
};

// ---- "Boss Assault": all three bosses together mid-road, missiles raining overhead, a MELTDOWN going off ----
window.stageBoss = function () {
  G3.ft = -1e9; game.status = 'play'; game.gold = 1e7; game.energy = 1e7; game.waveT = 1e9; game.wave = 48;
  const LP = PRESETS.find(d => d.role === 'launcher'), P = n => PRESETS.find(d => d.name === n);
  const tiles = [];
  for (let x = 0; x < COLS; x++) for (let y = 0; y < ROWS; y++) {
    if (PATH.has(x + ',' + y)) continue; let near = 99, at = 0;
    for (let d = 0; d < PATHLEN; d += .1) { const [px, py] = posAt(d), r = Math.hypot(px - x - .5, py - y - .5); if (r < near) { near = r; at = d / PATHLEN; } }
    tiles.push({x, y, near, at});
  }
  const used = new Set(), put = (spec, lvl, pred) => {
    const t = tiles.filter(t => !used.has(t.x + ',' + t.y) && pred(t)).sort((a, b) => a.near - b.near)[0]; if (!t) return;
    used.add(t.x + ',' + t.y); applyCmd(game, 'def', {type:'place', x:t.x, y:t.y, spec});
    const tw = game.towers[game.towers.length - 1]; for (let l = 1; l < lvl; l++) applyCmd(game, 'def', {type:'upgrade', id:tw.id});
  };
  // a fortress around the middle of the road: three ANNIHILATORs and a laser out of rocket reach, a ring of soldiers close in
  put(LP, 5, t => t.at > .3 && t.at < .45 && t.near > 2.2);
  put(LP, 5, t => t.at > .5 && t.at < .65 && t.near > 2.2);
  put(LP, 5, t => t.at > .65 && t.at < .85 && t.near > 2.2);
  put(LP, 4, t => t.at > .2 && t.at < .35 && t.near > 1.5);
  put(LP, 3, t => t.at > .7 && t.at < .9 && t.near > 1.2);
  const army = [['Sniper', 4], ['Boomer', 4], ['Frost', 4], ['Trooper', 4], ['Boomer', 4], ['Sniper', 4], ['Trooper', 4], ['Frost', 3], ['DJ', 4], ['Reviver', 3], ['Trooper', 3], ['Boomer', 3]];
  army.forEach(([n, l], i) => put(P(n), l, t => t.near < 1.7 && Math.abs(t.at - (.25 + .5*(i + .5)/army.length)) < .1));
  const at = (k, f, mul = 1) => { spawnEnemy(game, k, mul, false); const e = game.enemies[game.enemies.length - 1]; e.d = f*routeLen(e); return e; };
  window.BOSSES = {m1: at('erad', .4, 60), m2: at('erad2', .55, 60), vd: at('void', .68, 60)};
  BOSSES.m2.hp = BOSSES.m2.m*.4;
  const escort = ['avatar', 'avatar', 'brute', 'riot', 'zombie', 'medic', 'avatar', 'brute', 'phantom', 'zombie'];
  for (let i = 0; i < 30; i++) at(escort[i % escort.length], .3 + i*.45/30 + (Math.random() - .5)*.01, 60);
  for (let i = 0; i < 6; i++) at('bat', .35 + i*.07, 60);
  return {towers: game.towers.length, enemies: game.enemies.length};
};
// keep the bosses firing: missile rain and rocket bursts on a short fuse, the MK II laser charging
window.bossTick = function () {
  keepAlive();
  const {m1, m2} = BOSSES;
  if (m2 && m2.mr > .8) m2.mr = .8;
  if (m1 && m1.emp > 1.2) m1.emp = 1.2;
  if (m2 && m2.emp > 1.6) m2.emp = 1.6;
  for (const e of game.enemies) if (ENEMIES[e.k].boss && e.d > routeLen(e)*.7) e.d = routeLen(e)*.7;
};
// go out with a bang: the MK I melts down just before the freeze
window.meltdown = () => { const e = BOSSES.m1; window.EXTRA = {meltdown: [e.x - COLS/2, e.y - ROWS/2]}; e.hp = 0; };
