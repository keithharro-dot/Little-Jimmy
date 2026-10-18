# Builds the Eradicator MK IV in Blender and exports it for augmented reality and previews.
#   pip install bpy==5.2.2   (Blender as a Python module), then:
#   python models/build_eradicator_mk4.py [--render <dir>]
# Writes models/eradicator-mk4.glb (Android / web) and models/eradicator-mk4.usdz (iPhone / iPad AR Quick Look).
# The design matches mk4Tpl in tower-defence.html, with extra close-up detail. It is our own next model in the game's
# Eradicator line, in the spirit of TDX-style mechs, not a copy of TDX's MK IV: a tall humanoid war-suit with a shoulder
# artillery cannon, angular shoulder guards, two ordinary armoured arms with hands, and armoured boots.
import bpy, math, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))
SCALE = 1.35         # game units -> metres: about 2.2 m tall with the cannon raised
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

GUN    = mat('Gunmetal plate', '#2b2e33', .6, .5)
GUND   = mat('Gunmetal dark', '#1a1c20', .6, .55)
GUNL   = mat('Gunmetal light', '#4a4f57', .65, .4)
OLIVE  = mat('Olive panel', '#4f6436', .25, .5)
OLIVED = mat('Olive dark', '#36472a', .25, .55)
OLIVEL = mat('Olive light', '#728a49', .25, .45)
STEEL  = mat('Steel', '#6a707b', .85, .3)
BLACK  = mat('Rubber', '#111214', .2, .8)
HOLE   = mat('Bore', '#050506', 0, .9)
DECAL  = mat('Decal', '#d8dde6', 0, .6)
RED    = mat('Red eye', '#ff2a1a', 0, .3, emit=True, strength=8)
WHITE  = mat('Crest light', '#f4f7ff', 0, .3, emit=True, strength=5)
ORANGE = mat('Muzzle cap', '#ff7a2a', .1, .4, emit=True, strength=2)
AMBER  = mat('Exhaust', '#ffb03a', 0, .3, emit=True, strength=6)

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

def cylx(r, length, m, x, y, z, seg=12, bevel=.004, tilt=0):
    """cylinder whose axis points forward (tilt: raised nose, radians)"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=length, location=G(x, y, z), rotation=(math.pi/2 + tilt, 0, 0))
    return finish(bpy.context.object, m, min(bevel, r/4))

def cyly(r, h, m, x, y, z, seg=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=G(x, y, z))
    return finish(bpy.context.object, m, min(.004, r/4))

def cylz(r, length, m, x, y, z, seg=12):
    """cylinder whose axis points sideways"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=length, location=G(x, y, z), rotation=(0, math.pi/2, 0))
    return finish(bpy.context.object, m, min(.004, r/4))

def discx(r, m, x, y, z, seg=12, back=False, tilt=0):
    bpy.ops.mesh.primitive_circle_add(vertices=seg, radius=r, fill_type='NGON', location=G(x, y, z), rotation=((math.pi/2 if not back else -math.pi/2) + tilt, 0, 0))
    return finish(bpy.context.object, m, 0)

def text(txt, size, x, y, z, side_y=0.0):
    bpy.ops.object.text_add(location=G(x, y, z), rotation=(math.pi/2, 0, side_y))
    o = bpy.context.object; o.data.body = txt; o.data.size = size; o.data.extrude = .002
    o.data.align_x = 'CENTER'; o.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object, DECAL, 0)

def xpanel(x, y, z, w, h, ry=0):
    """a recessed square plate with a cross brace, the MK IV's panel motif (on a side face at x)"""
    box(.012, h, w, GUND, x, y, z, ry=ry, bevel=.003)
    L = math.hypot(w, h)*.92
    for a in (math.atan2(h, w), -math.atan2(h, w)):
        box(.008, .014, L, GUNL, x + .008, y, z, ry=ry, rx=a, bevel=0)

