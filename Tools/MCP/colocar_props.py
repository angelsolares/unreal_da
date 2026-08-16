import json

# Sustituye placeholders por las mallas reales de Tripo dentro de un Level
# Instance. Un solo ciclo edit/commit; el commit va aparte, con li_commit.py.
#
# Las mallas de Tripo traen el **pivote en la base** y miden ~1 uu, asi que la
# escala es directamente el tamano en centimetros y la z de destino es la cota
# donde se apoyaba el placeholder.
#
# Se calca el transform del placeholder y se iguala la dimension que manda en
# cada pieza (el ancho en las que son mas anchas que altas, el alto en el resto).
# Editar el bloque de constantes y lanzar.

ETIQUETA = "LI_07_PuenteAscendente"
SUBNIVEL = "L_DA_Malkuth_Puente_Sub"

# El angel gigante del fondo del puente. Era `SM_SM_DA_AngelSilueta`, un recorte
# plano de 1350 uu de grosor estirado a 15355 de ancho, y en las notas del 01/08
# ya salia como "lee como cruz blanca".
#
# Angel decidio reutilizar el coloso del Jardin: es el mismo angel de la lamina y
# el asset ya esta importado, asi que no suma ni un byte al proyecto.
#
# El placeholder medía 8190 de alto con base en z=2621. La malla del coloso mide
# 0,735 x 0,699 x 0,979 (deducido del actor del Jardin: 14072 x 13387 x 18750 a
# escala 19143). Igualando el alto: 8190 / 0,979 -> escala 8365.
CAMBIOS = [
    {
        "quitar": "Puente_Angel_Gigante",
        "poner": "/Game/DarkAngels/Characters/Colosos/SK_DA_Coloso_Angel_V2",
        "nombre": "Puente_Angel_Gigante",
        "loc": {"x": 16000.0, "y": 76000.0, "z": 2621.0},
        "rot": {"pitch": 0.0, "yaw": -90.0, "roll": 0.0},
        "escala": 8365.0,
    },
]

# Actores que se borran sin poner nada en su lugar.
SOLO_BORRAR = []


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
    for nom in SOLO_BORRAR:
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
