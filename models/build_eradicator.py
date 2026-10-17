# Builds the Eradicator MK II in Blender and exports it for augmented reality.
#   pip install bpy==5.2.2   (Blender as a Python module), then:
#   python models/build_eradicator.py
# Writes models/eradicator-mk2.glb (Android / web) and models/eradicator-mk2.usdz (iPhone / iPad AR Quick Look).
# The design matches mk2Tpl in tower-defence.html, with extra close-up detail. Original model, not a copy of TDX's.
import bpy, math, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))
SCALE = 1.3          # game units -> metres: about 2 m tall (antenna included), so it fits under a lounge-room ceiling
RENDER = '--render' in sys.argv

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- materials ----------
def mat(name, col, metal=.15, rough=.55, emit=None, strength=6.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    c = tuple(int(col[i:i + 2], 16)/255 for i in (1, 3, 5))
    c = tuple(x/12.92 if x <= .04045 else ((x + .055)/1.055)**2.4 for x in c) + (1,)
    p.inputs['Base Color'].default_value = c
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    if emit:
        p.inputs['Emission Color'].default_value = c
        p.inputs['Emission Strength'].default_value = strength
    return m

OLIVE  = mat('Olive paint', '#5a6e3a', .25, .5)
OLIVED = mat('Olive dark', '#3e4d29', .25, .55)
OLIVEL = mat('Olive light', '#7d9450', .25, .45)
STEEL  = mat('Steel', '#3a3d44', .8, .38)
STEELL = mat('Steel light', '#6a707b', .85, .3)
BLACK  = mat('Gunmetal', '#1c1e22', .7, .45)
HOLE   = mat('Bore', '#050506', 0, .9)
DECAL  = mat('Decal', '#d8dde6', 0, .6)
RED    = mat('Red eye', '#ff2a1a', 0, .3, emit=True, strength=8)
GREEN  = mat('Green light', '#8dff4a', 0, .3, emit=True, strength=5)
AMBER  = mat('Exhaust', '#ffb03a', 0, .3, emit=True, strength=6)
TIP    = mat('Missile tip', '#c8302a', .2, .4)

# ---------- helpers: every position is in game units (x forward, y up, z side), mapped to Blender (X=-z, Y=-x, Z=y) ----------
def G(x, y, z): return (-z, -x, y)

def finish(o, m, bevel):
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    for p in o.data.polygons: p.use_smooth = False
    return o

def box(w, h, d, m, x, y, z, ry=0, rx=0, rz=0, bevel=.008):
    """w along forward, h up, d sideways (same order as the game's box())"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=G(x, y, z))
    o = bpy.context.object; o.scale = (d, w, h)
    o.rotation_euler = (rz, -rx, ry)   # game rotations about z/x/y become Blender X/-Y/Z
    return finish(o, m, min(bevel, w/4, h/4, d/4))

def cylx(r, length, m, x, y, z, seg=12, bevel=.004):
    """cylinder whose axis points forward"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=length, location=G(x, y, z), rotation=(math.pi/2, 0, 0))
    return finish(bpy.context.object, m, min(bevel, r/4))

def cyly(r, h, m, x, y, z, seg=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=G(x, y, z))
    return finish(bpy.context.object, m, min(.004, r/4))

def discx(r, m, x, y, z, seg=12, back=False):
    bpy.ops.mesh.primitive_circle_add(vertices=seg, radius=r, fill_type='NGON', location=G(x, y, z), rotation=(math.pi/2 if not back else -math.pi/2, 0, 0))
    return finish(bpy.context.object, m, 0)

def cone(r, h, m, x, y, z, seg=10):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r, depth=h, location=G(x, y, z))
    return finish(bpy.context.object, m, 0)

def text(txt, size, x, y, z, side_y=0.0):
    bpy.ops.object.text_add(location=G(x, y, z), rotation=(math.pi/2, 0, side_y))
    o = bpy.context.object; o.data.body = txt; o.data.size = size; o.data.extrude = .002
    o.data.align_x = 'CENTER'; o.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object, DECAL, 0)

def hose(points, r, m):
    cu = bpy.data.curves.new('hose', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = G(*p); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new('hose', cu); scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object, m, 0)

