# Builds "the battlefield, mid-battle" for augmented reality, big enough to walk around on a sports oval.
#
#   1. models/battle/battle.glb + battle.json come from the real game: a staged mid-battle moment in
#      tower-defence.html, frozen and exported with three.js (see models/battle/README.md).
#   2. This script (Blender as a Python module: pip install bpy==5.2.2) turns the game's vertex-painted
#      blocks into real materials (iPhone AR ignores vertex colours), adds the epic part — fireballs,
#      smoke columns, missile trails, glowing beams, sparks, boss auras, scorch marks — scales it so
#      1 game tile = TILE metres, and writes models/battlefield.glb (Android/web) and
#      models/battlefield.usdz (iPhone/iPad AR Quick Look).
#
#   python models/build_battlefield.py [--render <dir>]
import bpy, bmesh, json, math, os, struct, sys, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'battle')
TILE = 4.5            # metres per game tile: the board is 67.5 x 40.5 m, ~95 x 63 m with the scenery
KEEP = (10.5, 7.0)    # trim scenery further than this (in tiles) from the board's centre
rng = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, 'battle.glb'))
info = json.load(open(os.path.join(SRC, 'battle.json')))
for o in scene.objects: o.select_set(True)
bpy.ops.object.make_single_user(object=True, obdata=True)   # the game shares one mesh between copies; give each its own
COLS, ROWS = info['cols'], info['rows']

# ---------- the glTF's own material list (for colours, unlit flags and opacity) ----------
with open(os.path.join(SRC, 'battle.glb'), 'rb') as f:
    f.seek(12); n, = struct.unpack('<I', f.read(4)); f.read(4); gltf = json.loads(f.read(n))
GM = gltf.get('materials', [])

def lin(c): return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
def hexlin(h): return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))
def srgb(c): return 12.92 * c if c <= .0031308 else 1.055 * c ** (1 / 2.4) - .055

MATS, META = {}, {}   # META: what the iPhone file needs per material, patched in after export (Blender's USD
                      # exporter drops transparency, and AR clips glow above 1, which turns orange fire white)
def mat(key, col, emit=0.0, alpha=1.0, rough=.75, metal=0.0):
    """col: linear RGB. One shared material per look."""
    k = (key, tuple(round(c, 3) for c in col), round(emit, 2), round(alpha, 2))
    if k in MATS: return MATS[k]
    name = 'M_%03d' % len(MATS)
    peak = max(col) or 1
    META[name] = {'opacity': alpha, 'emit': [c / peak for c in col] if emit else None}
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*col, 1)
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*col, 1); p.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    MATS[k] = m
    return m

# colours that glow in the game (sRGB hex): ANNIHILATOR pink, laser cyan, lava, eyes, muzzles, reactor amber
GLOW = {h: hexlin(h) for h in ['#ff2bd6', '#ff7be8', '#3ee6ff', '#bff6ff', '#ff3b30', '#ff2a10', '#ff4020', '#ffe680', '#ffb03a', '#8dff4a', '#ff7a1a', '#ffc23a']}
def glowish(c):
    return any(sum(abs(a - b) for a, b in zip(c, g)) < .06 for g in GLOW.values())

# ---------- 1. turn every imported material / vertex colour into a plain, AR-friendly material ----------
meshes = [o for o in scene.objects if o.type == 'MESH']
for o in meshes:
    me = o.data
    if me.color_attributes:
        ca = me.color_attributes[0]; me.materials.clear(); slots = {}
        for poly in me.polygons:
            if ca.domain == 'CORNER': cs = [ca.data[i].color for i in poly.loop_indices]
            else: cs = [ca.data[me.loops[i].vertex_index].color for i in poly.loop_indices]
            c = tuple(sum(x[j] for x in cs) / len(cs) for j in range(3))
            q = tuple(round(x, 2) for x in c)
            if q not in slots:
                slots[q] = len(me.materials)
                me.materials.append(mat('Paint', q, emit=4.0 if glowish(q) else 0))
            poly.material_index = slots[q]
        me.color_attributes.remove(ca)
        continue
    for i, slot in enumerate(o.material_slots):
        m = slot.material
        if not m: continue
        gi = int(m.name.split('_')[-1].split('.')[0]) if m.name.startswith('Material_') else -1
        g = GM[gi] if 0 <= gi < len(GM) else {}
        pbr = g.get('pbrMetallicRoughness', {})
        bc = pbr.get('baseColorFactor', [1, 1, 1, 1])
        unlit = 'KHR_materials_unlit' in g.get('extensions', {})
        if 'baseColorTexture' in pbr:   # the board: keep its texture, brightened for daylight, and make it matte
            for nd in m.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.image and not nd.image.get('lit'):
                    im = nd.image; px = list(im.pixels)
                    for j in range(0, len(px), 4):
                        for c in range(3): px[j + c] = min(1.0, px[j + c] * 1.55 + .02)
                    im.pixels = px; im['lit'] = 1; im.pack()
            p = m.node_tree.nodes.get('Principled BSDF')
            if p: p.inputs['Roughness'].default_value = .9; p.inputs['Metallic'].default_value = 0
            if not m.name.startswith('Board'): m.name = 'Board'
            continue
        col = tuple(bc[:3]); a = bc[3] if g.get('alphaMode') == 'BLEND' else 1.0
        lum = .2126 * col[0] + .7152 * col[1] + .0722 * col[2]
        slot.material = mat('Unlit' if unlit else 'Solid', col, emit=(5.0 if lum > .05 else 0) if unlit else 0, alpha=max(a, .55) if unlit else a)

