# El orbe de nubes del cielo de Malkuth: un nucleo que arde dentro de tres
# cascaras de nube que giran en sentidos distintos. Va en el eje de la espiral
# de la hueste y por encima de ella, para que la procesion suba hacia el.
#
# Reutiliza los dos materiales que ya estaban pintados y que no usaba nadie:
# M_DA_OrbeLuz (opaco, con Color y Brillo) para el nucleo y M_DA_NubeOrbe
# (translucido, a dos caras) para las cascaras.
import unreal, math

V = unreal.Vector
BP_RUTA = "/Game/DarkAngels/Blueprints/World/BP_DA_OrbeNubes"
MI_NUCLEO = "/Game/DarkAngels/Materials/MI_DA_OrbeNubes_Nucleo"
CENTRO = V(14000.0, 14000.0, 88000.0)      # sobre la cima de la espiral (60.000)
# capa: (sufijo, escala xyz, material, giro yaw, giro pitch)
# El nucleo va pequeno y las cascaras muy separadas y achatadas: con esferas
# concentricas del mismo tamano el orbe se leia como una canica lisa.
NUBE = "/Game/DarkAngels/Materials/M_DA_NubeOrbe"
CAPAS = [
    ("Nucleo", V(95.0, 95.0, 95.0), MI_NUCLEO, 1.2, 0.0),
    ("Nube_A", V(200.0, 200.0, 150.0), NUBE, -2.4, 0.6),
    ("Nube_B", V(285.0, 250.0, 205.0), NUBE, 1.7, -0.9),
    ("Nube_C", V(360.0, 395.0, 250.0), NUBE, -1.1, 0.4),
    ("Nube_D", V(470.0, 430.0, 320.0), NUBE, 0.7, -0.3),
]


def crear_blueprint():
    if unreal.EditorAssetLibrary.does_asset_exist(BP_RUTA):
        return unreal.load_asset(BP_RUTA)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", unreal.Actor)
    ruta, nombre = BP_RUTA.rsplit("/", 1)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(nombre, ruta, unreal.Blueprint, f)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

    def mano(pred):
        for h in sds.k2_gather_subobject_data_for_blueprint(bp):
            d = sds.k2_find_subobject_data_from_handle(h)
            o = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(d) if d else None
            if o and pred(o.get_name()):
                return h, o
        return None, None

    raiz, _ = mano(lambda n: n.startswith("DefaultSceneRoot"))
    for clase, nom in ((unreal.StaticMeshComponent, "Capa"), (unreal.RotatingMovementComponent, "Giro")):
        p = unreal.AddNewSubobjectParams(parent_handle=raiz, new_class=clase, blueprint_context=bp)
        h, err = sds.add_new_subobject(p)
        sds.rename_subobject(h, unreal.Text(nom))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_RUTA, only_if_is_dirty=False)
    print("blueprint creado")
    return bp


def crear_material():
    if unreal.EditorAssetLibrary.does_asset_exist(MI_NUCLEO):
        return unreal.load_asset(MI_NUCLEO)
    f = unreal.MaterialInstanceConstantFactoryNew()
    ruta, nombre = MI_NUCLEO.rsplit("/", 1)
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(nombre, ruta, unreal.MaterialInstanceConstant, f)
    mi.set_editor_property("parent", unreal.load_asset("/Game/DarkAngels/Materials/M_DA_OrbeLuz"))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(1.0, 0.93, 0.78, 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Brillo", 3.2)
    unreal.MaterialEditingLibrary.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_asset(MI_NUCLEO, only_if_is_dirty=False)
    print("material del nucleo creado")
    return mi


def run():
    crear_material()
    bp = crear_blueprint()
    clase = bp.generated_class()
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    esfera = unreal.load_asset("/Engine/BasicShapes/Sphere")
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Orbe_"):
            a.destroy_actor()
    for sufijo, esc, mat, yaw, pitch in CAPAS:
        act = eas.spawn_actor_from_class(clase, CENTRO, unreal.Rotator(0, 0, 0))
        act.set_actor_label("Orbe_" + sufijo)
        act.set_folder_path("Cielo")
        act.set_actor_scale3d(esc)
        comps = act.get_components_by_class(unreal.ActorComponent)
        capa = [c for c in comps if isinstance(c, unreal.StaticMeshComponent) and not isinstance(c, unreal.InstancedStaticMeshComponent)]
        giro = [c for c in comps if isinstance(c, unreal.RotatingMovementComponent)]
        if not capa:
            print("!! sin componente de malla en", sufijo); continue
        c = capa[0]
        c.set_static_mesh(esfera)
        c.set_material(0, unreal.load_asset(mat))
        c.set_editor_property("cast_shadow", False)
        c.set_editor_property("affect_distance_field_lighting", False)
        c.set_editor_property("affect_dynamic_indirect_lighting", False)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        if giro:
            giro[0].set_editor_property("rotation_rate", unreal.Rotator(0.0, pitch, yaw))
        act.modify()
        print("  %-10s escala %s  material %-24s giro yaw %.1f pitch %.1f" % (sufijo, esc, mat.rsplit("/", 1)[-1], yaw, pitch))
    print("guardado:", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())


run()
