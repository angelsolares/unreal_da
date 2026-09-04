import unreal, math, random
V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CLASE = unreal.load_asset("/Game/DarkAngels/Blueprints/World/BP_DA_HuesteEspiral").generated_class()
CENTRO = V(14000, 14000, 22000)
# barrer la anterior si la hubiera
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("Hueste_Espiral"):
        a.destroy_actor()
act = eas.spawn_actor_from_class(CLASE, CENTRO, unreal.Rotator(0, 0, 0))
act.set_actor_label("Hueste_Espiral")
act.set_folder_path("Cielo")
comps = act.get_components_by_class(unreal.ActorComponent)
print("componentes del actor colocado:", [(c.get_name(), c.get_class().get_name()) for c in comps])
ism = [c for c in comps if isinstance(c, unreal.InstancedStaticMeshComponent)]
print("mallas instanciadas:", len(ism))
if not ism:
    print("!! sin componente de malla instanciada"); raise SystemExit
h = ism[0]
h.clear_instances()
# espiral logaritmica: cuatro vueltas, subiendo, con los angeles mirando al centro
N = 150
for i in range(N):
    f = i / float(N - 1)
    ang = f * 3.5 * 2.0 * math.pi
    radio = 22000.0 + f * 46000.0
    alt = f * 40000.0
    random.seed(i * 7919)
    radio += random.uniform(-2600.0, 2600.0)
    alt += random.uniform(-2200.0, 2200.0)
    x, y = math.cos(ang) * radio, math.sin(ang) * radio
    yaw = math.degrees(ang) + 90.0 + random.uniform(-14.0, 14.0)   # de perfil, como en procesion
    esc = 3.0 + f * 6.5                     # mas grandes cuanto mas lejos, para que se lean igual
    t = unreal.Transform(V(x, y, alt), unreal.Rotator(0.0, 0.0, yaw), V(esc, esc, esc))
    h.add_instance(t)
print("instancias:", h.get_instance_count())
act.modify()
print("guardado:", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
