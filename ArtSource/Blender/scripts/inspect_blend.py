# Inspect a .blend file: list collections, objects, dimensions and materials.
# Usage: blender -b <file.blend> --python inspect_blend.py
import bpy
import json

data = {"collections": [], "objects": []}

for col in bpy.data.collections:
    data["collections"].append({"name": col.name, "objects": len(col.objects)})

for obj in bpy.data.objects:
    dims = [round(d, 3) for d in obj.dimensions] if obj.type == "MESH" else None
    mats = []
    if obj.type == "MESH":
        mats = [ms.material.name for ms in obj.material_slots if ms.material]
    data["objects"].append({
        "name": obj.name,
        "type": obj.type,
        "dims": dims,
        "materials": mats,
        "collections": [c.name for c in obj.users_collection],
    })

out = "INSPECT_JSON_BEGIN" + json.dumps(data) + "INSPECT_JSON_END"
print(out)

with open(bpy.path.abspath("//inspect_output.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1)
