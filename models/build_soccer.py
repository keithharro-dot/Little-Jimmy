# Pocket Soccer's BOSS ROUND with every chaos power going off, for augmented reality, life size for a sports oval.
#
#   python models/build_soccer.py [--render <dir>]
#
# models/soccer/boss.glb + .json come from the real game (models/soccer/export.mjs): a staged 4-a-side boss round
# with all ten powers on, frozen and exported with three.js. This adds the epic part — the homing rocket ball
# streaking overhead, a nuclear-ball mushroom cloud behind the red goal, the freeze ray, giant boss name signs,
# steam, sparks — scales it so 1 game unit = UNIT metres and writes models/soccer-boss.glb/.usdz (+ a -mini copy).
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arlib import *

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = 'soccer-boss'
UNIT = .5            # metres per game unit: the pitch is 50 x 80 m, about 66 x 115 m with the pipes and gears
TEAM = ['#3b82f6', '#ef4444']

GM = start(os.path.join(HERE, 'soccer', 'boss.glb'))
info = json.load(open(os.path.join(HERE, 'soccer', 'boss.json')))

# unlit textured materials (the faces on top of the players) become normal ones, so the iPhone file keeps them
for m in list(bpy.data.materials):
    nt = m.node_tree if m.use_nodes else None
    if not nt or nt.nodes.get('Principled BSDF'): continue
    tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if not tex: continue
    for n in list(nt.nodes):
        if n.name != tex.name: nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(tex.outputs['Color'], p.inputs['Base Color']); nt.links.new(tex.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = .6; p.inputs['Roughness'].default_value = .9
    nt.links.new(p.outputs['BSDF'], out.inputs['Surface'])
meshes = convert_materials(GM, ['#38bdf8', '#ff3b3b'], metal_keep=True)
X = fx_mats()
W = {w['id']: w for w in info['widgets']}

# 1. the homing rocket ball, blasting off the blue boss and arcing high over the pitch towards the red goal
bb = next(W[b['id']] for b in info['bosses'] if W[b['id']]['team'] == 0)
ball_obj = min((o for o in bpy.context.scene.objects if o.type == 'MESH' and 5 < o.dimensions.x < 8 and abs(o.dimensions.x - o.dimensions.z) < .5),
               key=lambda o: (o.matrix_world.translation - B(*info['ball']['p'])).length)
start_p, end_p, peak = B(bb['x'], 12, bb['z']), B(0, 6, -80), 42
arc = lambda q: start_p.lerp(end_p, q) + Vector((0, 0, math.sin(math.pi * q) * peak))
q0 = .52; head = arc(q0); dirv = (arc(q0 + .01) - head).normalized()
ball_obj.matrix_world = Matrix.Translation(head) @ Matrix.Diagonal((1.6, 1.6, 1.6, 1))   # a big flaming ball in the sky
cone(head - dirv * 2, -dirv, 3.2, 9, X['FLAME'])
ball(head - dirv * 4, 3.4, mat('Rocket fire', hexlin('#ffb23a'), emit=8, alpha=.75))
trail([arc(q0 - .025 * (i + 1)) for i in range(20)], 1.4, 5, X['TRAIL'])
for i in range(16):
    p = arc(q0 - rng.random() * .3)
    ball(p + Vector(((rng.random() - .5) * 6, (rng.random() - .5) * 6, (rng.random() - .5) * 6)), .5, mat('Spark', hexlin('#ffd23f'), emit=9), sub=1)
explosion(B(bb['x'], 0, bb['z'] - 14), 7)   # the launch blast at the boss's feet

# 2. the nuclear ball has gone off behind the red goal: a mushroom cloud towering over the gears
mushroom(B(0, 0, -100), 78)

# 3. the freeze ray: a crackling cyan beam from the red boss to a frozen blue player, ice shards all round
x1, z1, x2, z2 = info['zap']
a, b = B(x1, 7, z1), B(x2, 4, z2)
tube(a, b, .5, mat('Beam core', (1, 1, 1), emit=14)); tube(a, b, 1.3, mat('Freeze beam', hexlin('#67e8f9'), emit=9, alpha=.8)); tube(a, b, 3, mat('Freeze glow', hexlin('#67e8f9'), emit=4, alpha=.25))
ICE = mat('Ice shard', hexlin('#bfe9ff'), emit=2, alpha=.7, rough=.1)
for fid in info['frozen']:
    w = W[fid]
    for k in range(10):
        ang = rng.random() * 6.3; d = w['h'] * (1.1 + rng.random() * .5)
        chunk(B(w['x'] + math.cos(ang) * d, 1 + rng.random() * 9, w['z'] + math.sin(ang) * d), 1.2 + rng.random() * 1.2, ICE)

# 4. giant name signs floating over the two bosses
for b_ in info['bosses']:
    w = W[b_['id']]; col = hexlin(TEAM[w['team']])
    c = B(w['x'], 24, w['z']); m_ = mat('Sign', col, emit=3)
    t1 = text(b_['name'].upper(), c + Vector((0, -.9, 0)), 5, m_, face_y=-1, depth=.4)          # one face each way,
    text(b_['name'].upper(), c + Vector((0, .9, 0)), 5, m_, face_y=1, depth=.4)                 # with a dark board between
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); s_ = bpy.context.object
    s_.scale = (t1.dimensions.x + 4, 1.2, 7.5); s_.data.materials.append(mat('Sign board', hexlin('#1a120b'), rough=.6)); link(s_)
    disc(B(w['x'], .1, w['z']), w['h'] * 1.7, mat('Boss glow', col, emit=2, alpha=.3))

# 5. ghosts leave purple wisps, the steam vents puff, a cannon shot has just landed
for w in info['widgets']:
    if w['team'] == 1 and not w['gk'] and not w['boss']:
        for k in range(6): ball(B(w['x'] + (rng.random() - .5) * 8, 6 + k * 2.2, w['z'] + (rng.random() - .5) * 8), 1 + k * .25, mat('Ghost wisp', hexlin('#b57bff'), emit=3, alpha=.35), sub=1)
for vx, vz in ((-64, -60), (-64, 20), (64, -60), (64, 20)):
    trail([B(vx + (rng.random() - .5) * 2, 11 + i * 3.2, vz + (rng.random() - .5) * 2) for i in range(7)], 1.5, 4.5, mat('Steam', hexlin('#f2efe8'), alpha=.45, rough=1))
explosion(B(28, 0, 40), 6)

# (the game's own particles are left out here: soccer's are huge, soft sprites that turn into blobs as solid shapes)

world = finish(UNIT, NAME)
export_sizes(world, HERE, NAME, 55)
if '--render' in sys.argv:
    render(sys.argv[sys.argv.index('--render') + 1], NAME, [('aerial', (55, -95, 70), (0, 0, 6), 28), ('ground', (-22, -52, 1.6), (4, 0, 12), 16)])
