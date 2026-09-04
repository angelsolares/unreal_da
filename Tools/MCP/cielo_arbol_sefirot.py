# Cuarta capa del cielo: el Arbol de la Vida, las diez sefirot como orbes.
#
# Usa los diez MI_DA_Orbe_S01..S10 que llevaban semanas pintados y sin colocar:
# son instancias de M_DA_HazLuz con Color, Brillo y Opacidad, una por sefira,
# de Keter (blanco, brillo 4,5) a Malkuth (oro, 1,8).
#
# Van muy al norte y muy alto, como una constelacion que se ve desde el valle,
# en el orden clasico del arbol. Reutiliza BP_DA_OrbeNubes: raiz, malla y giro.
import unreal

V = unreal.Vector
BP = "/Game/DarkAngels/Blueprints/World/BP_DA_OrbeNubes"
MAT = "/Game/DarkAngels/Materials/MI_DA_Orbe_"
CENTRO = V(14000.0, 130000.0, 56000.0)
ANCHO, ALTO = 23000.0, 27000.0
# (sufijo del material, x relativa, z relativa, escala)
SEFIROT = [
    ("S01_Keter", 0.0, 1.00, 84.0),
    ("S02_Chokmah", 1.0, 0.78, 62.0),
    ("S03_Binah", -1.0, 0.78, 62.0),
    ("S04_Chesed", 1.0, 0.44, 57.0),
    ("S05_Gevurah", -1.0, 0.44, 57.0),
    ("S06_Tiferet", 0.0, 0.34, 73.0),
    ("S07_Netzach", 1.0, 0.10, 54.0),
    ("S08_Hod", -1.0, 0.10, 54.0),
    ("S09_Yesod", 0.0, -0.16, 65.0),
    ("S10_Malkuth", 0.0, -0.56, 78.0),
]


def run():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    clase = unreal.load_asset(BP).generated_class()
    esfera = unreal.load_asset("/Engine/BasicShapes/Sphere")
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Sefira_"):
            a.destroy_actor()
    for suf, rx, rz, esc in SEFIROT:
        mat = unreal.load_asset(MAT + suf)
        if mat is None:
            print("!! sin material", suf); continue
        p = V(CENTRO.x + rx * ANCHO, CENTRO.y, CENTRO.z + rz * ALTO)
        act = eas.spawn_actor_from_class(clase, p, unreal.Rotator(0, 0, 0))
        act.set_actor_label("Sefira_" + suf)
        act.set_folder_path("Cielo/Sefirot")
        act.set_actor_scale3d(V(esc, esc, esc))
        for c in act.get_components_by_class(unreal.ActorComponent):
            if isinstance(c, unreal.StaticMeshComponent) and not isinstance(c, unreal.InstancedStaticMeshComponent):
                c.set_static_mesh(esfera)
                c.set_material(0, mat)
                c.set_editor_property("cast_shadow", False)
                c.set_editor_property("affect_distance_field_lighting", False)
                c.set_editor_property("affect_dynamic_indirect_lighting", False)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            elif isinstance(c, unreal.RotatingMovementComponent):
                c.set_editor_property("rotation_rate", unreal.Rotator(0.0, 0.0, 0.8))
        act.modify()
        print("  %-14s en (%7.0f %7.0f %7.0f) escala %4.0f" % (suf, p.x, p.y, p.z, esc))
    print("guardado:", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())


run()
