import json

# Donde se puede pedir la guia y donde no.
#
# `PermiteGuia` es un bool por instancia de `BP_DA_ZoneTrigger`, a true por
# defecto. Se pone a false en las zonas donde la guia estorbaria —la arena de
# Gabriel— y `Guia_Tick` lo consulta antes de soltar nada.
#
# NO SE TOCA EL GRAFO DEL TRIGGER. Solo se le anade la variable: quien decide es
# el HUD, que recorre los triggers y mira si hay alguno cerca que lo prohiba. El
# `FireZoneEntry` del trigger ya funciona y no merece la pena arriesgarlo por
# esto.

TRIGGER = "/Game/DarkAngels/Blueprints/Level/BP_DA_ZoneTrigger.BP_DA_ZoneTrigger"
RUTA = "/Game/DarkAngels/Blueprints/Level/BP_DA_Ruta.BP_DA_Ruta"

# Zonas donde la guia se apaga. Se busca por el `ZoneName` de cada trigger.
SIN_GUIA = ["Gabriel"]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {}

    # --- 1. la variable en el trigger ---
    bp = {"refPath": TRIGGER}
    if "PermiteGuia" not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": "PermiteGuia", "type_name": "bool"})
    bt("set_variable_instance_editable",
       {"blueprint": bp, "variable_name": "PermiteGuia", "instance_editable": True})
    bt("compile_blueprint", {"blueprint": bp})
    ot("set_properties", {"instance": bt("get_default_object", {"blueprint": bp}),
                          "values": json.dumps({"PermiteGuia": True})})
    bt("compile_blueprint", {"blueprint": bp})
    out["trigger_vars"] = bt("list_variables", {"blueprint": bp})

    # --- 2. apagarla donde toque ---
    #
    # LOS TRIGGERS QUE VIVEN DENTRO DE UN LEVEL INSTANCE SE SALTAN. Escribirles
    # exige entrar en modo edicion de su LI una por una, y ademas el valor por
    # defecto de la clase ya es `true`, que es lo que quieren todas menos las de
    # Gabriel. Esas se apagan aparte, con su pasada de edit/commit.
    out["zonas"] = []
    out["en_level_instance"] = []
    for a in sc("find_actors", {"name": "", "tag": "", "collision_channels": []}):
        if "ZoneTrigger" not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        if "_LevelInstance_" in a["refPath"]:
            out["en_level_instance"].append(at("get_label", {"actor": a}))
            continue
        zona = json.loads(ot("get_properties", {"instance": a,
                                                "properties": ["ZoneName"]}))["ZoneName"]
        permite = not any(x.lower() in str(zona).lower() for x in SIN_GUIA)
        ot("set_properties", {"instance": a,
                              "values": json.dumps({"PermiteGuia": permite})})
        leido = json.loads(ot("get_properties", {"instance": a,
                                                 "properties": ["ZoneName", "PermiteGuia"]}))
        out["zonas"].append({str(leido["ZoneName"]): leido["PermiteGuia"]})

    # --- 3. fuera la variable de pruebas ---
    rbp = {"refPath": RUTA}
    if "Prueba" in str(bt("list_variables", {"blueprint": rbp})):
        bt("remove_variable", {"blueprint": rbp, "name": "Prueba"})
        bt("compile_blueprint", {"blueprint": rbp})
    out["ruta_vars"] = bt("list_variables", {"blueprint": rbp})

    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [TRIGGER.split(".")[0], RUTA.split(".")[0],
                          "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"]})
    return out