# ---------- 2. trim scenery that sprawls too far from the board ----------
for o in meshes:
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); M = o.matrix_world
    dead = [f for f in bm.faces if (lambda c: abs(c.x) > KEEP[0] or abs(c.y) > KEEP[1])(M @ f.calc_center_median())]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me)
    bm.free()

# ---------- 3. the epic part ----------
# game coordinates (three.js: x, height, z) -> Blender (x, -z, height)
B = lambda x, h, z: Vector((x, -z, h))
fxcol = bpy.data.collections.new('Effects'); scene.collection.children.link(fxcol)
def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    fxcol.objects.link(o); return o
def ball(p, r, m, sub=2, squash=1.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=p)
    o = bpy.context.object; o.scale.z = squash; o.data.materials.append(m)
    for f in o.data.polygons: f.use_smooth = True
    return link(o)
def tube(a, b, r, m, verts=10):
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    o.data.materials.append(m); return link(o)
def cone(p, d, r, length, m):
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r, depth=length, location=p - d.normalized() * length / 2)
    o = bpy.context.object; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
    o.data.materials.append(m); return link(o)
def disc(p, r, m):
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=r, fill_type='NGON', location=p)
    o = bpy.context.object; o.data.materials.append(m); return link(o)
def chunk(p, s, m):
    bpy.ops.mesh.primitive_cube_add(size=s, location=p, rotation=(rng.random() * 3, rng.random() * 3, rng.random() * 3))
    o = bpy.context.object; o.data.materials.append(m); return link(o)

FIRE_CORE = mat('Fire core', hexlin('#fff4c2'), emit=12)
FIRE = mat('Fire', hexlin('#ffb23a'), emit=8, alpha=.9)
FIRE_OUT = mat('Fire edge', hexlin('#ff5a1a'), emit=5, alpha=.55)
SMOKE_D = mat('Smoke dark', hexlin('#3a3632'), alpha=.6, rough=1)
SMOKE_L = mat('Smoke', hexlin('#a9a49c'), alpha=.4, rough=1)
SCORCH = mat('Scorch', hexlin('#14110e'), alpha=.85, rough=1)
DEBRIS = mat('Debris', hexlin('#3a2f25'))
FLAME = mat('Thruster', hexlin('#ffb040'), emit=9)
TRAIL = mat('Missile smoke', hexlin('#e8e4dc'), alpha=.5, rough=1)

def explosion(c, size, column=False):
    """Fireball with a white-hot core, debris and a scorch mark; the big ones also send up a smoke column."""
    g = Vector((c.x, c.y, 0))
    disc(g + Vector((0, 0, .02)), size * 1.3, SCORCH)
    ball(g + Vector((0, 0, size * .55)), size * .35, FIRE_CORE)
    for k in range(5):
        a = k * 2 * math.pi / 5 + rng.random()
        ball(g + Vector((math.cos(a) * size * .35, math.sin(a) * size * .35, size * (.45 + rng.random() * .4))), size * (.32 + rng.random() * .15), FIRE)
    ball(g + Vector((0, 0, size * .65)), size * .85, FIRE_OUT, squash=.8)
    h = size * 1.1
    for k in range(9 if column else 3):   # smoke, widening as it rises
        h += size * (.35 + rng.random() * .2)
        ball(g + Vector(((rng.random() - .5) * size * .6, (rng.random() - .5) * size * .6, h)), size * (.35 + k * .07), SMOKE_D if k < 4 else SMOKE_L)
    for k in range(8):   # debris flung outwards
        a = rng.random() * 2 * math.pi; d = size * (.8 + rng.random() * 1.2)
        chunk(g + Vector((math.cos(a) * d, math.sin(a) * d, size * (.2 + rng.random() * 1.4))), size * (.08 + rng.random() * .08), DEBRIS)

