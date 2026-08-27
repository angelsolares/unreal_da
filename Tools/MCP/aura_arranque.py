# -*- coding: utf-8 -*-
#
# EL AURA DEL PORTADOR ARRANCA "TRAS POCOS SEGUNDOS" (§5.1, la señal de timing).
#
#   node ue.mjs script aura_arranque.py
#
# ### QUE PIDE EL PDF
#
# La tabla del §5.1: "Estandarte empieza buff tras pocos segundos -> se convierte
# en prioridad tactica sin marcador obligatorio". Hasta hoy el aura nacia
# ENCENDIDA en el BeginPlay del componente: el anillo y el buff estaban ahi desde
# antes de que el jugador entrara, o sea que no habia ningun "empieza" que leer.
#
# ### POR QUE EL ARRANQUE ES POR PROXIMIDAD Y NO POR OLEADA
#
# El BeginPlay del componente corre AL CARGAR EL NIVEL, no al entrar en combate:
# un retraso contado desde ahi se consume antes de que el jugador llegue y no
# señala nada. Y engancharlo a la arena (Sellar/EntrarOleada) dejaria COLGADOS a
# los portadores sueltos, los que se colocan sin arena (El Claro).
#
# Por eso el arranque es: cuando el JUGADOR entra en `RadioArranque` (1500 por
# defecto), empieza la cuenta de `RetrasoAura` (4 s), y al agotarse se monta el
# visual y empieza el buff. Desde el punto de vista del jugador es exactamente la
# señal del PDF: te acercas, y a los pocos segundos el anillo se enciende y los
# aliados pegan mas. Vale igual para el portador de una arena que para uno suelto.
# `SiempreActiva` se respeta: con ella puesta, enciende en BeginPlay como siempre.
#
# ### EL ESPEJO DEL SIMULADOR
#
# La regla de la casa: si tocas una formula, tocala en los dos lados y en la
# prueba. `sim.js` gana `_pasoAura()` (sella `tVistaAura` al entrar el jugador en
# `radioArranque`) y `_danoDe()` solo suma el bono si `t - tVistaAura >= retraso`.
# Los numeros viven en `calibracion.json` (aura.retraso, aura.radioArranque) y la
# prueba `pruebas/aura.mjs` cubre el arranque ademas de lo de siempre.
#
# ### COMO SE TOCA EL COMPONENTE SIN REESCRIBIR SU EVENTGRAPH
#
# Los eventos no se reescriben por DSL con seguridad, asi que el EventGraph se
# opera por CIRUGIA de un nodo por evento, y toda la logica nueva vive en
# funciones (que si se escriben enteras, con prevuelo):
#
#   BeginPlay ---> ArrancarAura     (antes: MontarVisual + SetTimer RevisarAura;
#                                    los dos nodos viejos se borran)
#   EndPlay   ---> LimpiarArranque -> (la cadena vieja de ClearTimer+QuitarATodos)
#
#   ArrancarAura():    SiempreActiva ? ActivarAura : SetTimer VigilarArranque 0.5s
#   VigilarArranque(): jugador a < RadioArranque ? (parar vigia; SetTimer
#                      ActivarAura en RetrasoAura) : nada
#   ActivarAura():     MontarVisual + SetTimer RevisarAura 1.0 (el ciclo de siempre)
#   LimpiarArranque(): ClearTimer de VigilarArranque y de ActivarAura
#
# El buff en si (RevisarAura/QuitarATodos) NO se toca: sigue siendo el medido.

import json

BPP = "/Game/DarkAngels/Blueprints/Combat/BP_DA_AuraComponent.BP_DA_AuraComponent"
RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_AuraComponent"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeAura"

RETRASO = 4.0
RADIO_ARRANQUE = 1500.0

ARRANCAR = '''(fn ArrancarAura ()
  (bind _self self)
  (if (Variables|Default|GetSiempreActiva)
    (CallFunction|ActivarAura)
    (else
      (Utilities|Time|SetTimerbyFunctionName _self "VigilarArranque" 0.5 true))))
'''

