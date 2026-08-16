import json

# Sustituye placeholders por las mallas reales de Tripo dentro de un Level
# Instance. Un solo ciclo edit/commit; el commit va aparte, con li_commit.py.
#
# Las mallas de Tripo traen el **pivote en la base** y miden ~1 uu, asi que la
# escala es directamente el tamano en centimetros y la z de destino es la cota
# donde se apoyaban los placeholders.
#
# Aqui la escala SI se calca del placeholder, porque el Gazebo ya estaba
# compuesto: la rotonda encaja con la plataforma, la tableta con su luz y el
# Fragmento con la cara del pedestal. Se iguala la dimension que manda en cada
# pieza (ancho en la rotonda, alto en tableta y Fragmento).

ETIQUETA = "LI_07_PuenteAscendente"
SUBNIVEL = "L_DA_Malkuth_Puente_Sub"

# La puerta del fondo del puente, la que Angel marco en rojo sobre la lamina 07.
#
# Lo que habia eran dos pilares sueltos, `Puente_Portal_L` y `_R`, de 216 x 216 x
# 1104, a x=15500 y x=16500 con base en z=2866. O sea, 1216 uu de vano exterior.
# Se sustituyen los dos por la puerta entera, centrada en x=16000.
#
# `Puente_Luz_Portal_L` y `_R` NO se tocan: siguen enmarcando el vano.
#
# La malla mide 0,98 x 0,438 x 0,558 con el pivote en la base. Igualando el ancho
# de los dos pilares: 1216 / 0,98 -> escala 1241, que deja la puerta en
# 1216 x 543 x 692 cm. Menos alta que los pilares (1104) porque aquello eran
# columnas y esto es un portico entero.

# La fuente del Santuario, la que sale en la lamina delante de Cassiel.
#
# Lo que habia era un kitbash de cuatro piezas `GardenFountain*` de Megascans
# apiladas —Base 0-56, Pie 56-146, Cuenco 146-187 y Aguja 187-290—, 275 uu de
# ancho en total. Se sustituyen las cuatro por la malla unica.
#
# `Luz_Altar` NO se toca: sigue iluminando el mismo punto.
#
# La malla mide 0,712 x 0,979 x 0,551 con el pivote en la base. Se iguala el
# ancho del conjunto anterior: 275 / 0,979 -> escala 281, que deja la fuente en
# 200 x 275 x 155 cm. Es mas baja que el apilado porque aquella tenia encima una
# aguja de 100 uu; esta es una fuente de verdad, a la altura del pecho.
CAMBIOS = [
    {
        "quitar": "Puente_Portal_L",
        "poner": "/Game/DarkAngels/Environment/Props/SK_DA_Puerta_Templo",
        "nombre": "Puente_Puerta_Templo",
        "loc": {"x": 16000.0, "y": 66700.0, "z": 2866.0},
        "rot": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
        "escala": 1241.0,
    },
]
# El segundo pilar se borra sin sustituto: la puerta cubre los dos.
SOLO_BORRAR = ["Puente_Portal_R"]


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

    sueltos = []
    for nom in globals().get("SOLO_BORRAR", []):
        for a in find(nom):
            if SUBNIVEL in a["refPath"] and label(a) == nom:
                if call("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": a}):
                    sueltos.append(nom)

    hecho = []
    for c in CAMBIOS:
        borrados = 0
        for a in find(c["quitar"]):
            if SUBNIVEL not in a["refPath"] or label(a) != c["quitar"]:
                continue
            if call("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": a}):
                borrados += 1

        esc = {"x": c["escala"], "y": c["escala"], "z": c["escala"]}
        nuevo = call("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_asset", {
            "asset_path": c["poner"], "name": c["nombre"],
            "xform": {"location": c["loc"], "rotation": c["rot"], "scale": esc}})
        # set_actor_transform resetea escala y rotacion si no se le pasan las tres.
        call("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
            "actor": nuevo,
            "xform": {"location": c["loc"], "rotation": c["rot"], "scale": esc},
            "worldspace": True})
        call("editor_toolset.toolsets.actor.ActorTools.set_label",
             {"actor": nuevo, "label": c["nombre"]})

        b = call("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": nuevo})
        hecho.append({
            "placeholder_borrados": borrados,
            "nuevo": c["nombre"],
            "dentro_del_sub": SUBNIVEL in nuevo["refPath"],
            "tamano_uu": [round(b["max"]["x"] - b["min"]["x"]),
                           round(b["max"]["y"] - b["min"]["y"]),
                           round(b["max"]["z"] - b["min"]["z"])],
            "base_z": round(b["min"]["z"]),
            "cima_z": round(b["max"]["z"]),
        })

    return {"li": ETIQUETA, "cambios": hecho, "borrados_sin_sustituto": sueltos}
