# Shared toolkit for turning a frozen game moment (a three.js GLB exported from the game) into an AR scene:
# AR-friendly materials, effect builders (fireballs, smoke, beams, mushroom clouds, 3D text), scaling and ground
# clipping, and export to GLB (Android/web) + USDZ (iPhone/iPad) with the USD's transparency and glow patched in.
# Used by build_battlefield.py and build_soccer.py. Needs Blender as a Python module: pip install bpy==5.2.2
import bpy, bmesh, json, math, os, struct, sys, random, tempfile
from mathutils import Vector, Matrix

rng = random.Random(7)

def lin(c): return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
def hexlin(h): return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))

# game coordinates (three.js: x, height, z) -> Blender (x, -z, height)
B = lambda x, h, z: Vector((x, -z, h))

MATS, META = {}, {}   # META: what the iPhone file needs per material, patched in after export (Blender's USD
                      # exporter drops transparency, and AR clips glow above 1, which turns orange fire white)
def mat(key, col, emit=0.0, alpha=1.0, rough=.75, metal=0.0):
    """col: linear RGB. One shared material per look."""
    k = (key, tuple(round(c, 3) for c in col), round(emit, 2), round(alpha, 2), rough, metal)
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

def start(glb):
    """Fresh Blender, import the game's GLB, give every object its own mesh. Returns the glTF's material list."""
    MATS.clear(); META.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    for o in bpy.context.scene.objects: o.select_set(True)
    bpy.ops.object.make_single_user(object=True, obdata=True)   # the game shares one mesh between copies
    with open(glb, 'rb') as f:
        f.seek(12); n, = struct.unpack('<I', f.read(4)); f.read(4); gltf = json.loads(f.read(n))
    global FX; FX = None
    return gltf.get('materials', [])

def convert_materials(GM, glow_hexes=(), brighten=1.0, metal_keep=False):
    """Vertex colours -> one material per colour (iPhone AR ignores vertex colours); glTF materials -> plain ones.
    Textured materials keep their texture (optionally brightened). Unlit (MeshBasic) materials glow."""
    glow = [hexlin(h) for h in glow_hexes]
    glowish = lambda c: any(sum(abs(a - b) for a, b in zip(c, g)) < .06 for g in glow)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        me = o.data
        if me.color_attributes:
            ca = me.color_attributes[0]; me.materials.clear(); slots = {}
            for poly in me.polygons:
                if ca.domain == 'CORNER': cs = [ca.data[i].color for i in poly.loop_indices]
                else: cs = [ca.data[me.loops[i].vertex_index].color for i in poly.loop_indices]
                q = tuple(round(sum(x[j] for x in cs) / len(cs), 2) for j in range(3))
                if q not in slots:
                    slots[q] = len(me.materials)
                    me.materials.append(mat('Paint', q, emit=4.0 if glowish(q) else 0))
                poly.material_index = slots[q]
            me.color_attributes.remove(ca)
            continue
        for slot in o.material_slots:
            m = slot.material
            if not m or m.name.startswith('M_') or m.name.startswith('Tex'): continue
            gi = int(m.name.split('_')[-1].split('.')[0]) if m.name.startswith('Material_') else -1
            g = GM[gi] if 0 <= gi < len(GM) else {}
            pbr = g.get('pbrMetallicRoughness', {})
            bc = pbr.get('baseColorFactor', [1, 1, 1, 1])
            unlit = 'KHR_materials_unlit' in g.get('extensions', {})
            a = bc[3] if g.get('alphaMode') == 'BLEND' else 1.0
            if 'baseColorTexture' in pbr:   # pitch, board, faces, nets: keep the texture
                for nd in m.node_tree.nodes:
                    if nd.type == 'TEX_IMAGE' and nd.image and brighten != 1 and not nd.image.get('lit'):
                        im = nd.image; px = list(im.pixels)
                        for j in range(0, len(px), 4):
                            for c in range(3): px[j + c] = min(1.0, px[j + c] * brighten + .02)
                        im.pixels = px; im['lit'] = 1; im.pack()
                p = m.node_tree.nodes.get('Principled BSDF')
                if p:
                    p.inputs['Roughness'].default_value = .9
                    if not metal_keep: p.inputs['Metallic'].default_value = 0
                m.name = 'Tex_%03d' % len(META); META[m.name] = {'opacity': a, 'emit': None}
                continue
            col = tuple(bc[:3])
            lum = .2126 * col[0] + .7152 * col[1] + .0722 * col[2]
            metal = pbr.get('metallicFactor', 0) if metal_keep else 0
            rough = pbr.get('roughnessFactor', .75) if metal_keep else .75
            slot.material = mat('Unlit' if unlit else 'Solid', col, emit=(5.0 if lum > .05 else 0) if unlit else 0,
                                alpha=max(a, .3) if unlit else a, rough=rough, metal=metal)
    return meshes