VIGILAR = '''(fn VigilarArranque ()
  (bind _self self)
  (bind _j (Game|GetPlayerCharacter 0))
  (bind _o (Components|GetOwner _self))
  (Utilities|IsValid _j
    (:"Is Valid"
      (if (< (Math|Vector|Distance(Vector) (Transformation|GetActorLocation _j) (Transformation|GetActorLocation _o)) (Variables|Default|GetRadioArranque))
        (Utilities|Time|ClearTimerbyFunctionName _self "VigilarArranque")
        (Utilities|Time|SetTimerbyFunctionName _self "ActivarAura" (Variables|Default|GetRetrasoAura))))))
'''

ACTIVAR = '''(fn ActivarAura ()
  (bind _self self)
  (CallFunction|MontarVisual)
  (Utilities|Time|SetTimerbyFunctionName _self "RevisarAura" 1.0 true))
'''

LIMPIAR = '''(fn LimpiarArranque ()
  (bind _self self)
  (Utilities|Time|ClearTimerbyFunctionName _self "VigilarArranque")
  (Utilities|Time|ClearTimerbyFunctionName _self "ActivarAura"))
'''

VARIABLES = [("RetrasoAura", "double", "%s" % RETRASO, ""),
             ("RadioArranque", "double", "%s" % RADIO_ARRANQUE, "")]
FUNCIONES = [("ActivarAura", ACTIVAR), ("VigilarArranque", VIGILAR),
             ("ArrancarAura", ARRANCAR), ("LimpiarArranque", LIMPIAR)]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def vue(t, a):
    return call("VibeUE.BlueprintService." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def grafos():
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]


def vaciar(g):
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def prevuelo(codigo, nombre):
    g = {"refPath": BPP + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + nombre + " ", "(fn " + SCRATCH + " ", 1)
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        vaciar(g)
        return m[:200]


def pin(direccion, indice, nodo):
    return {"direction": direccion, "index_id": indice, "node": nodo}


def exec_pins(inf, clave):
    return [p for p in inf[clave] if str(p["type_id"]) == "Exec"]


def nodos_eventgraph():
    g = {"refPath": BPP + ":EventGraph"}
    out = []
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        out.append((n, info(n)))
    return out


