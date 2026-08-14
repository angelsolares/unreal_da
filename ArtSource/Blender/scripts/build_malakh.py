# Build SK_Malakh_Placeholder: the player character for the Three.js POC.
# Dark monastic robe, pale skin, white hair, white wings (Malkuth stage).
# Body is one mesh; wings are separate nodes with pivots at the shoulders
# so Three.js can flap them procedurally. No armature: code-driven.
# Usage: blender -b --python build_malakh.py -- <out_dir>
import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT_DIR = argv[0]
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0


def mat(name, color, rough=0.8, metallic=0.0, emission=None, estr=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = estr
    return m


ROBE = mat("M_Malakh_Robe", (0.043, 0.043, 0.055), rough=0.92)       # charcoal black
TRIM = mat("M_Malakh_SilverTrim", (0.55, 0.56, 0.60), rough=0.35, metallic=0.9)
SKIN = mat("M_Malakh_Skin", (0.87, 0.80, 0.74), rough=0.6)           # pale
HAIR = mat("M_Malakh_Hair", (0.96, 0.96, 0.97), rough=0.45)          # white
WING = mat("M_Malakh_WingWhite", (0.98, 0.98, 1.0), rough=0.55)      # white wings (Malkuth)
EYES = mat("M_Malakh_Eyes", (0.85, 0.62, 0.10), rough=0.3, emission=(0.85, 0.55, 0.08), estr=1.5)

parts = []


def add_primitive(kind, name, loc, scale, material, rot=(0, 0, 0)):
    if kind == "uv":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc, rotation=rot)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=scale[0], radius2=scale[1], depth=scale[2],
                                        location=loc, rotation=rot)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=scale[0], depth=scale[1],
                                            location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if kind == "uv":
        obj.scale = scale
        bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = True
    parts.append(obj)
    return obj


# --- Body (joined single mesh), pivot at feet (0,0,0) ---
# Robe: flared cone from ankles to chest
add_primitive("cone", "robe", (0, 0, 0.85), (0.34, 0.19, 1.45), ROBE)
# Torso
add_primitive("uv", "torso", (0, 0, 1.42), (0.21, 0.15, 0.30), ROBE)
# Hooded shoulders
add_primitive("uv", "shoulders", (0, 0, 1.58), (0.24, 0.16, 0.14), ROBE)
# Head
add_primitive("uv", "head", (0, 0.01, 1.72), (0.105, 0.10, 0.125), SKIN)
# Hair: flattened sphere over the head, falling forward
add_primitive("uv", "hair", (0, 0.015, 1.78), (0.115, 0.115, 0.12), HAIR)
add_primitive("uv", "hairfall", (0, 0.09, 1.70), (0.09, 0.06, 0.14), HAIR)
# Eyes (small emissive amber discs)
add_primitive("uv", "eye_l", (-0.04, 0.105, 1.73), (0.016, 0.010, 0.020), EYES)
add_primitive("uv", "eye_r", (0.04, 0.105, 1.73), (0.016, 0.010, 0.020), EYES)
# Arms hanging (sleeves)
add_primitive("cyl", "arm_l", (-0.26, 0.0, 1.28), (0.055, 0.62), ROBE, rot=(0, math.radians(12), 0))
add_primitive("cyl", "arm_r", (0.26, 0.0, 1.28), (0.055, 0.62), ROBE, rot=(0, math.radians(-12), 0))
# Hands
add_primitive("uv", "hand_l", (-0.33, 0.0, 0.98), (0.05, 0.04, 0.07), SKIN)
add_primitive("uv", "hand_r", (0.33, 0.0, 0.98), (0.05, 0.04, 0.07), SKIN)
# Silver trim belt + hem
add_primitive("cyl", "belt", (0, 0, 1.12), (0.215, 0.05), TRIM)
add_primitive("cyl", "hem", (0, 0, 0.16), (0.335, 0.04), TRIM)

bpy.ops.object.select_all(action="DESELECT")
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
body = bpy.context.active_object
body.name = "Malakh_Body"
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
bpy.context.scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR")


# --- Wings: separate meshes, origin at the shoulder joint ---
def build_wing(name, side):
    """Fan of 3 layered feather plates; origin at shoulder (0, z=1.55)."""
    shoulder = Vector((0.16 * side, -0.07, 1.55))
    wing_parts = []
    for i, (length, lift, drop) in enumerate([(0.95, 0.28, 0.10), (0.75, 0.16, 0.02), (0.55, 0.06, -0.05)]):
        bm = bmesh.new()
        # Feather plate: tapered quad strip pointing outward-back
        verts = []
        segs = 5
        for s in range(segs + 1):
            t = s / segs
            x = length * t
            z = lift * math.sin(t * math.pi * 0.62) - drop * t
            w = 0.16 * (1.0 - t * 0.55) * (1.0 - 0.35 * i / 3.0)
            verts.append((Vector((x, -w, z)), Vector((x, w, z))))
        for s in range(segs):
            a0, b0 = verts[s]
            a1, b1 = verts[s + 1]
            bm.verts.new(a0)
            bm.verts.new(a1)
            bm.verts.new(b1)
            bm.verts.new(a0)
            v = list(bm.verts)[-4:]
            bm.faces.new(v)
        mesh = bpy.data.meshes.new(name + "_plate")
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name + "_plate%d" % i, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(WING)
        # Mirror for right side, fold slightly back and down per layer
        obj.scale = (side, 1, 1)
        obj.rotation_euler = (math.radians(-8 - i * 7), math.radians(side * (10 + i * 8)), 0)
        obj.location = (0, -0.02 * i, -0.03 * i)
        wing_parts.append(obj)

    bpy.ops.object.select_all(action="DESELECT")
    for o in wing_parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = wing_parts[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    wing = bpy.context.active_object
    wing.name = name
    # Solidify for thickness
    mod = wing.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = 0.015
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # Place so origin sits at the shoulder
    wing.location = shoulder
    return wing


wing_l = build_wing("Malakh_Wing_L", 1)
wing_r = build_wing("Malakh_Wing_R", -1)

# Fold wings: rotate down/back so they rest closed (POC reads silhouette)
wing_l.rotation_euler = (math.radians(18), math.radians(-58), math.radians(6))
wing_r.rotation_euler = (math.radians(18), math.radians(58), math.radians(-6))

bpy.ops.object.select_all(action="DESELECT")
for o in (body, wing_l, wing_r):
    o.select_set(True)
bpy.context.view_layer.objects.active = body

path = os.path.join(OUT_DIR, "SK_Malakh_Placeholder.glb")
bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_apply=False,
                          export_animations=False, export_yup=True)
print("MALAKH_DONE", path)
