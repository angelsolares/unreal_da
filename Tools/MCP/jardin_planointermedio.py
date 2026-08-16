import json

# Plano intermedio del Jardin: apaga unos montes y enciende otros, en un solo
# ciclo de edicion.
#
# Primer intento: seis montes de cima 0,8-1,7 grados. Medido contra la captura
# anterior, movieron 2 puntos de luma y el 3% de los pixeles de la franja del
# horizonte: no se ven, se los come la linea de arboles.
#
# Segundo intento, el que queda: seis de 4,7-6,8 grados, a 847-1061 m. Siguen
# muy por debajo de las cumbres pintadas (20-30 grados), asi que hacen de
# silueta intermedia sin volver a cerrar el horizonte. Se evita el azimut 0-10,
# que es donde esta el coloso.

ETIQUETA = "LI_01_JardinGeometrico"
SUBNIVEL = "L_DA_Malkuth_Jardin_Sub"
APAGAR = ["Monte_Medio_52", "Monte_Medio_59", "Monte_Medio_42",
          "Monte_Medio_58", "Monte_Medio_61", "Monte_Medio_56"]
ENCENDER = ["Monte_Medio_45", "Monte_Medio_40", "Monte_Medio_39",
            "Monte_Medio_63", "Monte_Medio_60", "Monte_Medio_43"]


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

    hecho = {}
    for a in find("Monte"):
        if SUBNIVEL not in a["refPath"]:
            continue
        lab = label(a)
        if lab in APAGAR:
            quiero = False
        elif lab in ENCENDER:
            quiero = True
        else:
            continue
        for c in call("editor_toolset.toolsets.actor.ActorTools.get_components", {"actor": a}):
            if "MeshComponent" not in c["refPath"]:
                continue
            call("editor_toolset.toolsets.object.ObjectTools.set_properties",
                 {"instance": c, "values": json.dumps({"bVisible": quiero})})
            v = json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                                {"instance": c, "properties": ["bVisible"]}))
            hecho[lab] = v["bVisible"]

    mal = [k for k, v in hecho.items() if (k in ENCENDER) != bool(v)]
    return {"estado": hecho, "discrepancias": mal}