def cirugia():
    """BeginPlay -> ArrancarAura (borrando la cadena vieja) y EndPlay ->
    LimpiarArranque -> cadena vieja. Idempotente y con abortos con nombre."""
    g = {"refPath": BPP + ":EventGraph"}
    todos = nodos_eventgraph()
    tipos = {n["refPath"]: str(i["type_id"]) for n, i in todos}
    if any("ArrancarAura" in t for t in tipos.values()):
        return "ya estaba"

    def unico(pred, que):
        cands = [(n, i) for n, i in todos if pred(str(i["type_id"]))]
        if len(cands) != 1:
            raise RuntimeError("ABORTADO: %d nodos para %s" % (len(cands), que))
        return cands[0]

    begin, i_begin = unico(lambda t: "EventBeginPlay" in t or t.endswith("BeginPlay"), "BeginPlay")
    endp, i_end = unico(lambda t: "EndPlay" in t, "EndPlay")
    montar, _ = unico(lambda t: t.endswith("|MontarVisual"), "call MontarVisual")
    settimer, _ = unico(lambda t: "SetTimerbyFunctionName" in t, "SetTimer de BeginPlay")
    cleartimer, i_clear = unico(lambda t: "ClearTimerbyFunctionName" in t, "ClearTimer de EndPlay")

    # tipos de nodo para las llamadas nuevas
    def tipo_de(nombre):
        ts = bt("find_node_types", {"graph": g, "type_id_filter": nombre, "context_pins": []})
        t = next((str(x) for x in ts if nombre in str(x)), None)
        if t is None:
            raise RuntimeError("ABORTADO: no hay tipo de nodo para " + nombre)
        return t

    # --- BeginPlay ---
    sal_b = exec_pins(i_begin, "output_pins")
    if len(sal_b) != 1:
        raise RuntimeError("ABORTADO: BeginPlay con %d salidas exec" % len(sal_b))
    # cortar hacia MontarVisual y borrar la cadena vieja
    for c in sal_b[0]["connected_pins"]:
        bt("break_pins", {"output_pin": pin("EGPD_Output", sal_b[0]["pin_id"]["index_id"], begin),
                          "input_pin": pin(c["direction"], c["index_id"], c["node"])})
    bt("delete_node", {"node": montar})
    bt("delete_node", {"node": settimer})
    pos = i_begin["position"]
    nuevo = bt("create_node", {"graph": g, "type_id": tipo_de("ArrancarAura"),
                               "pos": {"x": int(pos["x"]) + 300, "y": int(pos["y"])}})
    ent = exec_pins(info(nuevo), "input_pins")
    bt("connect_pins", {"output_pin": pin("EGPD_Output", sal_b[0]["pin_id"]["index_id"], begin),
                        "input_pin": pin("EGPD_Input", ent[0]["pin_id"]["index_id"], nuevo)})

    # --- EndPlay: splice antes del ClearTimer viejo ---
    sal_e = exec_pins(i_end, "output_pins")
    objetivo = None
    for p in sal_e:
        for c in p["connected_pins"]:
            if c["node"]["refPath"] == cleartimer["refPath"]:
                objetivo = (p, c)
    if objetivo is None:
        raise RuntimeError("ABORTADO: EndPlay no conecta con su ClearTimer")
    p, c = objetivo
    bt("break_pins", {"output_pin": pin("EGPD_Output", p["pin_id"]["index_id"], endp),
                      "input_pin": pin("EGPD_Input", c["index_id"], cleartimer)})
    pos = i_end["position"]
    limpiar = bt("create_node", {"graph": g, "type_id": tipo_de("LimpiarArranque"),
                                 "pos": {"x": int(pos["x"]) + 300, "y": int(pos["y"])}})
    i_l = info(limpiar)
    bt("connect_pins", {"output_pin": pin("EGPD_Output", p["pin_id"]["index_id"], endp),
                        "input_pin": pin("EGPD_Input", exec_pins(i_l, "input_pins")[0]["pin_id"]["index_id"], limpiar)})
    bt("connect_pins", {"output_pin": pin("EGPD_Output", exec_pins(i_l, "output_pins")[0]["pin_id"]["index_id"], limpiar),
                        "input_pin": pin("EGPD_Input", c["index_id"], cleartimer)})
    return "cosido: BeginPlay->ArrancarAura (cadena vieja borrada) y EndPlay->LimpiarArranque"


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"variables": [], "prevuelo": {}, "escritas": [], "vaciados": {}}

    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": RUTA}))
    for nombre, tipo, defecto, cont in VARIABLES:
        if nombre in existentes:
            out["variables"].append(nombre + " (ya estaba)")
            continue
        vue("AddMemberVariable", {"blueprintPath": RUTA, "variableName": nombre,
                                  "variableType": tipo, "defaultValue": defecto,
                                  "containerType": cont})
        bt("set_variable_instance_editable", {"blueprint": BP, "variable_name": nombre,
                                              "instance_editable": True})
        out["variables"].append(nombre + " (creada, editable)")

    if SCRATCH not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": SCRATCH})

    # LOS GRAFOS SE CREAN (VACIOS) ANTES DEL PREVUELO: `ArrancarAura` llama a
    # `ActivarAura`, y un `CallFunction|X` solo se puede escribir si X existe.
    # Un grafo vacio de mas no rompe nada; un prevuelo que no puede correr, si.
    for nombre, _ in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
            out["escritas"].append("nuevo grafo -> " + nombre)

    for nombre, codigo in FUNCIONES:
        out["prevuelo"][nombre] = prevuelo(codigo, nombre) or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado nada"
        return out

    for nombre, codigo in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    out["cirugia"] = cirugia()
    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    out["releido"] = {"EventGraph": str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":EventGraph"}}))}
    for nombre, _ in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