def trim(meshes, keep):
    """Delete faces whose centre fails keep(Vector) — scenery that sprawls too far."""
    for o in meshes:
        me = o.data; bm = bmesh.new(); bm.from_mesh(me); M = o.matrix_world
        dead = [f for f in bm.faces if not keep(M @ f.calc_center_median())]
        if dead: bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me)
        bm.free()

# ---------- effect builders ----------
def _fxcol():
    c = bpy.data.collections.get('Effects')
    if not c: c = bpy.data.collections.new('Effects'); bpy.context.scene.collection.children.link(c)
    return c
def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    _fxcol().objects.link(o); return o
def ball(p, r, m, sub=2, squash=1.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=p)
    o = bpy.context.object; o.scale.z = squash; o.data.materials.append(m)
    for f in o.data.polygons: f.use_smooth = True
    return link(o)
def tube(a, b, r, m, verts=10, r2=None):
    d = b - a
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(a + b) / 2)
    else: bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d.length, location=(a + b) / 2)
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
def text(txt, p, size, m, face_y=-1, depth=.1, outline=None):
    """Upright 3D lettering standing at p, facing towards -Y (face_y=-1) or +Y; optional dark outline slab behind."""
    bpy.ops.object.text_add(location=p, rotation=(math.pi / 2, 0, 0 if face_y < 0 else math.pi))
    o = bpy.context.object; o.data.body = txt; o.data.size = size; o.data.extrude = depth
    o.data.align_x = 'CENTER'; o.data.align_y = 'CENTER'; o.data.bevel_depth = depth * .25
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object
    o.data.materials.append(m); link(o)
    if outline:
        d = o.dimensions
        bpy.ops.mesh.primitive_cube_add(size=1, location=p - Vector((0, -face_y * depth * 1.6, 0)))
        s = bpy.context.object; s.scale = (d.x + size * .5, depth, d.y + size * .4); s.data.materials.append(outline); link(s)
    return o

def fx_mats():
    global FX
    if FX: return FX
    FX = dict(
        CORE=mat('Fire core', hexlin('#fff4c2'), emit=12), FIRE=mat('Fire', hexlin('#ffb23a'), emit=8, alpha=.9),
        EDGE=mat('Fire edge', hexlin('#ff5a1a'), emit=5, alpha=.55), SMOKE_D=mat('Smoke dark', hexlin('#3a3632'), alpha=.6, rough=1),
        SMOKE=mat('Smoke', hexlin('#a9a49c'), alpha=.4, rough=1), SCORCH=mat('Scorch', hexlin('#14110e'), alpha=.85, rough=1),
        DEBRIS=mat('Debris', hexlin('#3a2f25')), FLAME=mat('Thruster', hexlin('#ffb040'), emit=9),
        TRAIL=mat('Missile smoke', hexlin('#e8e4dc'), alpha=.5, rough=1))
    return FX

def explosion(c, size, column=False):
    """Fireball with a white-hot core, debris and a scorch mark; the big ones also send up a smoke column."""
    X = fx_mats(); g = Vector((c.x, c.y, 0))
    disc(g + Vector((0, 0, .02 * size)), size * 1.3, X['SCORCH'])
    ball(g + Vector((0, 0, size * .55)), size * .35, X['CORE'])
    for k in range(5):
        a = k * 2 * math.pi / 5 + rng.random()
        ball(g + Vector((math.cos(a) * size * .35, math.sin(a) * size * .35, size * (.45 + rng.random() * .4))), size * (.32 + rng.random() * .15), X['FIRE'])
    ball(g + Vector((0, 0, size * .65)), size * .85, X['EDGE'], squash=.8)
    h = size * 1.1
    for k in range(9 if column else 3):
        h += size * (.35 + rng.random() * .2)
        ball(g + Vector(((rng.random() - .5) * size * .6, (rng.random() - .5) * size * .6, h)), size * (.35 + k * .07), X['SMOKE_D'] if k < 4 else X['SMOKE'])
    for k in range(8):
        a = rng.random() * 2 * math.pi; d = size * (.8 + rng.random() * 1.2)
        chunk(g + Vector((math.cos(a) * d, math.sin(a) * d, size * (.2 + rng.random() * 1.4))), size * (.08 + rng.random() * .08), X['DEBRIS'])

