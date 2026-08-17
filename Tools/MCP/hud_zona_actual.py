import json

# Que el subrayado del panel SALTO DE ZONA siga a la zona en la que estas, no
# solo a la tecla que pulsas.
#
# El panel se subraya con `ZonaActualDebug` del HUD, y hasta ahora solo lo tocaba
# el teclado numerico. El objetivo si se actualizaba al entrar caminando, porque
# lo hace `FireZoneEntry` del trigger de zona. Asi que se cuelga ahi mismo: ese
# grafo YA tiene el cast al HUD hecho para llamar a `SetObjective`, o sea que
# solo hay que anadir un nodo detras y reaprovechar la referencia.
#
# El indice es el del panel, que **no** coincide con el orden del recorrido: en
# `hud_teclas.py` el Yesod va en el 6 y el Anfiteatro en el 7.

TRIGGER = "/Game/DarkAngels/Blueprints/Level/BP_DA_ZoneTrigger.BP_DA_ZoneTrigger"
FN = {"refPath": TRIGGER + ":FireZoneEntry"}

# Los que estan sueltos en el Master: se escriben directos, por su ZoneName.
SUELTOS = {"Jardin Geometrico": 0, "El Claro": 2, "Santuario de Malkuth": 4}

# Los que viven dentro de un Level Instance: hay que entrar a editarla.
# etiqueta del trigger -> (trozo del nombre de su LI, indice del panel)
EN_LI = {
    "Mirador_Trigger": ("Mirador", 1),
    "Gazebo_Trigger": ("Gazebo", 3),
    "Puente_Trigger_Entrada": ("Puente", 5),
    "Yesod_Trigger": ("Yesod", 6),
    "Elevador_Trigger": ("Elevador", 8),
    "GC1_Trigger": ("GabrielC1", 9),
    "GC3_Trigger": ("GabrielC3", 9),
}


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def pin(n, direccion, nombre):
    clave = "input_pins" if direccion == "in" else "output_pins"
    for p in info(n)[clave]:
        if p["name"] == nombre:
            return p["pin_id"]
    raise RuntimeError("sin pin '%s' en %s" % (nombre, info(n)["type_id"]))


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    bp = {"refPath": TRIGGER}
    out = {}

    if "IndicePanel" not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": "IndicePanel", "type_name": "int"})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": "IndicePanel", "instance_editable": True})
        bt("compile_blueprint", {"blueprint": bp})

    # --- el nodo, detras del banner y colgando del cast que ya existe ---
    banner = casteo = ya = None
    for n in bt("find_nodes", {"graph": FN, "title": "", "entry_points_only": False}):
        t = str(info(n)["type_id"])
        if t.endswith("ShowZoneBanner"):
            banner = n
        if "CastToBP_DA_HUD" in t:
            casteo = n
        if "SetZonaActualDebug" in t:
            ya = n
    if banner is None or casteo is None:
        return {"error": "no encuentro ShowZoneBanner o el cast al HUD"}

    if ya is None:
        marca = bt("create_node", {"graph": FN,
                                   "type_id": "Class|BPDAHUD|SetZonaActualDebug",
                                   "pos": {"x": 900, "y": 300}})
        lee = bt("create_node", {"graph": FN,
                                 "type_id": "Variables|Default|GetIndicePanel",
                                 "pos": {"x": 700, "y": 460}})
        bt("connect_pins", {"output_pin": pin(banner, "out", "then"),
                            "input_pin": pin(marca, "in", "execute")})
        bt("connect_pins", {"output_pin": pin(casteo, "out", "AsBP DA HUD"),
                            "input_pin": pin(marca, "in", "self")})
        bt("connect_pins", {"output_pin": pin(lee, "out", "IndicePanel"),
                            "input_pin": pin(marca, "in", "ZonaActualDebug")})
        out["nodo"] = "creado"
    else:
        out["nodo"] = "ya estaba"

    bt("compile_blueprint", {"blueprint": bp})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [TRIGGER.split(".")[0]]})
    out["fn"] = bt("read_graph_dsl", {"graph": FN})

    # --- el indice de cada trigger ---
    out["puestos"] = []
    for a in sc("find_actors", {"name": "", "tag": "", "collision_channels": []}):
        if "ZoneTrigger" not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        if "_LevelInstance_" in a["refPath"]:
            continue
        z = str(json.loads(ot("get_properties", {"instance": a,
                                                 "properties": ["ZoneName"]}))["ZoneName"])
        if z in SUELTOS:
            ot("set_properties", {"instance": a,
                                  "values": json.dumps({"IndicePanel": SUELTOS[z]})})
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
        ot("set_properties", {"instance": t, "values": json.dumps({"IndicePanel": idx})})
        sc("commit_level_instance", {"level_instance": li, "discard": False})
        out["puestos"].append([etiqueta, idx])

    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": ["/Game/DarkAngels/Maps/L_DA_Malkuth_Master"]})
    return out
