"""Generate SM_Malkuth_RuinsKit."""
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix
from pathlib import Path
import importlib.util

CORE = Path(r'd:/Game Projects/Unreal DA/DarkAngelsPOC 5.8/ArtSource/Blender/scripts/da_kit_core.py')
spec = importlib.util.spec_from_file_location('da_kit_core', CORE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

rng = random.Random(17)


def mats():
    core.ensure_mat('M_MRK_Stone_Ivory', (0.86, 0.82, 0.74), 0.62)
    core.ensure_mat('M_MRK_Stone_Dark', (0.35, 0.33, 0.30), 0.7)
    core.ensure_mat('M_MRK_Gold_Aged', (0.72, 0.58, 0.28), 0.45, 0.65, (0.85, 0.7, 0.35), 0.08)
    core.ensure_mat('M_MRK_Moss', (0.22, 0.38, 0.18), 0.8)
    core.ensure_mat('M_MRK_Soil', (0.28, 0.2, 0.12), 0.9)
    core.ensure_mat('M_MRK_Emissive_Subtle', (0.9, 0.85, 0.65), 0.4, 0.1, (1.0, 0.92, 0.7), 0.35)


def column(name, height, radius, col, broken_top=False, half=False):
    bm = bmesh.new()
    # base
    core.add_cyl(bm, radius * 1.35, 0.25, (0, 0, 0), 16, 0)
    core.add_box(bm, radius * 2.4, radius * 2.4, 0.12, (0, 0, 0), 0)
    # shaft
    shaft_h = height - 0.55
    if broken_top:
        shaft_h = height * 0.75
    if half:
        # half cylinder approximated by thin box + cyl cut visual
        core.add_box(bm, radius * 1.05, radius * 0.55, shaft_h, (0, -radius * 0.25, 0.25), 0)
        core.add_cyl(bm, radius * 0.55, shaft_h, (0, 0, 0.25), 12, 0)
    else:
        core.add_cyl(bm, radius, shaft_h, (0, 0, 0.25), 16, 0)
        # fluting hint
        for i in range(8):
            a = i * math.tau / 8
            core.add_box(
                bm, 0.04, 0.04, shaft_h * 0.9,
                (math.cos(a) * radius * 0.92, math.sin(a) * radius * 0.92, 0.35), 1
            )
    # capital / break
    if broken_top:
        core.add_ico(bm, radius * 0.7, (radius * 0.2, 0, 0.25 + shaft_h), 1, 1)
        core.add_box(bm, radius * 0.9, radius * 0.5, 0.2, (0, 0, 0.15 + shaft_h), 1)
    else:
        core.add_cyl(bm, radius * 1.25, 0.18, (0, 0, 0.25 + shaft_h), 16, 0)
        core.add_box(bm, radius * 2.5, radius * 2.5, 0.12, (0, 0, 0.4 + shaft_h), 2)
    mats_list = ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged']
    obj = core.finish_mesh(name, col, bm, (0, 0, 0), mats_list, bevel=0.015)
    core.make_ucx(name, 0, (radius * 2.6, radius * 2.6, height), (0, 0, 0), 'MRK_Collisions')
    return obj


def build_columns():
    col = 'MRK_Columns'
    column('SM_MRK_Column_Intact_400', 4.0, 0.40, col)
    column('SM_MRK_Column_Intact_600', 6.0, 0.50, col)
    column('SM_MRK_Column_Half_250', 2.5, 0.40, col, broken_top=True, half=True)
    column('SM_MRK_Column_Broken_A', 2.2, 0.38, col, broken_top=True)
    column('SM_MRK_Column_Broken_B', 1.4, 0.36, col, broken_top=True)

    # Base
    bm = bmesh.new()
    core.add_box(bm, 1.2, 1.2, 0.2, (0, 0, 0), 0)
    core.add_cyl(bm, 0.55, 0.25, (0, 0, 0.2), 16, 0)
    core.finish_mesh('SM_MRK_Column_Base', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Column_Base', 0, (1.2, 1.2, 0.45), (0, 0, 0), 'MRK_Collisions')

    # Capital
    bm = bmesh.new()
    core.add_box(bm, 1.3, 1.3, 0.18, (0, 0, 0), 0)
    core.add_cyl(bm, 0.55, 0.25, (0, 0, 0.15), 12, 2)
    core.add_box(bm, 0.9, 0.9, 0.2, (0, 0, 0.35), 0)
    core.finish_mesh('SM_MRK_Column_Capital', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Column_Capital', 0, (1.3, 1.3, 0.55), (0, 0, 0), 'MRK_Collisions')

    # Fallen 400 — horizontal shaft along +Y
    bm = bmesh.new()
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.4, radius2=0.4, depth=2.2)
    bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.radians(90), 4, 'X'))
    bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((0, 1.1, 0.4)))
    ret2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.38, radius2=0.35, depth=1.6)
    bmesh.ops.rotate(bm, verts=ret2['verts'], cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.radians(90), 4, 'X'))
    bmesh.ops.translate(bm, verts=ret2['verts'], vec=Vector((0.15, 3.0, 0.35)))
    core.add_box(bm, 1.1, 1.1, 0.25, (0, 0.2, 0), 0)
    core.add_ico(bm, 0.35, (0.2, 2.2, 0.35), 0, 1)
    core.finish_mesh('SM_MRK_Column_Fallen_400', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Column_Fallen_400', 0, (1.2, 4.0, 0.9), (0, 2.0, 0), 'MRK_Collisions')

    # Collapsed cluster
    bm = bmesh.new()
    core.add_box(bm, 1.2, 1.2, 0.35, (-0.8, -0.5, 0), 0)
    core.add_cyl(bm, 0.35, 2.0, (0.5, 0.2, 0.35), 12, 0)
    # tip fallen
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.3, radius2=0.3, depth=1.5)
    bmesh.ops.rotate(bm, verts=ret['verts'], cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.radians(75), 4, 'X'))
    bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((-0.2, 1.2, 0.5)))
    core.add_box(bm, 1.1, 1.1, 0.3, (1.2, -0.8, 0), 0)
    core.add_ico(bm, 0.4, (1.0, 0.8, 0.4), 0, 3)
    core.finish_mesh('SM_MRK_Column_CollapsedCluster', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged', 'M_MRK_Moss'])
    core.make_ucx('SM_MRK_Column_CollapsedCluster', 0, (4.0, 3.0, 1.5), (0, 0, 0), 'MRK_Collisions')


def build_pedestals_obelisks():
    from mathutils import Matrix
    col = 'MRK_Pedestals'
    # square 100
    bm = bmesh.new()
    core.add_box(bm, 1.0, 1.0, 0.2, (0, 0, 0), 0)
    core.add_box(bm, 0.85, 0.85, 0.6, (0, 0, 0.2), 0)
    core.finish_mesh('SM_MRK_Pedestal_Square_100', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Pedestal_Square_100', 0, (1, 1, 0.8), (0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 1.5, 1.5, 0.25, (0, 0, 0), 0)
    core.add_box(bm, 1.25, 1.25, 0.7, (0, 0, 0.25), 0)
    core.add_box(bm, 1.35, 1.35, 0.15, (0, 0, 0.95), 2)
    core.add_box(bm, 1.1, 1.1, 0.1, (0, 0, 1.1), 0)
    core.finish_mesh('SM_MRK_Pedestal_Square_150', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Pedestal_Square_150', 0, (1.5, 1.5, 1.2), (0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_cyl(bm, 0.6, 0.2, (0, 0, 0), 20, 0)
    core.add_cyl(bm, 0.5, 0.7, (0, 0, 0.2), 20, 0)
    core.finish_mesh('SM_MRK_Pedestal_Round_120', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Pedestal_Round_120', 0, (1.2, 1.2, 0.9), (0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 2.0, 2.0, 0.25, (0, 0, 0), 0)
    core.add_box(bm, 1.7, 1.7, 0.35, (0, 0, 0.25), 0)
    core.add_box(bm, 1.4, 1.4, 0.5, (0, 0, 0.6), 0)
    core.add_box(bm, 1.5, 1.5, 0.1, (0, 0, 1.1), 2)
    core.add_box(bm, 1.2, 1.2, 0.3, (0, 0, 1.2), 0)
    core.finish_mesh('SM_MRK_StatueBase_200', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_StatueBase_200', 0, (2, 2, 1.5), (0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 1.5, 1.5, 0.25, (0, 0, 0), 0)
    core.add_box(bm, 1.2, 1.2, 0.7, (0, 0, 0.25), 0)
    core.add_box(bm, 0.8, 0.6, 0.5, (0.4, -0.2, 0.3), 1)
    core.add_ico(bm, 0.3, (0.6, 0.4, 0.3), 0, 3)
    core.finish_mesh('SM_MRK_Pedestal_Broken', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged', 'M_MRK_Moss'])
    core.make_ucx('SM_MRK_Pedestal_Broken', 0, (1.5, 1.5, 1.0), (0, 0, 0), 'MRK_Collisions')

    col = 'MRK_Obelisks'

    def obelisk(name, height, base):
        bm = bmesh.new()
        core.add_box(bm, base, base, 0.25, (0, 0, 0), 0)
        core.add_box(bm, base * 0.75, base * 0.75, 0.2, (0, 0, 0.25), 0)
        # taper shaft via stacked boxes
        steps = 8
        for i in range(steps):
            t = i / steps
            s = base * 0.55 * (1 - t * 0.55)
            z = 0.45 + t * (height - 0.9)
            h = (height - 0.9) / steps
            core.add_box(bm, s, s, h, (0, 0, z), 0)
            if i % 2 == 0:
                core.add_box(bm, s * 1.02, 0.03, h * 0.8, (0, s * 0.5, z), 2)
        # tip
        core.add_box(bm, base * 0.12, base * 0.12, 0.35, (0, 0, height - 0.45), 2)
        core.finish_mesh(name, col, bm, (0, 0, 0),
                         ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
        core.make_ucx(name, 0, (base, base, height), (0, 0, 0), 'MRK_Collisions')

    obelisk('SM_MRK_Obelisk_400', 4.0, 1.2)
    obelisk('SM_MRK_Obelisk_700', 7.0, 1.8)

    bm = bmesh.new()
    core.add_box(bm, 1.0, 1.0, 0.2, (0, 0, 0), 0)
    for i in range(5):
        s = 0.7 * (1 - i * 0.1)
        core.add_box(bm, s, s, 0.45, (0, 0, 0.2 + i * 0.45), 0)
    core.add_box(bm, 0.45, 0.45, 0.8, (0.35, 0.2, 0.5), 1)
    core.finish_mesh('SM_MRK_Obelisk_Broken', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Obelisk_Broken', 0, (1.4, 1.4, 3.0), (0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 1.4, 1.4, 0.3, (0, 0.3, 0), 0)
    for i in range(6):
        s = 0.7 * (1 - i * 0.08)
        # along Y
        core.add_box(bm, s, 0.7, s, (0.1, 1.0 + i * 0.7, 0.35), 0)
    core.add_box(bm, 0.35, 0.35, 0.5, (0.5, 4.2, 0.2), 1)
    core.finish_mesh('SM_MRK_Obelisk_Fallen', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Obelisk_Fallen', 0, (1.6, 5.0, 1.0), (0, 2.2, 0), 'MRK_Collisions')


def build_domes_extras():
    from mathutils import Matrix
    col = 'MRK_Domes'

    def dome_shell(bm, radius, thickness, z0, segs, start_a, end_a, mat=0):
        # approximate dome quarter/half with stacked rings of boxes/cyl wedges
        rings = 6
        for ri in range(rings):
            t0 = ri / rings
            t1 = (ri + 1) / rings
            # sphere y = sqrt(r^2 - x^2) style: height from equator-ish
            elev0 = math.sin(t0 * math.pi * 0.5)
            elev1 = math.sin(t1 * math.pi * 0.5)
            rad0 = math.cos(t0 * math.pi * 0.5) * radius
            rad1 = math.cos(t1 * math.pi * 0.5) * radius
            z = z0 + elev0 * radius
            h = max(0.15, (elev1 - elev0) * radius)
            # ring segment
            steps = max(4, int(segs * (end_a - start_a) / math.tau))
            for si in range(steps):
                a0 = start_a + (end_a - start_a) * si / steps
                a1 = start_a + (end_a - start_a) * (si + 1) / steps
                am = (a0 + a1) * 0.5
                w = abs(a1 - a0) * ((rad0 + rad1) * 0.5)
                core.add_box(
                    bm, max(0.2, w), thickness, h,
                    (math.cos(am) * ((rad0 + rad1) * 0.5), math.sin(am) * ((rad0 + rad1) * 0.5), z),
                    mat
                )

    bm = bmesh.new()
    dome_shell(bm, 3.0, 0.35, 0.0, 24, 0, math.pi * 0.5, 0)
    core.add_box(bm, 0.4, 3.2, 0.35, (1.5, 0, 0.1), 1)
    core.finish_mesh('SM_MRK_Dome_Quarter_600', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Dome_Quarter_600', 0, (3.2, 3.2, 3.2), (1.2, 1.2, 0), 'MRK_Collisions')

    bm = bmesh.new()
    dome_shell(bm, 4.0, 0.4, 0.0, 28, -math.pi * 0.5, math.pi * 0.5, 0)
    # front opening edges
    core.add_box(bm, 0.4, 0.4, 3.5, (0, -4.0, 0), 1)
    core.add_box(bm, 0.4, 0.4, 3.5, (0, 4.0, 0), 1)
    core.finish_mesh('SM_MRK_Dome_HalfBroken_800', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Dome_HalfBroken_800', 0, (4.5, 8.2, 4.2), (0, 0, 0), 'MRK_Collisions')

    # Rib
    bm = bmesh.new()
    for i in range(10):
        t = i / 9
        ang = t * math.pi * 0.5
        x = math.cos(ang) * 2.0
        z = math.sin(ang) * 2.0
        core.add_box(bm, 0.25, 0.35, 0.35, (x, 0, z), 0)
    core.finish_mesh('SM_MRK_Dome_Rib_400', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Dome_Rib_400', 0, (2.2, 0.5, 2.2), (1.0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_cyl(bm, 1.4, 0.35, (0, 0, 0), 16, 0)
    core.add_cyl(bm, 1.0, 0.5, (0, 0, 0.3), 12, 0, radius2=0.4)
    core.add_box(bm, 0.8, 0.8, 0.2, (0.6, 0.4, 0.1), 1)
    core.finish_mesh('SM_MRK_Dome_CapFragment', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Dome_CapFragment', 0, (3, 3, 1.0), (0, 0, 0), 'MRK_Collisions')

    # Rotunda ruin
    bm = bmesh.new()
    core.add_cyl(bm, 4.0, 0.4, (0, 0, 0), 24, 0)
    core.add_cyl(bm, 3.4, 0.2, (0, 0, 0.35), 24, 1)
    for i in range(4):
        a = i * math.tau / 4
        x, y = math.cos(a) * 3.2, math.sin(a) * 3.2
        core.add_cyl(bm, 0.35, 1.8, (x, y, 0.4), 10, 0)
        core.add_box(bm, 0.7, 0.7, 0.2, (x, y, 2.1), 0)
    core.finish_mesh('SM_MRK_Rotunda_Ruin_800', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_Rotunda_Ruin_800', 0, (8, 8, 0.5), (0, 0, 0), 'MRK_Collisions')
    for i in range(4):
        a = i * math.tau / 4
        core.make_ucx('SM_MRK_Rotunda_Ruin_800', i + 1, (0.8, 0.8, 2.2),
                      (math.cos(a) * 3.2, math.sin(a) * 3.2, 0.4), 'MRK_Collisions')

    col = 'MRK_Extras'
    # Ruined arch
    bm = bmesh.new()
    core.add_box(bm, 0.7, 0.7, 3.4, (-2.0, 0, 0), 0)
    core.add_box(bm, 0.7, 0.7, 3.0, (2.0, 0, 0), 0)
    core.add_box(bm, 4.6, 0.7, 0.55, (0, 0, 3.2), 0)
    core.add_box(bm, 0.5, 0.5, 0.8, (-0.3, 0.2, 2.6), 1)
    core.add_box(bm, 0.2, 0.2, 0.3, (0, -0.4, 3.4), 2)
    core.finish_mesh('SM_MRK_RuinedArch_300', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged'])
    core.make_ucx('SM_MRK_RuinedArch_300', 0, (0.8, 0.8, 3.5), (-2, 0, 0), 'MRK_Collisions')
    core.make_ucx('SM_MRK_RuinedArch_300', 1, (0.8, 0.8, 3.2), (2, 0, 0), 'MRK_Collisions')
    core.make_ucx('SM_MRK_RuinedArch_300', 2, (4.6, 0.8, 0.6), (0, 0, 3.2), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 3.0, 0.45, 2.0, (0, 1.5, 0), 0)  # pivot at end y=0, extends +Y
    core.add_box(bm, 2.4, 0.45, 0.6, (0.2, 1.5, 2.0), 0)
    core.add_box(bm, 1.2, 0.45, 0.5, (-0.5, 1.5, 2.4), 1)
    core.add_ico(bm, 0.2, (1.0, 1.3, 0.2), 0, 3)
    # rebuild with pivot at y=0 end
    bm.free()
    bm = bmesh.new()
    core.add_box(bm, 0.45, 3.0, 1.8, (0, 1.5, 0), 0)
    core.add_box(bm, 0.45, 2.2, 0.7, (0, 1.4, 1.8), 0)
    core.add_box(bm, 0.45, 1.0, 0.5, (0, 0.8, 2.3), 1)
    core.add_ico(bm, 0.18, (0.3, 2.5, 0.15), 0, 3)
    core.finish_mesh('SM_MRK_WallFragment_300', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged', 'M_MRK_Moss'])
    core.make_ucx('SM_MRK_WallFragment_300', 0, (0.5, 3.0, 2.6), (0, 1.5, 0), 'MRK_Collisions')

    bm = bmesh.new()
    for i in range(10):
        core.add_box(bm, 0.3 + rng.random() * 0.5, 0.3 + rng.random() * 0.5, 0.2 + rng.random() * 0.5,
                     ((rng.random() - 0.5) * 1.6, (rng.random() - 0.5) * 1.6, 0), 0 if i % 2 == 0 else 1)
    core.add_ico(bm, 0.2, (0.5, -0.4, 0.15), 0, 3)
    core.finish_mesh('SM_MRK_RubbleCluster_A', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged', 'M_MRK_Moss'])
    core.make_ucx('SM_MRK_RubbleCluster_A', 0, (2, 2, 0.8), (0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    for i in range(12):
        core.add_box(bm, 0.35 + rng.random() * 0.4, 0.4 + rng.random() * 0.6, 0.15 + rng.random() * 0.4,
                     ((rng.random() - 0.5) * 1.2, -1.2 + i * 0.25, 0), 1 if i % 3 == 0 else 0)
        if i % 4 == 0:
            core.add_ico(bm, 0.12, ((rng.random() - 0.5), -1.0 + i * 0.25, 0.2), 0, 3)
    core.finish_mesh('SM_MRK_RubbleCluster_B', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged', 'M_MRK_Moss'])
    core.make_ucx('SM_MRK_RubbleCluster_B', 0, (1.5, 3.0, 0.7), (0, 0, 0), 'MRK_Collisions')

    bm = bmesh.new()
    core.add_box(bm, 1.2, 0.35, 2.2, (0, 0, 0), 0)
    # abstract geometric grooves
    for i in range(5):
        core.add_box(bm, 0.9, 0.05, 0.05, (0, -0.2, 0.4 + i * 0.3), 2)
    core.add_box(bm, 0.4, 0.05, 0.4, (0, -0.22, 1.5), 5)
    core.finish_mesh('SM_MRK_InscribedSlab', col, bm, (0, 0, 0),
                     ['M_MRK_Stone_Ivory', 'M_MRK_Stone_Dark', 'M_MRK_Gold_Aged', 'M_MRK_Moss', 'M_MRK_Soil', 'M_MRK_Emissive_Subtle'])
    core.make_ucx('SM_MRK_InscribedSlab', 0, (1.2, 0.4, 2.2), (0, 0, 0), 'MRK_Collisions')


def showcase_and_qa(names, col_map):
    # minimal showcase floor + few previews
    show = 'MRK_Showcase'
    core.remove_object_by_name('PREVIEW_MRK_Floor')
    bm = bmesh.new()
    core.add_box(bm, 30, 30, 0.05, (0, 0, -0.05), 0)
    obj = core.new_mesh_object('PREVIEW_MRK_Floor', show)
    core.bm_to_obj(bm, obj)
    bm.free()
    core.assign_mats(obj, ['M_MRK_Soil'])
    obj.location = (40, 0, 0)

    for i, n in enumerate(names[:12]):
        src = bpy.data.objects.get(n)
        if not src:
            continue
        pn = f'PREVIEW_{n}'
        core.remove_object_by_name(pn)
        dup = src.copy()
        dup.data = src.data
        dup.name = pn
        core.link_exclusive(dup, show)
        dup.location = Vector((40 + (i % 4) * 5, (i // 4) * 6, 0))
        try:
            if dup.asset_data:
                dup.asset_clear()
        except Exception:
            pass

    count, issues = core.qa_assets(names, col_map, 'MRK_Collisions', 'MRK_QA_Report')
    return count, issues


def run():
    from mathutils import Matrix  # ensure available in nested
    globals()['Matrix'] = Matrix
    core.ensure_kit_collections('SM_Malkuth_RuinsKit', [
        'MRK_Columns', 'MRK_Domes', 'MRK_Pedestals', 'MRK_Obelisks', 'MRK_Extras',
        'MRK_Collisions', 'MRK_Showcase'
    ])
    mats()
    build_columns()
    build_pedestals_obelisks()
    build_domes_extras()

    names = [
        'SM_MRK_Column_Intact_400', 'SM_MRK_Column_Intact_600', 'SM_MRK_Column_Half_250',
        'SM_MRK_Column_Broken_A', 'SM_MRK_Column_Broken_B', 'SM_MRK_Column_Base',
        'SM_MRK_Column_Capital', 'SM_MRK_Column_Fallen_400', 'SM_MRK_Column_CollapsedCluster',
        'SM_MRK_Dome_Quarter_600', 'SM_MRK_Dome_HalfBroken_800', 'SM_MRK_Dome_Rib_400',
        'SM_MRK_Dome_CapFragment', 'SM_MRK_Rotunda_Ruin_800',
        'SM_MRK_Pedestal_Square_100', 'SM_MRK_Pedestal_Square_150', 'SM_MRK_Pedestal_Round_120',
        'SM_MRK_StatueBase_200', 'SM_MRK_Pedestal_Broken',
        'SM_MRK_Obelisk_400', 'SM_MRK_Obelisk_700', 'SM_MRK_Obelisk_Broken', 'SM_MRK_Obelisk_Fallen',
        'SM_MRK_RuinedArch_300', 'SM_MRK_WallFragment_300', 'SM_MRK_RubbleCluster_A',
        'SM_MRK_RubbleCluster_B', 'SM_MRK_InscribedSlab',
    ]
    col_map = {}
    for n in names:
        if 'Column' in n or n.startswith('SM_MRK_Column'):
            col_map[n] = 'MRK_Columns'
        elif 'Dome' in n or 'Rotunda' in n:
            col_map[n] = 'MRK_Domes'
        elif 'Pedestal' in n or 'StatueBase' in n:
            col_map[n] = 'MRK_Pedestals'
        elif 'Obelisk' in n:
            col_map[n] = 'MRK_Obelisks'
        else:
            col_map[n] = 'MRK_Extras'

    count, issues = showcase_and_qa(names, col_map)

    blend = Path(r'd:/Game Projects/Unreal DA/DarkAngelsPOC 5.8/ArtSource/Blender/SM_Malkuth_RuinsKit.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))

    exported = core.export_kit_fbx(
        'SM_MRK_',
        r'd:/Game Projects/Unreal DA/DarkAngelsPOC 5.8/Content/Blender/RuinsKit',
        also_all_name='SM_Malkuth_RuinsKit_ALL.fbx'
    )
    return {'assets': count, 'issues': len(issues), 'exported': len(exported), 'blend': str(blend)}


if __name__ == '__main__':
    print(run())
