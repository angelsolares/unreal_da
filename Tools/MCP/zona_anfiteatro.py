import json

# El trigger de zona que le faltaba al Anfiteatro.
#
# No estaba por ningun conflicto: al reconstruirse el nivel se recrearon diez
# triggers y este se quedo fuera. Sin el, al entrar caminando no cambiaba ni el
# objetivo ni el subrayado del panel, y su fila (la 7) no se encendia nunca.
#
# Va SUELTO EN EL MASTER, como los del Jardin, El Claro y el Santuario, y no
# dentro de `LI_08_Anfiteatro`: asi se le pueden tocar las variables sin entrar
# a editar la Level Instance cada vez.
#
# El tamanio se copia del trigger del Jardin: caja de (1500,1500,400) en el
# blueprint y escala 8/8/3 en el actor, o sea 12.000 x 12.000 x 1.200 de
# semiextension. NO se toca `BoxExtent` por instancia: el setter de structs solo
# aplica la X y deja Y/Z en su valor por defecto —fue lo que en su dia dejo la
# caja del Jardin en Y=1500 y el trigger no disparaba nunca—.

CLASE = "/Game/DarkAngels/Blueprints/Level/BP_DA_ZoneTrigger.BP_DA_ZoneTrigger_C"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
ETIQUETA = "Zone_Anfiteatro"

SITIO = {"x": -74000.0, "y": 42000.0, "z": 100.0}
ESCALA = {"x": 8.0, "y": 8.0, "z": 3.0}

VALORES = {
    "ZoneName": "Anfiteatro",
    "ObjectiveText": "Cruza el Anfiteatro hacia el Elevador del Trono",
    # La progresion va Jardin 1, Claro 2, Santuario 3; el Anfiteatro cae detras
    # del Puente. `SetObjective` solo avanza si el indice sube, asi que este
    # numero es lo que decide que no retroceda al volver atras.
    "ObjectiveIndex": 5,
    "IndicePanel": 7,      # la fila del panel SALTO DE ZONA
    "PermiteGuia": True,
}


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    actor = None
    for a in sc("find_actors", {"name": ETIQUETA, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == ETIQUETA:
            actor = a
            break
    xform = {"location": SITIO, "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
             "scale": ESCALA}
    if actor is None:
        actor = sc("add_to_scene_from_class", {
            "actor_type": {"refPath": CLASE}, "name": ETIQUETA, "xform": xform,
            "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": actor, "label": ETIQUETA})
        creado = "creado"
    else:
        creado = "ya estaba"
    # `set_actor_transform` resetea escala y rotacion si no se le pasan las tres.
    at("set_actor_transform", {"actor": actor, "worldspace": True, "xform": xform})
    sc("set_actor_folder", {"actor": actor, "folder_path": "Guidance"})

    for k in VALORES:
        ot("set_properties", {"instance": actor, "values": json.dumps({k: VALORES[k]})})

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [MAESTRO]})
    t = at("get_actor_transform", {"actor": actor})
    return {"estado": creado,
            "pos": [round(t["location"][k]) for k in ("x", "y", "z")],
            "esc": [t["scale"][k] for k in ("x", "y", "z")],
            "valores": json.loads(ot("get_properties", {"instance": actor,
                                                        "properties": list(VALORES)})),
            "sucio": call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                          {"asset_path": MAESTRO})}
