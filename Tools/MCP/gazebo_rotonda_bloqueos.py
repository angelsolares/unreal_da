import json


# Le pone cuerpo a las columnas de la rotonda con cajas invisibles, porque la
# malla no puede colisionar por si misma.
#
# POR QUE CAJAS Y NO LA MALLA: `Gazebo_Rotonda` es un `SkeletalMeshActor`, y un
# `SkeletalMeshComponent` sin PhysicsAsset **no tiene colision ninguna** por mucho
# que su perfil diga `BlockAll`. Se probo `bEnablePerPolyCollision = true` en la
# tableta y el Fragmento y se midio con trazas: **sigue sin parar nada**, ni
# despues de recargar el nivel. Y aunque funcionase, la rotonda tiene
# **1.014.955 vertices**: cocinar eso como trimesh es absurdo para un adorno.
#
# COMO SE ALINEAN: se colocan VISIBLES (`VISIBLE = True`), se saca una captura
# cenital por debajo del entablamento y otra de frente, se corrigen los angulos y
# el radio aqui, y cuando encajan se pasa `VISIBLE = False`. Un componente
# invisible **sigue colisionando**.
#
# EL MAPEO DE LA CAPTURA CENITAL, por si hay que volver a medir. Camara en
# (64000, 16650, 620) mirando abajo; el viewport coincide con la captura de
# 1195x928. Comprobado proyectando puntos conocidos con `WorldPosToScreenCoords`,
# que devuelve coordenadas **normalizadas de 0 a 1**, no pixeles:
#     worldY = 16650 + (px/1195 - 0.5) * 835.9
#     worldX = 64000 - (py/928  - 0.5) * 649.2
# OJO: eso vale para puntos **en el suelo**. Lo que esta mas alto sale empujado
# hacia afuera por la perspectiva, que es justo por lo que los fustes se abren en
# la captura y no se puede leer en ellos donde apoya la columna.

SUB = "L_DA_Malkuth_Gazebo_Sub"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Gazebo_Sub"
CUBO = "/Engine/BasicShapes/Cube.Cube"      # 100x100x100

CENTRO = (64000.0, 16650.0)
SUELO = 202.0

VISIBLE = False         # True para alinear por captura, False cuando encaje

# DONDE ESTAN LAS COLUMNAS: leidas de la captura CENITAL, no de la frontal.
#
# La frontal enganio dos veces. Primero porque de frente los fustes se ven en
# parejas y confundi la pareja de al lado con una fila mas lejana, y me salio
# radio 253. Y sobre todo porque **en la cenital los fustes se abren**: la camara
# esta a z=620 y el remate de la columna a ~600, o sea a 20 de la camara, y a esa
# distancia la perspectiva lo dispara fuera del encuadre. Lo unico que se puede
# leer es la BASA, que apoya en el suelo y por tanto cae donde el mapeo dice.
#
# Basas leidas en `bloq3.png` (1195x928) y pasadas a mundo con
#     worldY = 16650 + (px/1195 - 0.5) * 835.9
#     worldX = 64000 - (py/928  - 0.5) * 649.2
#   (540, 265) -> (64139, 16610)
#   (560, 660) -> (63863, 16624)
# o sea un eje a 138 de radio, no 253.
#
# NO ESTAN EN CRUZ: se probo con dos cajas mas en la perpendicular —en
# (64008, 16755) y (63994, 16479)— y en la captura caen sobre losa lisa. Ahi no
# hay nada.
#
# **LAS COLUMNAS VAN PAREADAS**, que es lo que despistaba desde el principio y
# se ve en la lamina del PDF. Cada una de las dos medidas tiene su gemela al
# lado. En la frontal, con la caja ya puesta encima de una de ellas para tener
# referencia, la gemela queda a 85 px, que a 660 de profundidad son 94 uu en X:
#   izquierda: 64139 -> gemela en 64233   (predice px 387, medida 375)
#   derecha:   63863 -> gemela en 63769   (predice px 802, medida 802)
# UNA CAJA POR COSTADO, no una por columna, y GORDA. Perseguir columna a columna
# no compensaba: con cuatro cajas de 60 seguia asomando piedra, y al medirla
# salia otra fila mas adelantada, sobre Y=16450, con las basas escondidas bajo
# los helechos. Todas caen dentro de la misma franja de X que sus parejas, asi
# que en vez de seguir afinando se le da a cada costado una caja de 154 x 260 que
# se las traga todas.
#
# Deja un pasillo central de 216 entre las dos —de x=63893 a x=64109— que es por
# donde se entra a la tableta. Como son invisibles, lo que importa es que no
# quede piedra sin tapar, no que el borde case al milimetro.
ALTO = 420.0
COLUMNAS = [
    {"centro": (64186.0, 16545.0), "tam": (154.0, 260.0)},   # costado este
    {"centro": (63816.0, 16545.0), "tam": (154.0, 260.0)},   # costado oeste
]
SOBRAN = ["Gazebo_Bloqueo_Col_2", "Gazebo_Bloqueo_Col_3"]

