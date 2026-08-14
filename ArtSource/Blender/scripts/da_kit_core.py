"""Shared helpers for Dark Angels Malkuth Blender kits (UE 5.8)."""
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix


def setup_metric():
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = 'METERS'


def ensure_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    root = bpy.context.scene.collection
    if parent is None:
        if col.name not in [c.name for c in root.children]:
            try:
                root.children.link(col)
            except RuntimeError:
                pass
    else:
        parent_col = bpy.data.collections.get(parent) if isinstance(parent, str) else parent
        # unlink from scene root if needed
        if col.name in [c.name for c in root.children]:
            try:
                root.children.unlink(col)
            except RuntimeError:
                pass
        if parent_col and col.name not in [c.name for c in parent_col.children]:
            try:
                parent_col.children.link(col)
            except RuntimeError:
                pass
    return col


def ensure_kit_collections(root_name, sub_names):
    setup_metric()
    root = ensure_collection(root_name)
    subs = {n: ensure_collection(n, root) for n in sub_names}
    return root, subs


def kit_names():
    return {
        'SM_Malkuth_GardenKit', 'MGK_Hedges', 'MGK_Benches', 'MGK_Fountains', 'MGK_Paths',
        'MGK_Extras', 'MGK_Collisions', 'MGK_Showcase',
        'SM_Malkuth_RuinsKit', 'MRK_Columns', 'MRK_Domes', 'MRK_Pedestals', 'MRK_Obelisks',
        'MRK_Extras', 'MRK_Collisions', 'MRK_Showcase',
        'SM_Malkuth_SanctuaryKit', 'MSK_Trunks', 'MSK_BranchesRoots', 'MSK_Altars', 'MSK_Barriers',
        'MSK_Extras', 'MSK_Collisions', 'MSK_Showcase',
        'SM_Malkuth_MirrorLabyrinthKit', 'MMLK_Mirrors', 'MMLK_Bases', 'MMLK_Posts', 'MMLK_Extras',
        'MMLK_Collisions', 'MMLK_Showcase',
        'SK_Malkuth_AngelPlaceholder', 'MAP_Messenger', 'MAP_Archangel', 'MAP_Gabriel',
        'MAP_Attachments', 'MAP_Rigs', 'MAP_Showcase',
        'SM_Malkuth_Props', 'MP_Thrones', 'MP_Portals', 'MP_Stairs', 'MP_Bridges', 'MP_Extras',
        'MP_Collisions', 'MP_Showcase',
    }


def remove_object_by_name(name, allowed_prefix_collections=None):
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    allowed = kit_names()
    if allowed_prefix_collections:
        allowed = allowed | set(allowed_prefix_collections)
    cols = [c.name for c in obj.users_collection]
    if cols and not any(c in allowed for c in cols):
        return
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data and getattr(data, 'users', 1) == 0:
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Armature):
            bpy.data.armatures.remove(data)


def link_exclusive(obj, col_name):
    col = bpy.data.collections.get(col_name)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def new_mesh_object(name, col_name):
    remove_object_by_name(name)
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    link_exclusive(obj, col_name)
    return obj


def bm_to_obj(bm, obj):
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    obj.data.update()


