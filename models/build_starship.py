# SpaceX Starship at full size on its launch pad, fuelled and ready to go, for walking under and around in AR.
#
#   python models/build_starship.py [--render <dir>]
#
# Writes models/<scene>.glb/.usdz (+ a 1:100 -mini copy) for two scenes:
#   starship:          the full Starship V3 stack (124.4 m) on an orbital launch mount beside the launch tower
#   starship-saturn-v: the same, with a standing Saturn V (from build_saturnv.py) alongside for comparison
#
# Built from published figures, not plans: Super Heavy V3 about 72.3 m with 33 Raptor engines and three grid fins,
# Starship (the upper stage) about 52.1 m, both 9 m wide. The pad follows Starbase's first pad: the rocket sits on a
# ring held about 20 m up on six legs, so you can walk underneath and look up at the engines. (The V3 flights use the
# newer Pad 2, which has a flame trench instead.) The tower, its "chopsticks" and the vapour are approximations.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_saturnv as sv
from arlib import *
from build_saturnv import lathe, box, rod, mesh, place

HERE = os.path.dirname(os.path.abspath(__file__))
R = 4.5                  # Starship and Super Heavy radius
B0 = 20.5                # height of the launch ring's top, where the booster's skirt sits
BOOST, SHIP = 72.3, 52.1
TOWER_X, TOWER_W, TOWER_H = 24.0, 11.0, 137.0

def mats():
    global STEEL, FROST, DARK, TILE, ENGINE, ENGINE_IN, CONCRETE, PADSTEEL, TRUSS, ARM, VAPOUR, VAPOUR2
    sv.make_mats()
    STEEL = mat('Stainless', hexlin('#b9bec4'), rough=.3, metal=.85)
    FROST = mat('Frost', hexlin('#eef3f6'), rough=.95)
    DARK = mat('Hot stage ring', hexlin('#2a2a2c'), rough=.6, metal=.4)
    TILE = mat('Heat tiles', hexlin('#161616'), rough=.8)
    ENGINE = mat('Raptor', hexlin('#5a5550'), rough=.4, metal=.7)
    ENGINE_IN = mat('Raptor inside', hexlin('#0d0c0c'), rough=.9)
    CONCRETE = mat('Concrete', hexlin('#a7a49c'), rough=1)
    PADSTEEL = mat('Launch mount', hexlin('#8e9196'), rough=.6, metal=.4)
    TRUSS = mat('Tower', hexlin('#4b4e53'), rough=.6, metal=.4)
    ARM = mat('Chopsticks', hexlin('#d9dadb'), rough=.5, metal=.3)
    VAPOUR = mat('Vapour', hexlin('#f4f6f8'), alpha=.35, rough=1)
    VAPOUR2 = mat('Vapour thin', hexlin('#f4f6f8'), alpha=.18, rough=1)

def plate(theta, prof, m, t=.2):
    """A flat fin/flap standing out radially at angle theta: prof = [(radius, z), ...] round its outline."""
    c, s = math.cos(theta), math.sin(theta); nx, ny = -s, c; n = len(prof)
    V = [(r * c + k * nx, r * s + k * ny, z) for k in (-t, t) for r, z in prof]
    F = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh('plate', V, F, [m] * len(F), smooth=False)

def grid_fin(theta, z):
    """A big grid fin sticking straight out from the booster, its lattice open to the flow along the rocket."""
    c, s = math.cos(theta), math.sin(theta); out = []
    W, L = 4.6, 3.6
    def at(u, v):   # u along the radius from the hull, v sideways
        return Vector((c * (R + u) - s * v, s * (R + u) + c * v, z))
    for u in (0, L): out.append(rod(at(u, -W / 2), at(u, W / 2), .12, DARK))
    for v in (-W / 2, W / 2): out.append(rod(at(0, v), at(L, v), .12, DARK))
    for k in range(1, 7): v = -W / 2 + W * k / 7; out.append(rod(at(0, v), at(L, v), .04, DARK))
    for k in range(1, 6): u = L * k / 6; out.append(rod(at(u, -W / 2), at(u, W / 2), .04, DARK))
    out.append(box(at(-.2, 0), (1.0, 1.6, 1.4), DARK, rz=theta))   # actuator housing
    return out

def raptors(z_exit, rings, r_exit, length):
    out = []
    for n, rr, a0 in rings:
        for k in range(n):
            a = a0 + 2 * math.pi * k / n; x, y = rr * math.cos(a), rr * math.sin(a)
            out.append(lathe([(z_exit, r_exit), (z_exit + length * .45, r_exit * .7), (z_exit + length * .8, r_exit * .42), (z_exit + length, r_exit * .42)], ENGINE, cx=x, cy=y, segs=24))
            out.append(lathe([(z_exit + .05, r_exit * .97), (z_exit + .06, 0)], ENGINE_IN, cx=x, cy=y, segs=24))
    return out