def mushroom(c, h, glow='#ffb23a'):
    """A towering mushroom cloud of height h: fire at the base, a rising stem, a rolling cap and a shock ring."""
    X = fx_mats(); g = Vector((c.x, c.y, 0)); r = h * .14
    hot = mat('Nuke fire', hexlin(glow), emit=8, alpha=.85)
    ember = mat('Nuke ember', hexlin('#ff5a1a'), emit=5, alpha=.7)
    cap_d = mat('Nuke cap', hexlin('#6b5a48'), alpha=.85, rough=1)
    cap_l = mat('Nuke cap light', hexlin('#b39a7c'), alpha=.75, rough=1)
    disc(g + Vector((0, 0, .02 * h)), h * .55, X['SCORCH'])
    for k in range(10):   # fireball skirt at the base
        a = k * 2 * math.pi / 10
        ball(g + Vector((math.cos(a) * r * 1.3, math.sin(a) * r * 1.3, r * .5)), r * (.7 + rng.random() * .3), hot if k % 2 else ember)
    ball(g + Vector((0, 0, r * .7)), r * 1.1, X['CORE'])
    for k in range(12):   # the stem
        z = r + k * (h * .62 - r) / 12
        ball(g + Vector(((rng.random() - .5) * r * .3, (rng.random() - .5) * r * .3, z)), r * (.55 + .15 * math.sin(k)), hot if k < 4 else cap_d if k % 3 else ember)
    for ring_r, z, n in ((h * .2, h * .7, 12), (h * .3, h * .8, 16), (h * .22, h * .92, 12), (h * .1, h * 1.0, 6)):   # the cap
        for k in range(n):
            a = k * 2 * math.pi / n + rng.random() * .3
            ball(g + Vector((math.cos(a) * ring_r, math.sin(a) * ring_r, z + (rng.random() - .5) * h * .05)), h * (.09 + rng.random() * .04), cap_l if k % 3 else cap_d)
    ball(g + Vector((0, 0, h * .78)), h * .16, ember)
    ball(g + Vector((0, 0, h * .84)), h * .2, cap_d, squash=.6)

def trail(points, r0, r1, m):
    """Smoke puffs along a path, growing from r0 to r1."""
    n = len(points)
    for i, p in enumerate(points):
        ball(p + Vector(((rng.random() - .5) * r1 * .3, (rng.random() - .5) * r1 * .3, 0)), r0 + (r1 - r0) * i / max(1, n - 1), m, sub=1)

# ---------- finish: one object, scaled, clipped at ground level, exported ----------
def finish(scale, name='Scene'):
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type == 'MESH': o.select_set(True)
    bpy.context.view_layer.objects.active = [o for o in sc.objects if o.type == 'MESH'][0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    world = bpy.context.object; world.name = name
    for o in list(sc.objects):
        if o.type != 'MESH': bpy.data.objects.remove(o)
    world.data.transform(Matrix.Scale(scale, 4))
    bm = bmesh.new(); bm.from_mesh(world.data)   # slice off anything below the ground, so AR puts it flat on the grass
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(world.data); bm.free()
    bpy.context.view_layer.update()
    print(name, 'triangles', sum(len(p.vertices) - 2 for p in world.data.polygons), 'size m %.0f x %.0f x %.0f' % tuple(world.dimensions), 'materials', len(world.data.materials))
    return world

def export(out_dir, name):
    """Write <out_dir>/<name>.glb and <name>.usdz (the USD gets its transparency and glow patched in)."""
    sys.path.insert(0, os.path.join(bpy.utils.resource_path('LOCAL'), 'python', 'lib', 'python%d.%d' % sys.version_info[:2], 'site-packages'))
    from pxr import Usd, UsdShade, UsdUtils, Sdf, Gf   # Blender's own USD library
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + '.glb'), export_format='GLB', export_apply=True,
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
    out = os.path.join(out_dir, name + '.usdz')
    if os.path.exists(out): os.remove(out)
    UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usdc), out)
    print(name, 'usd materials patched', patched, 'of', len(META))

def export_sizes(world, out_dir, name, mini_div):
    """Life size, then a table-size copy (1/mini_div) for the lounge room."""
    export(out_dir, name)
    world.data.transform(Matrix.Scale(1 / mini_div, 4)); export(out_dir, name + '-mini'); world.data.transform(Matrix.Scale(mini_div, 4))

def render(out_dir, prefix, shots, sky=(.42, .55, .75)):
    """Preview stills in Cycles: shots = [(name, camera location, look-at point, lens mm)]."""
    sc = bpy.context.scene
    bpy.ops.object.light_add(type='SUN', rotation=(.85, .15, -.9)); bpy.context.object.data.energy = 3.2
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (*sky, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -.01)); bpy.context.object.data.materials.append(mat('Oval grass', hexlin('#4f7a34'), rough=1))
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = 'AgX'
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    for name, loc, look, lens in shots:
        cam.location = loc; cam.data.lens = lens
        d = Vector(look) - Vector(loc); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out_dir, prefix + '-' + name + '.png'); bpy.ops.render.render(write_still=True)
