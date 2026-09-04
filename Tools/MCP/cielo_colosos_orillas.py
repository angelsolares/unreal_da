# Tercera capa del cielo: las caras colosales de las dos orillas.
#
# La direccion de arte pide "caras colosales de angeles en las dos orillas del
# encuadre, enmarcando la vista del valle". Ya existia UNA, Coloso_Angel_V2 al
# este del Jardin, que se lee muy bien; faltaba su pareja al oeste para que el
# valle quede encuadrado por los dos lados.
#
# Se clona el que ya hay: misma malla, mismo material y misma escala, espejado
# y girado para que mire al valle.
import unreal

V = unreal.Vector
ORIGINAL = "Coloso_Angel_V2"
# (etiqueta, x, y, z, yaw, escala)
NUEVOS = [
    ("Coloso_Angel_Norte", 58000.0, 41000.0, -40.0, 235.0, 17000.0),
]


def run():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # El original vive en un submapa, asi que get_all_level_actors (que solo ve el
    # nivel actual) no lo encuentra: hay que buscarlo por el mundo entero.
    orig = None
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.SkeletalMeshActor):
        if a.get_actor_label() == ORIGINAL:
            orig = a
            break
    if orig is None:
        print("!! no encuentro", ORIGINAL)
        return
    for etiqueta, x, y, z, yaw, esc in NUEVOS:
        for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.SkeletalMeshActor):
            if a.get_actor_label() == etiqueta:
                a.destroy_actor()
        nuevo = eas.duplicate_actor(orig, w, V(0, 0, 0))
        nuevo.set_actor_label(etiqueta)
        nuevo.set_folder_path("Hitos")
        nuevo.set_actor_location(V(x, y, z), False, True)
        nuevo.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
        nuevo.set_actor_scale3d(V(esc, esc, esc))
        for c in nuevo.get_components_by_class(unreal.ActorComponent):
            if isinstance(c, unreal.SkeletalMeshComponent):
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                c.set_editor_property("cast_shadow", False)
        nuevo.modify()
        o, e = nuevo.get_actor_bounds(False)
        print("%-22s en (%8.0f %8.0f %8.0f) yaw %5.1f escala %.0f  cima %8.0f" % (etiqueta, x, y, z, yaw, esc, o.z + e.z))
    print("guardado:", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())


run()
