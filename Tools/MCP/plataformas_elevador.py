# -*- coding: utf-8 -*-
import json

# `BP_DA_Plataforma`: mueve una terraza de lado a lado, y una instancia por
# plataforma. Monta las ocho de la fila del Elevador.
#
# ### UN ACTOR POR PLATAFORMA, NO UNO CON ARRAYS
#
# Lo natural seria un solo actor con arrays paralelos (objetivo, amplitud,
# periodo, desfase). No se puede: el `for` del DSL **itera elementos, no indices**,
# asi que dentro del bucle no hay con que leer el array paralelo. Y de paso sale
# mejor asi: cada plataforma se ajusta sola desde el editor, que es lo que se
# quiere al afinar un salto.
#
# ### LAS TERRAZAS ERAN `Static`
#
# Las doce estaban en **`Mobility = Static`**, y un actor estatico **no se mueve en
# runtime**: `SetActorLocation` no hace nada. Este script pasa a `Movable` **solo
# las ocho que se mueven**. Efecto secundario a asumir: pierden la iluminacion
# horneada y pasan a dinamica.
#
# ### LAS APILADAS SE QUEDAN QUIETAS
#
# `_10`/`_11` y `_14`/`_15` comparten Y y solo cambian de Z: son escalones, no
# plataformas del recorrido. Decision de Angel: no se tocan, ni su movilidad.
#
# ### SE MUEVEN EN X, PERPENDICULAR A LA FILA
#
# La fila corre a lo largo de **+Y** (de y=10455 a y=35935) con la X clavada en
# −74000. Moviendolas en X cada disco **cruza el eje del camino dos veces por
# ciclo**, que es lo que obliga a cronometrar el salto. Moverlas a lo largo de la
# fila solo abriria y cerraria huecos.
#
# ### LA AMPLITUD ES LO QUE GARANTIZA QUE SIEMPRE SE PUEDA SALTAR
#
# **El desfase NO lo garantiza**: con periodos distintos, dos vecinas coinciden a
# veces desplazadas a lados contrarios. Lo que lo garantiza es acotar la amplitud.
# Los discos miden 2600 de diametro y sus centros estan a 2700-3000, o sea que
# alineados el hueco entre bordes es de ~200. Con desplazamiento en X:
#
#     0 uu   -> hueco ~200      1.200 uu -> ~450
#     2.000  -> ~840            3.000    -> ~1.500
#
# Por eso se arranca en **1200**: en el peor desfase el salto sigue siendo de ~450.
# Subirla es un numero por instancia, pero conviene probar el salto de Malakh antes.
#
# ### DOS DETALLES DEL MOVIMIENTO
#
# - **`bTeleport = false`** a proposito. Con `true` Unreal resetea el estado fisico
#   y el jugador **no se deja arrastrar** por la plataforma; con `false` calcula la
#   velocidad de la base y te lleva encima, que es lo que se quiere.
# - Solo se guarda la **X** de origen, no el vector entero: la Y y la Z se leen del
#   actor en cada Tick. Asi no hace falta una variable de tipo vector y si algo mas
#   sube o baja la plataforma, no se pelea con ella.

CARPETA = "/Game/DarkAngels/Blueprints/Level"
NOMBRE = "BP_DA_Plataforma"
BPP = CARPETA + "/" + NOMBRE + "." + NOMBRE
BP = {"refPath": BPP}
CLASE = BPP + "_C"
SUB = "/Game/DarkAngels/Maps/L_DA_Malkuth_Elevador_Sub"

AMPLITUD = 1200.0

# (terraza, periodo en segundos, desfase 0..1)
# Periodos distintos y **no multiplos entre si**, para que el patron tarde en
# repetirse y no acaben todas alineadas cada pocos segundos.
PLAN = [("Elevador_Terraza_12", 4.3, 0.00),
        ("Elevador_Terraza_13", 5.1, 0.37),
        ("Elevador_Terraza_16", 6.2, 0.61),
        ("Elevador_Terraza_17", 4.7, 0.18),
        ("Elevador_Terraza_18", 5.8, 0.83),
        ("Elevador_Terraza_19", 6.7, 0.29),
        ("Elevador_Terraza_20", 5.4, 0.71),
        ("Elevador_Terraza_21", 4.9, 0.45)]

MOVER = """(fn MoverPlataforma ()
  (if (Variables|Default|GetListo)
    (bind _obj (Variables|Default|GetObjetivo))
    (bind _loc (Transformation|GetActorLocation _obj))
    (bind _ang (* 360.0 (+ (/ (Utilities|Time|GetGameTimeinSeconds)
                              (Variables|Default|GetPeriodo))
                           (Variables|Default|GetDesfase))))
    (Transformation|SetActorLocation :self _obj
      :NewLocation (Math|Vector|MakeVector
                     :X (+ (Variables|Default|GetOrigenX)
                           (* (Variables|Default|GetAmplitud)
                              (Math|Trig|Sin(Degrees) _ang)))
                     :Y (.y _loc) :Z (.z _loc))
      :bSweep false :bTeleport false)))
"""

