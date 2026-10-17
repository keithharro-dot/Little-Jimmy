# Doom Dad for augmented reality: a chunky cartoon space marine in green armour with a BFG, and Keith's own
# pixel-art face looking out of the helmet (models/doomdad-face.png, the same face as the boss in tower-defence.html).
# Original design in the spirit of the classic 90s shooters, not a copy of anyone's art.
#
#   python models/build_doomdad.py [--render <dir>]
#
# Writes models/doom-dad.glb (Android / web) and models/doom-dad.usdz (iPhone / iPad AR Quick Look), about 2.15 m tall.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arlib import *

HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS.clear(); META.clear()

GREEN  = mat('Armour', hexlin('#4f7a2e'), rough=.45, metal=.2)
GREEND = mat('Armour dark', hexlin('#36561f'), rough=.5, metal=.2)
GREENL = mat('Armour light', hexlin('#6f9e45'), rough=.4, metal=.2)
PANTS  = mat('Trousers', hexlin('#6b5a45'), rough=.9)
BOOT   = mat('Boots', hexlin('#2a2016'), rough=.6)
LEATH  = mat('Belt', hexlin('#5a4030'), rough=.7)
GOLD   = mat('Buckle', hexlin('#c9a227'), rough=.3, metal=.9)
STEEL  = mat('Gun steel', hexlin('#5c616b'), rough=.35, metal=.8)
DARK   = mat('Gun dark', hexlin('#2b2e33'), rough=.45, metal=.7)
PLASMA = mat('Plasma', hexlin('#8dff4a'), emit=6, rough=.3)
GLOW   = mat('Plasma glow', hexlin('#8dff4a'), emit=3, alpha=.3)

def box(c, s, m, bevel=.03):
    """c: centre (x right, y back, z up), s: full size. Rounded edges for the cartoon look."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL'); b.width = min(bevel, *[v/2.2 for v in s]); b.segments = 3
    o.data.materials.append(m); return link(o)

def blob(c, r, m, sq=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=r, location=c); o = bpy.context.object; o.scale = sq
    for f in o.data.polygons: f.use_smooth = True
    o.data.materials.append(m); return link(o)

def cyl(a, b, r, m, verts=20):
    o = tube(Vector(a), Vector(b), r, m, verts=verts)
    for f in o.data.polygons: f.use_smooth = True
    return o

# ---------- legs ----------
for s in (-1, 1):
    x = s*.17
    box((x, -.05, .11), (.24, .4, .22), BOOT, .06)                  # big boots
    box((x, -.05, .2), (.25, .41, .03), LEATH, 0)                   # boot strap
    box((x, 0, .4), (.19, .2, .4), PANTS, .05)                      # shins
    box((x, -.03, .6), (.22, .2, .16), GREEN, .05)                  # knee pads
    box((x, 0, .8), (.21, .22, .3), PANTS, .05)                     # thighs
    box((x + s*.06, 0, .82), (.08, .16, .14), GREEND, .03)          # thigh holster

# ---------- belt and armoured torso ----------
box((0, 0, .97), (.56, .32, .1), LEATH, .03)
box((0, -.165, .97), (.1, .02, .08), GOLD, .01)
for x in (-.2, .2): box((x, -.15, .95), (.1, .06, .1), GREEND, .02)  # pouches
box((0, 0, 1.25), (.62, .36, .5), GREEN, .09)
for x in (-.14, .14): box((x, -.175, 1.33), (.24, .04, .22), GREENL, .04)   # chest plates
for z in (1.08, 1.15): box((0, -.175, z), (.3, .03, .05), GREEND, .015)    # stomach plates
box((0, -.18, 1.45), (.34, .03, .04), GREEND, .015)                         # collar ridge
box((0, .2, 1.25), (.36, .08, .34), GREEND, .04)                            # back pack

# ---------- shoulders and arms holding the BFG ----------
for s in (-1, 1):
    blob((s*.42, 0, 1.44), .2, GREEN, (1, 1.05, .78))
    bpy.ops.mesh.primitive_torus_add(major_radius=.19, minor_radius=.025, location=(s*.42, 0, 1.4)); link(bpy.context.object).data.materials.append(GREEND)   # pad trim
    cyl((s*.41, 0, 1.36), (s*.4, -.02, 1.08), .075, GREEN)                   # upper arm
    blob((s*.4, -.02, 1.08), .08, GREEND)                                    # elbow
    cyl((s*.4, -.02, 1.08), (s*.17, -.32, 1.0), .068, GREEND)                # forearm, reaching for the gun
    box((s*.15, -.34, 1.0), (.12, .12, .12), BOOT, .04)                      # gloves
# the BFG: a big plasma cannon held across the hips, muzzle forward
box((0, -.5, .95), (.3, .62, .28), STEEL, .05)
box((0, -.5, 1.11), (.16, .44, .06), DARK, .02)                              # carry rail
box((0, -.82, .95), (.36, .06, .34), DARK, .03)                              # front ring
box((0, -.25, .86), (.12, .14, .18), DARK, .03)                              # grip block
for y in (-.4, -.55, -.68): box((0, y, .95), (.32, .03, .3), PLASMA, .01)    # glowing coils
blob((0, -.86, .95), .08, PLASMA)                                             # plasma ball in the muzzle
blob((0, -.88, .95), .13, GLOW)
cyl((-.17, -.3, .95), (-.17, -.75, .95), .02, DARK); cyl((.17, -.3, .95), (.17, -.75, .95), .02, DARK)   # side pipes

# ---------- head: rounded helmet, open face with the photo ----------
box((0, 0, 1.53), (.18, .18, .1), PANTS, .03)                                # neck
box((0, .02, 1.78), (.5, .46, .54), GREEN, .17)                              # helmet shell
box((0, -.215, 2.01), (.44, .07, .07), GREENL, .03)                          # brow ridge
box((0, .02, 2.05), (.12, .42, .06), GREEND, .03)                             # crest
for s in (-1, 1):
    box((s*.2, -.2, 1.76), (.06, .08, .42), GREEND, .025)                    # cheek guards
    blob((s*.255, .02, 1.8), .07, GREEND, (.6, 1, 1))                       # ear pieces
box((0, -.2, 1.535), (.34, .08, .06), GREEND, .025)                          # chin guard

# the face: the game's pixel art, kept crisp (nearest-neighbour), on a panel set into the helmet
img = bpy.data.images.load(os.path.join(HERE, 'doomdad-face.png'))
face = bpy.data.materials.new('Face'); face.use_nodes = True
nt = face.node_tree; p = nt.nodes['Principled BSDF']; tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Closest'
nt.links.new(tx.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = .7
W = .33; H = W*85/56
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -.222, 1.77), rotation=(math.pi/2, 0, 0)); o = bpy.context.object
o.scale = (W, H, 1); o.data.materials.append(face); link(o)

# ---------- one object, feet on the floor ----------
for o in bpy.context.scene.objects:
    if o.type == 'MESH': bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.convert(target='MESH')   # bake the bevels in before joining
world = finish(1.0, 'Doom Dad')
export(HERE, 'doom-dad')
if '--render' in sys.argv:
    render(sys.argv[sys.argv.index('--render') + 1], 'doom-dad', [('front', (1.6, -5.2, 1.5), (0, 0, 1.08), 40), ('face', (.35, -1.6, 1.8), (0, 0, 1.75), 50)], sky=(.55, .6, .68))
