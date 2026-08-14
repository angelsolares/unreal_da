"""
Build all remaining Dark Angels Malkuth kits for UE5.8.
Run: blender --background --python build_all_malkuth_kits.py
"""
import bpy
import bmesh
import math
import random
import sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(r'd:/Game Projects/Unreal DA/DarkAngelsPOC 5.8')
SCRIPTS = ROOT / 'ArtSource' / 'Blender' / 'scripts'
CONTENT = ROOT / 'Content' / 'Blender'
ART = ROOT / 'ArtSource' / 'Blender'
sys.path.insert(0, str(SCRIPTS))

import da_kit_core as core  # noqa: E402

rng = random.Random(42)
IVORY = ['M_DA_Stone_Ivory', 'M_DA_Stone_Dark', 'M_DA_Gold_Aged']


def reset_scene():
    # Keep default world; clear mesh/armature objects carefully? For background start fresh.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    core.setup_metric()


def shared_mats():
    specs = [
        ('M_DA_Stone_Ivory', (0.86, 0.82, 0.74), 0.62, 0, None, 0),
        ('M_DA_Stone_Dark', (0.35, 0.33, 0.30), 0.7, 0, None, 0),
        ('M_DA_Gold_Aged', (0.72, 0.58, 0.28), 0.45, 0.65, (0.85, 0.7, 0.35), 0.08),
        ('M_DA_Moss', (0.22, 0.38, 0.18), 0.8, 0, None, 0),
        ('M_DA_Soil', (0.28, 0.2, 0.12), 0.9, 0, None, 0),
        ('M_DA_Bark_Pale', (0.55, 0.42, 0.28), 0.75, 0, None, 0),
        ('M_DA_Bark_Dark', (0.28, 0.18, 0.12), 0.8, 0, None, 0),
        ('M_DA_Leaves_Emerald', (0.12, 0.42, 0.22), 0.75, 0, None, 0),
        ('M_DA_Leaves_Olive', (0.28, 0.36, 0.14), 0.78, 0, None, 0),
        ('M_DA_Flower_White', (0.92, 0.92, 0.9), 0.55, 0, (0.95, 0.95, 0.9), 0.05),
        ('M_DA_Flower_Purple', (0.42, 0.22, 0.55), 0.55, 0, (0.5, 0.25, 0.65), 0.08),
        ('M_DA_Wood_Pale', (0.62, 0.48, 0.32), 0.7, 0, None, 0),
        ('M_DA_Mirror', (0.7, 0.8, 0.9), 0.05, 0.9, (0.6, 0.75, 0.95), 0.2),
        ('M_DA_Mirror_Damaged', (0.45, 0.5, 0.55), 0.25, 0.5, None, 0),
        ('M_DA_Emissive_Purple', (0.5, 0.25, 0.7), 0.4, 0, (0.55, 0.3, 0.85), 0.6),
        ('M_DA_Emissive_Gold', (0.95, 0.85, 0.45), 0.35, 0.2, (1.0, 0.9, 0.5), 0.5),
        ('M_DA_Portal', (0.35, 0.2, 0.55), 0.15, 0.1, (0.45, 0.25, 0.75), 0.8),
        ('M_DA_Body', (0.85, 0.78, 0.7), 0.55, 0, None, 0),
        ('M_DA_Cloth', (0.9, 0.88, 0.82), 0.65, 0, None, 0),
        ('M_DA_Wings_White', (0.95, 0.95, 0.92), 0.45, 0, (1, 1, 0.95), 0.1),
        ('M_DA_Wings_Shadow', (0.25, 0.2, 0.35), 0.6, 0, None, 0),
        ('M_DA_Water', (0.35, 0.55, 0.65), 0.08, 0, (0.4, 0.65, 0.75), 0.25),
    ]
    for n, c, r, m, e, es in specs:
        core.ensure_mat(n, c, r, m, e, es)
    # kit aliases
    aliases = {
        'M_MRK_Stone_Ivory': 'M_DA_Stone_Ivory', 'M_MRK_Stone_Dark': 'M_DA_Stone_Dark',
        'M_MRK_Gold_Aged': 'M_DA_Gold_Aged', 'M_MRK_Moss': 'M_DA_Moss', 'M_MRK_Soil': 'M_DA_Soil',
        'M_MRK_Emissive_Subtle': 'M_DA_Emissive_Gold',
        'M_MSK_Bark_Pale': 'M_DA_Bark_Pale', 'M_MSK_Bark_Dark': 'M_DA_Bark_Dark',
        'M_MSK_Leaves_Emerald': 'M_DA_Leaves_Emerald', 'M_MSK_Leaves_Olive': 'M_DA_Leaves_Olive',
        'M_MSK_Stone_Ivory': 'M_DA_Stone_Ivory', 'M_MSK_Gold_Aged': 'M_DA_Gold_Aged',
        'M_MSK_Flower_White': 'M_DA_Flower_White', 'M_MSK_Flower_Purple': 'M_DA_Flower_Purple',
        'M_MSK_Emissive_Sap': 'M_DA_Emissive_Gold',
        'M_MMLK_Frame_Ivory': 'M_DA_Stone_Ivory', 'M_MMLK_Gold_Aged': 'M_DA_Gold_Aged',
        'M_MMLK_Stone_Dark': 'M_DA_Stone_Dark', 'M_MMLK_Mirror_Preview': 'M_DA_Mirror',
        'M_MMLK_Mirror_Damaged': 'M_DA_Mirror_Damaged', 'M_MMLK_Emissive_Purple': 'M_DA_Emissive_Purple',
        'M_MP_Stone_Ivory': 'M_DA_Stone_Ivory', 'M_MP_Stone_Dark': 'M_DA_Stone_Dark',
        'M_MP_Gold_Aged': 'M_DA_Gold_Aged', 'M_MP_Wood_Pale': 'M_DA_Wood_Pale',
        'M_MP_Roots': 'M_DA_Bark_Dark', 'M_MP_Emissive_Purple': 'M_DA_Emissive_Purple',
        'M_MP_Emissive_Gold': 'M_DA_Emissive_Gold', 'M_MP_Portal_Preview': 'M_DA_Portal',
        'M_MAP_Body_StonePale': 'M_DA_Body', 'M_MAP_Cloth_Ivory': 'M_DA_Cloth',
        'M_MAP_Armor_GoldAged': 'M_DA_Gold_Aged', 'M_MAP_Leather_Pale': 'M_DA_Wood_Pale',
        'M_MAP_Wings_White': 'M_DA_Wings_White', 'M_MAP_Wings_Shadow': 'M_DA_Wings_Shadow',
        'M_MAP_Emissive_Subtle': 'M_DA_Emissive_Gold', 'M_MAP_Emissive_Gabriel': 'M_DA_Emissive_Purple',
    }
    for alias, src in aliases.items():
        if bpy.data.materials.get(alias) is None and bpy.data.materials.get(src):
            m = bpy.data.materials.get(src).copy()
            m.name = alias


def fm(name, col, bm, mats, origin=(0, 0, 0), ucx=None, ucx_col=None):
    obj = core.finish_mesh(name, col, bm, origin, mats, bevel=0.0)
    if ucx and ucx_col:
        if isinstance(ucx[0], (int, float)):
            core.make_ucx(name, 0, ucx, (0, 0, 0), ucx_col)
        else:
            for i, (dims, loc) in enumerate(ucx):
                core.make_ucx(name, i, dims, loc, ucx_col)
    return obj


