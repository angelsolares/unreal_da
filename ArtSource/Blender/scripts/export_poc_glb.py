# Export curated Malkuth POC assets to GLB for the Three.js demo.
# Usage:
#   blender -b <file.blend> --python export_poc_glb.py -- <out_dir> <garden|allkits>
import bpy
import json
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:]
OUT_DIR = argv[0]
MODE = argv[1]

os.makedirs(OUT_DIR, exist_ok=True)

# Each entry: output name -> list of object names to include (first is primary)
GARDEN = {
    "SM_MGK_Hedge_Straight_400": ["SM_MGK_Hedge_Straight_400"],
    "SM_MGK_Hedge_Straight_200": ["SM_MGK_Hedge_Straight_200"],
    "SM_MGK_Hedge_Corner_90": ["SM_MGK_Hedge_Corner_90"],
    "SM_MGK_Hedge_End": ["SM_MGK_Hedge_End"],
    "SM_MGK_Hedge_GateArch": ["SM_MGK_Hedge_GateArch"],
    "SM_MGK_Hedge_Low_200": ["SM_MGK_Hedge_Low_200"],
    "SM_MGK_Path_Straight_300": ["SM_MGK_Path_Straight_300"],
    "SM_MGK_Path_Plaza_600": ["SM_MGK_Path_Plaza_600"],
    "SM_MGK_Fountain_Octagonal": [
        "SM_MGK_Fountain_Octagonal_Centerpiece",
        "SM_MGK_Fountain_Octagonal_Centerpiece_Water",
        "SM_MGK_Fountain_Octagonal_Centerpiece_WaterUpper",
    ],
    "SM_MGK_Fountain_Round_Small": [
        "SM_MGK_Fountain_Round_Small",
        "SM_MGK_Fountain_Round_Small_Water",
    ],
    "SM_MGK_Bench_Straight_A": ["SM_MGK_Bench_Straight_A"],
    "SM_MGK_GardenLamp": ["SM_MGK_GardenLamp"],
    "SM_MGK_Topiary_Sphere": ["SM_MGK_Topiary_Sphere"],
    "SM_MGK_Topiary_Spiral": ["SM_MGK_Topiary_Spiral"],
    "SM_MGK_Flowerbed_Round": ["SM_MGK_Flowerbed_Round"],
    "SM_MGK_Trellis_Arch": ["SM_MGK_Trellis_Arch"],
}

ALLKITS = {
    # Ruins
    "SM_MRK_Column_Intact_400": ["SM_MRK_Column_Intact_400"],
    "SM_MRK_Column_Intact_600": ["SM_MRK_Column_Intact_600"],
    "SM_MRK_Column_Broken_A": ["SM_MRK_Column_Broken_A"],
    "SM_MRK_Column_Fallen_400": ["SM_MRK_Column_Fallen_400"],
    "SM_MRK_Column_CollapsedCluster": ["SM_MRK_Column_CollapsedCluster"],
    "SM_MRK_Obelisk_400": ["SM_MRK_Obelisk_400"],
    "SM_MRK_Obelisk_700": ["SM_MRK_Obelisk_700"],
    "SM_MRK_Dome_HalfBroken_800": ["SM_MRK_Dome_HalfBroken_800"],
    "SM_MRK_Pedestal_Square_150": ["SM_MRK_Pedestal_Square_150"],
    "SM_MRK_StatueBase_200": ["SM_MRK_StatueBase_200"],
    "SM_MRK_RuinedArch_300": ["SM_MRK_RuinedArch_300"],
    "SM_MRK_RubbleCluster_A": ["SM_MRK_RubbleCluster_A"],
    # Sanctuary
    "SM_MSK_Trunk_Twisted_800": ["SM_MSK_Trunk_Twisted_800"],
    "SM_MSK_Trunk_Straight_600": ["SM_MSK_Trunk_Straight_600"],
    "SM_MSK_CanopyCluster": ["SM_MSK_CanopyCluster"],
    "SM_MSK_Altar_Main_300": ["SM_MSK_Altar_Main_300"],
    "SM_MSK_RitualCircle_400": ["SM_MSK_RitualCircle_400"],
    "SM_MSK_RootCluster_A": ["SM_MSK_RootCluster_A"],
    "SM_MSK_FlowerCluster": ["SM_MSK_FlowerCluster"],
    "SM_MSK_Barrier_ThornStraight_300": ["SM_MSK_Barrier_ThornStraight_300"],
    "SM_MSK_SanctuaryArch": ["SM_MSK_SanctuaryArch"],
    # Mirror labyrinth (frame + separate mirror surface node)
    "SM_MMLK_Mirror_Straight_200x300": [
        "SM_MMLK_Mirror_Straight_200x300",
        "SM_MMLK_Mirror_Straight_200x300_MirrorSurface",
    ],
    "SM_MMLK_Mirror_Cracked_A": [
        "SM_MMLK_Mirror_Cracked_A",
        "SM_MMLK_Mirror_Cracked_A_MirrorSurface",
    ],
    "SM_MMLK_Mirror_Broken": [
        "SM_MMLK_Mirror_Broken",
        "SM_MMLK_Mirror_Broken_MirrorSurface",
    ],
    "SM_MMLK_Post_Ornate": ["SM_MMLK_Post_Ornate"],
    "SM_MMLK_CentralOculus": [
        "SM_MMLK_CentralOculus",
        "SM_MMLK_CentralOculus_MirrorSurface",
    ],
    # Props
    "SM_MP_Throne_Malkuth_Main": ["SM_MP_Throne_Malkuth_Main"],
    "SM_MP_Throne_Dais_400": ["SM_MP_Throne_Dais_400"],
    "SM_MP_Portal_Arch_500": ["SM_MP_Portal_Arch_500"],
    "SM_MP_Portal_RuneRing": ["SM_MP_Portal_RuneRing"],
    "SM_MP_PortalSurface_Preview": ["SM_MP_PortalSurface_Preview"],
    "SM_MP_PortalSteps": ["SM_MP_PortalSteps"],
    "SM_MP_Bridge_Straight_300x1200": ["SM_MP_Bridge_Straight_300x1200"],
    "SM_MP_BridgeRailing_300": ["SM_MP_BridgeRailing_300"],
    "SM_MP_Bridge_Pillar": ["SM_MP_Bridge_Pillar"],
    "SM_MP_Stair_Wide_600x600": ["SM_MP_Stair_Wide_600x600"],
    # Angels (skinned: rig + body + wings)
    "SK_MAP_Messenger": ["RIG_MAP_Messenger", "SK_MAP_Messenger", "SK_MAP_Messenger_Wings"],
    "SK_MAP_Archangel": ["RIG_MAP_Archangel", "SK_MAP_Archangel", "SK_MAP_Archangel_Wings"],
    "SK_MAP_Gabriel_Base": ["RIG_MAP_Gabriel", "SK_MAP_Gabriel_Base", "SK_MAP_Gabriel_Base_Wings"],
    # Attachments
    "SM_MAP_Sword_Ceremonial": ["SM_MAP_Sword_Ceremonial"],
    "SM_MAP_Spear_Light": ["SM_MAP_Spear_Light"],
    "SM_MAP_HaloRing": ["SM_MAP_HaloRing"],
    "SM_MAP_GabrielBlade": ["SM_MAP_GabrielBlade"],
}

