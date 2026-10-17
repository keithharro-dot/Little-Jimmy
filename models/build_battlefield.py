# Tower Defence frozen mid-battle, for augmented reality, big enough to walk around on a sports oval.
#
#   python models/build_battlefield.py [battle|boss] [--render <dir>]
#
#   battle: "The Battlefield" — the whole defence at work against a horde and three bosses.
#   boss:   "Boss Assault" — MK II raining missiles overhead, the Void, MK I melting down, three ANNIHILATORs firing back.
#
# models/battle/<scene>.glb + .json come from the real game (models/battle/export.mjs): a staged moment, frozen and
# exported with three.js. This adds the epic part — fireballs, smoke, missile trails, glowing beams, sparks, boss
# auras, a meltdown — scales it so 1 game tile = TILE metres, and writes models/<name>.glb/.usdz (+ a -mini copy).
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arlib import *

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = next((a for a in sys.argv[1:] if a in ('battle', 'boss')), 'battle')
NAME = {'battle': 'battlefield', 'boss': 'td-boss'}[SCENE]
TILE = 4.5            # metres per game tile: the board is 67.5 x 40.5 m, ~93 x 65 m with the scenery
KEEP = (10.5, 7.0)    # trim scenery further than this (in tiles) from the board's centre

GM = start(os.path.join(HERE, 'battle', SCENE + '.glb'))
info = json.load(open(os.path.join(HERE, 'battle', SCENE + '.json')))
COLS, ROWS = info['cols'], info['rows']
# colours that glow in the game: ANNIHILATOR pink, laser cyan, lava, eyes, muzzles, reactor amber
meshes = convert_materials(GM, ['#ff2bd6', '#ff7be8', '#3ee6ff', '#bff6ff', '#ff3b30', '#ff2a10', '#ff4020', '#ffe680', '#ffb03a', '#8dff4a', '#ff7a1a', '#ffc23a'], brighten=1.55)
trim(meshes, lambda c: abs(c.x) <= KEEP[0] and abs(c.y) <= KEEP[1])
X = fx_mats()

# missiles in flight: smoke trails back along their arcs, and a flame at the tail
def arc_at(m, q):
    (ax, ay, ah), (bx, by) = m['a'], m['b']
    x, y = ax + (bx - ax) * q, ay + (by - ay) * q
    return B(x - COLS / 2, ah * (1 - q) + .2 * q + math.sin(math.pi * q) * m['arc'], y - ROWS / 2)
impacts = []
for m in info['missiles']:
    k = min(1, m['t'] / m['dur'])
    head = arc_at(m, k); tail_dir = head - arc_at(m, max(0, k - .02))
    if not m['shell']: cone(head - tail_dir.normalized() * .16, tail_dir, .05, .28, X['FLAME'])
    pts = [arc_at(m, q) for q in [k - .032 * (i + 1) for i in range(14)] if q > max(0, k - .45)]
    trail(pts, .022, .022 + len(pts) * .006, X['TRAIL'])
    impacts.append(B(m['b'][0] - COLS / 2, 0, m['b'][1] - ROWS / 2))
for q in info['proj']: impacts.append(B(q['x'], 0, q['z']))

# explosions where the missiles are landing (one per neighbourhood), plus the big ones
sites = []
for p in impacts:
    if all((p - s).length > 1.2 for s in sites): sites.append(p)
for i, p in enumerate(sites[:7 if SCENE == 'battle' else 9]):
    explosion(p + Vector(((rng.random() - .5) * .5, (rng.random() - .5) * .5, 0)), .5 + rng.random() * .2, column=(i == 2))
for e in info['enemies']:
    if e['k'] == 'erad': explosion(B(e['x'] + .9, 0, e['z'] + .3), .8, column=True)
if 'meltdown' in info.get('extra', {}):   # the MK I going up: a mushroom of fire where it stood
    mx, mz = info['extra']['meltdown']
    mushroom(B(mx, 0, mz), 4.2)

# beams: a bright core, a soft glow sleeve, a flare where they hit and sparks along the way
for bm_ in info['beams']:
    a, b = Vector(bm_['a']), Vector(bm_['b']); a, b = B(a.x, a.y, a.z), B(b.x, b.y, b.z)
    r, g_, b_ = (int(bm_['c'][-6:][i:i + 2], 16) / 255 for i in (0, 2, 4))
    hexc = '#3ee6ff' if r < .75 and g_ > .8 and b_ > .8 else '#ff2bd6' if r > .8 and g_ < .6 and b_ > .8 else '#ff3b30' if r > .8 and g_ < .7 else '#fff2b0'
    col = hexlin(hexc); w = .035 * max(1, bm_['w'])
    tube(a, b, w * .45, mat('Beam core', (1, 1, 1), emit=14))
    tube(a, b, w, mat('Beam', col, emit=10, alpha=.85))
    tube(a, b, w * 2.6, mat('Beam glow', col, emit=4, alpha=.3))
    ball(b, w * 4, mat('Flare', col, emit=10, alpha=.7))
    for i in range(10):
        p = a.lerp(b, rng.random())
        ball(p + Vector(((rng.random() - .5) * .3, (rng.random() - .5) * .3, rng.random() * .3)), .03, mat('Spark', col, emit=10), sub=1)

# the game's own particles at the moment of the freeze: sparks glow, grey ones are smoke
for q in info['parts']:
    p = Vector(q['p']); p = B(p.x, p.y, p.z); c = hexlin(q['c'])
    if max(c) - min(c) < .08: ball(p, max(.04, q['s'] * .35), X['SMOKE'], sub=1)
    else: ball(p, max(.03, q['s'] * .25), mat('Spark', c, emit=8), sub=1)

# boss auras: the raging MK II glows red, the Void floats in a purple haze
for e in info['enemies']:
    if e['k'] == 'erad2':
        ball(B(e['x'], 0, e['z']), 1.5, mat('Rage aura', hexlin('#ff3b30'), emit=2.5, alpha=.12), sub=3, squash=1.1)
        disc(B(e['x'], .03, e['z']), 1.9, mat('Rage ground', hexlin('#ff3b30'), emit=2, alpha=.35))
    if e['k'] == 'void':
        ball(B(e['x'], .4, e['z']), 1.2, mat('Void haze', hexlin('#6e28be'), emit=2.5, alpha=.18), sub=3)

world = finish(TILE, NAME)
export_sizes(world, HERE, NAME, 48)
if '--render' in sys.argv:
    render(sys.argv[sys.argv.index('--render') + 1], NAME, [('aerial', (0, -78, 52), (0, 0, 2), 30), ('ground', (-14, -26, 1.6), (4, 2, 7), 16)])