# ===================== RUINS =====================
def build_ruins():
    core.ensure_kit_collections('SM_Malkuth_RuinsKit', [
        'MRK_Columns', 'MRK_Domes', 'MRK_Pedestals', 'MRK_Obelisks', 'MRK_Extras',
        'MRK_Collisions', 'MRK_Showcase'])
    S, D, G, M = 'M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged', 'M_MRK_Moss'
    mats = [S, D, G]

    def col(name, h, r, broken=False, half=False):
        bm = bmesh.new()
        core.add_box(bm, r * 2.4, r * 2.4, 0.15, (0, 0, 0), 0)
        core.add_cyl(bm, r * 1.3, 0.2, (0, 0, 0.15), 12, 0)
        sh = h - 0.55
        if broken:
            sh = h * 0.7
        if half:
            core.add_box(bm, r * 1.1, r * 0.55, sh, (0, -r * 0.2, 0.35), 0)
        else:
            core.add_cyl(bm, r, sh, (0, 0, 0.35), 12, 0)
        if broken:
            core.add_ico(bm, r * 0.55, (r * 0.15, 0, 0.35 + sh), 0, 1)
        else:
            core.add_cyl(bm, r * 1.2, 0.15, (0, 0, 0.35 + sh), 12, 0)
            core.add_box(bm, r * 2.4, r * 2.4, 0.1, (0, 0, 0.5 + sh), 2)
        fm(name, 'MRK_Columns', bm, mats, ucx=(r * 2.5, r * 2.5, h), ucx_col='MRK_Collisions')

    col('SM_MRK_Column_Intact_400', 4, 0.4)
    col('SM_MRK_Column_Intact_600', 6, 0.5)
    col('SM_MRK_Column_Half_250', 2.5, 0.4, broken=True, half=True)
    col('SM_MRK_Column_Broken_A', 2.2, 0.38, broken=True)
    col('SM_MRK_Column_Broken_B', 1.4, 0.36, broken=True)

    bm = bmesh.new(); core.add_box(bm, 1.2, 1.2, 0.2); core.add_cyl(bm, 0.55, 0.25, (0, 0, 0.2), 12, 0)
    fm('SM_MRK_Column_Base', 'MRK_Columns', bm, mats, ucx=(1.2, 1.2, 0.45), ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.3, 1.3, 0.2); core.add_cyl(bm, 0.55, 0.25, (0, 0, 0.15), 12, 2); core.add_box(bm, 0.9, 0.9, 0.2, (0, 0, 0.35))
    fm('SM_MRK_Column_Capital', 'MRK_Columns', bm, mats, ucx=(1.3, 1.3, 0.55), ucx_col='MRK_Collisions')

    bm = bmesh.new()
    for y, l, r in [(1.0, 2.0, 0.4), (3.0, 1.6, 0.35)]:
        ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r, depth=l)
        bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 4, 'X'))
        bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((0, y, 0.4)))
    core.add_box(bm, 1.1, 1.1, 0.25, (0, 0.2, 0))
    fm('SM_MRK_Column_Fallen_400', 'MRK_Columns', bm, mats, ucx=(1.2, 4.0, 0.9), ucx_col='MRK_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 1.2, 1.2, 0.35, (-0.8, -0.5, 0))
    core.add_cyl(bm, 0.35, 2.0, (0.5, 0.2, 0.35), 10, 0)
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.3, radius2=0.3, depth=1.5)
    bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(75), 4, 'X'))
    bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((-0.2, 1.2, 0.5)))
    core.add_box(bm, 1.1, 1.1, 0.3, (1.2, -0.8, 0)); core.add_ico(bm, 0.35, (1.0, 0.8, 0.35), 0, 3)
    fm('SM_MRK_Column_CollapsedCluster', 'MRK_Columns', bm, [S, D, G, M], ucx=(4, 3, 1.5), ucx_col='MRK_Collisions')

    # Pedestals
    for name, s, h in [('SM_MRK_Pedestal_Square_100', 1.0, 0.8), ('SM_MRK_Pedestal_Square_150', 1.5, 1.2)]:
        bm = bmesh.new(); core.add_box(bm, s, s, 0.2); core.add_box(bm, s * 0.85, s * 0.85, h - 0.2, (0, 0, 0.2))
        if s > 1.2: core.add_box(bm, s * 0.9, s * 0.9, 0.1, (0, 0, h - 0.1), 2)
        fm(name, 'MRK_Pedestals', bm, mats, ucx=(s, s, h), ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 0.6, 0.2); core.add_cyl(bm, 0.5, 0.7, (0, 0, 0.2), 14, 0)
    fm('SM_MRK_Pedestal_Round_120', 'MRK_Pedestals', bm, mats, ucx=(1.2, 1.2, 0.9), ucx_col='MRK_Collisions')
    bm = bmesh.new()
    for z, s in [(0, 2), (0.25, 1.7), (0.6, 1.4), (1.2, 1.2)]:
        core.add_box(bm, s, s, 0.3 if z < 1 else 0.3, (0, 0, z))
    fm('SM_MRK_StatueBase_200', 'MRK_Pedestals', bm, mats, ucx=(2, 2, 1.5), ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.5, 1.5, 0.25); core.add_box(bm, 1.2, 1.2, 0.7, (0, 0, 0.25)); core.add_box(bm, 0.8, 0.55, 0.45, (0.4, -0.2, 0.3), 1); core.add_ico(bm, 0.25, (0.55, 0.4, 0.25), 0, 3)
    fm('SM_MRK_Pedestal_Broken', 'MRK_Pedestals', bm, [S, D, G, M], ucx=(1.5, 1.5, 1.0), ucx_col='MRK_Collisions')

    # Obelisks
    def obelisk(name, h, base):
        bm = bmesh.new(); core.add_box(bm, base, base, 0.25); core.add_box(bm, base * 0.75, base * 0.75, 0.2, (0, 0, 0.25))
        steps = 7
        for i in range(steps):
            t = i / steps; s = base * 0.55 * (1 - t * 0.55); z = 0.45 + t * (h - 0.9); hh = (h - 0.9) / steps
            core.add_box(bm, s, s, hh, (0, 0, z)); 
            if i % 2 == 0: core.add_box(bm, s * 1.02, 0.03, hh * 0.7, (0, s * 0.5, z), 2)
        core.add_box(bm, base * 0.12, base * 0.12, 0.3, (0, 0, h - 0.4), 2)
        fm(name, 'MRK_Obelisks', bm, mats, ucx=(base, base, h), ucx_col='MRK_Collisions')
    obelisk('SM_MRK_Obelisk_400', 4, 1.2); obelisk('SM_MRK_Obelisk_700', 7, 1.8)
    bm = bmesh.new(); core.add_box(bm, 1, 1, 0.2)
    for i in range(5): core.add_box(bm, 0.7 * (1 - i * 0.1), 0.7 * (1 - i * 0.1), 0.45, (0, 0, 0.2 + i * 0.45))
    core.add_box(bm, 0.45, 0.45, 0.8, (0.35, 0.2, 0.5), 1)
    fm('SM_MRK_Obelisk_Broken', 'MRK_Obelisks', bm, mats, ucx=(1.4, 1.4, 3), ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.4, 1.4, 0.3, (0, 0.3, 0))
    for i in range(6):
        s = 0.7 * (1 - i * 0.08); core.add_box(bm, s, 0.7, s, (0.1, 1.0 + i * 0.7, 0.35))
    fm('SM_MRK_Obelisk_Fallen', 'MRK_Obelisks', bm, mats, ucx=(1.6, 5, 1), ucx_col='MRK_Collisions')

    # Domes simplified
    bm = bmesh.new()
    for i in range(5):
        t = i / 5; rad = 3.0 * math.cos(t * math.pi * 0.5); z = 3.0 * math.sin(t * math.pi * 0.5)
        core.add_cyl(bm, max(0.4, rad), 0.4, (0, 0, z), 8, 0)
        # cut to quarter by removing - use boxes in quarter only
    bm.free()
    bm = bmesh.new()
    for i in range(6):
        t = i / 6; r = 3 * (1 - t * 0.85); z = t * 2.8
        for a in [0.2, 0.6, 1.0, 1.4]:
            core.add_box(bm, 0.55, 0.35, 0.45, (math.cos(a) * r, math.sin(a) * r, z))
    fm('SM_MRK_Dome_Quarter_600', 'MRK_Domes', bm, mats, ucx=(3.2, 3.2, 3.2), ucx_col='MRK_Collisions')

    bm = bmesh.new()
    for i in range(7):
        t = i / 7; r = 4 * (1 - t * 0.85); z = t * 3.6
        for k in range(8):
            a = -math.pi * 0.45 + k * (math.pi * 0.9 / 8)
            core.add_box(bm, 0.6, 0.4, 0.5, (math.cos(a) * r, math.sin(a) * r, z))
    fm('SM_MRK_Dome_HalfBroken_800', 'MRK_Domes', bm, mats, ucx=(4.5, 8, 4), ucx_col='MRK_Collisions')

    bm = bmesh.new()
    for i in range(8):
        t = i / 7; ang = t * math.pi * 0.5
        core.add_box(bm, 0.25, 0.35, 0.35, (math.cos(ang) * 2, 0, math.sin(ang) * 2))
    fm('SM_MRK_Dome_Rib_400', 'MRK_Domes', bm, mats, ucx=(2.2, 0.5, 2.2), ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 1.4, 0.35, segments=12); core.add_cyl(bm, 1.0, 0.5, (0, 0, 0.3), 10, 0, 0.4); core.add_box(bm, 0.8, 0.8, 0.2, (0.6, 0.4, 0.1), 1)
    fm('SM_MRK_Dome_CapFragment', 'MRK_Domes', bm, mats, ucx=(3, 3, 1), ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 4, 0.4, segments=16); core.add_cyl(bm, 3.4, 0.2, (0, 0, 0.35), 16, 1)
    for i in range(4):
        a = i * math.tau / 4; core.add_cyl(bm, 0.35, 1.8, (math.cos(a) * 3.2, math.sin(a) * 3.2, 0.4), 8, 0)
    fm('SM_MRK_Rotunda_Ruin_800', 'MRK_Domes', bm, mats,
       ucx=[((8, 8, 0.5), (0, 0, 0))] + [((0.8, 0.8, 2.2), (math.cos(i * math.tau / 4) * 3.2, math.sin(i * math.tau / 4) * 3.2, 0.4)) for i in range(4)],
       ucx_col='MRK_Collisions')

    # Extras
    bm = bmesh.new(); core.add_box(bm, 0.7, 0.7, 3.4, (-2, 0, 0)); core.add_box(bm, 0.7, 0.7, 3.0, (2, 0, 0)); core.add_box(bm, 4.6, 0.7, 0.55, (0, 0, 3.2)); core.add_box(bm, 0.5, 0.5, 0.8, (-0.3, 0.2, 2.6), 1)
    fm('SM_MRK_RuinedArch_300', 'MRK_Extras', bm, mats, ucx=[((0.8, 0.8, 3.5), (-2, 0, 0)), ((0.8, 0.8, 3.2), (2, 0, 0)), ((4.6, 0.8, 0.6), (0, 0, 3.2))], ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 0.45, 3.0, 1.8, (0, 1.5, 0)); core.add_box(bm, 0.45, 2.2, 0.7, (0, 1.4, 1.8)); core.add_box(bm, 0.45, 1.0, 0.5, (0, 0.8, 2.3), 1); core.add_ico(bm, 0.15, (0.3, 2.5, 0.15), 0, 3)
    fm('SM_MRK_WallFragment_300', 'MRK_Extras', bm, [S, D, G, M], ucx=(0.5, 3, 2.6), ucx_col='MRK_Collisions')
    bm = bmesh.new()
    for i in range(8):
        core.add_box(bm, 0.35 + rng.random() * 0.4, 0.35 + rng.random() * 0.4, 0.2 + rng.random() * 0.4,
                     ((rng.random() - 0.5) * 1.5, (rng.random() - 0.5) * 1.5, 0), i % 2)
    fm('SM_MRK_RubbleCluster_A', 'MRK_Extras', bm, [S, D, G, M], ucx=(2, 2, 0.8), ucx_col='MRK_Collisions')
    bm = bmesh.new()
    for i in range(10):
        core.add_box(bm, 0.35, 0.5, 0.25, ((rng.random() - 0.5), -1.3 + i * 0.28, 0), i % 2)
    fm('SM_MRK_RubbleCluster_B', 'MRK_Extras', bm, [S, D, G, M], ucx=(1.5, 3, 0.7), ucx_col='MRK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.2, 0.35, 2.2)
    for i in range(5): core.add_box(bm, 0.9, 0.05, 0.05, (0, -0.2, 0.4 + i * 0.3), 2)
    core.add_box(bm, 0.4, 0.05, 0.4, (0, -0.22, 1.5), 5)
    fm('SM_MRK_InscribedSlab', 'MRK_Extras', bm, [S, D, G, M, 'M_MRK_Soil', 'M_MRK_Emissive_Subtle'], ucx=(1.2, 0.4, 2.2), ucx_col='MRK_Collisions')

    names = [o.name for o in bpy.data.objects if o.name.startswith('SM_MRK_')]
    core.write_qa('MRK_QA_Report', [f'RUINS assets={len(names)}'] + [f'- {n}' for n in sorted(names)])
    return names


# ===================== SANCTUARY =====================
def build_sanctuary():
    core.ensure_kit_collections('SM_Malkuth_SanctuaryKit', [
        'MSK_Trunks', 'MSK_BranchesRoots', 'MSK_Altars', 'MSK_Barriers', 'MSK_Extras',
        'MSK_Collisions', 'MSK_Showcase'])
    BP, BD, LE, LO, S, G, FW, FP = (
        'M_MSK_Bark_Pale', 'M_MSK_Bark_Dark', 'M_MSK_Leaves_Emerald', 'M_MSK_Leaves_Olive',
        'M_MSK_Stone_Ivory', 'M_MSK_Gold_Aged', 'M_MSK_Flower_White', 'M_MSK_Flower_Purple')

    def trunk(name, h, r_base, twist=False, hollow=False, split=False):
        bm = bmesh.new()
        steps = 8
        for i in range(steps):
            t = i / steps
            r = r_base * (1 - t * 0.35)
            z = t * h
            off = (math.sin(t * 4) * 0.25, math.cos(t * 3) * 0.2, 0) if twist else (0, 0, 0)
            core.add_cyl(bm, r, h / steps + 0.05, (off[0], off[1], z), 8, 0 if i % 2 == 0 else 1)
        if hollow:
            # opening
            core.add_box(bm, r_base * 1.2, 0.2, min(2.2, h * 0.45), (0, -r_base * 0.3, 0.3), 1)
        if split:
            for side in (-1, 1):
                for i in range(4):
                    t = i / 4
                    core.add_cyl(bm, r_base * 0.35 * (1 - t * 0.3), 1.2,
                                 (side * (0.4 + t), t * 0.3, h * 0.55 + t * 1.5), 6, 0)
        fm(name, 'MSK_Trunks', bm, [BP, BD], ucx=(r_base * 2.2, r_base * 2.2, h), ucx_col='MSK_Collisions')

    trunk('SM_MSK_Trunk_Straight_600', 6, 0.55)
    trunk('SM_MSK_Trunk_Twisted_800', 8, 0.9, twist=True)
    trunk('SM_MSK_Trunk_Hollow_500', 5, 0.7, hollow=True)
    trunk('SM_MSK_Trunk_Split_700', 7, 0.75, split=True)
    bm = bmesh.new(); core.add_cyl(bm, 0.7, 0.8, segments=10); core.add_cyl(bm, 0.9, 0.25, (0, 0, 0), 10, 1)
    for a in range(5):
        ang = a * math.tau / 5; core.add_cyl(bm, 0.12, 0.8, (math.cos(ang) * 0.7, math.sin(ang) * 0.7, 0.1), 5, 1)
        ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.12, radius2=0.08, depth=0.9)
        bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 4, 'X'))
        bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((math.cos(ang) * 1.0, math.sin(ang) * 1.0, 0.15)))
    fm('SM_MSK_Stump_150', 'MSK_Trunks', bm, [BP, BD], ucx=(2, 2, 1.5), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 2.0, 0.6, segments=12); core.add_cyl(bm, 1.2, 0.8, (0, 0, 0.5), 10, 1)
    for i in range(6):
        a = i * math.tau / 6; core.add_box(bm, 0.35, 1.2, 0.35, (math.cos(a) * 1.5, math.sin(a) * 1.5, 0.1), 1)
    fm('SM_MSK_TrunkBase_400', 'MSK_Trunks', bm, [BP, BD], ucx=(4, 4, 1.4), ucx_col='MSK_Collisions')

    # Branches / roots
    def branch(name, length, curved=False, fork=False, arch=False):
        bm = bmesh.new()
        if arch:
            for i in range(10):
                t = i / 9; a = t * math.pi
                core.add_cyl(bm, 0.18, 0.7, (math.cos(a) * 3, 0, math.sin(a) * 3.0 + 0.2), 6, 0)
            fm(name, 'MSK_BranchesRoots', bm, [BP, BD, LE], ucx=[((0.5, 0.5, 3.4), (-3, 0, 0)), ((0.5, 0.5, 3.4), (3, 0, 0)), ((6.2, 0.5, 0.5), (0, 0, 3.2))], ucx_col='MSK_Collisions')
            return
        steps = 6
        for i in range(steps):
            t = i / steps
            y = t * length
            x = math.sin(t * math.pi) * (1.2 if curved else 0)
            z = t * 0.4 if curved else 0.2
            core.add_cyl(bm, 0.16 * (1 - t * 0.4), length / steps + 0.05, (x, y, z), 6, 0)
        if fork:
            for side in (-1, 1):
                core.add_cyl(bm, 0.12, length * 0.45, (side * 0.5, length * 0.55, 0.5), 5, 1)
        fm(name, 'MSK_BranchesRoots', bm, [BP, BD], ucx=(1.5, length, 1.2), ucx_col='MSK_Collisions')

    branch('SM_MSK_Branch_Straight_300', 3)
    branch('SM_MSK_Branch_Fork_400', 4, fork=True)
    branch('SM_MSK_Branch_Curved_400', 4, curved=True)
    branch('SM_MSK_Branch_Arch_600', 6, arch=True)
    bm = bmesh.new()
    for i in range(12):
        a = i * math.tau / 12; core.add_cyl(bm, 0.08, 1.2, (math.cos(a) * 1.2, math.sin(a) * 1.2, 1.0), 4, 0)
        core.add_ico(bm, 0.35, (math.cos(a) * 1.5, math.sin(a) * 1.5, 2.0), 0, 2 if i % 2 == 0 else 3)
    fm('SM_MSK_CanopyCluster', 'MSK_BranchesRoots', bm, [BP, BD, LE, LO], ucx=(4, 4, 3), ucx_col='MSK_Collisions')

    def root(name, length, corner=False, fork=False):
        bm = bmesh.new()
        if corner:
            for i in range(5):
                core.add_cyl(bm, 0.12, 0.45, (0, i * 0.4, 0.05), 5, 0)
                core.add_cyl(bm, 0.12, 0.45, (i * 0.4, 0, 0.05), 5, 0)
        else:
            for i in range(6):
                t = i / 6; core.add_cyl(bm, 0.14 * (1 - t * 0.3), 0.5, ((rng.random() - 0.5) * 0.2, t * length, 0.05), 5, 0)
            if fork:
                for i in range(4):
                    core.add_cyl(bm, 0.1, 0.5, (0.4 + i * 0.25, length * 0.5 + i * 0.1, 0.05), 4, 1)
        fm(name, 'MSK_BranchesRoots', bm, [BP, BD], ucx=(max(1.5, length * 0.4), max(1.5, length), 0.5), ucx_col='MSK_Collisions')

    root('SM_MSK_Root_Straight_300', 3)
    root('SM_MSK_Root_Corner_90', 2, corner=True)
    root('SM_MSK_Root_Fork', 3, fork=True)
    bm = bmesh.new()
    for i in range(8):
        a = i * math.tau / 8; core.add_cyl(bm, 0.12, 1.2, (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.05), 4, 0)
        ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.12, radius2=0.08, depth=1.3)
        bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 4, 'X'))
        bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((math.cos(a) * 1.2, math.sin(a) * 1.2, 0.1)))
    fm('SM_MSK_RootCluster_A', 'MSK_BranchesRoots', bm, [BP, BD], ucx=(3, 3, 0.6), ucx_col='MSK_Collisions')
    bm = bmesh.new()
    for i in range(7):
        core.add_cyl(bm, 0.12, 0.7, ((rng.random() - 0.5) * 0.8, i * 0.55, 0.05), 4, i % 2)
    fm('SM_MSK_RootCluster_B', 'MSK_BranchesRoots', bm, [BP, BD], ucx=(2, 4, 0.5), ucx_col='MSK_Collisions')

    # Altars
    bm = bmesh.new(); core.add_box(bm, 3, 1.5, 0.4); core.add_box(bm, 2.7, 1.2, 0.5, (0, 0, 0.4)); core.add_box(bm, 2.8, 1.3, 0.08, (0, 0, 0.9), 2); core.add_box(bm, 0.15, 1.0, 0.4, (-1.3, 0, 0.95), 1)
    fm('SM_MSK_Altar_Main_300', 'MSK_Altars', bm, [S, BP, G], ucx=(3, 1.5, 1.2), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.5, 0.8, 0.35); core.add_box(bm, 1.3, 0.65, 0.6, (0, 0, 0.35))
    fm('SM_MSK_Altar_Minor_150', 'MSK_Altars', bm, [S, BP, G], ucx=(1.5, 0.8, 0.95), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 2.0, 1.5, 0.9, (0, 0, 0), 0)
    for i in range(6):
        a = i * math.tau / 6; core.add_cyl(bm, 0.1, 1.0, (math.cos(a) * 1.0, math.sin(a) * 0.7, 0.2), 4, 1)
    fm('SM_MSK_Altar_RootBound', 'MSK_Altars', bm, [S, BP, G], ucx=(2.5, 2, 1.2), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.8, 0.8, 0.15); core.add_box(bm, 0.12, 0.12, 0.75, (-0.7, -0.3, 0)); core.add_box(bm, 0.12, 0.12, 0.75, (0.7, -0.3, 0)); core.add_box(bm, 0.12, 0.12, 0.75, (-0.7, 0.3, 0)); core.add_box(bm, 0.12, 0.12, 0.75, (0.7, 0.3, 0)); core.add_box(bm, 1.8, 0.8, 0.08, (0, 0, 0.75), 1)
    fm('SM_MSK_OfferingTable', 'MSK_Altars', bm, [S, BP, G], ucx=(1.8, 0.8, 0.9), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 0.7, 0.5, segments=14); core.add_cyl(bm, 0.55, 0.15, (0, 0, 0.4), 12, 1)
    fm('SM_MSK_SanctuaryBasin', 'MSK_Altars', bm, [S, S, G], ucx=(1.4, 1.4, 0.6), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 0.5, 0.03, (0, 0, 0.48), 14, 0)
    fm('SM_MSK_SanctuaryBasin_Water', 'MSK_Altars', bm, ['M_DA_Water'], ucx=None)
    bm = bmesh.new(); core.add_cyl(bm, 2.0, 0.12, segments=24)
    for i in range(8):
        a = i * math.tau / 8; core.add_box(bm, 0.15, 1.5, 0.04, (math.cos(a) * 0.7, math.sin(a) * 0.7, 0.12), 2)
    core.add_cyl(bm, 0.4, 0.05, (0, 0, 0.12), 12, 5)
    fm('SM_MSK_RitualCircle_400', 'MSK_Altars', bm, [S, BP, G, LE, LO, 'M_MSK_Emissive_Sap'], ucx=(4, 4, 0.2), ucx_col='MSK_Collisions')

    # Barriers
    def barrier(name, length=3, h=1.4, thorn=False, stone=False):
        bm = bmesh.new()
        if stone:
            core.add_box(bm, 0.55, length, 1.0, (0, length / 2, 0), 0)
            for i in range(4):
                core.add_cyl(bm, 0.1, 0.8, ((rng.random() - 0.5) * 0.3, 0.4 + i * 0.7, 0.8), 4, 1)
        else:
            for i in range(6):
                y = i * (length / 5)
                core.add_cyl(bm, 0.12, h * (0.7 + rng.random() * 0.3), ((rng.random() - 0.5) * 0.2, y, 0), 5, 0)
                if thorn:
                    core.add_box(bm, 0.08, 0.08, 0.35, (0.15, y, h * 0.7), 1)
        fm(name, 'MSK_Barriers', bm, [BP, BD, S], ucx=(0.7, length, h), ucx_col='MSK_Collisions')

    barrier('SM_MSK_Barrier_RootStraight_300')
    bm = bmesh.new()
    for i in range(5):
        core.add_cyl(bm, 0.12, 1.3, (0, i * 0.4, 0), 5, 0)
        core.add_cyl(bm, 0.12, 1.3, (i * 0.4, 0, 0), 5, 0)
    fm('SM_MSK_Barrier_RootCorner_90', 'MSK_Barriers', bm, [BP, BD], ucx=(2.2, 2.2, 1.4), ucx_col='MSK_Collisions')
    barrier('SM_MSK_Barrier_ThornStraight_300', thorn=True)
    bm = bmesh.new()
    for x in (-1.9, 1.9):
        for i in range(5):
            core.add_cyl(bm, 0.14, 2.5, (x + (rng.random() - 0.5) * 0.2, (rng.random() - 0.5) * 0.3, 0), 5, 0)
    for i in range(6):
        core.add_cyl(bm, 0.1, 0.8, (-1.5 + i * 0.6, 0, 2.4), 4, 1)
    fm('SM_MSK_Barrier_ThornGate', 'MSK_Barriers', bm, [BP, BD], ucx=[((0.6, 0.6, 2.8), (-1.9, 0, 0)), ((0.6, 0.6, 2.8), (1.9, 0, 0)), ((4, 0.6, 0.5), (0, 0, 2.5))], ucx_col='MSK_Collisions')
    barrier('SM_MSK_Barrier_StoneRoot_300', stone=True)
    bm = bmesh.new(); core.add_cyl(bm, 0.18, 1.8, segments=8); core.add_cyl(bm, 0.25, 0.15, (0, 0, 0), 8, 1)
    fm('SM_MSK_Barrier_Post', 'MSK_Barriers', bm, [BP, BD], ucx=(0.4, 0.4, 1.8), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 0.2, 1.4, segments=8); core.add_ico(bm, 0.25, (0, 0, 1.4), 0, 1)
    fm('SM_MSK_Barrier_EndCap', 'MSK_Barriers', bm, [BP, BD], ucx=(0.5, 0.5, 1.6), ucx_col='MSK_Collisions')
    bm = bmesh.new()
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.2, radius2=0.15, depth=2.5)
    bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(70), 4, 'X'))
    bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((0, 1.0, 0.35)))
    fm('SM_MSK_Barrier_Fallen', 'MSK_Barriers', bm, [BP, BD], ucx=(0.8, 2.5, 0.8), ucx_col='MSK_Collisions')

    # Extras
    bm = bmesh.new()
    for i in range(10):
        core.add_box(bm, 0.05, 0.4, 1.8, ((rng.random() - 0.5) * 1.5, (rng.random() - 0.5) * 0.3, 0.1), 2 if i % 2 == 0 else 3)
        core.add_ico(bm, 0.12, ((rng.random() - 0.5) * 1.5, 0, 1.5 + rng.random()), 0, 2)
    fm('SM_MSK_HangingVines_Cluster', 'MSK_Extras', bm, [BP, BD, LE, LO], ucx=None)
    bm = bmesh.new()
    for i in range(10):
        core.add_ico(bm, 0.08, ((rng.random() - 0.5) * 0.8, (rng.random() - 0.5) * 0.8, rng.random() * 0.3), 0, 6 if i % 2 == 0 else 7)
    fm('SM_MSK_FlowerCluster', 'MSK_Extras', bm, [BP, BD, LE, LO, S, G, FW, FP], ucx=None)
    bm = bmesh.new(); core.add_box(bm, 0.8, 0.35, 1.6); core.add_box(bm, 0.5, 0.05, 0.5, (0, -0.2, 1.0), 2)
    fm('SM_MSK_StoneMarker', 'MSK_Extras', bm, [S, BP, G], ucx=(0.8, 0.4, 1.6), ucx_col='MSK_Collisions')
    bm = bmesh.new(); core.add_ico(bm, 0.45, (0, 0, 0.5), 1, 0); core.add_ico(bm, 0.2, (0, 0, 0.7), 0, 5)
    fm('SM_MSK_SacredSeedPod', 'MSK_Extras', bm, [BP, BD, LE, LO, S, 'M_MSK_Emissive_Sap'], ucx=(1.0, 1.0, 1.2), ucx_col='MSK_Collisions')
    # emissive core separate? optional - skip separate for speed
    bm = bmesh.new()
    for x in (-1.8, 1.8):
        core.add_box(bm, 0.5, 0.5, 3.0, (x, 0, 0), 0)
        for i in range(4):
            core.add_cyl(bm, 0.1, 1.5, (x, (rng.random() - 0.5) * 0.3, 0.5 + i * 0.5), 4, 1)
    core.add_box(bm, 4.0, 0.5, 0.5, (0, 0, 3.1), 0)
    fm('SM_MSK_SanctuaryArch', 'MSK_Extras', bm, [S, BP, G], ucx=[((0.7, 0.7, 3.5), (-1.8, 0, 0)), ((0.7, 0.7, 3.5), (1.8, 0, 0)), ((4.2, 0.7, 0.6), (0, 0, 3.1))], ucx_col='MSK_Collisions')

    names = [o.name for o in bpy.data.objects if o.name.startswith('SM_MSK_')]
    core.write_qa('MSK_QA_Report', [f'SANCTUARY assets={len(names)}'] + [f'- {n}' for n in sorted(names)])
    return names


