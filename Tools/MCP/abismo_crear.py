# -*- coding: utf-8 -*-
import json

# `BP_DA_Abismo`: caer al vacio termina la partida.
#
# ### POR COTA, NO POR CAJA -- Y NO ES UN CAPRICHO
#
# La caja `TR_DeathVoid_Malkuth` que se puso a mano mide **200.000 x 200.000 x
# 20.000 uu** y su techo esta en **z = 4927**. El suelo del mapa esta a −40, o sea
# que **el jugador nace dentro**: el Game Over saltaria en el primer fotograma.
#
# Con un umbral de cota se arregla eso y ademas se cubre **todo el mapa con un
# solo actor**, en vez de una caja por precipicio. Es exactamente lo que ya hace
# `BP_RespawnVolume` en este proyecto --comparar la Z del jugador contra una
# referencia en Tick--, asi que la tecnica esta probada aqui.
#
# ### POR QUE NO KILL Z
#
# `KillZ` esta en −1.048.575, o sea desactivado, y asi se queda: destruye el pawn
# y despues no hay a quien enseniarle la pantalla ni a quien devolverle el control.
#
# ### LA PANTALLA SE PINTA CON LO QUE YA HAY
#
# `BP_DA_HUD` tiene `ShowZoneBanner(InText)`, que ya dibuja texto. **No se toca el
# HUD**: se le llama desde fuera, que es la unica via que permite el DSL para
# hablar con otro blueprint.
#
# Hay un detalle: `ShowZoneBanner` guarda `ZoneBannerEnd = ahora + 5s`, o sea que
# el cartel **se borra solo a los 5 segundos**. Por eso se le llama **en cada
# Tick** mientras dure la caida: cada llamada empuja el vencimiento 5 s hacia
# delante y el cartel se queda fijo. Es un apaño consciente, no un descuido.
#
# **Lo que NO puedo montar es la pantalla de UMG** con su boton de Reintentar: el
# MCP no expone ningun toolset de UMG --hay actor, blueprint, material, texture...
# y ninguno de widgets--, asi que anadir un Text o un Button al arbol de un
# `WBP_` es trabajo a mano. De ahi que el reintento vaya por tecla.
#
# ### LA TECLA Y EL MAPA VAN COMO LITERALES, NO COMO VARIABLE
#
# `WasInputKeyJustPressed` pide un `FKey` y `OpenLevel(byName)` un `FName`. Una
# variable String **no conecta** a esos pines; solo el literal se convierte. Lo que
# si queda configurable por instancia es lo que es String o float de verdad:
# `Texto`, `Flag` y `CotaMortal`.

CARPETA = "/Game/DarkAngels/Blueprints/Level"
NOMBRE = "BP_DA_Abismo"
BPP = CARPETA + "/" + NOMBRE + "." + NOMBRE
BP = {"refPath": BPP}

TECLA = "R"
MAPA = "L_DA_Malkuth_Master"
COTA = -3000.0                     # muy por debajo de cualquier suelo pisable
TEXTO = "HAS CAIDO AL VACIO   -   [R] Reintentar"
FLAG = "MUERTE_ABISMO"