# ---------- legs: stubby armoured legs, knee guards, pistons, big flat feet ----------
for s in (-1, 1):
    z = s*.17
    box(.22, .2, .2, STEEL, 0, .32, z)                      # thigh
    box(.03, .14, .16, OLIVEL, .12, .32, z)                  # thigh plate
    box(.24, .17, .23, OLIVE, .02, .15, z)                   # shin armour
    box(.03, .12, .03, OLIVEL, .15, .15, z - .05); box(.03, .12, .03, OLIVED, .15, .15, z + .05)
    box(.08, .09, .19, OLIVED, .15, .25, z, rz=-.25)         # knee guard
    cyly(.018, .2, STEELL, -.13, .25, z - .07); cyly(.026, .1, BLACK, -.13, .3, z - .07)   # rear piston
    box(.36, .07, .27, BLACK, .05, .035, z)                  # foot
    box(.1, .05, .25, STEELL, .2, .05, z)                    # toe cap
    for tz in (-.08, 0, .08): box(.06, .03, .05, BLACK, .245, .02, z + tz)   # toe claws
    box(.08, .06, .22, STEEL, -.14, .04, z)                  # heel

# ---------- hips ----------
box(.3, .16, .5, STEEL, 0, .45, 0)
box(.02, .1, .14, BLACK, .152, .45, .12, bevel=.004); text('02', .06, .163, .45, .12)
for s in (-1, 1): box(.12, .1, .06, OLIVED, .04, .45, s*.27)

T0 = .52   # torso base height
# ---------- chest: steel core with a grille, striped olive flanks ----------
box(.32, .34, .38, STEEL, 0, T0 + .2, 0)
box(.03, .16, .14, STEELL, .17, T0 + .16, 0)
for y in (.1, .13, .16, .19, .22): box(.012, .012, .11, BLACK, .188, T0 + y, 0, bevel=0)
box(.01, .05, .13, BLACK, .162, T0 + .3, -.13, bevel=.003); text('CM 02', .032, .168, T0 + .3, -.13)
for s in (-1, 1):
    box(.3, .22, .14, OLIVE, 0, T0 + .1, s*.26)
    for dz in (-.035, .035): box(.01, .2, .03, OLIVED if dz*s > 0 else OLIVEL, .155, T0 + .1, s*.26 + dz, bevel=.003)
    # tall shoulder blocks with recessed panels and rivets
    box(.34, .3, .22, OLIVE, -.02, T0 + .42, s*.3)
    box(.02, .18, .15, OLIVED, .155, T0 + .42, s*.3)
    box(.35, .03, .23, OLIVEL, -.02, T0 + .58, s*.3)
    for ry in (.34, .5):
        for rz in (-.08, .08): cylx(.008, .01, STEELL, .155, T0 + ry, s*.3 + rz, seg=8)

# ---------- missile box on the back, with missiles in the hatches ----------
box(.22, .3, .28, STEELL, -.17, T0 + .62, -.04)
box(.01, .3, .012, BLACK, -.055, T0 + .62, -.04, bevel=0); box(.01, .012, .28, BLACK, -.055, T0 + .62, -.04, bevel=0)
for dx in (-.21, -.13):
    for dz in (-.1, .02):
        box(.06, .01, .08, HOLE, dx, T0 + .775, dz, bevel=0)
        for mz in (-.02, .02):
            cyly(.012, .04, STEELL, dx, T0 + .79, dz + mz, seg=8); cone(.012, .03, TIP, dx, T0 + .825, dz + mz, seg=8)
cyly(.006, .3, BLACK, -.25, T0 + .9, .1, seg=6); cyly(.012, .02, RED, -.25, T0 + 1.05, .1, seg=8)   # antenna

# tube cluster on one shoulder, warning light on the other
for z in (-.25, -.31, -.37):
    cylx(.025, .1, BLACK, .02, T0 + .63, z, seg=8); discx(.018, HOLE, .071, T0 + .63, z, seg=8)
cyly(.03, .04, RED, .04, T0 + .62, .34)

# ---------- head: small, angled, sunk between the shoulders; green crest light, one red eye ----------
box(.18, .15, .17, STEEL, .1, T0 + .4, 0)
for s in (-1, 1): box(.03, .12, .1, STEELL, .2, T0 + .41, s*.04, ry=s*.55)
box(.08, .06, .1, STEELL, .16, T0 + .31, 0)
for vz in (-.025, 0, .025): box(.01, .04, .008, BLACK, .2, T0 + .31, vz, bevel=0)   # jaw vents
box(.12, .022, .15, GREEN, .09, T0 + .485, 0, bevel=0)
cylx(.05, .02, BLACK, .215, T0 + .43, -.06, seg=16)       # eye housing
bpy.ops.mesh.primitive_uv_sphere_add(radius=.04, segments=16, ring_count=10, location=G(.225, T0 + .43, -.06))
finish(bpy.context.object, RED, 0)