def build_mirrors():
    core.ensure_kit_collections('SM_Malkuth_MirrorLabyrinthKit', [
        'MMLK_Mirrors', 'MMLK_Bases', 'MMLK_Posts', 'MMLK_Extras', 'MMLK_Collisions', 'MMLK_Showcase'])
    FI, G, SD, MP, MD, EP = (
        'M_MMLK_Frame_Ivory', 'M_MMLK_Gold_Aged', 'M_MMLK_Stone_Dark',
        'M_MMLK_Mirror_Preview', 'M_MMLK_Mirror_Damaged', 'M_MMLK_Emissive_Purple')

    def mirror_panel(name, w, h, cracked=False, broken=False, double=False, arch=False):
        bm = bmesh.new()
        # frame
        t = 0.08
        core.add_box(bm, w, 0.18, t, (0, 0, 0), 0)  # bottom
        core.add_box(bm, w, 0.18, t, (0, 0, h - t), 0)  # top
        core.add_box(bm, t, 0.18, h, (-w / 2 + t / 2, 0, 0), 0)
        core.add_box(bm, t, 0.18, h, (w / 2 - t / 2, 0, 0), 0)
        core.add_box(bm, w - 0.05, 0.06, h - 0.05, (0, 0.06, t / 2), 2)  # back
        if arch:
            core.add_cyl(bm, w / 2, 0.18, (0, 0, h - 0.1), 12, 0)
        if cracked:
            for i in range(4):
                core.add_box(bm, 0.03, 0.1, h * 0.4, (-0.4 + i * 0.3, -0.02, 0.4 + i * 0.2), 1)
        if broken:
            core.add_box(bm, w * 0.35, 0.18, h * 0.4, (w * 0.25, 0, h * 0.5), 1)
        fm(name, 'MMLK_Mirrors', bm, [FI, G, SD, MD], ucx=(w, 0.25, h), ucx_col='MMLK_Collisions')
        # separate mirror surface(s)
        bm = bmesh.new()
        core.add_box(bm, w - 0.2, 0.02, h - 0.25, (0, -0.05, 0.12), 0)
        fm(name + '_MirrorSurface', 'MMLK_Mirrors', bm, [MP if not cracked else MD], ucx=None)
        if double:
            bm = bmesh.new()
            core.add_box(bm, w - 0.2, 0.02, h - 0.25, (0, 0.12, 0.12), 0)
            fm(name + '_MirrorSurface_B', 'MMLK_Mirrors', bm, [MP], ucx=None)

    mirror_panel('SM_MMLK_Mirror_Straight_100x300', 1.0, 3.0)
    mirror_panel('SM_MMLK_Mirror_Straight_150x300', 1.5, 3.0)
    mirror_panel('SM_MMLK_Mirror_Straight_200x300', 2.0, 3.0)
    mirror_panel('SM_MMLK_Mirror_Low_200x150', 2.0, 1.5)
    # corner
    bm = bmesh.new()
    for ang_off, ox, oy in [(0, 0, 0), (math.pi / 2, 0, 0)]:
        pass
    core.add_box(bm, 1.5, 0.18, 3.0, (0.75, 0, 0), 0)
    core.add_box(bm, 0.18, 1.5, 3.0, (0, 0.75, 0), 0)
    fm('SM_MMLK_Mirror_Corner_90', 'MMLK_Mirrors', bm, [FI, G, SD], ucx=(1.6, 1.6, 3), ucx_col='MMLK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.3, 0.02, 2.8, (0.75, -0.05, 0.1), 0); core.add_box(bm, 0.02, 1.3, 2.8, (-0.05, 0.75, 0.1), 0)
    fm('SM_MMLK_Mirror_Corner_90_MirrorSurface', 'MMLK_Mirrors', bm, [MP], ucx=None)

    # curved 30 deg
    bm = bmesh.new()
    radius = 4.0
    for i in range(6):
        a = math.radians(-15 + i * 5)
        core.add_box(bm, 0.35, 0.18, 3.0, (math.sin(a) * radius, -math.cos(a) * radius + radius, 0), 0)
    fm('SM_MMLK_Mirror_Curved_30', 'MMLK_Mirrors', bm, [FI, G, SD], ucx=(2.2, 1.2, 3), ucx_col='MMLK_Collisions')
    bm = bmesh.new()
    for i in range(5):
        a = math.radians(-12 + i * 6)
        core.add_box(bm, 0.3, 0.02, 2.8, (math.sin(a) * (radius - 0.1), -math.cos(a) * (radius - 0.1) + radius, 0.1), 0)
    fm('SM_MMLK_Mirror_Curved_30_MirrorSurface', 'MMLK_Mirrors', bm, [MP], ucx=None)

    mirror_panel('SM_MMLK_Mirror_Cracked_A', 2.0, 3.0, cracked=True)
    mirror_panel('SM_MMLK_Mirror_Cracked_B', 2.0, 3.0, cracked=True)
    mirror_panel('SM_MMLK_Mirror_Broken', 2.0, 3.0, broken=True)
    mirror_panel('SM_MMLK_Mirror_Arch_300', 3.0, 3.8, arch=True)
    # doorway no mirror
    bm = bmesh.new()
    core.add_box(bm, 0.25, 0.25, 2.9, (-1.1, 0, 0), 0); core.add_box(bm, 0.25, 0.25, 2.9, (1.1, 0, 0), 0)
    core.add_box(bm, 2.5, 0.25, 0.3, (0, 0, 2.7), 0)
    fm('SM_MMLK_Mirror_Doorway', 'MMLK_Mirrors', bm, [FI, G, SD], ucx=[((0.35, 0.35, 3), (-1.1, 0, 0)), ((0.35, 0.35, 3), (1.1, 0, 0)), ((2.5, 0.35, 0.35), (0, 0, 2.7))], ucx_col='MMLK_Collisions')
    mirror_panel('SM_MMLK_Mirror_DoubleSided_200', 2.0, 3.0, double=True)

    # Bases
    for name, length in [('SM_MMLK_Base_Straight_100', 1), ('SM_MMLK_Base_Straight_150', 1.5), ('SM_MMLK_Base_Straight_200', 2)]:
        bm = bmesh.new(); core.add_box(bm, 0.45, length, 0.35, (0, length / 2, 0), 0); core.add_box(bm, 0.1, length * 0.9, 0.05, (0, length / 2, 0.35), 1)
        fm(name, 'MMLK_Bases', bm, [FI, G, SD], ucx=(0.45, length, 0.35), ucx_col='MMLK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 0.45, 1.5, 0.35, (0, 0.75, 0)); core.add_box(bm, 1.5, 0.45, 0.35, (0.75, 0, 0))
    fm('SM_MMLK_Base_Corner_90', 'MMLK_Bases', bm, [FI, G, SD], ucx=(1.7, 1.7, 0.35), ucx_col='MMLK_Collisions')
    bm = bmesh.new()
    for i in range(5):
        a = math.radians(-15 + i * 7.5)
        core.add_box(bm, 0.4, 0.45, 0.35, (math.sin(a) * 4, -math.cos(a) * 4 + 4, 0), 0)
    fm('SM_MMLK_Base_Curved_30', 'MMLK_Bases', bm, [FI, G, SD], ucx=(2, 1.2, 0.35), ucx_col='MMLK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 0.5, 0.5, 0.4); core.add_box(bm, 0.35, 0.2, 0.25, (0, 0.25, 0.1), 1)
    fm('SM_MMLK_Base_EndCap', 'MMLK_Bases', bm, [FI, G, SD], ucx=(0.5, 0.6, 0.4), ucx_col='MMLK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 2.0, 0.45, 0.35); core.add_box(bm, 0.45, 1.2, 0.35, (0, 0.6, 0))
    fm('SM_MMLK_Base_Junction_T', 'MMLK_Bases', bm, [FI, G, SD], ucx=(2, 1.5, 0.35), ucx_col='MMLK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 2.0, 0.45, 0.35); core.add_box(bm, 0.45, 2.0, 0.35)
    fm('SM_MMLK_Base_Junction_Cross', 'MMLK_Bases', bm, [FI, G, SD], ucx=(2, 2, 0.35), ucx_col='MMLK_Collisions')

    # Posts
    for name, s, h, ornate in [
        ('SM_MMLK_Post_Simple', 0.35, 3.2, False),
        ('SM_MMLK_Post_Ornate', 0.55, 3.6, True),
        ('SM_MMLK_Post_Corner', 0.45, 3.3, False),
        ('SM_MMLK_Post_Gate', 0.6, 4.0, True),
    ]:
        bm = bmesh.new(); core.add_box(bm, s, s, h)
        if ornate:
            core.add_box(bm, s * 1.2, s * 1.2, 0.15, (0, 0, 0), 1)
            core.add_box(bm, s * 1.1, s * 1.1, 0.12, (0, 0, h - 0.2), 1)
        fm(name, 'MMLK_Posts', bm, [FI, G, SD], ucx=(s * 1.2, s * 1.2, h), ucx_col='MMLK_Collisions')

    # Extras
    bm = bmesh.new(); core.add_cyl(bm, 2.0, 0.3, segments=8)
    for i in range(4):
        a = i * math.tau / 4 + math.pi / 8
        core.add_box(bm, 1.2, 0.15, 1.5, (math.cos(a) * 1.3, math.sin(a) * 1.3, 0.3), 0)
    fm('SM_MMLK_MirrorIsland', 'MMLK_Extras', bm, [FI, G, SD], ucx=(4, 4, 1.8), ucx_col='MMLK_Collisions')
    bm = bmesh.new()
    for i in range(4):
        a = i * math.tau / 4 + math.pi / 8
        core.add_box(bm, 1.0, 0.02, 1.3, (math.cos(a) * 1.25, math.sin(a) * 1.25, 0.4), 0)
    fm('SM_MMLK_MirrorIsland_MirrorSurface', 'MMLK_Extras', bm, [MP], ucx=None)

    bm = bmesh.new(); core.add_cyl(bm, 0.35, 1.0, segments=10); core.add_box(bm, 0.6, 0.08, 0.6, (0, 0.1, 1.0), 1)
    fm('SM_MMLK_PedestalReflector', 'MMLK_Extras', bm, [FI, G, SD], ucx=(0.8, 0.8, 1.2), ucx_col='MMLK_Collisions')
    bm = bmesh.new(); core.add_box(bm, 0.55, 0.02, 0.55, (0, -0.05, 1.05), 0)
    fm('SM_MMLK_PedestalReflector_MirrorSurface', 'MMLK_Extras', bm, [MP], ucx=None)

    for name, sx, sy in [('SM_MMLK_ShardCluster_A', 1.5, 1.5), ('SM_MMLK_ShardCluster_B', 2.0, 1.0)]:
        bm = bmesh.new(); core.add_box(bm, sx * 0.8, sy * 0.8, 0.2, (0, 0, 0), 2)
        for i in range(5):
            core.add_box(bm, 0.15 + rng.random() * 0.2, 0.05, 0.4 + rng.random() * 0.5,
                         ((rng.random() - 0.5) * sx * 0.5, (rng.random() - 0.5) * sy * 0.5, 0.2), 3)
        fm(name, 'MMLK_Extras', bm, [FI, G, SD, MD], ucx=(sx, sy, 0.9), ucx_col='MMLK_Collisions')

    bm = bmesh.new(); core.add_cyl(bm, 1.2, 0.4, segments=16); core.add_cyl(bm, 1.5, 0.15, (0, 0, 0.35), 16, 1); core.add_cyl(bm, 0.2, 1.5, (0, 0, 0.4), 8, 0)
    fm('SM_MMLK_CentralOculus', 'MMLK_Extras', bm, [FI, G, SD, EP], ucx=(3, 3, 2), ucx_col='MMLK_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 1.4, 0.03, (0, 0, 1.9), 20, 0)
    fm('SM_MMLK_CentralOculus_MirrorSurface', 'MMLK_Extras', bm, [MP], ucx=None)

    names = [o.name for o in bpy.data.objects if o.name.startswith('SM_MMLK_')]
    core.write_qa('MMLK_QA_Report', [f'MIRROR assets={len(names)}'] + [f'- {n}' for n in sorted(names)])
    return names


def build_props():
    core.ensure_kit_collections('SM_Malkuth_Props', [
        'MP_Thrones', 'MP_Portals', 'MP_Stairs', 'MP_Bridges', 'MP_Extras', 'MP_Collisions', 'MP_Showcase'])
    S, D, G, W, R, EP, EG, PP = (
        'M_MP_Stone_Ivory', 'M_MP_Stone_Dark', 'M_MP_Gold_Aged', 'M_MP_Wood_Pale',
        'M_MP_Roots', 'M_MP_Emissive_Purple', 'M_MP_Emissive_Gold', 'M_MP_Portal_Preview')

    # Thrones
    bm = bmesh.new()
    core.add_box(bm, 1.8, 1.2, 0.45); core.add_box(bm, 1.6, 0.35, 1.8, (0, 0.4, 0.45)); core.add_box(bm, 0.3, 1.0, 1.2, (-0.75, 0, 0.45)); core.add_box(bm, 0.3, 1.0, 1.2, (0.75, 0, 0.45))
    core.add_box(bm, 1.5, 0.2, 0.8, (0, 0.5, 2.0), 2); core.add_box(bm, 0.15, 0.8, 1.5, (-0.9, 0.2, 0.3), 4)
    fm('SM_MP_Throne_Malkuth_Main', 'MP_Thrones', bm, [S, D, G, W, R], ucx=(1.9, 1.4, 3.2), ucx_col='MP_Collisions')
    bm = bmesh.new()
    core.add_box(bm, 1.8, 1.2, 0.45); core.add_box(bm, 1.6, 0.35, 1.6, (0, 0.4, 0.45))
    for i in range(6):
        a = -0.6 + i * 0.25; core.add_cyl(bm, 0.1, 1.8, (a, 0.6, 0.3), 4, 4)
    fm('SM_MP_Throne_RootBound', 'MP_Thrones', bm, [S, D, G, W, R], ucx=(1.9, 1.4, 2.8), ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_box(bm, 1.7, 1.1, 0.4); core.add_box(bm, 1.4, 0.3, 1.2, (0, 0.35, 0.4)); core.add_box(bm, 0.5, 0.5, 0.8, (0.6, -0.2, 0.3), 1)
    fm('SM_MP_Throne_Damaged', 'MP_Thrones', bm, [S, D, G, W, R], ucx=(1.8, 1.3, 2.0), ucx_col='MP_Collisions')
    bm = bmesh.new()
    for z, s in [(0, 4), (0.25, 3.4), (0.5, 2.8)]:
        core.add_box(bm, s, s, 0.25, (0, 0, z))
    fm('SM_MP_Throne_Dais_400', 'MP_Thrones', bm, [S, D, G], ucx=(4, 4, 0.75), ucx_col='MP_Collisions')

    # Portals
    bm = bmesh.new(); core.add_cyl(bm, 2.2, 0.8, segments=20); core.add_cyl(bm, 1.7, 0.8, (0, 0, 0), 20, 1)
    # hollow approx - outer ring via boxes
    bm.free(); bm = bmesh.new()
    for i in range(16):
        a = i * math.tau / 16
        core.add_box(bm, 0.45, 0.8, 0.5, (math.cos(a) * 2.0, math.sin(a) * 0.1, math.sin(a) * 0 + 2.0 + math.sin(a) * 0), 0)
    # better torus-like vertical ring in XY facing +Y
    bm.free(); bm = bmesh.new()
    for i in range(20):
        a = i * math.tau / 20
        core.add_box(bm, 0.4, 0.8, 0.4, (math.cos(a) * 2.0, 0, 2.0 + math.sin(a) * 2.0), 0)
    fm('SM_MP_Portal_Frame_Round_400', 'MP_Portals', bm, [S, D, G], ucx=(4.5, 1.0, 4.5), ucx_col='MP_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 0.6, 0.8, 4.5, (-2.0, 0, 0)); core.add_box(bm, 0.6, 0.8, 4.5, (2.0, 0, 0))
    core.add_box(bm, 4.6, 0.8, 0.7, (0, 0, 4.5))
    for i in range(6):
        a = i / 5 * math.pi
        core.add_box(bm, 0.5, 0.8, 0.4, (math.cos(a) * 2.0, 0, 4.5 + math.sin(a) * 1.0), 0)
    fm('SM_MP_Portal_Arch_500', 'MP_Portals', bm, [S, D, G], ucx=[((0.7, 0.9, 4.6), (-2, 0, 0)), ((0.7, 0.9, 4.6), (2, 0, 0)), ((4.8, 0.9, 1.5), (0, 0, 4.5))], ucx_col='MP_Collisions')

    bm = bmesh.new(); core.add_box(bm, 0.6, 0.8, 3.5, (-2, 0, 0)); core.add_box(bm, 0.6, 0.8, 2.2, (2, 0, 0)); core.add_box(bm, 2.5, 0.8, 0.5, (-0.5, 0, 3.5), 1)
    fm('SM_MP_Portal_Broken', 'MP_Portals', bm, [S, D, G], ucx=[((0.7, 0.9, 3.6), (-2, 0, 0)), ((0.7, 0.9, 2.3), (2, 0, 0))], ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_box(bm, 0.8, 0.5, 0.6); core.add_box(bm, 0.5, 0.5, 0.4, (0, 0, 0.5), 2)
    fm('SM_MP_Portal_Keystone', 'MP_Portals', bm, [S, D, G], ucx=(0.9, 0.6, 1.0), ucx_col='MP_Collisions')
    bm = bmesh.new()
    for i in range(24):
        a = i * math.tau / 24
        core.add_box(bm, 0.15, 0.1, 0.15, (math.cos(a) * 1.7, 0, 2.0 + math.sin(a) * 1.7), 5)
    fm('SM_MP_Portal_RuneRing', 'MP_Portals', bm, [S, D, G, W, R, EP], ucx=None)
    bm = bmesh.new(); core.add_box(bm, 3.0, 1.5, 0.15)
    fm('SM_MP_Portal_Threshold', 'MP_Portals', bm, [S, D, G], ucx=(3, 1.5, 0.15), ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_box(bm, 3.2, 0.05, 3.2, (0, 0, 0.5), 0)
    fm('SM_MP_PortalSurface_Preview', 'MP_Portals', bm, [PP], ucx=None)

    # Stairs
    def stairs(name, width, depth, height, broken=False, blocked=False):
        bm = bmesh.new()
        steps = max(3, int(round(height / 0.167)))
        step_d = depth / steps
        step_h = height / steps
        for i in range(steps):
            if broken and i > steps * 0.5 and (i % 2 == 0):
                # leave gap on one side
                core.add_box(bm, width * 0.55, step_d, step_h, (-width * 0.2, step_d * (i + 0.5), step_h * i), 0)
            elif blocked and i > steps * 0.4:
                core.add_box(bm, width, step_d, step_h * 2, (0, step_d * (i + 0.5), step_h * i), 1)
            else:
                core.add_box(bm, width, step_d * (steps - i), step_h, (0, depth / 2 + step_d * i / 2, step_h * i), 0)
                # simpler consistent steps:
        bm.free(); bm = bmesh.new()
        for i in range(steps):
            w = width * (0.55 if (broken and i % 3 == 0) else 1.0)
            ox = -0.3 if (broken and i % 3 == 0) else 0
            if blocked and i > steps * 0.5:
                core.add_box(bm, width, step_d, step_h + 0.4, (0, step_d * (i + 0.5), step_h * i), 1)
            else:
                core.add_box(bm, w, step_d, step_h, (ox, step_d * (i + 0.5), step_h * i), 0)
        fm(name, 'MP_Stairs', bm, [S, D, G], ucx=(width, depth, height), ucx_col='MP_Collisions')

    stairs('SM_MP_Stair_Straight_300x300', 3, 3, 1.5)
    stairs('SM_MP_Stair_Straight_300x600', 3, 6, 3)
    stairs('SM_MP_Stair_Wide_600x600', 6, 6, 3)
    # corner stair simplified
    bm = bmesh.new()
    for i in range(8):
        core.add_box(bm, 3, 0.4, 0.2, (0, 0.4 * (i + 0.5), 0.2 * i), 0)
    for i in range(8):
        core.add_box(bm, 0.4, 3, 0.2, (0.4 * (i + 0.5), 3.2, 0.2 * (i + 8)), 0)
    core.add_box(bm, 3, 3, 0.2, (1.5, 1.5, 1.6), 0)
    fm('SM_MP_Stair_Corner_90', 'MP_Stairs', bm, [S, D, G], ucx=(6, 6, 3.2), ucx_col='MP_Collisions')
    for name, s in [('SM_MP_Landing_300', 3), ('SM_MP_Landing_600', 6)]:
        bm = bmesh.new(); core.add_box(bm, s, s, 0.2)
        fm(name, 'MP_Stairs', bm, [S, D, G], ucx=(s, s, 0.2), ucx_col='MP_Collisions')
    stairs('SM_MP_Stair_Broken_A', 3, 3, 1.5, broken=True)
    stairs('SM_MP_Stair_Broken_B', 3, 3, 1.5, blocked=True)
    bm = bmesh.new(); core.add_box(bm, 0.12, 3.0, 1.1, (0, 1.5, 0)); core.add_box(bm, 0.2, 3.0, 0.08, (0, 1.5, 1.1), 2)
    fm('SM_MP_StairRailing_Straight_300', 'MP_Stairs', bm, [S, D, G], ucx=(0.25, 3, 1.15), ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 0.1, 1.15, segments=8); core.add_box(bm, 0.25, 0.25, 0.1, (0, 0, 1.1), 2)
    fm('SM_MP_StairRailing_End', 'MP_Stairs', bm, [S, D, G], ucx=(0.3, 0.3, 1.2), ucx_col='MP_Collisions')

    # Bridges
    def bridge(name, w, length, arch=False, broken=False):
        bm = bmesh.new()
        if arch:
            for i in range(12):
                t = i / 11
                z = math.sin(t * math.pi) * 1.2
                core.add_box(bm, w, length / 12 + 0.05, 0.45, (0, length * t, z), 0)
        else:
            core.add_box(bm, w, length, 0.45, (0, length / 2, 0), 0)
            if length >= 10:
                for y in (length * 0.25, length * 0.5, length * 0.75):
                    core.add_box(bm, w * 0.15, 0.4, 1.2, (-w * 0.35, y, -1.2), 1)
                    core.add_box(bm, w * 0.15, 0.4, 1.2, (w * 0.35, y, -1.2), 1)
        if broken:
            # chop end
            core.add_box(bm, w * 0.7, 0.8, 0.5, ((rng.random() - 0.5) * 0.3, length * 0.85, 0.1), 1)
        fm(name, 'MP_Bridges', bm, [S, D, G], ucx=(w, length, 1.0 if not arch else 1.8), ucx_col='MP_Collisions')

    bridge('SM_MP_Bridge_Straight_300x600', 3, 6)
    bridge('SM_MP_Bridge_Straight_300x1200', 3, 12)
    bridge('SM_MP_Bridge_Wide_600x1200', 6, 12)
    bridge('SM_MP_Bridge_Arch_300x900', 3, 9, arch=True)
    bridge('SM_MP_Bridge_BrokenHalf_A', 3, 6, broken=True)
    bridge('SM_MP_Bridge_BrokenHalf_B', 3, 6, broken=True)
    bm = bmesh.new(); core.add_box(bm, 1.2, 1.2, 4.0)
    fm('SM_MP_Bridge_Pillar', 'MP_Bridges', bm, [S, D, G], ucx=(1.2, 1.2, 4), ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_box(bm, 0.12, 3.0, 1.1, (0, 1.5, 0)); core.add_box(bm, 0.2, 3.0, 0.08, (0, 1.5, 1.1), 2)
    fm('SM_MP_BridgeRailing_300', 'MP_Bridges', bm, [S, D, G], ucx=(0.25, 3, 1.15), ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_box(bm, 0.12, 2.0, 1.0, (0, 1.0, 0)); core.add_box(bm, 0.3, 0.4, 0.5, (0.1, 2.2, 0.3), 1)
    fm('SM_MP_BridgeRailing_Broken', 'MP_Bridges', bm, [S, D, G], ucx=(0.4, 2.5, 1.1), ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_box(bm, 3.0, 1.5, 0.35); core.add_box(bm, 3.0, 0.8, 0.2, (0, 0.3, 0.35))
    fm('SM_MP_Bridge_EndCap', 'MP_Bridges', bm, [S, D, G], ucx=(3, 1.5, 0.55), ucx_col='MP_Collisions')

    # Extras
    bm = bmesh.new(); core.add_cyl(bm, 0.4, 0.5, segments=10); core.add_box(bm, 0.2, 0.2, 0.7, (0, 0, 0.5), 2)
    fm('SM_MP_Bridge_Anchor', 'MP_Extras', bm, [S, D, G], ucx=(0.9, 0.9, 1.2), ucx_col='MP_Collisions')
    bm = bmesh.new()
    for i in range(3):
        core.add_box(bm, 4.0, 1.2 - i * 0.15, 0.17, (0, 0.5 + i * 0.35, i * 0.17), 0)
    fm('SM_MP_PortalSteps', 'MP_Extras', bm, [S, D, G], ucx=(4, 1.5, 0.55), ucx_col='MP_Collisions')
    bm = bmesh.new()
    for x in (-1.8, 1.8):
        core.add_box(bm, 0.35, 0.35, 4.0, (x, 0, 0), 0)
    core.add_box(bm, 4.0, 0.35, 0.35, (0, 0, 4.0), 0)
    core.add_box(bm, 3.6, 0.2, 1.5, (0, 0.1, 3.2), 2)
    fm('SM_MP_ThroneCanopy', 'MP_Extras', bm, [S, D, G], ucx=[((0.5, 0.5, 4.2), (-1.8, 0, 0)), ((0.5, 0.5, 4.2), (1.8, 0, 0)), ((4.2, 0.5, 0.5), (0, 0, 4))], ucx_col='MP_Collisions')
    bm = bmesh.new(); core.add_cyl(bm, 0.1, 4.0, segments=8); core.add_box(bm, 0.35, 0.1, 0.35, (0, 0, 3.6), 2)
    fm('SM_MP_BannerPole', 'MP_Extras', bm, [S, D, G], ucx=(0.4, 0.4, 4), ucx_col='MP_Collisions')

    names = [o.name for o in bpy.data.objects if o.name.startswith('SM_MP_')]
    core.write_qa('MP_QA_Report', [f'PROPS assets={len(names)}'] + [f'- {n}' for n in sorted(names)])
    return names


def build_angels():
    core.ensure_kit_collections('SK_Malkuth_AngelPlaceholder', [
        'MAP_Messenger', 'MAP_Archangel', 'MAP_Gabriel', 'MAP_Attachments', 'MAP_Rigs', 'MAP_Showcase'])
    mats_body = ['M_MAP_Body_StonePale', 'M_MAP_Cloth_Ivory', 'M_MAP_Armor_GoldAged', 'M_MAP_Leather_Pale',
                 'M_MAP_Wings_White', 'M_MAP_Wings_Shadow', 'M_MAP_Emissive_Subtle', 'M_MAP_Emissive_Gabriel']

    def make_rig(name):
        core.remove_object_by_name(name)
        arm = bpy.data.armatures.new(name)
        obj = bpy.data.objects.new(name, arm)
        core.link_exclusive(obj, 'MAP_Rigs')
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        eb = arm.edit_bones

        def add(bname, head, tail, parent=None):
            b = eb.new(bname)
            b.head = Vector(head)
            b.tail = Vector(tail)
            if parent:
                b.parent = eb[parent]
            return b

        add('root', (0, 0, 0), (0, 0.1, 0))
        add('pelvis', (0, 0, 1.0), (0, 0.1, 1.05), 'root')
        add('spine_01', (0, 0, 1.05), (0, 0.05, 1.25), 'pelvis')
        add('spine_02', (0, 0, 1.25), (0, 0.05, 1.45), 'spine_01')
        add('spine_03', (0, 0, 1.45), (0, 0.05, 1.65), 'spine_02')
        add('neck_01', (0, 0, 1.65), (0, 0.05, 1.75), 'spine_03')
        add('head', (0, 0, 1.75), (0, 0.05, 1.95), 'neck_01')
        for side, s in [('l', 1), ('r', -1)]:
            add(f'clavicle_{side}', (0, 0, 1.6), (0.15 * s, 0.05, 1.62), 'spine_03')
            add(f'upperarm_{side}', (0.15 * s, 0, 1.6), (0.45 * s, 0.1, 1.35), f'clavicle_{side}')
            add(f'lowerarm_{side}', (0.45 * s, 0.1, 1.35), (0.65 * s, 0.15, 1.1), f'upperarm_{side}')
            add(f'hand_{side}', (0.65 * s, 0.15, 1.1), (0.75 * s, 0.18, 1.05), f'lowerarm_{side}')
            add(f'thumb_01_{side}', (0.72 * s, 0.18, 1.06), (0.78 * s, 0.22, 1.06), f'hand_{side}')
            add(f'thumb_02_{side}', (0.78 * s, 0.22, 1.06), (0.82 * s, 0.24, 1.06), f'thumb_01_{side}')
            add(f'index_01_{side}', (0.75 * s, 0.18, 1.05), (0.82 * s, 0.2, 1.04), f'hand_{side}')
            add(f'index_02_{side}', (0.82 * s, 0.2, 1.04), (0.86 * s, 0.21, 1.03), f'index_01_{side}')
            add(f'finger_01_{side}', (0.74 * s, 0.15, 1.04), (0.81 * s, 0.16, 1.02), f'hand_{side}')
            add(f'finger_02_{side}', (0.81 * s, 0.16, 1.02), (0.85 * s, 0.16, 1.01), f'finger_01_{side}')
            add(f'thigh_{side}', (0.12 * s, 0, 1.0), (0.15 * s, 0.05, 0.55), 'pelvis')
            add(f'calf_{side}', (0.15 * s, 0.05, 0.55), (0.12 * s, 0.08, 0.15), f'thigh_{side}')
            add(f'foot_{side}', (0.12 * s, 0.08, 0.15), (0.12 * s, 0.22, 0.05), f'calf_{side}')
            add(f'ball_{side}', (0.12 * s, 0.22, 0.05), (0.12 * s, 0.28, 0.05), f'foot_{side}')
            add(f'wing_root_{side}', (0.1 * s, -0.1, 1.5), (0.3 * s, -0.3, 1.55), 'spine_03')
            add(f'wing_01_{side}', (0.3 * s, -0.3, 1.55), (0.7 * s, -0.7, 1.7), f'wing_root_{side}')
            add(f'wing_02_{side}', (0.7 * s, -0.7, 1.7), (1.1 * s, -1.1, 1.75), f'wing_01_{side}')
            add(f'wing_03_{side}', (1.1 * s, -1.1, 1.75), (1.5 * s, -1.4, 1.7), f'wing_02_{side}')
            add(f'weapon_{side}', (0.7 * s, 0.2, 1.05), (0.7 * s, 0.35, 1.05), f'hand_{side}')
        add('halo_socket', (0, 0, 2.05), (0, 0.1, 2.05), 'head')
        add('vfx_chest', (0, 0.15, 1.45), (0, 0.25, 1.45), 'spine_02')
        add('vfx_back', (0, -0.15, 1.5), (0, -0.25, 1.5), 'spine_03')
        bpy.ops.object.mode_set(mode='OBJECT')
        return obj

    def make_body(prefix, height, wing_span, col, heavy=False, gabriel=False):
        scale = height / 1.9
        bm = bmesh.new()
        # torso
        core.add_box(bm, 0.4 * scale, 0.25 * scale, 0.65 * scale, (0, 0, 1.05 * scale), 0)
        core.add_box(bm, 0.45 * scale, 0.28 * scale, 0.25 * scale, (0, 0, 1.55 * scale), 1)  # chest cloth/armor
        # head
        core.add_ico(bm, 0.12 * scale, (0, 0.02 * scale, 1.85 * scale), 1, 0)
        # legs
        for s in (-1, 1):
            core.add_cyl(bm, 0.08 * scale, 0.45 * scale, (0.1 * s * scale, 0, 0.55 * scale), 6, 0)
            core.add_cyl(bm, 0.07 * scale, 0.4 * scale, (0.1 * s * scale, 0.02 * scale, 0.15 * scale), 6, 0)
            core.add_box(bm, 0.1 * scale, 0.2 * scale, 0.06 * scale, (0.1 * s * scale, 0.1 * scale, 0), 3)
            # arms
            core.add_cyl(bm, 0.06 * scale, 0.35 * scale, (0.28 * s * scale, 0.05 * scale, 1.4 * scale), 5, 0)
            core.add_cyl(bm, 0.05 * scale, 0.3 * scale, (0.5 * s * scale, 0.1 * scale, 1.2 * scale), 5, 0)
        # armor pads
        if heavy or gabriel:
            core.add_box(bm, 0.55 * scale, 0.35 * scale, 0.2 * scale, (0, 0, 1.55 * scale), 2)
            core.add_box(bm, 0.25 * scale, 0.25 * scale, 0.2 * scale, (-0.3 * scale, 0, 1.65 * scale), 2)
            core.add_box(bm, 0.25 * scale, 0.25 * scale, 0.2 * scale, (0.3 * scale, 0, 1.65 * scale), 2)
        if gabriel:
            core.add_box(bm, 0.2 * scale, 0.08 * scale, 0.25 * scale, (0, 0.18 * scale, 1.45 * scale), 7)
        body = core.finish_mesh(f'{prefix}_Body', col, bm, (0, 0, 0), mats_body, bevel=0.0, as_asset=True)

        # wings
        bm = bmesh.new()
        span = wing_span / 2
        for s in (-1, 1):
            for i in range(4):
                t = i / 3
                core.add_box(bm, 0.15 * scale, span / 3, 0.6 * scale * (1 - t * 0.3),
                             (s * (0.3 + t * span) * 0.7, -0.4 - t * span * 0.5, (1.5 + t * 0.2) * scale),
                             4 if not gabriel else (5 if i > 1 else 4))
        wings = core.finish_mesh(f'{prefix}_Wings', col, bm, (0, 0, 0), mats_body, bevel=0.0, as_asset=True)
        return body, wings

    def skin(mesh_obj, arm_obj):
        mod = mesh_obj.modifiers.new(name='Armature', type='ARMATURE')
        mod.object = arm_obj
        mesh_obj.parent = arm_obj
        # simple vertex groups by height/x for placeholder
        mesh = mesh_obj.data
        groups = {}
        for b in arm_obj.data.bones:
            groups[b.name] = mesh_obj.vertex_groups.new(name=b.name)
        for v in mesh.vertices:
            # assign nearest bone by head distance
            best = 'spine_02'
            best_d = 1e9
            for b in arm_obj.data.bones:
                d = (v.co - b.head_local).length
                if d < best_d:
                    best_d = d
                    best = b.name
            groups[best].add([v.index], 1.0, 'REPLACE')

    characters = [
        ('SK_MAP_Messenger', 'MAP_Messenger', 1.9, 3.6, False, False),
        ('SK_MAP_Archangel', 'MAP_Archangel', 2.2, 5.0, True, False),
        ('SK_MAP_Gabriel_Base', 'MAP_Gabriel', 2.8, 7.0, True, True),
    ]
    for prefix, col, h, span, heavy, gab in characters:
        rig = make_rig(f'RIG_MAP_{prefix.replace("SK_MAP_", "")}')
        # rename rig properly
        if prefix.endswith('_Base'):
            rig.name = 'RIG_MAP_Gabriel'
        elif 'Archangel' in prefix:
            rig.name = 'RIG_MAP_Archangel'
        else:
            rig.name = 'RIG_MAP_Messenger'
        body, wings = make_body(prefix, h, span, col, heavy, gab)
        # rename meshes to character names as main exportables - keep parts
        skin(body, rig)
        skin(wings, rig)
        # also create empty root object named SK_* parenting? Use body as SK name
        body.name = prefix
        body.data.name = prefix

    # Attachments
    bm = bmesh.new(); core.add_box(bm, 0.08, 1.0, 0.02, (0, 0.5, 0), 2); core.add_box(bm, 0.12, 0.2, 0.05, (0, 0, 0), 3)
    fm('SM_MAP_Sword_Ceremonial', 'MAP_Attachments', bm, mats_body, origin=(0, 0, 0), ucx=None)
    bm = bmesh.new(); core.add_cyl(bm, 0.03, 2.2, (0, 0, 0), 6, 2); core.add_box(bm, 0.15, 0.05, 0.25, (0, 0, 1.0), 3)
    # orient spear along +Y
    bm.free(); bm = bmesh.new()
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.03, radius2=0.03, depth=2.2)
    bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 4, 'X'))
    bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((0, 1.1, 0)))
    core.add_box(bm, 0.08, 0.2, 0.08, (0, 0, 0), 3)
    fm('SM_MAP_Spear_Light', 'MAP_Attachments', bm, mats_body, ucx=None)
    bm = bmesh.new(); core.add_cyl(bm, 0.275, 0.04, segments=20)
    fm('SM_MAP_HaloRing', 'MAP_Attachments', bm, ['M_MAP_Armor_GoldAged', 'M_MAP_Emissive_Subtle'], ucx=None)
    bm = bmesh.new(); core.add_box(bm, 0.15, 1.7, 0.04, (0, 0.85, 0), 2); core.add_box(bm, 0.2, 0.3, 0.08, (0, 0, 0), 3); core.add_box(bm, 0.04, 1.4, 0.02, (0, 0.9, 0.04), 7)
    fm('SM_MAP_GabrielBlade', 'MAP_Attachments', bm, mats_body, ucx=None)
    bm = bmesh.new(); core.add_box(bm, 1.2, 0.5, 0.7, (0, -0.1, 0.2), 1); core.add_box(bm, 0.4, 0.4, 0.35, (-0.5, 0.1, 0.5), 2); core.add_box(bm, 0.4, 0.4, 0.35, (0.5, 0.1, 0.5), 2)
    fm('SM_MAP_ShoulderMantle', 'MAP_Attachments', bm, mats_body, ucx=None)
    bm = bmesh.new()
    for i in range(8):
        core.add_box(bm, 0.15, 0.5, 0.05, ((rng.random() - 0.5) * 0.5, rng.random() * 0.3, rng.random() * 0.2), 4)
    fm('SM_MAP_FeatherCluster', 'MAP_Attachments', bm, mats_body, ucx=None)

    # human scale ref
    bm = bmesh.new(); core.add_cyl(bm, 0.15, 1.8, segments=8)
    core.finish_mesh('PREVIEW_HumanScale_180', 'MAP_Showcase', bm, (0, 0, 0), ['M_MAP_Cloth_Ivory'], bevel=0.0, as_asset=False)

    names = [o.name for o in bpy.data.objects if o.name.startswith('SK_MAP_') or o.name.startswith('SM_MAP_') or o.name.startswith('RIG_MAP_')]
    core.write_qa('MAP_QA_Report', [
        'ANGEL PLACEHOLDER',
        'NOTE: Custom rigs; retarget to Manny/Quinn not verified.',
        f'assets={len(names)}'
    ] + [f'- {n}' for n in sorted(names)])
    return names


def export_all():
    mapping = [
        ('SM_MRK_', CONTENT / 'RuinsKit', 'SM_Malkuth_RuinsKit_ALL.fbx'),
        ('SM_MSK_', CONTENT / 'SanctuaryKit', 'SM_Malkuth_SanctuaryKit_ALL.fbx'),
        ('SM_MMLK_', CONTENT / 'MirrorLabyrinthKit', 'SM_Malkuth_MirrorLabyrinthKit_ALL.fbx'),
        ('SM_MP_', CONTENT / 'PropsKit', 'SM_Malkuth_Props_ALL.fbx'),
        ('SM_MAP_', CONTENT / 'AngelPlaceholder', None),
        ('SK_MAP_', CONTENT / 'AngelPlaceholder', None),
    ]
    results = {}
    for prefix, out, allname in mapping:
        results[prefix] = core.export_kit_fbx(prefix, str(out), also_all_name=allname)
    # export skeletal with armatures specially
    for sk in ['SK_MAP_Messenger', 'SK_MAP_Archangel', 'SK_MAP_Gabriel_Base']:
        obj = bpy.data.objects.get(sk)
        if not obj:
            continue
        objs = [obj]
        if obj.parent and obj.parent.type == 'ARMATURE':
            objs = [obj.parent, obj]
        # include sibling meshes under same armature
        arm = obj.parent if obj.parent and obj.parent.type == 'ARMATURE' else None
        if arm:
            objs = [arm] + [c for c in bpy.data.objects if c.parent == arm and c.type == 'MESH']
        path = CONTENT / 'AngelPlaceholder' / f'{sk}.fbx'
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.export_scene.fbx(
            filepath=str(path), use_selection=True, object_types={'MESH', 'ARMATURE'},
            apply_scale_options='FBX_SCALE_ALL', axis_forward='-Y', axis_up='Z',
            apply_unit_scale=True, bake_space_transform=False, add_leaf_bones=False,
            armature_nodetype='NULL', use_mesh_modifiers=True)
        results.setdefault('SK_', []).append(sk)
    return results


def main():
    reset_scene()
    shared_mats()
    summary = {}
    print('Building Ruins...')
    summary['ruins'] = len(build_ruins())
    print('Building Sanctuary...')
    summary['sanctuary'] = len(build_sanctuary())
    print('Building Mirrors...')
    summary['mirrors'] = len(build_mirrors())
    print('Building Props...')
    summary['props'] = len(build_props())
    print('Building Angels...')
    summary['angels'] = len(build_angels())

    blend_path = ART / 'SM_Malkuth_AllKits.blend'
    ART.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print('Exporting FBX...')
    exported = export_all()
    summary['exported_groups'] = {k: len(v) if isinstance(v, list) else v for k, v in exported.items()}
    summary['blend'] = str(blend_path)
    qa = ART / 'MALKUTH_KITS_SUMMARY.txt'
    qa.write_text('\n'.join(f'{k}: {v}' for k, v in summary.items()), encoding='utf-8')
    print('DONE', summary)
    return summary


if __name__ == '__main__':
    main()
