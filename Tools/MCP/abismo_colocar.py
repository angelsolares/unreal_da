# -*- coding: utf-8 -*-
import json

# Coloca el unico `BP_DA_Abismo` que hace falta. Lanzar tras `abismo_crear.py`.
#
# **La posicion da igual**: el actor no tiene volumen, compara la Z del jugador
# contra `CotaMortal` en Tick. Por eso va uno solo y en el origen, donde se
# encuentra. Poner mas de uno solo multiplicaria el Tick.

MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
CLASE = "/Game/DarkAngels/Blueprints/Level/BP_DA_Abismo.BP_DA_Abismo_C"
ETIQUETA = "Abismo_Malkuth"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


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

    xf = {"location": {"x": 0.0, "y": 0.0, "z": 0.0},
          "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
          "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
    a = busca(ETIQUETA)
    if a is None:
        a = sc("add_to_scene_from_class", {"actor_type": {"refPath": CLASE},
                                           "name": ETIQUETA, "xform": xf,
                                           "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": a, "label": ETIQUETA})
        out["actor"] = "creado"
    else:
        out["actor"] = "ya estaba"

    ast("save_assets", {"asset_paths": [MAESTRO]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": MAESTRO})

    # --- releer del actor, no del script ---
    a = busca(ETIQUETA)
    out["leido"] = json.loads(ot("get_properties", {
        "instance": a, "properties": ["CotaMortal", "Texto", "Flag", "Caido"]}))
    # Y la caja gigante que se puso a mano: sigue ahi?
    caja = busca("TR_DeathVoid_Malkuth")
    out["triggerbox_de_angel"] = "sigue en el nivel" if caja else "ya no esta"
    return out
