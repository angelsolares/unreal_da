# -*- coding: utf-8 -*-
import json

# Coloca el primer par de `BP_DA_Paso` de Malkuth: la puerta de bronce de El
# Claro. Lanzar DESPUES de `paso_verbo.py` y `paso_crear.py`.
#
# ### LA GEOMETRIA, MEDIDA -- NO COPIADA DE LAS NOTAS
#
# Todo lo de abajo sale de `trace_world` y `get_actor_bounds` sobre el submapa
# abierto suelto, que es donde los actores estan en **coordenadas del submapa**:
# la Level Instance del maestro les suma su offset. Escribir aqui numeros leidos
# en el maestro manda el actor a decenas de km.
#
#   - `Claro_Puerta_Bronce` esta en (8245, 3090), y **tapa de verdad**: una traza
#     horizontal por el eje a z=400 y a z=700 choca en y = 3080. O sea que el
#     hueco norte del anillo esta sellado y no se puede pasar andando. Por eso
#     este paso tiene sentido y no es un atajo: no hay ruta alternativa.
#   - Al sur de la puerta se sube por `Claro_Escalera`: el suelo va de z=43 en
#     y=2400 a z=183 en y=3000. La cota del rellano es **~182**, no los 232 que
#     dan los bounds --los bounds son la caja del mesh entero, la traza es la
#     superficie que se pisa--.
#   - Al norte, pasada la puerta, hay un bolsillo entre `Claro_GateRock_L` y
#     `_R` con suelo **plano a z=-40** desde y=3400 hasta el fondo de roca en
#     y~5600.
#
# ### VAN DOS PASOS, NO UNO
#
# El bolsillo del norte no tiene salida: la puerta lo cierra y el escalon de
# 220 uu del rellano no se sube. Con un solo paso, cruzar seria quedarse
# encerrado y habria que reiniciar el nivel para seguir probando -- y probar
# ANDANDO es justo lo que pide la nota del salto de zona. Asi que el de ida
# tiene su gemelo de vuelta, con el destino en el rellano.
#
# ### LOS DESTINOS SON `TargetPoint` Y SU YAW IMPORTA
#
# `CruzarPaso` copia el yaw del actor `Destino` al pawn Y al controlador. Aqui:
# el de ida mira al norte (yaw 90), que es hacia donde ibas; el de vuelta mira
# al sur (yaw -90), hacia el claro. Sin esto reapareces mirando a donde mirabas
# antes de pulsar.
#
# La Z de un destino **no es la del suelo**: el origen de un Character es el
# centro de la capsula, o sea el suelo + 96. Es el mismo `+96` que ya se pago
# colocando los enemigos de El Claro.
#
# ### EL FLAG DE IDA SI, EL DE VUELTA NO
#
# `CLARO_PUERTA_CRUZADA` queda en el GameState en cuanto se cruza, y de ahi lo
# puede leer cualquiera --el Debug HUD, una linea de Gabriel, un `BP_DA_Decision`
# que solo aparezca si has estado detras de la puerta--. La vuelta no apunta
# nada: `FlagPaso` vacio esta contemplado y no escribe.
#
# `FlagRequerido` se deja VACIO en los dos, o sea la puerta esta abierta. Es el
# gancho para sellarla: el dia que haya que ganarse el paso, se escribe ahi el
# nombre del flag y el cartel pasa solo a decir "Sellado" (ver `paso_verbo.py`).

SUB = "/Game/DarkAngels/Maps/L_DA_Malkuth_Claro_Sub"
MAESTRO = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"
CLASE = "/Game/DarkAngels/Blueprints/Level/BP_DA_Paso.BP_DA_Paso_C"
DESTINO = "/Script/Engine.TargetPoint"
CARPETA = "Claro/Puerta"

EJE = 8245.0          # eje de la abertura norte, medido
SUELO_NORTE = -40.0   # suelo plano detras de la puerta
SUELO_SUR = 172.0     # rellano de la escalinata, delante de la puerta
CAPSULA = 96.0        # medio alto de la capsula del jugador
FLAG_CRUZADA = "CLARO_PUERTA_CRUZADA"

