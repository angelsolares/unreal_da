import json

# Baja a Sariel de su pedestal, quita el pedestal y lo pone junto a la llave.
#
# Lo que habia: `Mirador_EstatuaBase` (200 x 200 x 150, de z=318 a 468) con
# `NPC_Sariel` encima, a 468. Por eso parecia mucho mas alto que el jugador:
# eran los 150 uu del pedestal, no la escala. Medido, Sariel son 184 y el
# jugador 170.
#
# La silueta vieja `Mirador_Estatua_Sariel` esta en el mismo punto pero **ya
# estaba oculta**, asi que al quitar la base no queda nada flotando. No se toca.
#
# El suelo del mirador esta a z=318 en toda esa zona (comprobado con trazas en
# cinco puntos), asi que ahi va Sariel.

ETIQUETA = "LI_03_MiradorSariel"
SUBNIVEL = "L_DA_Malkuth_Mirador_Sub"

# La llave esta en (-16000, -23300) con la cara del plinto en 408. Sariel se
# pone al lado y un poco detras, de pie en la tarima, mirando por donde llega el
# jugador (yaw -90, que es hacia -Y).
SARIEL = {"x": -16150.0, "y": -23180.0, "z": 318.0}
# Su foco baja con el: quedaba a 620 sobre el pedestal.
LUZ = {"x": -16150.0, "y": -23120.0, "z": 560.0}
QUITAR = "Mirador_EstatuaBase"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def find(name):
    return call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": name, "tag": "", "collision_channels": []})


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def mover(nombre, destino):
    for a in find(nombre):
        if SUBNIVEL not in a["refPath"] or label(a) != nombre:
            continue
        t = call("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": a})
        # set_actor_transform resetea escala y rotacion si no se le pasan las tres.
        call("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
            "actor": a,
            "xform": {"location": destino, "rotation": t["rotation"], "scale": t["scale"]},
            "worldspace": True})
        b = call("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": a})
        return {"xyz": [round(destino["x"]), round(destino["y"]), round(destino["z"])],
                "base": round(b["min"]["z"]), "cima": round(b["max"]["z"])}
    return "no encontrado"


def run():
    li = None
    for a in find("LI_"):
        if label(a) == ETIQUETA:
            li = a
            break
    if li is None:
        return {"error": "no encontrado " + ETIQUETA}

    call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance", {"level_instance": li})

    borrados = 0
    for a in find(QUITAR):
        if SUBNIVEL in a["refPath"] and label(a) == QUITAR:
            if call("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": a}):
                borrados += 1

    return {"base_borrada": borrados,
            "sariel": mover("NPC_Sariel", SARIEL),
            "luz": mover("Mirador_Luz_Estatua", LUZ)}
