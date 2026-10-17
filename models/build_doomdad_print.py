# A 3D-printable Doom Dad kicking the golden LEO BOMB soccer ball, on a base with "DOOM DAD" on the front.
#
#   python models/build_doomdad_print.py [--height 150] [--render <dir>]
#
# Writes, in millimetres (default 150 mm tall):
#   models/print/doom-dad-kick.stl   everything as one solid piece, for a single-colour print (opens in any slicer)
#   models/print/doom-dad-kick.3mf   the same model as two coloured parts, lined up: Doom Dad and the base in green, the
#                                    ball in gold, for a multi-colour printer (Bambu AMS, Prusa MMU) or a filament swap
# Every part is fused into watertight, manifold solids with a voxel remesh, so slicers take them as they are.
# The face is a relief carved from Keith's photo (models/doomdad-face-relief.png): bright skin stands out, dark
# eyes, brows and mouth sink in. Original design in the spirit of the classic 90s shooters.
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'print')
HEIGHT = float(sys.argv[sys.argv.index('--height') + 1]) if '--height' in sys.argv else 150.0
VOXEL = .0045        # metres at life size: about 0.3 mm on a 150 mm print
KICK = math.radians(-55)
HEAD = 1.25          # cartoon head, bigger than life

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
BODY, BALL = [], []

def keep(o, group): (BALL if group == 'ball' else BODY).append(o); return o

