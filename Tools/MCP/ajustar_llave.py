import json

# La llave quedaba flotando 32 uu: la cara del plinto esta en z=408 y la base
# estaba puesta en 440. Sondeado con trazas alrededor: 408 en el centro, 338 en
# el escalon de ±60 y 318 en el suelo del mirador.
#
# El placeholder anterior tambien flotaba —su AABB empezaba en 439,8—, asi que
# esto viene heredado, no de la sustitucion.

ETIQUETA = "LI_03_MiradorSariel"
SUBNIVEL = "L_DA_Malkuth_Mirador_Sub"
LOC = {"x": -16000.0, "y": -23300.0, "z": 408.0}
ROT = {"pitch": 0.0, "yaw": 45.0, "roll": 0.0}
ESC = 71.0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def find(name):
    return call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": name, "tag": "", "collision_channels": []})


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def run():
    li = None
    for a in find("LI_"):
        if label(a) == ETIQUETA:
            li = a
            break
    if li is None:
        return {"error": "no encontrado " + ETIQUETA}

    call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance", {"level_instance": li})

    for a in find("Mirador_Llave"):
        if SUBNIVEL not in a["refPath"] or label(a) != "Mirador_Llave":
            continue
        # set_actor_transform resetea escala y rotacion si no se le pasan las tres.
        call("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
            "actor": a,
            "xform": {"location": LOC, "rotation": ROT,
                       "scale": {"x": ESC, "y": ESC, "z": ESC}},
            "worldspace": True})
        b = call("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": a})
        return {"base_z": round(b["min"]["z"], 1), "cima_z": round(b["max"]["z"], 1),
                "alto": round(b["max"]["z"] - b["min"]["z"], 1)}
    return {"error": "no encontrada la llave"}