# (etiqueta, x, y, z, yaw, es_paso, destino, flag)
PIEZAS = [
    ("Destino_TrasPuerta",  EJE, 3800.0, SUELO_NORTE + CAPSULA + 4,  90.0, False, None, ""),
    ("Destino_AntePuerta",  EJE, 2850.0, SUELO_SUR + CAPSULA + 4,   -90.0, False, None, ""),
    # el de ida: pegado a la cara sur de la puerta, sobre el rellano
    ("Paso_Puerta_Claro",   EJE, 3020.0, SUELO_SUR,                   0.0, True,
     "Destino_TrasPuerta", FLAG_CRUZADA),
    # el de vuelta: al otro lado de la hoja, sobre el suelo del bolsillo
    ("Paso_Puerta_Claro_Vuelta", EJE, 3450.0, SUELO_NORTE,            0.0, True,
     "Destino_AntePuerta", ""),
]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    out = {"puestos": {}}

    sc("load_level", {"level_path": SUB})
    if sc("get_current_level", {}) != SUB:
        return {"error": "no se abrio el submapa"}

    puestos = {}
    for etiqueta, x, y, z, yaw, es_paso, destino, flag in PIEZAS:
        # `set_actor_transform` RESETEA escala y rotacion si no se las pasas:
        # el xform va siempre entero.
        xf = {"location": {"x": x, "y": y, "z": z},
              "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
              "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
        a = busca(etiqueta)
        if a is None:
            a = sc("add_to_scene_from_class", {
                "actor_type": {"refPath": CLASE if es_paso else DESTINO},
                "name": etiqueta, "xform": xf, "parent": None, "snap_to_ground": False})
            at("set_label", {"actor": a, "label": etiqueta})
            out["puestos"][etiqueta] = "creado"
        else:
            out["puestos"][etiqueta] = "ya estaba"
        at("set_actor_transform", {"actor": a, "worldspace": True, "xform": xf})
        sc("set_actor_folder", {"actor": a, "folder_path": CARPETA})
        puestos[etiqueta] = a

        if es_paso:
            # Un campo por llamada: el setter de propiedades aplica la primera y
            # con la referencia de objeto conviene no mezclarla con cadenas.
            ot("set_properties", {"instance": a, "values": json.dumps(
                {"Destino": {"refPath": puestos[destino]["refPath"]}})})
            ot("set_properties", {"instance": a, "values": json.dumps({"FlagPaso": flag})})
            ot("set_properties", {"instance": a, "values": json.dumps({"FlagRequerido": ""})})

    # --- releer del actor, no del script ---
    for etiqueta, x, y, z, yaw, es_paso, destino, flag in PIEZAS:
        a = puestos[etiqueta]
        t = at("get_actor_transform", {"actor": a})
        ficha = {"loc": [round(t["location"][k]) for k in ("x", "y", "z")],
                 "yaw": round(t["rotation"]["yaw"], 1)}
        if es_paso:
            p = json.loads(ot("get_properties", {"instance": a, "properties":
                              ["Destino", "FlagPaso", "FlagRequerido"]}))
            ficha["Destino"] = str(p["Destino"]).split("/")[-1]
            ficha["FlagPaso"] = p["FlagPaso"]
            ficha["FlagRequerido"] = p["FlagRequerido"]
            b = at("get_actor_bounds", {"actor": a, "only_colliding": False})
            ficha["caja"] = {"min": [round(b["min"][k]) for k in ("x", "y", "z")],
                             "max": [round(b["max"][k]) for k in ("x", "y", "z")]}
        out.setdefault("comprobado", {})[etiqueta] = ficha

    ast("save_assets", {"asset_paths": [SUB]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": SUB})

    sc("load_level", {"level_path": MAESTRO})
    out["nivel_final"] = str(sc("get_current_level", {}))
    return out
