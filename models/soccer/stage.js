// Pocket Soccer "Boss Round, the lot": stages a 4-a-side boss round with every chaos power on, then freezes it. Runs inside the page.
window.stageSoccer = function () {
  const names = [['Eradicator the Dedicator', 'Blue Thunder', 'Sir Smashalot', 'Turbo Tank'], ['Goalzilla', 'Big Bad Barry', 'Captain Kaboom', 'The Meatball']];
  const players = [];
  for (let t = 0; t < 2; t++) for (let i = 0; i < 4; i++) players.push({pid:'p' + t + i, name:names[t][i], team:t, faces:[], boss:names[t][0]});
  mode = 'practice'; myPid = 'nobody'; flip = false;
  game = newMatch(players, 180); info = matchInfo(game); runSim(); startView();
  G3.ft = -1e9;
  return {widgets: game.widgets.length};
};
window.chaos = function () {
  const g = game;
  g.lv = [POWERS.length, POWERS.length];           // every power on both sides: turbo, bananas, cannon, rackets, ghosts, freeze, magnets, walls, rocket, nuke
  startBoss(g); g.status = 'play'; g.cd = 0; g.t = 150;
  const W = T => g.widgets.filter(w => w.team === T && w.role !== 'GK');
  const [blue, red] = [W(0), W(1)];
  const bb = blue.find(w => w.boss), rb = red.find(w => w.boss);
  // the two giants square up in the middle; everyone else scattered around them
  Object.assign(bb, {x:38, y:92}); Object.assign(rb, {x:60, y:66});
  blue.filter(w => !w.boss).forEach((w, i) => Object.assign(w, [{x:18, y:120}, {x:80, y:104}, {x:28, y:58}][i] || {}));
  red.filter(w => !w.boss).forEach((w, i) => Object.assign(w, [{x:76, y:126}, {x:20, y:84}, {x:84, y:44}][i] || {}));
  for (const w of g.widgets) { w.vx = w.vy = 0; }
  // red team cursed into ghosts, two blues frozen solid, one blue skidding on a banana
  g.ghost = [0, 8];
  const frozen = blue.filter(w => !w.boss).slice(1, 3); for (const w of frozen) w.frz = 6;
  blue.filter(w => !w.boss)[0].slip = 2;
  g.bananas = [[30, 112], [70, 96], [52, 130], [24, 70], [76, 60], [46, 40], [62, 112], [36, 78]].map(([x, y]) => ({x, y}));
  // the homing rocket ball, blasting off from the blue boss towards the red goal
  Object.assign(g.ball, {x:50, y:72, vx:22, vy:-150, home:1, homeT:5, homeX:50, nuke:false});   // home = team + 1: blue's rocket, steering for the red goal
  g.fx.push({id:g.id++, k:'zap', x:rb.x, y:rb.y, x2:frozen[0].x, y2:frozen[0].y, a:0, team:1});
  window.SOCCER = {bosses: g.boss, frozen: frozen.map(w => w.id), zap: [rb.x, rb.y, frozen[0].x, frozen[0].y]};
};
window.freezeSoccer = function () {
  clearInterval(simTimer);   // stop the match where it is
  const T = THREE, A = G3.arena.clone(true), drop = [];
  A.traverse(o => { if (o.isSprite || o.isLine || !o.visible || (o.isMesh && o.geometry && o.geometry.type === 'RingGeometry')) drop.push(o); });
  for (const o of drop) if (o.parent) o.parent.remove(o);
  const v3 = o => { const p = new T.Vector3(); o.getWorldPosition(p); return [p.x, p.y, p.z].map(n => +n.toFixed(2)); };
  const v = currentView();
  const info2 = {
    ballR: F.ballR, goalW: F.goalW, bossSize: BOSS_SIZE, r: F.r,
    parts: G3.parts.filter(q => q.life > 0 && q.sp.visible).map(q => ({p: v3(q.sp), s: +q.sp.scale.x.toFixed(2), c: '#' + q.sp.material.color.getHexString()})),
    ball: {p: v3(G3.ball), v: v.bv, home: v.bh},
    widgets: v.w.map(([x, y], i) => ({id: i, x: x - 50, z: y - 80, team: info.widgets[i].team, boss: !!info.widgets[i].boss, gk: info.widgets[i].role === 'GK', h: halfOf(v.lv, info.widgets[i])})),
    bosses: (v.bs || []).map(([id, name]) => ({id, name})),
    zap: SOCCER.zap.map((n, i) => n - (i % 2 ? 80 : 50)), frozen: SOCCER.frozen, bananas: (v.na || []).map(([x, y]) => [x - 50, y - 80]),
  };
  return new Promise(res => new T.GLTFExporter().parse(A, glb => {
    let bin = ''; const u8 = new Uint8Array(glb); for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    res({glb: btoa(bin), info: info2});
  }, err => res({error: String(err)}), {binary: true, onlyVisible: true, maxTextureSize: 2048}));
};