def starship():
    """The full stack on its launch mount, engines at the origin's axis, booster skirt at height B0."""
    objs = []; add = objs.append
    # ---- Super Heavy booster ----
    z = B0
    objs += raptors(z + .3, [(3, .9, math.pi / 2), (10, 2.45, 0), (20, 3.85, math.pi / 20)], .64, 2.6)
    add(lathe([(z + .2, R - .05), (z + 3.2, R - .05)], ENGINE_IN))                  # inside of the skirt
    add(lathe([(z + 3.0, .01), (z + 3.0, R - .05)], ENGINE_IN))                     # engine bay ceiling
    add(lathe([(z, R), (z + 6, R)], STEEL))                                         # aft skirt
    add(lathe([(z, R - .05), (z + .01, R)], STEEL))
    add(lathe([(z + 6, R), (z + 38, R)], FROST))                                    # liquid oxygen tank, frosted
    add(lathe([(z + 38, R), (z + 39.2, R)], STEEL))                                 # common dome
    add(lathe([(z + 39.2, R), (z + 64, R)], FROST))                                 # methane tank, frosted
    add(lathe([(z + 64, R), (z + 70.5, R)], STEEL))                                 # forward section
    for k in range(3): objs += grid_fin(math.pi / 2 + 2 * math.pi * k / 3, z + 67.0)
    add(lathe([(z + 70.5, R), (z + BOOST, R)], STEEL, 0, 2 * math.pi, pattern=[DARK, STEEL] * 24))   # hot-staging ring vents
    # ---- Starship (the ship) ----
    z = B0 + BOOST
    wind0, wind1 = math.pi / 2, 3 * math.pi / 2                                    # heat tiles on the half away from the tower
    add(lathe([(z, R), (z + 24, R)], TILE, wind0, wind1, segs=96))
    add(lathe([(z, R), (z + 3, R)], STEEL, wind1, wind1 + math.pi, segs=96))
    add(lathe([(z + 3, R), (z + 24, R)], FROST, wind1, wind1 + math.pi, segs=96))  # ship tanks, frosted
    add(lathe([(z + 24, R), (z + 34, R)], TILE, wind0, wind1, segs=96))
    add(lathe([(z + 24, R), (z + 34, R)], STEEL, wind1, wind1 + math.pi, segs=96))  # payload bay
    nose = [(z + 34 + 18.1 * t, R * math.cos(t * math.pi / 2) ** .75) for t in [i / 14 for i in range(15)]]
    nose[-1] = (nose[-1][0], .05)
    add(lathe(nose, TILE, wind0, wind1, segs=96))
    add(lathe(nose, STEEL, wind1, wind1 + math.pi, segs=96))
    add(lathe([(z + .4, .01), (z + .4, R - .05)], ENGINE_IN))
    objs += raptors(z - .1, [(3, 1.0, math.pi / 2)], .65, 2.4)                       # sea-level Raptors
    objs += raptors(z - .1, [(3, 3.0, -math.pi / 2)], 1.15, 3.2)                     # vacuum Raptors
    for a in (math.pi - .75, math.pi + .75):                               # flaps on the tiled side
        add(plate(a, [(R - .2, z + 1.0), (R + 3.4, z + 1.6), (R + 3.4, z + 9.0), (R - .2, z + 12.0)], TILE, .25))
        add(plate(a, [(R * .55, z + 40.0), (R * .55 + 2.6, z + 41.0), (R * .4 + 2.6, z + 46.5), (R * .35, z + 47.5)], TILE, .2))
    return objs