# Y la tableta, que si es un bloque y se aproxima con una caja exacta a su AABB.
# El Fragmento NO lleva: se midio y su huella (63838..63922 x 16733..16807) cae
# **entera dentro** de la del pedestal (63830..63930 x 16720..16820), que si
# bloquea. El jugador no puede llegar a el.
LOSAS = [
    {"nombre": "Gazebo_Bloqueo_Tableta",
     "centro": (64000.0, 16919.9, 312.1), "tam": (142.6, 82.1, 220.2)},
]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def en_la_zona(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if SUB not in a["refPath"] or "UEDPIE" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def poner_caja(nombre, centro, tam):
    """Un cubo del motor escalado a la caja que se quiere. Idempotente."""
    xform = {"location": {"x": centro[0], "y": centro[1], "z": centro[2]},
             "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
             "scale": {"x": tam[0] / 100.0, "y": tam[1] / 100.0, "z": tam[2] / 100.0}}
    a = en_la_zona(nombre)
    if a is None:
        a = sc("add_to_scene_from_asset", {"asset_path": CUBO, "name": nombre,
                                           "xform": xform, "parent": None,
                                           "snap_to_ground": False})
        at("set_label", {"actor": a, "label": nombre})
    # `set_actor_transform` resetea escala y rotacion si no se le pasan las tres.
    at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xform})
    for c in at("get_components", {"actor": a,
                                   "component_type": {"refPath": "/Script/Engine.MeshComponent"}}) or []:
        # Un campo por llamada: el setter de structs se deja los demas.
        ot("set_properties", {"instance": c, "values": json.dumps(
            {"bodyInstance": {"collisionProfileName": "BlockAll"}})})
        ot("set_properties", {"instance": c, "values": json.dumps({"bVisible": VISIBLE})})
        ot("set_properties", {"instance": c, "values": json.dumps({"castShadow": False})})
    return a


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    directo = sc("get_current_level", {}).startswith(ASSET)
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if "UEDPIE" in a["refPath"]:
                continue
            if "Gazebo" in at("get_label", {"actor": a}):
                li = a
                break
        if li is None:
            return {"error": "no encuentro el Level Instance del Gazebo"}
        sc("edit_level_instance", {"level_instance": li})

    out = {"visible": VISIBLE, "puestas": []}
    for i, col in enumerate(COLUMNAS):
        centro = (col["centro"][0], col["centro"][1], SUELO + ALTO / 2.0)
        nombre = "Gazebo_Bloqueo_Col_%d" % i
        poner_caja(nombre, centro, (col["tam"][0], col["tam"][1], ALTO))
        out["puestas"].append({nombre: [round(centro[0], 1), round(centro[1], 1),
                                        round(centro[2], 1)]})
    for l in LOSAS:
        poner_caja(l["nombre"], l["centro"], l["tam"])
        out["puestas"].append({l["nombre"]: list(l["centro"])})

    out["quitadas"] = []
    for nombre in SOBRAN:
        a = en_la_zona(nombre)
        if a is not None:
            sc("remove_from_scene", {"actor": a})
            out["quitadas"].append(nombre)

    if directo:
        ast("save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = ast("is_dirty", {"asset_path": ASSET})

    # Medir: ahora si tienen que dar todas.
    def traza(a, b):
        return sc("trace_world", {"start": {"x": a[0], "y": a[1], "z": a[2]},
                                  "end": {"x": b[0], "y": b[1], "z": b[2]}})
    # A la altura del pecho del jugador (302 = suelo 202 + 100).
    out["trazas"] = {
        "al costado este (espera ~109)": traza((64000, 16545, 302), (64400, 16545, 302)),
        "al costado oeste (espera ~107)": traza((64000, 16545, 302), (63600, 16545, 302)),
        "a la tableta (espera ~179)": traza((64000, 16700, 302), (64000, 17100, 302)),
        "pasillo central (espera nada)": traza((64000, 16300, 302), (64000, 16850, 302)),
    }
    return out
