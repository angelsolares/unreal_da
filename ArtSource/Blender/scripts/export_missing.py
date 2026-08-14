# Export specific objects to individual GLBs.
# Usage:
#   blender -b <file.blend> --python export_missing.py -- <out_dir> <obj1> [obj2 ...]
import bpy
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:]
OUT_DIR = argv[0]
NAMES = argv[1:]

os.makedirs(OUT_DIR, exist_ok=True)

for name in NAMES:
    obj = bpy.data.objects.get(name)
    if obj is None:
        print("MISSING " + name)
        continue
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(OUT_DIR, name + ".glb"),
        use_selection=True,
        export_apply=False,
        export_animations=False,
        export_yup=True,
    )
    print("EXPORTED " + name)

print("MISSING_DONE")