# ---------- legs: thigh, knee guard, shin armour, armoured boots with toe plates ----------
for s in (-1, 1):
    z = s*.17
    box(.22, .22, .2, GUN, 0, .5, z)                             # thigh
    box(.03, .16, .16, OLIVE, .12, .5, z); xpanel(.136, .5, z, .1, .1)
    box(.1, .1, .2, OLIVED, .13, .36, z, rz=-.3)                 # knee guard
    box(.2, .22, .18, GUN, 0, .25, z)                            # shin
    box(.24, .16, .22, OLIVE, .01, .22, z)
    box(.012, .14, .04, OLIVEL, .13, .22, z + s*.06, bevel=.003)
    cyly(.018, .2, STEEL, -.12, .3, z - s*.05); cyly(.028, .08, GUND, -.12, .38, z - s*.05)   # rear piston
    box(.36, .1, .24, GUND, .05, .05, z, bevel=.015)             # boot
    box(.12, .06, .22, GUNL, .22, .07, z)                        # toe plate
    for tz in (-.07, 0, .07): box(.06, .03, .04, GUNL, .27, .02, z + tz)
    box(.08, .07, .2, GUN, -.13, .04, z)                         # heel

# ---------- hips ----------
box(.3, .16, .5, GUN, 0, .64, 0)
box(.02, .1, .14, GUND, .152, .64, .12, bevel=.004); text('04', .06, .163, .64, .12)
for s in (-1, 1): box(.12, .1, .06, OLIVED, .04, .64, s*.27)

T0 = .72   # torso base height
# ---------- chest: upright gunmetal block, olive belly plate, white crest light over the head ----------
box(.34, .4, .42, GUN, 0, T0 + .22, 0, rz=.05)
box(.03, .18, .2, OLIVE, .21, T0 + .14, 0)
xpanel(.236, T0 + .14, 0, .14, .12)
for y in (.3, .34): box(.012, .012, .3, GUND, .2, T0 + y, 0, bevel=0)
for s in (-1, 1):
    box(.3, .2, .12, OLIVE, .02, T0 + .1, s*.28)                  # olive flanks
    box(.012, .18, .04, OLIVEL if s > 0 else OLIVED, .17, T0 + .1, s*.28, bevel=.003)
    # big angular shoulder guards, stepped, each with an X panel
    box(.36, .3, .26, GUN, -.04, T0 + .44, s*.34)
    box(.3, .08, .28, GUNL, -.04, T0 + .62, s*.34)
    box(.2, .06, .3, GUND, -.02, T0 + .68, s*.34, rz=s*.2)
    xpanel(.145, T0 + .44, s*.34, .18, .16)             # on the front face
    xpanel(.0, T0 + .44, s*.47, .22, .18, ry=s*math.pi/2)   # on the outer face

# ---------- back: reactor housing with two exhausts, a rack of shells for the cannon ----------
box(.18, .3, .36, GUNL, -.2, T0 + .4, 0)
for z in (-.1, .1):
    cylx(.05, .06, GUND, -.26, T0 + .3, z); discx(.04, AMBER, -.295, T0 + .3, z, back=True)
for i, z in enumerate((-.12, -.04, .04, .12)):
    cyly(.025, .16, STEEL, -.2, T0 + .62, z, seg=10); cyly(.027, .03, ORANGE, -.2, T0 + .71, z, seg=10)   # shells, orange caps up
cyly(.006, .32, GUND, -.26, T0 + .9, -.16, seg=6); cyly(.012, .02, RED, -.26, T0 + 1.06, -.16, seg=8)   # antenna

# ---------- head: wide visor slot with twin red eyes, white crest light, armoured brow ----------
box(.2, .16, .2, GUN, .14, T0 + .4, 0)
box(.22, .05, .22, GUNL, .14, T0 + .5, 0)                        # brow
box(.14, .024, .16, WHITE, .12, T0 + .535, 0, bevel=0)           # crest light
box(.03, .05, .18, GUND, .245, T0 + .42, 0, bevel=.003)          # visor slot
for s in (-1, 1):
    cylx(.028, .02, GUND, .255, T0 + .42, s*.055, seg=12)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.026, segments=14, ring_count=8, location=G(.262, T0 + .42, s*.055))
    finish(bpy.context.object, RED, 0)
box(.08, .06, .12, GUNL, .2, T0 + .32, 0)
for vz in (-.03, 0, .03): box(.01, .04, .008, GUND, .242, T0 + .32, vz, bevel=0)   # jaw vents

