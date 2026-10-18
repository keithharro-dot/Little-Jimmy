# The Saturn V moon rocket at full size, for walking around on a sports oval in AR.
#
#   python models/build_saturnv.py [--render <dir>]
#
# Writes models/saturn-v-<scene>.glb/.usdz (+ a 1:100 -mini copy) for three scenes:
#   both:     lying down like the one in the Apollo/Saturn V Center at Kennedy Space Center (stages pulled apart,
#             raised on cradles so you can walk underneath), with a second one standing upright beside its engines
#   lying:    just the lying-down one
#   standing: just the upright one
#
# Built from published dimensions, not a scan: 110.6 m tall, 10.1 m wide, about 19 m across the fins.
# Stage heights (from the bottom of the engines): S-IC 0-42.1 m, S-II 42.1-67.0, S-IVB 67.0-84.8, Instrument Unit
# 84.8-85.7, lunar module adapter 85.7-94.2, service module 94.2-98.1, command module 98.1-101.3, escape tower to 110.6.
# The paint follows the Apollo-era roll pattern only roughly; the KSC display's cradle height is an estimate.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arlib import *

HERE = os.path.dirname(os.path.abspath(__file__))
R1, R3, R5 = 5.03, 3.30, 1.96          # radius of S-IC/S-II, S-IVB/IU, service module
AXIS_H = 7.6                            # height of the lying rocket's centreline: about 2.5 m clear under the tanks
GAPS = (4.0, 4.0, 3.0)                  # lying display: gaps after S-IC, S-II and the Instrument Unit

COLOURS = dict(WHITE=('White', '#f1f1ec', .55, 0), BLACK=('Black', '#151515', .6, 0), ENGINE=('Engine', '#3b3a3a', .45, .6),
               ENGINE_IN=('Engine inside', '#0d0c0c', .9, 0), SILVER=('Service module', '#c4c8cc', .35, .7),
               RADIATOR=('Radiator', '#e6e8ea', .4, .3), CORK=('Adapter', '#e7e2d4', .7, 0), IU=('Instrument Unit', '#d4d5d0', .6, 0),
               TOWER=('Escape tower', '#b0352b', .6, 0), RED=('Flag red', '#b22234', .6, 0), BLUE=('Flag blue', '#3c3b6e', .6, 0),
               STEEL=('Cradle', '#6c7077', .7, .3))
def make_mats():
    """Fresh Blender, fresh materials (as module globals WHITE, BLACK, ...)."""
    MATS.clear(); META.clear(); bpy.ops.wm.read_factory_settings(use_empty=True)
    for k, (nm, hx, rough, metal) in COLOURS.items(): globals()[k] = mat(nm, hexlin(hx), rough=rough, metal=metal)