# Tres `if` hermanos y no anidados. El primero escribe `Caido` DENTRO de su rama:
# la condicion se evalua una sola vez en el Branch, asi que da igual que la
# invalide despues. Los otros dos leen la variable ya escrita, no un `bind`, que
# es la trampa de siempre --un bind sobre nodos puros no cachea nada--.
VIGILAR = """(fn VigilarAbismo ()
  (bind _pc (Game|GetPlayerController 0))
  (if (and (not (Variables|Default|GetCaido))
           (< (.z (Transformation|GetActorLocation (Game|GetPlayerCharacter 0)))
              (Variables|Default|GetCotaMortal)))
    (Variables|Default|SetCaido true)
    (Class|BPDAGameState|MarcarFlag
      :self (Utilities|Casting|CastToBP_DA_GameState (Game|GetGameState))
      :Nombre (Variables|Default|GetFlag))
    (Input|SetIgnoreMoveInput :self _pc :bNewMoveInput true)
    (Input|SetIgnoreLookInput :self _pc :bNewLookInput true))
  (if (Variables|Default|GetCaido)
    (Class|BPDAHUD|ShowZoneBanner
      :self (Utilities|Casting|CastToBP_DA_HUD (HUD|GetHUD :self _pc))
      :InText (Variables|Default|GetTexto)))
  (if (and (Variables|Default|GetCaido)
           (Game|Player|WasInputKeyJustPressed :self _pc :Key "%s"))
    (Game|OpenLevel(byName) :LevelName "%s")))
""" % (TECLA, MAPA)

EVENTOS = """(event EventTick (DeltaSeconds)
  (CallFunction|VigilarAbismo))
"""


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


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


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {}

    if ast("exists", {"path": CARPETA + "/" + NOMBRE}):
        out["blueprint"] = "reutilizado"
    else:
        bt("create", {"folder_path": CARPETA, "asset_name": NOMBRE,
                      "asset_type": {"refPath": "/Script/Engine.Actor"}})
        out["blueprint"] = "creado"

    ya = str(bt("list_variables", {"blueprint": BP}))
    for n, t in (("CotaMortal", "float"), ("Texto", "string"), ("Flag", "string"),
                 ("Caido", "bool")):
        if "'" + n + "'" not in ya:
            bt("add_variable", {"blueprint": BP, "name": n, "type_name": t})
    for n in ("CotaMortal", "Texto", "Flag"):
        bt("set_variable_instance_editable",
           {"blueprint": BP, "variable_name": n, "instance_editable": True})

    # El EventGraph se vacia lo PRIMERO: si una pasada anterior dejo la llamada,
    # rehacer la funcion con alguien llamandola deja el blueprint sin compilar.
    eg = {"refPath": BPP + ":EventGraph"}
    out["vaciado_eventgraph"] = vaciar(eg, True)

    grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]
    if "VigilarAbismo" not in grafos:
        bt("add_function_graph", {"blueprint": BP, "graph_name": "VigilarAbismo"})
    bt("compile_blueprint", {"blueprint": BP})

    gv = {"refPath": BPP + ":VigilarAbismo"}
    out["vaciado_funcion"] = vaciar(gv, True)
    bt("write_graph_dsl", {"graph": gv, "code": VIGILAR})
    bt("write_graph_dsl", {"graph": eg, "code": EVENTOS})
    bt("compile_blueprint", {"blueprint": BP})

    # Los defectos van DESPUES de compilar: hasta entonces el CDO no tiene las
    # propiedades recien creadas.
    cdo = bt("get_default_object", {"blueprint": BP})
    for k, v in (("CotaMortal", COTA), ("Texto", TEXTO), ("Flag", FLAG)):
        ot("set_properties", {"instance": cdo, "values": json.dumps({k: v})})
    bt("compile_blueprint", {"blueprint": BP})
    ast("save_assets", {"asset_paths": [CARPETA + "/" + NOMBRE]})

    # --- releer, que el `true` de estas APIs solo dice "acepte la llamada" ---
    out["VigilarAbismo"] = str(bt("read_graph_dsl", {"graph": gv}))
    out["EventGraph"] = str(bt("read_graph_dsl", {"graph": eg}))
    out["variables"] = [str(v) for v in bt("list_variables", {"blueprint": BP})]
    out["defectos"] = json.loads(ot("get_properties", {
        "instance": cdo, "properties": ["CotaMortal", "Texto", "Flag", "Caido"]}))
    for n in bt("find_nodes", {"graph": eg, "title": ""}):
        tid = str(info(n)["type_id"])
        if "Vigilar" in tid:
            out["a_quien_llama"] = tid
    return out