MANIFEST = GARDEN if MODE == "garden" else ALLKITS
report = {"exported": [], "missing": [], "bones": {}}

# Dump armature bone names so the Three.js side can animate them by name
for arm in bpy.data.armatures:
    report["bones"][arm.name] = [b.name for b in arm.bones]


def export_group(out_name, obj_names):
    bpy.ops.object.select_all(action="DESELECT")
    found = []
    for name in obj_names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            report["missing"].append(name)
            continue
        obj.select_set(True)
        found.append(obj)
    if not found:
        return
    bpy.context.view_layer.objects.active = found[0]
    path = os.path.join(OUT_DIR, out_name + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        use_selection=True,
        export_apply=False,
        export_animations=False,
        export_skins=True,
        export_morph=False,
        export_yup=True,
    )
    report["exported"].append(out_name)


def build_angel_terrestrial():
    """Kitbash: Archangel body+wings as a stone monument with roots and pedestal."""
    body = bpy.data.objects.get("SK_MAP_Archangel")
    wings = bpy.data.objects.get("SK_MAP_Archangel_Wings")
    base = bpy.data.objects.get("SM_MRK_StatueBase_200")
    roots = bpy.data.objects.get("SM_MSK_RootCluster_A")
    if not (body and wings and base):
        return
    bpy.ops.object.select_all(action="DESELECT")
    dupes = []
    for src in (body, wings, base, roots):
        if src is None:
            continue
        d = src.copy()
        d.data = src.data.copy()
        d.modifiers.clear()
        d.parent = None
        bpy.context.scene.collection.objects.link(d)
        dupes.append(d)
    body_d, wings_d, base_d, roots_d = dupes[0], dupes[1], dupes[2], dupes[3]

    stone = bpy.data.materials.get("M_MRK_Stone_Dark") or bpy.data.materials.new("M_Statue_Stone")
    gold = bpy.data.materials.get("M_MRK_Gold_Aged")
    body_d.data.materials.clear()
    body_d.data.materials.append(stone)
    wings_d.data.materials.clear()
    wings_d.data.materials.append(stone)
    if gold:
        wings_d.data.materials.append(gold)

    scale = 3.2
    for d in (body_d, wings_d):
        d.scale = (scale, scale, scale)
        d.location = (0, 0, 1.5)  # on top of the 1.5 m statue base
    base_d.location = (0, 0, 0)
    roots_d.location = (0, 0, 0)
    roots_d.scale = (1.6, 1.6, 1.2)

    bpy.ops.object.select_all(action="DESELECT")
    for d in dupes:
        d.select_set(True)
    bpy.context.view_layer.objects.active = body_d
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join()
    body_d.name = "SM_AngelTerrestrial"
    body_d.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

    path = os.path.join(OUT_DIR, "SM_AngelTerrestrial.glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        use_selection=True,
        export_apply=False,
        export_animations=False,
        export_yup=True,
    )
    report["exported"].append("SM_AngelTerrestrial")
    bpy.data.objects.remove(body_d, do_unlink=True)


for out_name, obj_names in MANIFEST.items():
    export_group(out_name, obj_names)

if MODE == "allkits":
    build_angel_terrestrial()

with open(os.path.join(OUT_DIR, "export_report_%s.json" % MODE), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1)

print("EXPORT_DONE mode=%s exported=%d missing=%d" % (MODE, len(report["exported"]), len(report["missing"])))
