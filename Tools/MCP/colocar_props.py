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

ETIQUETA = "LI_05_RuinasGazebo"
SUBNIVEL = "L_DA_Malkuth_Gazebo_Sub"

CAMBIOS = [
    {
        "quitar": "Gazebo_Rotonda",
        "poner": "/Game/DarkAngels/Environment/Props/SK_DA_Rotonda_Gazebo",
        "nombre": "Gazebo_Rotonda",
        # Placeholder: 800 x 800 x 220 con base en 147. Malla: 0,978 de ancho.
        "loc": {"x": 64000.0, "y": 16650.0, "z": 147.0},
        "rot": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
        "escala": 818.0,
    },
    {
        "quitar": "Gazebo_Tableta",
        "poner": "/Game/DarkAngels/Environment/Props/SK_DA_Tableta_Gazebo",
        "nombre": "Gazebo_Tableta",
        # Placeholder: 120 x 42 x 220 con base en 202. Malla: 0,979 de alto.
        "loc": {"x": 64000.0, "y": 16920.0, "z": 202.0},
        "rot": {"pitch": 0.0, "yaw": 180.0, "roll": 0.0},
        "escala": 225.0,
    },
    {
        "quitar": "Gazebo_Fragmento",
        "poner": "/Game/DarkAngels/Environment/Props/SK_DA_Fragmento",
        "nombre": "Gazebo_Fragmento",
        # Placeholder: 64 x 63 x 110 con base en 282, que es la cara del
        # Gazebo_Pedestal (202 + 80). Malla: 0,975 de alto.
        "loc": {"x": 64000.0, "y": 16480.0, "z": 282.0},
        "rot": {"pitch": 0.0, "yaw": 30.0, "roll": 0.0},
        "escala": 113.0,
    },
]


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

    return {"li": ETIQUETA, "cambios": hecho}
