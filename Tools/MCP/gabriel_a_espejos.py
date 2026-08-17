import json

# Mueve al jefe a la sala de los espejos (Camara II), donde esta el angel de
# primitivas `SM_Gabriel`. El placeholder se esconde, no se borra.
# El de la Camara III se quita: es un traslado, no una copia.

SUB = "L_DA_Malkuth_Gabriel_Sub"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gabriel_Sub"
C3 = "/Game/DarkAngels/Maps/L_DA_Malkuth_GabrielC3_Sub"
JEFE = "/Game/DarkAngels/Blueprints/Bosses/BP_DA_GiantBoss.BP_DA_GiantBoss_C"
ETIQUETA = "GC2_Gabriel"


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]
def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)
def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)
def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def dentro(nombre, sub):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if sub not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def li_de(trozo):
    for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
        if "UEDPIE" not in a["refPath"] and trozo in at("get_label", {"actor": a}):
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {}

    # --- quitar el de la Camara III ---
    li3 = li_de("GabrielC3")
    if li3 is not None:
        sc("edit_level_instance", {"level_instance": li3})
        v = dentro("GC3_GabrielGiant", C3)
        if v is not None:
            sc("remove_from_scene", {"actor": v})
            out["quitado_de_C3"] = True
        sc("commit_level_instance", {"level_instance": li3, "discard": False})

    # --- ponerlo en la sala de los espejos ---
    li2 = li_de("GabrielC2")
    if li2 is None:
        return {"error": "no encuentro LI_11_GabrielC2", "hecho": out}
    sc("edit_level_instance", {"level_instance": li2})
    ph = dentro("SM_Gabriel", SUB)
    if ph is None:
        sc("commit_level_instance", {"level_instance": li2, "discard": True})
        return {"error": "no esta SM_Gabriel", "hecho": out}
    t = at("get_actor_transform", {"actor": ph})
    b = at("get_actor_bounds", {"actor": ph})
    xform = {"location": {"x": t["location"]["x"], "y": t["location"]["y"],
                          "z": b["min"]["z"] + 270.0},
             "rotation": {"pitch": 0.0, "yaw": t["rotation"]["yaw"], "roll": 0.0},
             "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
    jefe = dentro(ETIQUETA, SUB)
    if jefe is None:
        jefe = sc("add_to_scene_from_class", {
            "actor_type": {"refPath": JEFE}, "name": ETIQUETA, "xform": xform,
            "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": jefe, "label": ETIQUETA})
    at("set_actor_transform", {"actor": jefe, "worldspace": True, "xform": xform})
    ot("set_properties", {"instance": ph, "values": json.dumps({"bHidden": True})})

    bj = at("get_actor_bounds", {"actor": jefe})
    out["placeholder"] = {"pos": [round(t["location"][k]) for k in ("x","y","z")],
                          "yaw": round(t["rotation"]["yaw"], 1),
                          "alto": round(b["max"]["z"] - b["min"]["z"]),
                          "suelo": round(b["min"]["z"])}
    out["jefe"] = {"pos": [round(xform["location"][k]) for k in ("x","y","z")],
                   "alto": round(bj["max"]["z"] - bj["min"]["z"]),
                   "suelo": round(bj["min"]["z"])}
    sc("commit_level_instance", {"level_instance": li2, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": ASSET})
    return out
