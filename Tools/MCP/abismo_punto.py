# -*- coding: utf-8 -*-
import json

# Le apunta a `Abismo_Malkuth` su `PuntoRespawn`: el PlayerStart persistente del
# maestro. Y comprueba **en el pin** que los dos desbloqueos de mando de
# `RenacerAbismo` sean `false` de verdad: `read_graph_dsl` omite los valores por
# defecto, asi que releyendo el texto no se distingue "false" de "sin poner", y
# un desbloqueo que no desbloquea deja al jugador congelado para siempre.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
BPP = "/Game/DarkAngels/Blueprints/Level/BP_DA_Abismo.BP_DA_Abismo"
ACTOR = "Abismo_Malkuth"
PUNTO = "PS_Master_Jardin"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    if sc("get_current_level", {}) != MAESTRO:
        sc("load_level", {"level_path": MAESTRO})
    out = {}

    abismo, punto = busca(ACTOR), busca(PUNTO)
    if abismo is None or punto is None:
        return {"error": "falta " + (ACTOR if abismo is None else PUNTO)}
    t = at("get_actor_transform", {"actor": punto})
    out["punto"] = [round(t["location"][k]) for k in ("x", "y", "z")]

    ot("set_properties", {"instance": abismo, "values": json.dumps(
        {"PuntoRespawn": {"refPath": punto["refPath"]}})})
    ast("save_assets", {"asset_paths": [MAESTRO]})

    # --- releer del actor ---
    out["leido"] = json.loads(ot("get_properties", {"instance": abismo,
        "properties": ["PuntoRespawn", "CotaMortal", "Caido"]}))
    out["leido"]["PuntoRespawn"] = str(out["leido"]["PuntoRespawn"]).split(".")[-1]

    # --- y los pines de mando, uno a uno ---
    pines = []
    for n in bt("find_nodes", {"graph": {"refPath": BPP + ":RenacerAbismo"}, "title": ""}):
        i = bt("get_node_infos", {"nodes": [n]})[0]
        tid = str(i["type_id"])
        if not tid.startswith("Input|SetIgnore"):
            continue
        for p in i["input_pins"]:
            if p["name"].startswith("bNew"):
                pines.append([tid.split("|")[-1], p["name"], str(p["value"])])
    out["pines_desbloqueo"] = pines
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": MAESTRO})
    return out