def box(c, s, bevel=.03, group='body'):
    """c: centre (x right, y back, z up, metres at life size), s: full size. Rounded edges for the cartoon look."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL'); b.width = min(bevel, *[v/2.2 for v in s]); b.segments = 3
    return keep(o, group)

def blob(c, r, sq=(1, 1, 1), group='body'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r, location=c); o = bpy.context.object; o.scale = sq
    return keep(o, group)

def cyl(a, b, r, verts=24, group='body'):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(a + b)/2); o = bpy.context.object
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return keep(o, group)

def pivot(objs, at, rot=None, scale=None):
    """Turn (and scale) a set of parts about a joint."""
    M = Matrix.Translation(at) @ (rot.to_matrix().to_4x4() if rot else Matrix()) @ (Matrix.Scale(scale, 4) if scale else Matrix()) @ Matrix.Translation(-Vector(at))
    for o in objs: o.matrix_world = M @ o.matrix_world

def text(txt, loc, size, depth, rot, group='body'):
    bpy.ops.object.text_add(location=loc, rotation=rot); t = bpy.context.object
    t.data.body = txt; t.data.size = size; t.data.extrude = depth; t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='MESH'); return keep(bpy.context.object, group)

# ---------- legs: the left one planted, the right one kicking ----------
def leg(x):
    n = len(BODY)
    box((x, -.05, .11), (.24, .4, .22), .06)                 # boot
    box((x, -.05, .2), (.25, .41, .03), 0)                   # strap
    box((x, 0, .4), (.19, .2, .4), .05)                      # shin
    box((x, -.03, .6), (.22, .2, .16), .05)                  # knee pad
    box((x, 0, .82), (.21, .22, .34), .05)                   # thigh
    return BODY[n:]
leg(-.17)
box((-.17 - .06, 0, .82), (.08, .16, .14), .03)              # holster on the standing leg
pivot(leg(.17), Vector((.17, 0, .95)), Matrix.Rotation(KICK, 3, 'X').to_quaternion())

# ---------- belt and armoured torso ----------
box((0, 0, .97), (.56, .32, .1), .03)
box((0, -.165, .97), (.1, .03, .08), .01)
for x in (-.2, .2): box((x, -.15, .95), (.1, .07, .1), .02)
box((0, 0, 1.25), (.62, .36, .5), .09)
for x in (-.14, .14): box((x, -.175, 1.33), (.24, .05, .22), .04)
for z in (1.08, 1.15): box((0, -.175, z), (.3, .04, .05), .015)
box((0, .2, 1.25), (.36, .1, .34), .04)                      # back pack

# ---------- shoulders, and the BFG held up at chest height ----------
for s in (-1, 1):
    blob((s*.42, 0, 1.44), .2, (1, 1.05, .78))
    n = len(BODY); bpy.ops.mesh.primitive_torus_add(major_radius=.19, minor_radius=.03, location=(s*.42, 0, 1.4)); keep(bpy.context.object, 'body')
    cyl((s*.41, 0, 1.38), (s*.36, -.12, 1.12), .08)          # upper arm
    blob((s*.36, -.12, 1.12), .085)                          # elbow
    cyl((s*.36, -.12, 1.12), (s*.17, -.36, 1.2), .072)       # forearm
    box((s*.15, -.38, 1.2), (.13, .13, .13), .04)            # glove
box((0, -.56, 1.2), (.3, .62, .28), .05)                     # the BFG
box((0, -.56, 1.36), (.16, .44, .06), .02)                   # carry rail
box((0, -.88, 1.2), (.36, .07, .34), .03)                    # front ring
for y in (-.46, -.61, -.74): box((0, y, 1.2), (.33, .035, .31), .01)   # coils
blob((0, -.92, 1.2), .09)                                    # plasma ball in the muzzle

# ---------- head: rounded helmet, a carved face, all a bit oversized ----------
n = len(BODY)
box((0, 0, 1.55), (.2, .2, .14), .03)                        # neck
box((0, .02, 1.78), (.5, .46, .54), .17)                     # helmet shell
box((0, -.215, 2.01), (.44, .07, .07), .03)                  # brow ridge
box((0, .02, 2.05), (.12, .42, .06), .03)                    # crest
for s in (-1, 1):
    box((s*.2, -.2, 1.76), (.06, .08, .42), .025)            # cheek guards
    blob((s*.255, .02, 1.8), .07, (.6, 1, 1))                # ear pieces
box((0, -.2, 1.535), (.34, .08, .06), .025)                  # chin guard
# the face relief: a height map grid set into the helmet opening, given thickness so it fuses with the helmet
def read_png_grey(path):
    img = bpy.data.images.load(path); w, h = img.size; px = list(img.pixels)
    return w, h, [[px[(y*w + x)*4] for x in range(w)] for y in range(h)]   # rows bottom to top
W, H = .33, .33*85/56
gw, gh, G = read_png_grey(os.path.join(HERE, 'doomdad-face-relief.png'))
bm = bmesh.new(); verts = {}
DEPTH, Y0 = .03, -.2
for j in range(gh):
    for i in range(gw):
        u, v = i/(gw - 1), j/(gh - 1)
        edge = max(0, min(1, (1 - ((u - .5)/.5)**2 - ((v - .5)/.5)**2)/.25))   # fades out at the rim of the oval
        d = DEPTH*G[j][i]*edge*edge*(3 - 2*edge)
        verts[i, j] = bm.verts.new(((u - .5)*W, Y0 - .012 - d, 1.77 + (v - .5)*H))
for j in range(gh - 1):
    for i in range(gw - 1):
        bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
me = bpy.data.meshes.new('Face'); bm.to_mesh(me); bm.free()
face = bpy.data.objects.new('Face', me); sc.collection.objects.link(face)
sol = face.modifiers.new('Solidify', 'SOLIDIFY'); sol.thickness = .06; sol.offset = -1   # grows back into the helmet
keep(face, 'body')
for o in BODY[n:]: o.matrix_world = Matrix.Translation((0, 0, 1.48)) @ Matrix.Scale(HEAD, 4) @ Matrix.Translation((0, 0, -1.48)) @ o.matrix_world

# ---------- the golden LEO BOMB, right on the toe of the kicking boot ----------
R = .32; C = Vector((.17, -1.0, R))
blob(C, R, group='ball')
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1); ico = bpy.context.object
dirs = [v.co.normalized() for v in ico.data.vertices]; bpy.data.objects.remove(ico)
for d in dirs:   # the twelve pentagons of a soccer ball, raised so they show in a single-colour print
    if d.z < -.6: continue   # (the ones it sits on)
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=R*.3, depth=.04, location=C + d*R)
    o = bpy.context.object; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); keep(o, 'ball')
text('LEO', C + Vector((0, -R + .035, .02)), .17, .05, (math.pi/2, 0, 0), group='ball')

# ---------- base: an octagon with DOOM DAD on the front face ----------
BC = Vector((0, -.55, 0)); BR = 1.12; BH = .1
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=BR, depth=BH, location=BC + Vector((0, 0, -BH/2 + .01)), rotation=(0, 0, math.pi/8)); keep(bpy.context.object, 'body')
front = BC.y - BR*math.cos(math.pi/8)
text('DOOM DAD', (0, front + .004, -BH/2 + .01), .075, .014, (math.pi/2, 0, 0))

# ---------- fuse each group into one watertight solid, scale to millimetres, export ----------
def fuse(objs, name, faces):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join(); o = bpy.context.object; o.name = name
    rm = o.modifiers.new('Remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = VOXEL; rm.adaptivity = 0
    bpy.ops.object.modifier_apply(modifier='Remesh')
    dec = o.modifiers.new('Decimate', 'DECIMATE'); dec.ratio = min(1, faces/max(1, len(o.data.polygons)))
    bpy.ops.object.modifier_apply(modifier='Decimate')
    bm = bmesh.new(); bm.from_mesh(o.data)   # drop any crumbs that didn't fuse
    islands, seen = [], set()
    for f in bm.faces:
        if f.index in seen: continue
        stack, isl = [f], []
        while stack:
            g = stack.pop()
            if g.index in seen: continue
            seen.add(g.index); isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: stack.append(h)
        islands.append(isl)
    islands.sort(key=len, reverse=True)
    small = [f for isl in islands[1:] if len(isl) < len(islands[0])*.02 for f in isl]
    bmesh.ops.delete(bm, geom=small, context='FACES')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    print(name, 'islands', len(islands), '-> dropped', len(islands) - 1 - sum(1 for isl in islands[1:] if len(isl) >= len(islands[0])*.02), 'non-manifold edges', nm, 'triangles', sum(len(f.verts) - 2 for f in bm.faces))
    bm.to_mesh(o.data); bm.free()
    return o

body = fuse(BODY, 'Doom Dad', 130000); ball = fuse(BALL, 'LEO BOMB', 30000)
low = min(min(v.co.z for v in body.data.vertices), min(v.co.z for v in ball.data.vertices))
top = max(v.co.z for v in body.data.vertices)
k = HEIGHT/1000/(top - low)*1000   # metres -> millimetres at the requested height
for o in (body, ball):
    o.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation((0, 0, -low)))
print('print size mm: %.0f wide x %.0f deep x %.0f tall' % tuple((Vector(body.dimensions))))
os.makedirs(OUT, exist_ok=True)
def write_3mf(path, parts):
    """3MF (zipped XML, millimetres): one object per part, each with its colour, lined up as one model."""
    import zipfile
    objs, items = [], []
    mats = ''.join('<base name="%s" displaycolor="%s"/>' % (n, c) for n, o, c in parts)
    for k_, (n, o, c) in enumerate(parts):
        me = o.data; me.calc_loop_triangles()
        vs = ''.join('<vertex x="%.3f" y="%.3f" z="%.3f"/>' % tuple(v.co) for v in me.vertices)
        ts = ''.join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(t.vertices) for t in me.loop_triangles)
        objs.append('<object id="%d" name="%s" type="model" pid="1" pindex="%d"><mesh><vertices>%s</vertices><triangles>%s</triangles></mesh></object>' % (k_ + 2, n, k_, vs, ts))
        items.append('<item objectid="%d"/>' % (k_ + 2))
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">Doom Dad kicking the LEO BOMB</metadata><resources><basematerials id="1">%s</basematerials>%s</resources><build>%s</build></model>') % (mats, ''.join(objs), ''.join(items))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model', model)
write_3mf(os.path.join(OUT, 'doom-dad-kick.3mf'), [('Doom Dad (green)', body, '#4F7A2EFF'), ('LEO BOMB (gold)', ball, '#E0A820FF')])
# one piece: the body and ball fused together, as an STL every slicer can open
body2 = body.copy(); body2.data = body.data.copy(); sc.collection.objects.link(body2)
ball2 = ball.copy(); ball2.data = ball.data.copy(); sc.collection.objects.link(ball2)
bpy.ops.object.select_all(action='DESELECT'); body2.select_set(True); ball2.select_set(True); bpy.context.view_layer.objects.active = body2
bpy.ops.object.join()
rm = body2.modifiers.new('Union', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = VOXEL*k; rm.adaptivity = 0; bpy.ops.object.modifier_apply(modifier='Union')
dec = body2.modifiers.new('Decimate', 'DECIMATE'); dec.ratio = min(1, 160000/len(body2.data.polygons)); bpy.ops.object.modifier_apply(modifier='Decimate')
bm = bmesh.new(); bm.from_mesh(body2.data); print('one piece: non-manifold edges', sum(1 for e in bm.edges if not e.is_manifold), 'triangles', sum(len(f.verts) - 2 for f in bm.faces)); bm.free()
bpy.ops.object.select_all(action='DESELECT'); body2.select_set(True)
bpy.ops.wm.stl_export(filepath=os.path.join(OUT, 'doom-dad-kick.stl'), export_selected_objects=True, global_scale=1, ascii_format=False, apply_modifiers=True)
body2.hide_render = True

if '--render' in sys.argv:
    d = sys.argv[sys.argv.index('--render') + 1]
    grey = bpy.data.materials.new('PLA'); grey.diffuse_color = (.35, .55, .25, 1); body.data.materials.append(grey)
    gold = bpy.data.materials.new('Gold PLA'); gold.diffuse_color = (.9, .65, .1, 1); ball.data.materials.append(gold)
    for m, col in ((grey, (.3, .5, .2, 1)), (gold, (.95, .62, .08, 1))):
        m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value = col; p.inputs['Roughness'].default_value = .55
    bpy.ops.object.light_add(type='SUN', rotation=(.8, .2, -.5)); bpy.context.object.data.energy = 4
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.6, .62, .66, 1)
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.device = 'CPU'; sc.render.resolution_x = sc.render.resolution_y = 900
    sc.view_settings.view_transform = 'AgX'
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 50
    cz = HEIGHT/2
    for name, loc, look in (('front', (140, -380, 150), (0, -30, cz)), ('side', (420, -60, 120), (0, -30, cz)), ('face', (20, -150, 140), (0, -20, HEIGHT*.84))):
        cam.location = loc; dv = Vector(look) - Vector(loc); cam.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(d, 'print-' + name + '.png'); bpy.ops.render.render(write_still=True)