def mesh(name, verts, faces, mats, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    for m in dict.fromkeys(mats): me.materials.append(m)
    idx = {m: i for i, m in enumerate(dict.fromkeys(mats))}
    for p, m in zip(me.polygons, mats): p.material_index = idx[m]; p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

def lathe(prof, m, a0=0.0, a1=2 * math.pi, segs=64, pattern=None, cap0=False, cap1=False, cx=0.0, cy=0.0):
    """Surface of revolution round the Z axis through (cx, cy): prof = [(z, r), ...] bottom to top.
    pattern: list of materials, one per equal sector (the black-and-white roll pattern)."""
    n = max(2, round(segs * (a1 - a0) / (2 * math.pi)))
    if pattern: n = max(n, len(pattern) * 8) // len(pattern) * len(pattern)
    ang = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    V = [(cx + r * math.cos(a), cy + r * math.sin(a), z) for z, r in prof for a in ang]
    F, M = [], []
    for j in range(len(prof) - 1):
        for i in range(n):
            b = j * (n + 1) + i; t = b + n + 1
            F.append((b, b + 1, t + 1, t)); M.append(pattern[i * len(pattern) // n] if pattern else m)
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    if full and cap0 and prof[0][1] > 0: F.append(tuple(range(n - 1, -1, -1))); M.append(m)
    if full and cap1 and prof[-1][1] > 0: k = (len(prof) - 1) * (n + 1); F.append(tuple(range(k, k + n))); M.append(m)
    return mesh('lathe', V, F, M)

def box(c, size, m, rz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=(0, 0, rz))
    o = bpy.context.object; o.scale = size; o.data.materials.append(m); return o

def rod(a, b, r, m):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    o.data.materials.append(m); return o

def fin(theta, m):
    """A trapezoid fin standing out radially at angle theta: root on the engine fairing, tip ~9.4 m out."""
    prof = [(5.9, 4.2), (9.4, 4.2), (9.4, 6.0), (5.9, 9.6)]
    c, s, t = math.cos(theta), math.sin(theta), .16
    nx, ny = -s, c
    V = [(rr * c + k * nx, rr * s + k * ny, z) for k in (-t, t) for rr, z in prof]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh('fin', V, F, [m] * 6, smooth=False)

def letter(ch, theta, z, size, R, m):
    """One painted letter on the hull at angle theta, upright, its foot centred at height z."""
    bpy.ops.object.text_add(location=(0, 0, 0))
    o = bpy.context.object; o.data.body = ch; o.data.size = size; o.data.extrude = .015
    o.data.align_x = 'CENTER'; o.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object; o.data.materials.append(m)
    o.rotation_euler = (math.pi / 2, 0, theta + math.pi / 2)
    o.location = (R * math.cos(theta), R * math.sin(theta), z); return o

def flag(theta, zc, w, h, R):
    """The US flag painted on the hull, curved with it: 13 stripes, a blue canton and 50 stars."""
    da = w / R; a0, a1 = theta - da / 2, theta + da / 2; z0 = zc - h / 2; sh = h / 13
    ac = a0 + da * .4                                       # the canton covers the left 40%, top 7 stripes
    out = []
    for k in range(13):
        zz = z0 + k * sh; col = RED if (12 - k) % 2 == 0 else WHITE
        start = ac if k >= 6 else a0
        out.append(lathe([(zz, R), (zz + sh, R)], col, start, a1, segs=256))
    out.append(lathe([(z0 + 6 * sh, R), (z0 + h, R)], BLUE, a0, ac, segs=256))
    ch = h * 7 / 13; cw = ac - a0
    for row in range(9):
        cols = 6 if row % 2 == 0 else 5
        for col in range(cols):
            a = a0 + cw * ((col * 2 + (1 if row % 2 == 0 else 2)) / 12)
            zz = z0 + 6 * sh + ch * (row + 1) / 10
            st = .06 * h
            out.append(lathe([(zz - st / 2, R + .01), (zz + st / 2, R + .01)], WHITE, a - st / 2 / R, a + st / 2 / R, segs=512))
    return out

def roll(n=8):
    """Alternating sectors, offset so the lettering (at 90° and 270°) sits on white and the fins on black."""
    return [WHITE if i % 2 == 0 else BLACK for i in range(n)]

def rocket(gaps=(0, 0, 0)):
    """The whole stack along +Z, engine exits at z=0. gaps push the stages apart for the museum display.
    Returns the list of objects (so the caller can lay it down)."""
    objs = []; add = objs.append
    off = -math.pi / 8      # sector pattern offset (sectors centred on 0°, 45°, 90°...)
    # ---- S-IC first stage: 0 - 42.1 m ----
    for i, (x, y) in enumerate([(0, 0)] + [(4.0 * math.cos(a), 4.0 * math.sin(a)) for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]):
        add(lathe([(0, 1.88), (.9, 1.62), (2.2, 1.2), (3.2, .78), (3.3, .7), (4.25, .7)], ENGINE, cap0=False, cx=x, cy=y, segs=40))   # F-1 bell
        add(lathe([(.05, 1.84), (.06, 0)], ENGINE_IN, cx=x, cy=y, segs=40))                                                             # dark throat
    for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
        add(lathe([(4.2, 2.05), (7.5, 1.55), (12.0, .5), (12.6, .05)], WHITE, cx=4.3 * math.cos(a), cy=4.3 * math.sin(a), segs=40, cap0=True))  # engine fairing
        add(fin(a, WHITE))
    add(lathe([(4.2, R1), (9.0, R1)], WHITE, off, off + 2 * math.pi, pattern=roll(8), cap0=True))     # thrust structure
    add(lathe([(9.0, R1), (22.6, R1)], WHITE))                                                         # fuel (RP-1) tank
    add(lathe([(22.6, R1), (27.0, R1)], WHITE, off, off + 2 * math.pi, pattern=roll(8)))              # intertank
    add(lathe([(27.0, R1), (42.1, R1)], WHITE, cap1=True))                                            # oxygen tank + forward skirt
    for th in (math.pi / 2, 3 * math.pi / 2):
        objs += flag(th, 36.0, 4.9, 2.6, R1 + .02)
        for k, ch in enumerate('UNITED STATES'):
            if ch != ' ': add(letter(ch, th, 32.6 - k * 1.75, 1.5, R1 + .03, BLACK))
    # ---- S-II second stage (with the interstage it sits on): 42.1 - 67.0 m ----
    z = 42.1 + gaps[0]; s2 = []
    for x, y in [(0, 0)] + [(2.3 * math.cos(a), 2.3 * math.sin(a)) for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]:
        s2.append(lathe([(z + .6, 1.0), (z + 2.2, .55), (z + 3.6, .35), (z + 4.4, .35)], ENGINE, cx=x, cy=y, segs=32))   # J-2 bells
        s2.append(lathe([(z + .62, .97), (z + .63, 0)], ENGINE_IN, cx=x, cy=y, segs=32))
    s2.append(lathe([(z, R1 - .05), (z + 5.6, R1 - .05)], WHITE, segs=64))                       # inside of interstage
    s2.append(lathe([(z + 4.4, 0.01), (z + 4.4, R1 - .05)], ENGINE_IN))                           # thrust plate
    s2.append(lathe([(z, R1), (z + 24.9, R1)], WHITE, cap1=True))
    s2.append(lathe([(z, R1 - .05), (z + .01, R1)], WHITE))                                        # rim
    objs += s2
    # ---- S-IVB third stage: 67.0 - 84.8 m, Instrument Unit to 85.7 ----
    z = 67.0 + gaps[0] + gaps[1]
    add(lathe([(z, R1), (z + 5.0, R3)], WHITE, cap0=True))                                        # aft interstage (cone)
    add(lathe([(z + 5.0, R3), (z + 7.6, R3)], WHITE, off, off + 2 * math.pi, pattern=roll(8)))   # aft skirt roll pattern
    add(lathe([(z + 7.6, R3), (z + 17.8, R3)], WHITE))
    for a in (0, math.pi):                                                                         # the two thruster pods
        add(box((math.cos(a) * (R3 + .35), math.sin(a) * (R3 + .35), z + 8.4), (.7, 1.6, 1.8), WHITE, rz=a))
    add(lathe([(z + 17.8, R3), (z + 18.7, R3)], IU, cap1=True))                                   # Instrument Unit
    # ---- Spacecraft: adapter, service module, command module, escape tower: 85.7 - 110.6 m ----
    z = 85.7 + sum(gaps)
    add(lathe([(z, R3), (z + 8.5, R5)], CORK, cap0=True))                                        # lunar module adapter
    z += 8.5
    add(lathe([(z, R5), (z + 3.9, R5)], SILVER))                                                  # service module
    for a in (math.pi / 6, math.pi * 5 / 6, math.pi * 3 / 2):
        add(lathe([(z + .4, R5 + .01), (z + 3.4, R5 + .01)], RADIATOR, a - .35, a + .35, segs=96))
    add(lathe([(z + 3.9, R5), (z + 5.3, 1.25), (z + 6.6, .55), (z + 7.1, .35), (z + 7.12, .01)], WHITE))   # command module under its cover
    z += 7.1
    legs = [(math.cos(a) * .75, math.sin(a) * .75) for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]
    top = [(x * .45, y * .45) for x, y in legs]
    for (x0, y0), (x1, y1) in zip(legs, top): add(rod((x0, y0, z - .1), (x1, y1, z + 3.1), .07, TOWER))   # tower legs
    for k in range(4):                                                                             # cross bracing
        (x0, y0), (x1, y1) = legs[k], legs[(k + 1) % 4]; (u0, v0), (u1, v1) = top[k], top[(k + 1) % 4]
        add(rod((x0, y0, z), (u1, v1, z + 3.0), .05, TOWER)); add(rod((x1, y1, z), (u0, v0, z + 3.0), .05, TOWER))
        add(rod(((x0 + u0) / 2, (y0 + v0) / 2, z + 1.5), ((x1 + u1) / 2, (y1 + v1) / 2, z + 1.5), .05, TOWER))
    z += 3.1
    add(lathe([(z, .38), (z + 4.2, .33), (z + 4.25, .33)], WHITE, cap0=True, segs=32))              # escape motor
    add(lathe([(z + 4.25, .33), (z + 5.6, .16), (z + 5.62, .16)], BLACK, segs=32))                 # canard section / nose
    add(lathe([(z + 5.62, .16), (z + 5.8, .19), (z + 6.1, .1), (z + 6.2, .01)], BLACK, segs=32))  # Q-ball
    return objs

def place(objs, M):
    for o in objs: o.matrix_world = M @ o.matrix_world

def cradle(x, r):
    """A museum cradle under the lying rocket at distance x along it, for a section of radius r."""
    top = AXIS_H - r * .97
    box((x, 0, top / 2), (1.2, r * 1.3, top), STEEL)
    box((x, 0, top - .25), (1.4, r * 1.5, .5), STEEL)

LAY = Matrix.Translation((0, 0, AXIS_H)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')   # +Z (nose) -> +X, fins at 45°

def build(scene):
    make_mats()
    if scene in ('both', 'lying'):
        place(rocket(GAPS), LAY)
        g0, g1, g2 = GAPS
        for x, r in ((9, R1), (36, R1), (42.1 + g0 + 5, R1), (67.0 + g0 - 3, R1), (67.0 + g0 + g1 + 12, R3),
                     (85.7 + g0 + g1 + g2 + 5, R3 * .75)):
            cradle(x, r)
    if scene in ('both', 'standing'):
        objs = rocket()
        place(objs, Matrix.Translation((5.0, -26.0, 0)) if scene == 'both' else Matrix())   # beside the lying one's engines
    world = finish(1.0, 'Saturn V')
    lo, hi = [min(v.co[i] for v in world.data.vertices) for i in range(3)], [max(v.co[i] for v in world.data.vertices) for i in range(3)]
    world.data.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, 0)))   # centre it on the spot you stand
    return world

if __name__ == '__main__':
    args = sys.argv[1:]
    rdir = args[args.index('--render') + 1] if '--render' in args else None
    for sc in ('both', 'lying', 'standing'):
        world = build(sc)
        name = 'saturn-v-' + sc
        export_sizes(world, HERE, name, 100)
        if rdir:
            os.makedirs(rdir, exist_ok=True)
            render(rdir, name, [('walk', (-40, -60, 1.7), (40, 0, 20), 24), ('far', (-150, -170, 40), (40, 0, 30), 35)])
