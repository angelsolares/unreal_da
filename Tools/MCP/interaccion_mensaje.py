import json

# Implementa `GetInteractionMessage` de `I_IsInteractable`: devuelve la variable
# `Verbo` del actor, que es lo que acaba escrito en `WB_InteractionMessage`.
#
# Esta si va por DSL, y sin pelea: solo lee una variable propia y devuelve. El
# DSL falla con los pines `Target`, y aqui no hay ninguno.
#
# `Interact` no se toca: no devuelve nada, asi que Unreal la implementa como
# EVENTO en el EventGraph, no como funcion, y de momento no tiene que hacer nada.
#
# De paso saca la ficha de los props que hay que convertir: malla, transform y
# en que Level Instance vive cada uno.

BP = "/Game/DarkAngels/Blueprints/Interaccion/BP_DA_Interactuable.BP_DA_Interactuable"

PROPS = ["Mirador_Llave", "Santuario_Cofre", "NPC_Sariel", "NPC_Cassiel"]


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t, json.dumps(a))["returnValue"]


def at(t, a):
    return execute_tool("editor_toolset.toolsets.actor.ActorTools." + t, json.dumps(a))["returnValue"]


def ot(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t, json.dumps(a))["returnValue"]


def st(t, a):
    return execute_tool("editor_toolset.toolsets.asset.AssetTools." + t, json.dumps(a))["returnValue"]


def find(nombre):
    return execute_tool("editor_toolset.toolsets.scene.SceneTools.find_actors",
                        json.dumps({"name": nombre, "tag": "", "collision_channels": []}))["returnValue"]


def run():
    out = {}
    bp = {"refPath": BP}

    grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": bp})]
    out["grafos"] = grafos

    if "GetInteractionMessage" in grafos:
        bt("write_graph_dsl", {"graph": {"refPath": BP + ":GetInteractionMessage"},
                               "code": "(fn GetInteractionMessage ()\n"
                                       "  (return (Variables|Default|GetVerbo)))"})
        bt("compile_blueprint", {"blueprint": bp})
        out["mensaje"] = bt("read_graph_dsl", {"graph": {"refPath": BP + ":GetInteractionMessage"}})
    else:
        out["mensaje"] = "no existe el grafo GetInteractionMessage"

    st("save_assets", {"asset_paths": [BP.split(".")[0]]})

    # --- ficha de los props ---
    fichas = []
    for nombre in PROPS:
        for a in find(nombre):
            if at("get_label", {"actor": a}) != nombre or "/Temp/" in a["refPath"]:
                continue
            t = at("get_actor_transform", {"actor": a})
            f = {"actor": nombre,
                 "mapa": a["refPath"].split(":")[0].split("/")[-1],
                 "clase": a["refPath"].split(".")[-1],
                 "loc": [round(t["location"][k], 1) for k in ("x", "y", "z")],
                 "rot": [round(t["rotation"][k], 1) for k in ("pitch", "yaw", "roll")],
                 "esc": [round(t["scale"][k], 3) for k in ("x", "y", "z")]}
            for c in at("get_components", {"actor": a}):
                if "SkeletalMeshComponent" not in c["refPath"]:
                    continue
                p = json.loads(ot("get_properties", {"instance": c,
                                                     "properties": ["SkeletalMeshAsset", "AnimationMode", "AnimationData"]}))
                for k in p:
                    f[k] = str(p[k])
            fichas.append(f)
            break
    out["props"] = fichas
    return out