EVENTOS = """(event EventBeginPlay ()
  (Utilities|IsValid (Variables|Default|GetObjetivo)
    (:"Is Valid"
      (Variables|Default|SetOrigenX
        (.x (Transformation|GetActorLocation (Variables|Default|GetObjetivo))))
      (Variables|Default|SetListo true))
    (:"Is Not Valid")))

(event EventTick (DeltaSeconds)
  (CallFunction|MoverPlataforma))
"""


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def vaciar(g, todo):
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        if not todo and tid.startswith("AddEvent|"):
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def busca(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"] or "/Temp/" in a["refPath"]:
            continue
        if at("get_label", {"actor": a}) == nombre:
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes"}
    out = {}

    # --- 1. el blueprint ---
    if ast("exists", {"path": CARPETA + "/" + NOMBRE}):
        out["blueprint"] = "reutilizado"
    else:
        bt("create", {"folder_path": CARPETA, "asset_name": NOMBRE,
                      "asset_type": {"refPath": "/Script/Engine.Actor"}})
        out["blueprint"] = "creado"

    ya = str(bt("list_variables", {"blueprint": BP}))
    for n, t in (("Amplitud", "float"), ("Periodo", "float"), ("Desfase", "float"),
                 ("OrigenX", "float"), ("Listo", "bool")):
        if "'" + n + "'" not in ya:
            bt("add_variable", {"blueprint": BP, "name": n, "type_name": t})
    if "'Objetivo'" not in ya:
        bt("add_object_variable", {"blueprint": BP, "name": "Objetivo",
                                   "object_class": {"refPath": "/Script/Engine.Actor"}})
    for n in ("Objetivo", "Amplitud", "Periodo", "Desfase"):
        bt("set_variable_instance_editable",
           {"blueprint": BP, "variable_name": n, "instance_editable": True})

    eg = {"refPath": BPP + ":EventGraph"}
    vaciar(eg, True)
    grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]
    if "MoverPlataforma" not in grafos:
        bt("add_function_graph", {"blueprint": BP, "graph_name": "MoverPlataforma"})
    bt("compile_blueprint", {"blueprint": BP})

    gm = {"refPath": BPP + ":MoverPlataforma"}
    vaciar(gm, True)
    bt("write_graph_dsl", {"graph": gm, "code": MOVER})
    bt("write_graph_dsl", {"graph": eg, "code": EVENTOS})
    bt("compile_blueprint", {"blueprint": BP})
    ast("save_assets", {"asset_paths": [CARPETA + "/" + NOMBRE]})
    out["MoverPlataforma"] = str(bt("read_graph_dsl", {"graph": gm}))
    out["EventGraph"] = str(bt("read_graph_dsl", {"graph": eg}))

    # --- 2. las instancias, dentro del submapa del Elevador ---
    volver = sc("get_current_level", {})
    if volver != SUB:
        sc("load_level", {"level_path": SUB})
    if "Elevador_Sub" not in sc("get_current_level", {}):
        return dict(out, error="no se abrio el submapa del Elevador")

    out["puestas"] = []
    for etiqueta, periodo, desfase in PLAN:
        terraza = busca(etiqueta)
        if terraza is None:
            out["puestas"].append({"n": etiqueta, "error": "no aparece"})
            continue
        # Sin `Movable` no se mueve: un actor Static ignora SetActorLocation.
        comp = at("get_components", {"actor": terraza})[0]
        ot("set_properties", {"instance": comp,
                              "values": json.dumps({"Mobility": "Movable"})})

        t = at("get_actor_transform", {"actor": terraza})
        nombre = "Mover_" + etiqueta
        xf = {"location": t["location"],
              "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
              "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}
        m = busca(nombre)
        if m is None:
            m = sc("add_to_scene_from_class", {"actor_type": {"refPath": CLASE},
                                               "name": nombre, "xform": xf,
                                               "parent": None, "snap_to_ground": False})
            at("set_label", {"actor": m, "label": nombre})
        at("set_actor_transform", {"actor": m, "worldspace": True, "xform": xf})
        for k, v in (("Objetivo", {"refPath": terraza["refPath"]}),
                     ("Amplitud", AMPLITUD), ("Periodo", periodo),
                     ("Desfase", desfase)):
            ot("set_properties", {"instance": m, "values": json.dumps({k: v})})
        out["puestas"].append({
            "n": etiqueta,
            "mob": json.loads(ot("get_properties", {"instance": comp,
                                 "properties": ["Mobility"]}))["Mobility"],
            "leido": json.loads(ot("get_properties", {"instance": m,
                                   "properties": ["Amplitud", "Periodo", "Desfase"]}))})

    ast("save_assets", {"asset_paths": [SUB]})
    out["sucio_tras_guardar"] = ast("is_dirty", {"asset_path": SUB})
    if volver != sc("get_current_level", {}):
        sc("load_level", {"level_path": volver})
    out["nivel_final"] = str(sc("get_current_level", {}))
    return out