def apply_all(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.data and getattr(obj.data, 'users', 1) > 1:
        obj.data = obj.data.copy()
        obj.data.name = obj.name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.select_set(False)


def set_origin_world(obj, world_point):
    mw = obj.matrix_world.copy()
    local = mw.inverted() @ Vector(world_point)
    obj.data.transform(Matrix.Translation(-local))
    obj.matrix_world.translation = Vector(world_point)


def shade_smooth(obj, angle_deg=40):
    for p in obj.data.polygons:
        p.use_smooth = True


def ensure_mat(name, color, roughness=0.55, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color[:3], 1.0)
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    noise = nodes.new('ShaderNodeTexNoise')
    mix = nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    noise.inputs['Scale'].default_value = 7.0
    noise.inputs['Detail'].default_value = 5.0
    c1 = (*color[:3], 1.0)
    c2 = (max(0, color[0] * 0.86), max(0, color[1] * 0.86), max(0, color[2] * 0.86), 1.0)
    mix.inputs['A'].default_value = c1
    mix.inputs['B'].default_value = c2
    links.new(noise.outputs['Fac'], mix.inputs['Factor'])
    links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = roughness
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = metallic
    emit_in = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
    strength_in = bsdf.inputs.get('Emission Strength')
    if emit_in is not None:
        e = emission if emission else (0, 0, 0)
        emit_in.default_value = (*e, 1.0)
    if strength_in is not None:
        strength_in.default_value = emission_strength
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def assign_mats(obj, mat_names):
    obj.data.materials.clear()
    for n in mat_names:
        m = bpy.data.materials.get(n)
        if m:
            obj.data.materials.append(m)


def ensure_uvs(obj, fast=True):
    """Ops-free box-ish UVs for speed under MCP timeouts."""
    mesh = obj.data
    if 'UVMap' not in mesh.uv_layers:
        if mesh.uv_layers:
            mesh.uv_layers[0].name = 'UVMap'
        else:
            mesh.uv_layers.new(name='UVMap')
    uv = mesh.uv_layers['UVMap']
    for poly in mesh.polygons:
        n = poly.normal
        an = (abs(n.x), abs(n.y), abs(n.z))
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            co = mesh.vertices[vi].co
            if an[2] >= an[0] and an[2] >= an[1]:
                u, v = co.x * 0.25, co.y * 0.25
            elif an[0] >= an[1]:
                u, v = co.y * 0.25, co.z * 0.25
            else:
                u, v = co.x * 0.25, co.z * 0.25
            uv.data[li].uv = (u, v)
    if 'LightmapUV' in mesh.uv_layers:
        lm = mesh.uv_layers['LightmapUV']
    else:
        lm = mesh.uv_layers.new(name='LightmapUV')
    for pi, poly in enumerate(mesh.polygons):
        ox = (pi % 16) * 0.06
        oy = (pi // 16) * 0.06
        for li in poly.loop_indices:
            base = uv.data[li].uv
            lm.data[li].uv = (base.x * 0.05 + ox, base.y * 0.05 + oy)
    mesh.uv_layers['UVMap'].active = True


def mark_asset(obj):
    return  # skip asset browser marking for MCP performance


def add_box(bm, sx, sy, sz, loc=(0, 0, 0), mat=0):
    verts_coords = [
        (-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0),
        (-sx / 2, -sy / 2, sz), (sx / 2, -sy / 2, sz), (sx / 2, sy / 2, sz), (-sx / 2, sy / 2, sz),
    ]
    verts = [bm.verts.new(Vector(v) + Vector(loc)) for v in verts_coords]
    bm.verts.ensure_lookup_table()
    for idxs in [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        f = bm.faces.new([verts[i] for i in idxs])
        f.material_index = mat
    return verts


def add_cyl(bm, radius, depth, loc=(0, 0, 0), segments=16, mat=0, radius2=None):
    r2 = radius if radius2 is None else radius2
    ret = bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments, radius1=radius, radius2=r2, depth=depth
    )
    bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector((loc[0], loc[1], loc[2] + depth / 2)))
    for f in bm.faces:
        if any(v in ret['verts'] for v in f.verts):
            f.material_index = mat
    return ret['verts']


def add_ico(bm, radius, loc=(0, 0, 0), subdiv=0, mat=0):
    ret = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    bmesh.ops.translate(bm, verts=ret['verts'], vec=Vector(loc))
    for f in bm.faces:
        if any(v in ret['verts'] for v in f.verts):
            f.material_index = mat
    return ret['verts']


def bevel_obj(obj, width=0.012, segments=1):
    # Skip interactive bevel ops for speed/stability in MCP; silhouette already readable
    return


def finalize(obj, origin, mats, bevel=0.01, as_asset=True, do_uv=True):
    assign_mats(obj, mats)
    if bevel and bevel > 0:
        bevel_obj(obj, width=bevel, segments=1)
    shade_smooth(obj)
    apply_all(obj)
    set_origin_world(obj, origin)
    apply_all(obj)
    obj.scale = (1, 1, 1)
    obj.rotation_euler = (0, 0, 0)
    if do_uv:
        ensure_uvs(obj)
    if as_asset:
        mark_asset(obj)
    return obj


def finish_mesh(name, col, bm, origin, mats, bevel=0.01, as_asset=True):
    obj = new_mesh_object(name, col)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm_to_obj(bm, obj)
    bm.free()
    return finalize(obj, origin, mats, bevel=bevel, as_asset=as_asset)


def make_ucx(source_name, n, dims, loc, col_name):
    name = f'UCX_{source_name}_{n:02d}'
    remove_object_by_name(name)
    bm = bmesh.new()
    add_box(bm, dims[0], dims[1], dims[2], loc=(0, 0, 0))
    obj = new_mesh_object(name, col_name)
    bm_to_obj(bm, obj)
    bm.free()
    obj.display_type = 'WIRE'
    obj.hide_viewport = True
    obj.hide_render = True
    obj.location = Vector(loc)
    apply_all(obj)
    set_origin_world(obj, Vector(loc))
    apply_all(obj)
    return obj


def write_qa(text_name, lines):
    t = bpy.data.texts.get(text_name)
    if t is None:
        t = bpy.data.texts.new(text_name)
    t.clear()
    t.write('\n'.join(lines))


def dims_of(obj):
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [v.x for v in bb]
    ys = [v.y for v in bb]
    zs = [v.z for v in bb]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def tris_of(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def export_kit_fbx(prefix, out_dir, also_all_name=None):
    from pathlib import Path
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assets = [o for o in bpy.data.objects if o.name.startswith(prefix) and o.type == 'MESH']
    assets = [o for o in assets if not o.name.startswith('UCX_') and not o.name.startswith('PREVIEW_')]
    assets.sort(key=lambda o: o.name)

    for o in bpy.data.objects:
        if o.name.startswith('UCX_'):
            o.hide_viewport = False
            o.hide_render = False
            try:
                o.hide_set(False)
            except Exception:
                pass

    def do_export(path, objects):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:
            try:
                o.hide_set(False)
            except Exception:
                pass
            o.hide_viewport = False
            o.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.export_scene.fbx(
            filepath=str(path),
            use_selection=True,
            object_types={'MESH', 'ARMATURE'},
            apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Y',
            axis_up='Z',
            apply_unit_scale=True,
            bake_space_transform=True,
            mesh_smooth_type='FACE',
            use_mesh_modifiers=True,
            add_leaf_bones=False,
            path_mode='AUTO',
            batch_mode='OFF',
            armature_nodetype='NULL',
        )

    exported = []
    for asset in assets:
        ucxs = [o for o in bpy.data.objects if o.name.startswith(f'UCX_{asset.name}_') and o.type == 'MESH']
        ucxs.sort(key=lambda o: o.name)
        objs = [asset] + ucxs
        # include child meshes parented for skeletal
        for ch in bpy.data.objects:
            if ch.parent == asset and ch.type == 'MESH' and ch not in objs:
                objs.append(ch)
        path = out / f'{asset.name}.fbx'
        try:
            do_export(path, objs)
            exported.append(asset.name)
        except Exception as e:
            exported.append(f'ERR:{asset.name}:{e}')

    if also_all_name:
        uniq = []
        seen = set()
        for asset in assets:
            bundle = [asset] + [o for o in bpy.data.objects if o.name.startswith(f'UCX_{asset.name}_')]
            for o in bundle:
                if o.name not in seen:
                    seen.add(o.name)
                    uniq.append(o)
        try:
            do_export(out / also_all_name, uniq)
            exported.append(also_all_name)
        except Exception as e:
            exported.append(f'ERR_ALL:{e}')

    for o in bpy.data.objects:
        if o.name.startswith('UCX_'):
            o.hide_viewport = True
            o.hide_render = True
            try:
                o.hide_set(True)
            except Exception:
                pass
    return exported


def qa_assets(names, col_map, collision_col, report_name, skip_ucx_suffixes=('_Water', '_MirrorSurface', '_WaterUpper', '_Emissive')):
    lines = [report_name, '=' * len(report_name), '']
    issues = []
    count = 0
    for n in names:
        obj = bpy.data.objects.get(n)
        if not obj:
            issues.append(f'MISSING {n}')
            lines.append(f'- {n}: MISSING')
            continue
        count += 1
        expected_col = col_map.get(n)
        if expected_col and expected_col not in [c.name for c in obj.users_collection]:
            link_exclusive(obj, expected_col)
            issues.append(f'relinked {n} -> {expected_col}')
        if any(abs(s - 1.0) > 1e-3 for s in obj.scale):
            apply_all(obj)
            issues.append(f'applied scale {n}')
        if obj.type == 'MESH':
            uvs = [uv.name for uv in obj.data.uv_layers]
            if 'UVMap' not in uvs or 'LightmapUV' not in uvs:
                if not n.startswith('SK_'):
                    ensure_uvs(obj)
                    issues.append(f'uv fixed {n}')
            mats = [m.name if m else 'None' for m in obj.data.materials]
            d = dims_of(obj)
            t = tris_of(obj)
            is_skip = any(n.endswith(s) for s in skip_ucx_suffixes)
            ucx = [o.name for o in bpy.data.objects if o.name.startswith(f'UCX_{n}_')]
            if not is_skip and obj.type == 'MESH' and not n.startswith('SK_') and not ucx:
                make_ucx(n, 0, (max(d[0], 0.2), max(d[1], 0.2), max(d[2], 0.2)), (0, 0, 0), collision_col)
                ucx = [o.name for o in bpy.data.objects if o.name.startswith(f'UCX_{n}_')]
                issues.append(f'ucx created {n}')
            lines.append(
                f'- {n}: size=({d[0]:.2f},{d[1]:.2f},{d[2]:.2f}) tris~{t} mats={mats} '
                f'ucx={ucx if not is_skip else "N/A"}'
            )
        else:
            lines.append(f'- {n}: type={obj.type}')
    lines.append('')
    lines.append('[ISSUES]')
    if issues:
        lines.extend('! ' + i for i in issues)
    else:
        lines.append('None critical')
    lines.append(f'TOTAL={count}')
    write_qa(report_name, lines)
    return count, issues
