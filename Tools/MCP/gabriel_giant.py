import json

# Pone al Giant en el sitio del Gabriel de utileria.
#
# El placeholder es `GC3_Gabriel`, un StaticMeshActor de la camara III, con su
# `GC3_Lanza` al lado. Se **esconden**, no se borran: asi queda la referencia de
# tamanio y sitio en el editor y se puede volver atras.
#
# El jefe es `BP_DA_GiantBoss`, nuestro, hijo de `BP_Giant` del pack. Ya trae
# implementadas `I_CanBeAttacked` e `I_IsTargetable` de DCS —eso hubo que
# anadirlo a mano en su dia, el MCP no puede poner interfaces— asi que el
# jugador puede pegarle y el le puede pegar a el.

SUB = "L_DA_Malkuth_GabrielC3_Sub"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_GabrielC3_Sub"
JEFE = "/Game/DarkAngels/Blueprints/Bosses/BP_DA_GiantBoss.BP_DA_GiantBoss_C"
ETIQUETA = "GC3_GabrielGiant"
ESCONDER = ["GC3_Gabriel", "GC3_Lanza"]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def en_la_zona(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if SUB not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    li = None
    for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        if "GabrielC3" in at("get_label", {"actor": a}):
            li = a
            break
    if li is None:
        return {"error": "no encuentro LI_12_GabrielC3"}
    sc("edit_level_instance", {"level_instance": li})

    out = {}
    viejo = en_la_zona("GC3_Gabriel")
    if viejo is None:
        sc("commit_level_instance", {"level_instance": li, "discard": True})
        return {"error": "no esta GC3_Gabriel"}
    t = at("get_actor_transform", {"actor": viejo})
    b = at("get_actor_bounds", {"actor": viejo})
    out["placeholder"] = {
        "pos": [round(t["location"][k]) for k in ("x", "y", "z")],
        "yaw": round(t["rotation"]["yaw"], 1),
        "alto": round(b["max"]["z"] - b["min"]["z"]),
        "suelo": round(b["min"]["z"]),
    }

    # El jefe va donde apoyaba el placeholder, mirando igual. `BP_Giant` deriva
    # de `Character`, o sea que su origen esta en el centro de la capsula: se
    # sube media capsula para que no nazca enterrado. La altura buena se afina
    # despues con una captura.
    xform = {"location": {"x": t["location"]["x"], "y": t["location"]["y"],
                          "z": b["min"]["z"] + 270.0},
             "rotation": {"pitch": 0.0, "yaw": t["rotation"]["yaw"], "roll": 0.0},
             "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
    jefe = en_la_zona(ETIQUETA)
    if jefe is None:
        jefe = sc("add_to_scene_from_class", {
            "actor_type": {"refPath": JEFE}, "name": ETIQUETA, "xform": xform,
            "parent": None, "snap_to_ground": False})
        at("set_label", {"actor": jefe, "label": ETIQUETA})
        out["jefe"] = "creado"
    else:
        out["jefe"] = "ya estaba"
    at("set_actor_transform", {"actor": jefe, "worldspace": True, "xform": xform})

    # Fuera la utileria, sin borrarla.
    out["escondidos"] = []
    for n in ESCONDER:
        a = en_la_zona(n)
        if a is None:
            continue
        ot("set_properties", {"instance": a, "values": json.dumps({"bHidden": True})})
        out["escondidos"].append(n)

    bj = at("get_actor_bounds", {"actor": jefe})
    out["giant"] = {"pos": [round(v) for v in (xform["location"]["x"],
                                               xform["location"]["y"],
                                               xform["location"]["z"])],
                    "alto": round(bj["max"]["z"] - bj["min"]["z"]),
                    "suelo": round(bj["min"]["z"])}

    sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                        {"asset_path": ASSET})
    return out
