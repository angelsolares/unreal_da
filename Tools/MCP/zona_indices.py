import json

# Ordena el `ObjectiveIndex` de los triggers de zona.
#
# EL PROBLEMA: `BP_DA_HUD.SetObjective` solo avanza **si el indice que recibe es
# mayor que el actual** —es una progresion monotona a proposito, para que volver
# atras no te cambie el objetivo—. Pero los indices estaban a medio poner: el
# Puente tenia 1, igual que el Jardin, y los siete triggers que viven dentro de
# Level Instances tenian todos 0. Resultado: esas zonas disparaban pero **no
# actualizaban el objetivo nunca**. El subrayado del panel si les funcionaba,
# porque eso no mira el indice.
#
# LOS RAMALES SE QUEDAN EN 0 A PROPOSITO. El Mirador y el Gazebo son opcionales,
# y como la progresion es monotona, si les diera un numero de la serie te
# cambiarian el objetivo principal al desviarte y no habria forma de recuperarlo
# al volver. Con 0 nunca pisan el objetivo. El precio es que su texto propio no
# llega a verse: si se quiere que se vea, hay que quitarle la guarda de
# monotonia a `SetObjective`, no cambiar estos numeros.

TRIGGER = "/Game/DarkAngels/Blueprints/Level/BP_DA_ZoneTrigger.BP_DA_ZoneTrigger"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"

# La ruta principal, en orden de recorrido. Los que estan sueltos en el Master
# se escriben directos; el resto necesita entrar a editar su Level Instance.
SUELTOS = {"Jardin Geometrico": 1, "El Claro": 2, "Santuario de Malkuth": 3,
           "Anfiteatro": 5}

# etiqueta del trigger -> (trozo del nombre de su LI, indice)
EN_LI = {
    "Puente_Trigger_Entrada": ("Puente", 4),
    "Elevador_Trigger": ("Elevador", 6),
    "GC1_Trigger": ("GabrielC1", 7),
    "GC3_Trigger": ("GabrielC3", 8),
    "Yesod_Trigger": ("Yesod", 9),
    # Ramales: fuera de la serie.
    "Mirador_Trigger": ("Mirador", 0),
    "Gazebo_Trigger": ("Gazebo", 0),
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
    out = {"puestos": []}

    for a in sc("find_actors", {"name": "", "tag": "", "collision_channels": []}):
        if "ZoneTrigger" not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        if "_LevelInstance_" in a["refPath"]:
            continue
        z = str(json.loads(ot("get_properties", {"instance": a,
                                                 "properties": ["ZoneName"]}))["ZoneName"])
        if z in SUELTOS:
            ot("set_properties", {"instance": a,
                                  "values": json.dumps({"ObjectiveIndex": SUELTOS[z]})})
            out["puestos"].append([z, SUELTOS[z]])

    for etiqueta in EN_LI:
        trozo, idx = EN_LI[etiqueta]
        li = None
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if "UEDPIE" in a["refPath"]:
                continue
            if trozo in at("get_label", {"actor": a}):
                li = a
                break
        if li is None:
            out["puestos"].append([etiqueta, "sin LI"])
            continue
        sc("edit_level_instance", {"level_instance": li})
        t = None
        for a in sc("find_actors", {"name": etiqueta, "tag": "", "collision_channels": []}):
            if "UEDPIE" not in a["refPath"] and at("get_label", {"actor": a}) == etiqueta:
                t = a
                break
        if t is None:
            sc("commit_level_instance", {"level_instance": li, "discard": True})
            out["puestos"].append([etiqueta, "no esta en su LI"])
            continue
        ot("set_properties", {"instance": t, "values": json.dumps({"ObjectiveIndex": idx})})
        leido = json.loads(ot("get_properties", {"instance": t, "properties":
                                                 ["ZoneName", "ObjectiveIndex"]}))
        sc("commit_level_instance", {"level_instance": li, "discard": False})
        out["puestos"].append([str(leido["ZoneName"]), leido["ObjectiveIndex"]])

    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [MAESTRO]})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": MAESTRO})
    return out