# missiles in flight: smoke trails back along their arcs, and a flame at the tail
def arc_at(m, q):
    (ax, ay, ah), (bx, by) = m['a'], m['b']
    x, y = ax + (bx - ax) * q, ay + (by - ay) * q
    return B(x - COLS / 2, ah * (1 - q) + .2 * q + math.sin(math.pi * q) * m['arc'], y - ROWS / 2)
impacts = []
for m in info['missiles']:
    k = min(1, m['t'] / m['dur'])
    head = arc_at(m, k); tail_dir = head - arc_at(m, max(0, k - .02))
    if not m['shell']: cone(head - tail_dir.normalized() * .16, tail_dir, .05, .28, FLAME)
    q = k; i = 0
    while q > max(0, k - .45) and i < 14:
        q -= .032; i += 1
        p = arc_at(m, q)
        ball(p + Vector(((rng.random() - .5) * .03, (rng.random() - .5) * .03, 0)), .022 + i * .006, TRAIL, sub=1)
    impacts.append(B(m['b'][0] - COLS / 2, 0, m['b'][1] - ROWS / 2))
for q in info['proj']: impacts.append(B(q['x'], 0, q['z']))

# explosions where the missiles are landing (one per neighbourhood), plus big ones by the bosses
sites = []
for p in impacts:
    if all((p - s).length > 1.2 for s in sites): sites.append(p)
for i, p in enumerate(sites[:7]): explosion(p + Vector(((rng.random() - .5) * .5, (rng.random() - .5) * .5, 0)), .5 + rng.random() * .2, column=(i == 2))
for e in info['enemies']:
    if e['k'] == 'erad': explosion(B(e['x'] + .9, 0, e['z'] + .3), .8, column=True)

# beams: a bright core, a soft glow sleeve, a flare where they hit and sparks along the way
for bm_ in info['beams']:
    a, b = Vector(bm_['a']), Vector(bm_['b']); a, b = B(a.x, a.y, a.z), B(b.x, b.y, b.z)
    r, g_, b_ = (int(bm_['c'][-6:][i:i + 2], 16) / 255 for i in (0, 2, 4))
    hexc = '#3ee6ff' if r < .75 and g_ > .8 and b_ > .8 else '#ff2bd6' if r > .8 and g_ < .6 and b_ > .8 else '#ff3b30' if r > .8 and g_ < .7 else '#fff2b0'
    col = hexlin(hexc)
    w = .035 * max(1, bm_['w'])
    tube(a, b, w * .45, mat('Beam core', (1, 1, 1), emit=14))
    tube(a, b, w, mat('Beam', col, emit=10, alpha=.85))
    tube(a, b, w * 2.6, mat('Beam glow', col, emit=4, alpha=.3))
    ball(b, w * 4, mat('Flare', col, emit=10, alpha=.7))
    for i in range(10):
        t = rng.random(); p = a.lerp(b, t)
        ball(p + Vector(((rng.random() - .5) * .3, (rng.random() - .5) * .3, rng.random() * .3)), .03, mat('Spark', col, emit=10), sub=1)

# the game's own particles at the moment of the freeze: sparks glow, grey ones are smoke
for q in info['parts']:
    p = Vector(q['p']); p = B(p.x, p.y, p.z); c = hexlin(q['c'])
    sat = max(c) - min(c)
    if sat < .08: ball(p, max(.04, q['s'] * .35), SMOKE_L, sub=1)
    else: ball(p, max(.03, q['s'] * .25), mat('Spark', c, emit=8), sub=1)

