import json

# Donde se puede pedir la guia y donde no, mas la limpieza de lo que quedo suelto.
#
# `PermiteGuia` es un bool por instancia de `BP_DA_ZoneTrigger`, a true por
# defecto. Se pone a false en las camaras de Gabriel, que es donde la guia
# estorbaria.
#
# LOS TRIGGERS VIVEN DENTRO DE LEVEL INSTANCES, asi que para escribirles hay que
# entrar en modo edicion de su LI y commitear al salir. Se hace uno por uno y
# solo con los que hay que apagar: los demas se quedan con el valor por defecto
# de la clase, que ya es el bueno.

TRIGGER = "/Game/DarkAngels/Blueprints/Level/BP_DA_ZoneTrigger.BP_DA_ZoneTrigger"
HUD = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"

# etiqueta del trigger -> trozo del nombre de su Level Instance
APAGAR = {"GC1_Trigger": "GabrielC1", "GC3_Trigger": "GabrielC3"}


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


def buscar(etiqueta):
    for a in sc("find_actors", {"name": etiqueta, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == etiqueta:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {"apagados": [], "huerfana": None}

    # --- 1. fuera la funcion que quedo sin usar en el HUD ---
    # `Guia_Tick` se monto ahi antes de descubrir que no hay forma de crear el
    # nodo que la llame. Ahora la tecla vive en `BP_DA_Ruta` y esta sobra.
    hud = {"refPath": HUD}
    if "Guia_Tick" in str(bt("list_functions", {"blueprint": hud})):
        bt("remove_function_graph", {"blueprint": hud, "graph_name": "Guia_Tick"})
        bt("compile_blueprint", {"blueprint": hud})
        call("editor_toolset.toolsets.asset.AssetTools.save_assets",
             {"asset_paths": [HUD.split(".")[0]]})
        out["huerfana"] = "borrada"
    else:
        out["huerfana"] = "ya no estaba"

    # --- 2. apagar la guia en las camaras de Gabriel ---
    for etiqueta in APAGAR:
        li = None
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if "UEDPIE" in a["refPath"]:
                continue
            if APAGAR[etiqueta] in at("get_label", {"actor": a}):
                li = a
                break
        if li is None:
            out["apagados"].append({etiqueta: "no encuentro su Level Instance"})
            continue
        sc("edit_level_instance", {"level_instance": li})
        t = buscar(etiqueta)
        if t is None:
            sc("commit_level_instance", {"level_instance": li, "discard": True})
            out["apagados"].append({etiqueta: "no esta dentro del LI"})
            continue
        ot("set_properties", {"instance": t, "values": json.dumps({"PermiteGuia": False})})
        leido = json.loads(ot("get_properties", {"instance": t,
                                                 "properties": ["ZoneName", "PermiteGuia"]}))
        sc("commit_level_instance", {"level_instance": li, "discard": False})
        out["apagados"].append({etiqueta: leido})

    return out
