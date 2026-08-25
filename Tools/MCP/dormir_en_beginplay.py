# -*- coding: utf-8 -*-
"""Tercera pasada sobre BP_DA_Arena: dormir a los enemigos en BeginPlay, no al sellar.

    node ue.mjs script dormir_en_beginplay.py

EL PROBLEMA. `BuscarEnemigos` —que es quien llama a `LeerOleadas` y `AplicarOleadas`—
solo corria desde `Sellar`. O sea que entre el BeginPlay y el momento en que el jugador
cruza el `BoxComponent` de `Entrada`, LOS CINCO ENEMIGOS ESTABAN SUELTOS. Antes no se
notaba porque el nivel exportado no tenia NavMesh y no podian moverse; en cuanto se le
puso volumen (25/08) salieron a recibir al jugador, y al sellar se les duerme DONDE
ESTEN. Medido en PIE: el Escudero de la segunda oleada se quedo congelado a 600 cm de
la puerta en vez de en su marca.

EL ARREGLO. Se inserta una llamada a `BuscarEnemigos` en el `EventBeginPlay`, justo
despues del `SetEstado 0` y antes de armar el temporizador del watchdog. A partir de
ahi, los de la oleada 2 en adelante nacen dormidos y nadie se mueve de su marca.

La oleada 1 SIGUE SUELTA a proposito: es el comite de recepcion, y en el flujo real la
ventana dura nada —el box de `Entrada` llega hasta x=-1870 y el jugador aparece en
-1900—. Dormirla tambien dejaria la arena llena de estatuas para quien la mire desde
fuera.

ORDEN DE ARRANQUE, que era el riesgo. `AplicarOleadas` necesita el AIController de cada
enemigo (`GetAIController` + `StopLogic`), y si al BeginPlay de la arena todavia no
estuvieran poseidos, el `IsValid` se los saltaria y se quedarian despiertos en silencio.
Se comprobo en PIE y SI estan: los controladores de los personajes colocados en el nivel
se crean durante la inicializacion del mundo, antes de los BeginPlay. Si algun dia
fallara, la solucion es un `SetTimerByFunctionName` de 0,2 s en vez de la llamada
directa. La llamada del `Sellar` se queda donde estaba: es idempotente y sigue haciendo
de red.

Como en las pasadas anteriores, el punto de insercion se busca POR FORMA —el unico
`SetEstado` del EventGraph— y no por nombre de nodo, para que aguante renumeraciones.
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BPP = RUTA + ".BP_DA_Arena"
BP = {"refPath": BPP}
GRAFO = {"refPath": BPP + ":EventGraph"}


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def enchufar():
    nodos = bt("find_nodes", {"graph": GRAFO, "title": ""})
    infos = bt("get_node_infos", {"nodes": nodos})
    for i in infos:
        if "BuscarEnemigos" in str(i["type_id"]):
            return "ya estaba enchufada"

    porRef = {}
    for i in infos:
        porRef[i["node"]["refPath"]] = i

    origen = None
    for i in infos:
        if str(i["type_id"]) == "|SetEstado":
            origen = i
    if origen is None:
        return "NO ENCONTRADO el SetEstado del EventBeginPlay"

    salida = None
    siguiente = None
    for p in origen["output_pins"]:
        if p["name"] != "then":
            continue
        salida = p["pin_id"]
        for c in p["connected_pins"]:
            ref = c["node"]["refPath"]
            if ref in porRef:
                siguiente = porRef[ref]
    if salida is None or siguiente is None:
        return "el SetEstado no tiene a quien encadenar"

    entrada = None
    for p in siguiente["input_pins"]:
        if p["type_id"] == "Exec" and p["name"] in ("execute", "then"):
            entrada = p["pin_id"]
    if entrada is None:
        return "el nodo siguiente no tiene pin de ejecucion de entrada"

    pos = origen["position"]
    nuevo = bt("create_node", {"graph": GRAFO, "type_id": "CallFunction|BuscarEnemigos",
                               "pos": {"x": int(pos["x"]) + 120, "y": int(pos["y"]) + 200}})
    ni = bt("get_node_infos", {"nodes": [nuevo]})[0]
    pin_in = None
    pin_out = None
    for p in ni["input_pins"]:
        if p["type_id"] == "Exec":
            pin_in = p["pin_id"]
    for p in ni["output_pins"]:
        if p["type_id"] == "Exec":
            pin_out = p["pin_id"]
    if pin_in is None or pin_out is None:
        return "el nodo nuevo no tiene pines de ejecucion"

    bt("break_pins", {"output_pin": salida, "input_pin": entrada})
    bt("connect_pins", {"output_pin": salida, "input_pin": pin_in})
    bt("connect_pins", {"output_pin": pin_out, "input_pin": entrada})
    return "enchufada"


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"enchufe": enchufar()}
    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})
    # Releer: el `true` de estas APIs solo dice que acepto la llamada.
    out["EventGraph"] = str(bt("read_graph_dsl", {"graph": GRAFO}))
    return out
