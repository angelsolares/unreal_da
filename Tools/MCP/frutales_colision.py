# Copias de los dos cerezos de FruitTree_Collection con colision de TRONCO.
#
# Los originales traen un unico convex que envuelve la copa entera: sus paredes
# suben en cono (radio 135 a z+40, 316 a z+400) y el jugador se sube al arbol
# andando. Aqui se sustituye por una capsula vertical, que bloquea el paso pero
# no se puede trepar.
#
# Se copian en vez de arreglar el original porque FruitTree_Collection es un pack
# de Fab y esta fuera del repo. Mismo criterio que SM_DA_Talud_Esquiva.
import unreal

ORIGEN = "/Game/FruitTree_Collection/Meshes/"
DESTINO = "/Game/DarkAngels/Environment/Props/"
COPIAS = [("SM_Cherry_Tree_01", "SM_DA_Frutal_Cerezo_01"),
          ("SM_Cherry_Tree_02", "SM_DA_Frutal_Cerezo_02")]


def capsula_de_tronco(malla):
    """Deja una sola capsula vertical, centrada en el eje del arbol y tan alta
    como el, en lugar del convex de la copa."""
    b = malla.get_bounds()
    radio = 0.5 * min(b.box_extent.x, b.box_extent.y)
    alto = 2.0 * b.box_extent.z
    largo = max(50.0, alto - 2.0 * radio)
    body = malla.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    elem = unreal.KSphylElem()
    elem.set_editor_property("center", unreal.Vector(b.origin.x, b.origin.y, b.origin.z))
    elem.set_editor_property("radius", radio)
    elem.set_editor_property("length", largo)
    agg.set_editor_property("convex_elems", [])
    agg.set_editor_property("box_elems", [])
    agg.set_editor_property("sphere_elems", [])
    agg.set_editor_property("sphyl_elems", [elem])
    body.set_editor_property("agg_geom", agg)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    return radio, largo, b.origin


def run():
    hechas = []
    for src, dst in COPIAS:
        ruta_dst = DESTINO + dst
        if unreal.EditorAssetLibrary.does_asset_exist(ruta_dst):
            unreal.EditorAssetLibrary.delete_asset(ruta_dst)
        nueva = unreal.EditorAssetLibrary.duplicate_asset(ORIGEN + src, ruta_dst)
        if not nueva:
            print("!! no pude copiar", src); continue
        radio, largo, o = capsula_de_tronco(nueva)
        unreal.EditorAssetLibrary.save_asset(ruta_dst, only_if_is_dirty=False)
        m = unreal.load_asset(ruta_dst)
        agg = m.get_editor_property("body_setup").get_editor_property("agg_geom")
        print("%-26s capsula radio %5.1f largo %5.1f en (%5.1f %5.1f %5.1f) | releido: sphyl=%d convex=%d" % (
            dst, radio, largo, o.x, o.y, o.z,
            len(agg.get_editor_property("sphyl_elems")), len(agg.get_editor_property("convex_elems"))))
        hechas.append((src, ruta_dst))
    # repuntar los actores del nivel
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    mapa = {s: unreal.load_asset(d) for s, d in hechas}
    n = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor):
        c = a.static_mesh_component
        if not c or not c.static_mesh:
            continue
        nombre = c.static_mesh.get_name()
        if nombre in mapa:
            c.set_static_mesh(mapa[nombre])
            a.modify()
            n += 1
    print("actores repuntados:", n)
    print("nivel guardado:", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())


run()
