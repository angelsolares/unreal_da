import json

# Mueve el conjunto del Fragmento —el propio Fragmento, su pedestal y su luz—
# dejando la tableta donde esta.
#
# El sitio NO se elige a ojo. Se captura la misma pose con y sin la rotonda y se
# restan las dos imagenes: los pixeles que cambian son exactamente la rotonda,
# asi que sale la ocupacion de las columnas columna a columna a la altura del
# Fragmento. Las trazas no sirven aqui porque un SkeletalMesh no colisiona.
#
# Medido desde la pose de aproximacion (64000, 15700, 470) yaw 90, recorriendo
# el arco de radio 170 alrededor del centro de la rotonda:
#
#   180 grados (63830, 16650) -> ocupacion 0,85  <- donde estaba: tapado
#   150 grados (63853, 16735) -> ocupacion 0,19
#   135 grados (63880, 16770) -> ocupacion 0,01  <- elegido
#   120 grados (63915, 16797) -> ocupacion 0,00, pero pisa la tableta en pantalla
#
# A 135 grados queda despejado de columnas **y** justo al lado de la tableta sin
# solaparla: la tableta ocupa de x=550 a 618 en pantalla y el Fragmento de 627 a
# 671. Y como a yaw 90 el lado -X es la derecha, cae a la derecha de la tableta,
# como en la lamina.

SUBNIVEL = "L_DA_Malkuth_Gazebo_Sub"
DESTINO_XY = (63880.0, 16770.0)
PIEZAS = ["Gazebo_Pedestal", "Gazebo_Fragmento", "Gazebo_Luz_Fragmento"]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def run():
    hecho = []
    for nom in PIEZAS:
        for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                      {"name": nom, "tag": "", "collision_channels": []}):
            if SUBNIVEL not in a["refPath"] or label(a) != nom:
                continue
            t = call("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": a})
            # set_actor_transform resetea escala y rotacion si no se le pasan las tres:
            # se reutilizan las que ya tenia y solo se cambia el XY.
            nueva = {"location": {"x": DESTINO_XY[0], "y": DESTINO_XY[1], "z": t["location"]["z"]},
                      "rotation": t["rotation"], "scale": t["scale"]}
            call("editor_toolset.toolsets.actor.ActorTools.set_actor_transform",
                 {"actor": a, "xform": nueva, "worldspace": True})
            leido = call("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": a})
            hecho.append([nom, round(leido["location"]["x"]), round(leido["location"]["y"]),
                          round(leido["location"]["z"]), round(leido["scale"]["x"], 2)])
    return {"movidos": hecho}