# ---------- exhausts on the back ----------
for z in (-.08, .08):
    cylx(.045, .06, BLACK, -.18, T0 + .22, z); discx(.035, AMBER, -.212, T0 + .22, z, back=True)

# ---------- arms with rocket pods: one on each shoulder, one on each forearm ----------
def pod(x, y, z, r):
    cylx(r, .26, BLACK, x, y, z, seg=8)
    cylx(r*1.06, .05, OLIVED, x - .1, y, z, seg=8)
    cylx(r*1.04, .03, STEEL, x + .11, y, z, seg=8)
    for i in range(8):   # rim bolts
        a = i*math.pi/4 + math.pi/8
        cylx(.008, .012, STEELL, x + .126, y + math.cos(a)*r*.93, z + math.sin(a)*r*.93, seg=6)
    for i in range(6):   # six hexagonal barrels
        a = i*math.pi/3; py, pz = math.cos(a)*r*.56, math.sin(a)*r*.56
        cylx(r*.24, .05, STEELL, x + .145, y + py, z + pz, seg=6)
        discx(r*.16, HOLE, x + .171, y + py, z + pz, seg=6)
    cylx(r*.14, .04, STEEL, x + .14, y, z, seg=8)        # hub

for s in (-1, 1):
    box(.12, .34, .12, BLACK, .02, T0 + .25, s*.44)           # arm
    cyly(.04, .06, STEELL, .02, T0 + .42, s*.44)              # shoulder joint
    pod(.06, T0 + .44, s*.5, .14)
    pod(.14, T0 + .08, s*.46, .13)
    hose([(-.05, T0 + .3, s*.2), (-.12, T0 + .2, s*.35), (-.04, T0 + .1, s*.46)], .014, BLACK)   # feed hoses

# ---------- scale to metres and tidy up ----------
for o in scene.objects: o.select_set(True)
bpy.context.view_layer.objects.active = scene.objects[0]
bpy.ops.object.convert(target='MESH')   # bakes the bevels in, since join keeps only the active object's modifiers
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.object.join()
rig = bpy.context.object; rig.name = 'Eradicator MK II'
scene.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')   # scale about the floor, not the first part
rig.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
low = min(v.co.z for v in rig.data.vertices)
for v in rig.data.vertices: v.co.z -= low   # feet exactly on the floor, so AR doesn't float or sink it
print('triangles', sum(len(p.vertices) - 2 for p in rig.data.polygons), 'height m', round(rig.dimensions.z, 2))

bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'eradicator-mk2.glb'), export_format='GLB', export_apply=True)
bpy.ops.wm.usd_export(filepath=os.path.join(OUT, 'eradicator-mk2.usdz'), export_materials=True,
                      convert_orientation=True, export_global_forward_selection='NEGATIVE_Z', export_global_up_selection='Y')   # Apple's Y-up convention

if RENDER:   # preview stills
    bpy.ops.object.light_add(type='SUN', rotation=(.9, .2, -.6)); bpy.context.object.data.energy = 3.5
    world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.55, .6, .68, 1); world.node_tree.nodes['Background'].inputs['Strength'].default_value = .9
    bpy.ops.mesh.primitive_plane_add(size=20); finish(bpy.context.object, mat('Floor', '#b8bcc2', 0, .8), 0)
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 48; scene.cycles.device = 'CPU'
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.view_settings.view_transform = 'AgX'
    bpy.ops.object.camera_add(); cam = bpy.context.object; scene.camera = cam; cam.data.lens = 50
    for name, loc, look in (('front', (1.6, -4.4, 1.6), (0, 0, 1.05)), ('back', (-2.6, 3.6, 2.4), (0, 0, 1.05)), ('pod', (1.6, -1.6, 1.5), (.75, -.2, 1.1))):
        cam.location = loc
        d = [l - c for l, c in zip(look, loc)]
        cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi/2)
        scene.render.filepath = os.path.join(sys.argv[sys.argv.index('--render') + 1], 'mk2-' + name + '.png')
        bpy.ops.render.render(write_still=True)