# boss auras: the raging MK II glows red, the Void floats in a purple haze
for e in info['enemies']:
    if e['k'] == 'erad2':
        ball(B(e['x'], 0, e['z']), 1.5, mat('Rage aura', hexlin('#ff3b30'), emit=2.5, alpha=.12), sub=3, squash=1.1)
        disc(B(e['x'], .03, e['z']), 1.9, mat('Rage ground', hexlin('#ff3b30'), emit=2, alpha=.35))
    if e['k'] == 'void':
        ball(B(e['x'], .4, e['z']), 1.2, mat('Void haze', hexlin('#6e28be'), emit=2.5, alpha=.18), sub=3)

# ---------- 4. one object, scaled to the oval, feet on the ground ----------
for o in list(scene.objects):
    if o.type != 'MESH': continue
    o.select_set(True)
bpy.context.view_layer.objects.active = [o for o in scene.objects if o.type == 'MESH'][0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
world = bpy.context.object; world.name = 'Battlefield'
for o in list(scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
world.data.transform(Matrix.Scale(TILE, 4))
bm = bmesh.new(); bm.from_mesh(world.data)   # slice off anything below the grass, so AR puts the board flat on the ground
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
bm.to_mesh(world.data); bm.free()
bpy.context.view_layer.update(); dims = world.dimensions
print('triangles', sum(len(p.vertices) - 2 for p in world.data.polygons), 'size m %.0f x %.0f x %.0f' % tuple(dims), 'materials', len(world.data.materials))

sys.path.insert(0, os.path.join(bpy.utils.resource_path('LOCAL'), 'python', 'lib', 'python%d.%d' % sys.version_info[:2], 'site-packages'))   # Blender's own USD library
from pxr import Usd, UsdShade, UsdUtils, Sdf, Gf
import tempfile

def export(name):
    """Write models/<name>.glb and models/<name>.usdz (the USD gets its transparency and glow patched in)."""
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, name + '.glb'), export_format='GLB', export_apply=True,
                              export_image_format='JPEG', export_jpeg_quality=88)
    tmp = tempfile.mkdtemp(); usdc = os.path.join(tmp, name + '.usdc')
    bpy.ops.wm.usd_export(filepath=usdc, export_materials=True, convert_orientation=True, export_textures_mode='NEW', relative_paths=True,
                          export_global_forward_selection='NEGATIVE_Z', export_global_up_selection='Y')
    st = Usd.Stage.Open(usdc); patched = 0
    for prim in st.Traverse():
        if prim.GetTypeName() != 'Shader': continue
        sh = UsdShade.Shader(prim)
        if sh.GetIdAttr().Get() != 'UsdPreviewSurface': continue
        meta = META.get(prim.GetParent().GetName())
        if not meta: continue
        sh.CreateInput('opacity', Sdf.ValueTypeNames.Float).Set(float(meta['opacity']))
        sh.CreateInput('emissiveColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*(meta['emit'] or (0, 0, 0))))
        patched += 1
    st.Save()
    out = os.path.join(HERE, name + '.usdz')
    if os.path.exists(out): os.remove(out)
    UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usdc), out)
    print(name, 'usd materials patched', patched, 'of', len(META))

export('battlefield')                                # life size, for the oval
world.data.transform(Matrix.Scale(1 / 48, 4))        # and a table-size copy (about 1.9 m across) for the lounge room
export('battlefield-mini')
world.data.transform(Matrix.Scale(48, 4))

if '--render' in sys.argv:   # preview stills: from above, and standing on the grass among them
    out = sys.argv[sys.argv.index('--render') + 1]
    bpy.ops.object.light_add(type='SUN', rotation=(.85, .15, -.9)); bpy.context.object.data.energy = 3.2
    w = bpy.data.worlds.new('w'); scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.42, .55, .75, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -.01)); bpy.context.object.data.materials.append(mat('Oval grass', hexlin('#4f7a34'), rough=1))
    scene.render.engine = 'BLENDER_EEVEE' if '--fast' in sys.argv else 'CYCLES'
    if scene.render.engine == 'CYCLES': scene.cycles.samples = 24; scene.cycles.device = 'CPU'
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.view_settings.view_transform = 'AgX'
    bpy.ops.object.camera_add(); cam = bpy.context.object; scene.camera = cam
    def shoot(name, loc, look, lens):
        cam.location = loc; cam.data.lens = lens
        d = Vector(look) - Vector(loc); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(out, 'field-' + name + '.png'); bpy.ops.render.render(write_still=True)
    shoot('aerial', (0, -78, 52), (0, 0, 2), 30)
    shoot('ground', (-14, -26, 1.6), (4, 2, 7), 16)