# ---------- right shoulder: the artillery cannon, angled up over the shoulder ----------
TILT = .5   # radians nose-up
CX, CY, CZ = -.1, T0 + .66, .4
cyly(.07, .1, GUND, CX, CY - .05, CZ, seg=12)                    # mount
box(.22, .18, .2, GUN, CX, CY + .02, CZ)                         # breech block
xpanel(.11, CY + .02, CZ, .12, .1)
box(.1, .14, .1, GUND, CX - .16, CY + .06, CZ, rz=.2)            # recoil buffer
box(.08, .12, .16, OLIVE, CX - .1, CY - .1, CZ, bevel=.004)      # magazine, with shell tips showing
for mz in (-.04, 0, .04): cyly(.014, .04, ORANGE, CX - .1, CY - .17, CZ + mz, seg=8)
def along(d): return (CX + math.cos(TILT)*d, CY + math.sin(TILT)*d, CZ)
for d, r, L, m in ((.3, .062, .3, GUN), (.56, .05, .3, GUND), (.78, .045, .2, GUN)):
    cylx(r, L, m, *along(d), seg=14, tilt=-TILT)
for d in (.42, .7): cylx(.07, .03, GUNL, *along(d), seg=14, tilt=-TILT)   # barrel bands
cylx(.075, .1, GUN, *along(.92), seg=14, tilt=-TILT)             # muzzle brake
for i in range(4):   # brake vents round the muzzle
    a = i*math.pi/2 + math.pi/4
    vx, vy, vz = along(.92)
    box(.05, .014, .014, HOLE, vx - math.sin(TILT)*math.cos(a)*.07, vy + math.cos(TILT)*math.cos(a)*.07, vz + math.sin(a)*.07, rz=TILT, bevel=0)
discx(.05, HOLE, *along(.975), seg=14, tilt=-TILT)
cylx(.06, .02, ORANGE, *along(.97), seg=14, tilt=-TILT)          # orange muzzle ring

# ---------- arms: ordinary armoured arms with hands, hanging at the sides, the right one slightly raised to brace the cannon ----------
def arm(sd, bend):
    z = sd*.46
    cyly(.05, .06, STEEL, 0, T0 + .5, z)                         # shoulder joint
    box(.13, .3, .13, GUND, 0, T0 + .32, z)                      # upper arm
    box(.03, .18, .11, OLIVE, .07, T0 + .32, z); xpanel(.086, T0 + .32, z, .08, .1)
    cylz(.05, .14, GUN, .02, T0 + .16, z, seg=10)                # elbow
    fx, fy = .04 + bend*.14, T0 + .02 - bend*.04                 # forearm angles forward when bent
    box(.12, .26, .12, GUND, fx, fy, z, rz=bend*.9)
    box(.14, .1, .14, OLIVED, fx + bend*.1, fy - .12 + bend*.03, z, rz=bend*.9)   # wrist guard
    hx, hy = fx + bend*.14, fy - .2 + bend*.05
    box(.1, .1, .11, GUN, hx, hy, z)                             # palm
    for i, fz in enumerate((-.04, -.013, .013, .04)):           # four fingers, curled
        box(.05, .035, .022, GUND, hx + .06, hy - .02, z + fz); box(.03, .035, .022, GUND, hx + .09, hy - .045, z + fz)
    box(.03, .03, .045, GUND, hx + .04, hy + .01, z - sd*.07)   # thumb
arm(-1, .15)
arm(1, .55)

# ---------- scale to metres and tidy up ----------
for o in list(scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
for o in scene.objects: o.select_set(True)
bpy.context.view_layer.objects.active = scene.objects[0]
bpy.ops.object.convert(target='MESH')   # bakes the bevels in, since join keeps only the active object's modifiers
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.object.join()
rig = bpy.context.object; rig.name = 'Eradicator MK IV'
scene.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')   # scale about the floor, not the first part
rig.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
low = min(v.co.z for v in rig.data.vertices)
for v in rig.data.vertices: v.co.z -= low   # feet exactly on the floor, so AR doesn't float or sink it
print('triangles', sum(len(p.vertices) - 2 for p in rig.data.polygons), 'height m', round(rig.dimensions.z, 2))

bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'eradicator-mk4.glb'), export_format='GLB', export_apply=True)
bpy.ops.wm.usd_export(filepath=os.path.join(OUT, 'eradicator-mk4.usdz'), export_materials=True,
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
    for name, loc, look in (('front', (1.8, -4.6, 1.7), (0, 0, 1.1)), ('side', (-4.6, -1.4, 1.9), (0, 0, 1.1)), ('back', (-2.8, 3.8, 2.5), (0, 0, 1.1)), ('hand', (2.0, -1.6, 1.0), (.3, -.3, .9))):
        cam.location = loc
        d = [l - c for l, c in zip(look, loc)]
        cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi/2)
        scene.render.filepath = os.path.join(sys.argv[sys.argv.index('--render') + 1], 'mk4-' + name + '.png')
        bpy.ops.render.render(write_still=True)