def pad():
    """Concrete apron, the orbital launch mount (a ring on six legs) and the launch tower with its chopsticks."""
    objs = []; add = objs.append
    add(lathe([(0, 36), (.08, 36)], CONCRETE, cap1=True, segs=96))
    add(lathe([(.08, 9), (.6, 9)], PADSTEEL, cap1=True))                            # water-cooled steel plate
    ri, ro, t = 5.4, 9.0, 3.4                                                        # the launch ring
    add(lathe([(B0 - t, ro), (B0, ro)], PADSTEEL, segs=64))
    add(lathe([(B0 - t, ri), (B0, ri)], PADSTEEL, segs=64))
    add(mesh('ring', *_annulus(B0, ri, ro, up=True), smooth=False))
    add(mesh('ring', *_annulus(B0 - t, ri, ro, up=False), smooth=False))
    for k in range(6):                                                               # the six legs
        a = math.pi / 6 + k * math.pi / 3
        add(box((math.cos(a) * 9.6, math.sin(a) * 9.6, (B0 - t) / 2), (3.2, 3.2, B0 - t), CONCRETE, rz=a))
        add(box((math.cos(a) * 8.6, math.sin(a) * 8.6, B0 - t - .6), (4.5, 3.6, 1.2), PADSTEEL, rz=a))
    for k in range(20):                                                              # hold-down clamps
        a = 2 * math.pi * k / 20
        add(box((math.cos(a) * (R + .3), math.sin(a) * (R + .3), B0 + .5), (.7, .5, 1.0), PADSTEEL, rz=a))
    # tower: four corner columns, beams every 8 m and crossed bracing on each face
    tx, w = TOWER_X, TOWER_W / 2
    corners = [(tx - w, -w), (tx + w, -w), (tx + w, w), (tx - w, w)]
    for x, y in corners: add(box((x, y, TOWER_H / 2), (1.3, 1.3, TOWER_H), TRUSS))
    zs = [z for z in range(0, int(TOWER_H) + 1, 8)]
    for j in range(len(zs)):
        for k in range(4):
            (x0, y0), (x1, y1) = corners[k], corners[(k + 1) % 4]
            add(rod((x0, y0, zs[j]), (x1, y1, zs[j]), .3, TRUSS))
            if j + 1 < len(zs):
                add(rod((x0, y0, zs[j]), (x1, y1, zs[j + 1]), .18, TRUSS)); add(rod((x1, y1, zs[j]), (x0, y0, zs[j + 1]), .18, TRUSS))
    add(box((tx, 0, TOWER_H + 1), (TOWER_W + 1.5, TOWER_W + 1.5, 2), TRUSS))
    add(rod((tx, 0, TOWER_H + 2), (tx, 0, TOWER_H + 9), .25, TRUSS))                 # lightning rod
    # the chopsticks, open either side of the rocket, on their carriage
    zc = B0 + 64
    add(box((tx, 0, zc), (TOWER_W + 3, TOWER_W + 3, 7), ARM))
    for sgn in (-1, 1):
        a = math.pi - sgn * .52; p0 = Vector((tx - w - 1.5, sgn * 4.5, zc))
        d = Vector((math.cos(a), math.sin(a), 0)); L = 34
        o = box(p0 + d * L / 2, (L, 1.6, 4.0), ARM, rz=a); add(o)
        add(box(p0 + d * (L - 1), (2.2, 2.4, 1.0), DARK, rz=a))                       # catch rail end
    # ship quick-disconnect arm reaching across to the ship, and the booster's at the mount
    zq = B0 + BOOST + 8
    add(box(((tx - w + R) / 2, 0, zq), (tx - w - R, 2.4, 3.2), ARM))
    add(box((R + 2.2, 0, B0 + 1.4), (4.0, 2.0, 2.4), PADSTEEL))
    return objs

def _annulus(z, ri, ro, up, n=64):
    V = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z) for r in (ri, ro) for i in range(n)]
    F = [((i + 1) % n, i, n + i, n + (i + 1) % n) if up else (i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return V, F, [PADSTEEL] * n

def vapour():
    """Fully fuelled: boil-off venting from the booster and ship, and a cold fog spilling off the frost."""
    rng.seed(3); out = []
    for z, n, r, spread in ((B0 + 70.8, 10, 1.6, 6.0), (B0 + BOOST + 21, 6, 1.3, 5.6), (B0 + 3, 12, 2.2, 7.0)):
        for k in range(n):
            a = 2 * math.pi * k / n + rng.random() * .4; d = spread + rng.random() * 1.5
            out.append(ball(Vector((math.cos(a) * d, math.sin(a) * d, z + rng.random() * 2)), r + rng.random() * .8, VAPOUR if k % 2 else VAPOUR2, sub=2))
    for k in range(14):   # fog rolling down off the tanks onto the mount
        a = rng.random() * 2 * math.pi; z = B0 + 8 + rng.random() * 50
        out.append(ball(Vector((math.cos(a) * (R + .8), math.sin(a) * (R + .8), z)), 1.0 + rng.random() * .8, VAPOUR2, sub=2))
    return out

def build(scene):
    mats()
    starship(); pad(); vapour()
    if scene == 'starship-saturn-v':
        place(sv.rocket(), Matrix.Translation((-52.0, 0, 0)))
    world = finish(1.0, 'Starship')
    lo = [min(v.co[i] for v in world.data.vertices) for i in range(2)]; hi = [max(v.co[i] for v in world.data.vertices) for i in range(2)]
    world.data.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, 0)))
    return world

if __name__ == '__main__':
    args = sys.argv[1:]
    rdir = args[args.index('--render') + 1] if '--render' in args else None
    for sc in ('starship', 'starship-saturn-v'):
        world = build(sc)
        export_sizes(world, HERE, sc, 100)
        if rdir:
            os.makedirs(rdir, exist_ok=True)
            render(rdir, sc, [('under', (-14, -16, 1.7), (0, 0, 30), 18), ('far', (-150, -190, 30), (0, 0, 60), 30)])
