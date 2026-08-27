# -*- coding: utf-8 -*-
#
# EL ENEMIGO DE ORIGEN VIAJA CON EL ARMA (§10, Show Weapon State).
#
#   node ue.mjs script arma_origen.py
#
# ### LA NOTA VIEJA ERA FALSA, Y CONVIENE DEJARLO ESCRITO
#
# El panel WEAPON decia "-- sin registrar: el pickup vive en DCS". Era verdad
# cuando se escribio y dejo de serlo sin que nadie actualizara la nota: desde que
# existe `BP_DA_DroppedWeapon`, TODO el camino del arma por el suelo es nuestro
# — el componente que la suelta (`BP_DA_WeaponDropComponent.DropOne`), el actor
# en el suelo, y la recogida (`EventInteract` -> `CanjearTemporal`). DCS no pinta
# nada aqui. Asi que registrar quien la solto son tres eslabones nuestros:
#
#   DropOne  --------> AnotarOrigen(destino)     [cirugia de UN nodo]
#                        \-> RegistrarOrigen(nombre del dueño) en el actor caido
#   EventInteract ----> CanjearTemporal          [reescrita: 4 lineas -> 5]
#                        \-> RegistrarOrigenArma(EnemigoOrigen) en el jugador
#
# `SustituirArmaTemporal` limpia el origen al empezar cada canje, asi que la
# secuencia deja el valor bueno: canje (limpia) -> registrar (escribe). Un arma
# dada por el Debug HUD se queda con origen vacio, que es la verdad.
#
# ### POR QUE DropOne VA POR CIRUGIA Y CanjearTemporal ENTERA
#
# `DropOne` contiene `Game|SpawnActorBPDADroppedWeapon`, un spawner tipado que el
# lector imprime y el escritor NO sabe crear (la misma trampa que
# `ReiniciarEncuentro`, ver arena_flechas.py). CanjearTemporal son cuatro lineas
# de nodos todos escribibles: entera y con rollback si falla.

import json

DW_RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_DroppedWeapon"
DW = DW_RUTA + ".BP_DA_DroppedWeapon"
WD_RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_WeaponDropComponent"
WD = WD_RUTA + ".BP_DA_WeaponDropComponent"

REGISTRAR = '''(fn RegistrarOrigen (Nombre)
  (Variables|Default|SetEnemigoOrigen Nombre))
'''

ANOTAR = '''(fn AnotarOrigen (Destino)
  (Class|BPDADroppedWeapon|RegistrarOrigen Destino (Utilities|GetDisplayName (Components|GetOwner self))))
'''

CANJEAR = '''(fn CanjearTemporal (Quien Nueva)
  (bind _p (Utilities|Casting|CastToBP_DA_PlayerCharacter Quien))
  (Class|BPDAPlayerCharacter|SustituirArmaTemporal _p Nueva)
  (Class|BPDAPlayerCharacter|RegistrarOrigenArma _p (Variables|Default|GetEnemigoOrigen))
  (Utilities|Time|SetTimerbyFunctionName _p "CorromperArmaTemporal" 0.6))
'''


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


def grafos(bpp):
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": {"refPath": bpp}})]


def vaciar(g):
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def pin(direccion, indice, nodo):
    return {"direction": direccion, "index_id": indice, "node": nodo}


def exec_pins(inf, clave):
    return [p for p in inf[clave] if str(p["type_id"]) == "Exec"]


def entradas_datos(nombre_grafo, bpp):
    g = {"refPath": bpp + ":" + nombre_grafo}
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        i = info(n)
        if "FunctionEntry" in str(i["type_id"]) + n["refPath"]:
            return [p for p in i["output_pins"] if str(p["type_id"]) != "Exec"]
    return []


def splice_dropone():
    """Cose AnotarOrigen en DropOne, tras el SetItemDrop VIVO.

    OJO: DropOne tiene TRES cuerpos — el vivo y dos huerfanos invisibles de
    pasadas viejas de write_graph_dsl (la trampa documentada: un write que
    triunfa sobre un grafo con cuerpo lo DUPLICA y el lector no lo delata).
    Por eso aqui no se busca por tipo a secas: se recorre la cadena de pines
    Exec desde el FunctionEntry y solo cuenta lo alcanzable. El Destino no se
    busca tampoco: se toma de donde ya bebe el propio SetItemDrop (su pin
    self), que por construccion es el cast vivo."""
    g = {"refPath": WD + ":DropOne"}
    todos = [(n, info(n)) for n in bt("find_nodes", {"graph": g, "title": ""})]
    if any("AnotarOrigen" in str(i["type_id"]) for _, i in todos):
        return "ya estaba"

    entry = next(((n, i) for n, i in todos
                  if "FunctionEntry" in str(i["type_id"]) + n["refPath"]), None)
    if entry is None:
        raise RuntimeError("ABORTADO: DropOne sin FunctionEntry")

    por_ref = {n["refPath"]: (n, i) for n, i in todos}
    vivos, cola = set(), [entry[0]["refPath"]]
    while cola:
        ref = cola.pop()
        if ref in vivos or ref not in por_ref:
            continue
        vivos.add(ref)
        _, i = por_ref[ref]
        for p in exec_pins(i, "output_pins"):
            for c in p["connected_pins"]:
                cola.append(c["node"]["refPath"])

    candidatos = [(n, i) for n, i in todos
                  if n["refPath"] in vivos and str(i["type_id"]).endswith("SetItemDrop")]
    if len(candidatos) != 1:
        raise RuntimeError("ABORTADO: %d SetItemDrop ALCANZABLES en DropOne" % len(candidatos))
    setdrop, i_set = candidatos[0]

    sal = exec_pins(i_set, "output_pins")
    if len(sal) != 1 or len(sal[0]["connected_pins"]) != 1:
        raise RuntimeError("ABORTADO: el SetItemDrop vivo no tiene una unica salida exec conectada")
    destino_c = sal[0]["connected_pins"][0]

    # de donde bebe su self: ese mismo origen alimentara el Destino
    self_pin = next((p for p in i_set["input_pins"]
                     if str(p["type_id"]) != "Exec" and p["connected_pins"]), None)
    if self_pin is None:
        raise RuntimeError("ABORTADO: el SetItemDrop vivo no tiene self conectado")
    fuente = self_pin["connected_pins"][0]

    ts = bt("find_node_types", {"graph": g, "type_id_filter": "AnotarOrigen", "context_pins": []})
    tipo = next((str(x) for x in ts if "AnotarOrigen" in str(x)), None)
    if tipo is None:
        raise RuntimeError("ABORTADO: no hay tipo de nodo para AnotarOrigen")

    pos = i_set["position"]
    nuevo = bt("create_node", {"graph": g, "type_id": tipo,
                               "pos": {"x": int(pos["x"]) + 260, "y": int(pos["y"]) + 180}})
    i_n = info(nuevo)
    ent = exec_pins(i_n, "input_pins")
    sal_n = exec_pins(i_n, "output_pins")
    datos = [p for p in i_n["input_pins"] if str(p["type_id"]) != "Exec"]
    destino_pin = next((p for p in datos if "Dropped" in str(p["type_id"])), None)
    if destino_pin is None or len(ent) != 1 or len(sal_n) != 1:
        bt("delete_node", {"node": nuevo})
        raise RuntimeError("ABORTADO: AnotarOrigen sin los pines esperados: %s"
                           % [str(p["name"]) + ":" + str(p["type_id"]) for p in datos])

    bt("break_pins", {"output_pin": pin("EGPD_Output", sal[0]["pin_id"]["index_id"], setdrop),
                      "input_pin": pin(destino_c["direction"], destino_c["index_id"], destino_c["node"])})
    bt("connect_pins", {"output_pin": pin("EGPD_Output", sal[0]["pin_id"]["index_id"], setdrop),
                        "input_pin": pin("EGPD_Input", ent[0]["pin_id"]["index_id"], nuevo)})
    bt("connect_pins", {"output_pin": pin("EGPD_Output", sal_n[0]["pin_id"]["index_id"], nuevo),
                        "input_pin": pin(destino_c["direction"], destino_c["index_id"], destino_c["node"])})
    bt("connect_pins", {"output_pin": pin(fuente["direction"], fuente["index_id"], fuente["node"]),
                        "input_pin": pin("EGPD_Input", destino_pin["pin_id"]["index_id"], nuevo)})
    return "cosido tras el SetItemDrop VIVO (hay 2 cuerpos huerfanos que no se tocan)"


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"escritas": [], "vaciados": {}}

    # --- BP_DA_DroppedWeapon: la variable y su setter -----------------------
    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": DW_RUTA}))
    if "EnemigoOrigen" not in existentes:
        vue("AddMemberVariable", {"blueprintPath": DW_RUTA, "variableName": "EnemigoOrigen",
                                  "variableType": "string", "defaultValue": "", "containerType": ""})
        out["escritas"].append("var nueva -> DroppedWeapon.EnemigoOrigen")
    if "RegistrarOrigen" not in grafos(DW):
        bt("add_function_graph", {"blueprint": {"refPath": DW}, "graph_name": "RegistrarOrigen"})
        out["escritas"].append("nuevo grafo -> RegistrarOrigen")
    if not entradas_datos("RegistrarOrigen", DW):
        bt("add_function_param", {"graph": {"refPath": DW + ":RegistrarOrigen"},
                                  "param_name": "Nombre", "param_type": "string",
                                  "input_param": True})
    g = {"refPath": DW + ":RegistrarOrigen"}
    out["vaciados"]["RegistrarOrigen"] = vaciar(g)
    bt("write_graph_dsl", {"graph": g, "code": REGISTRAR})
    out["escritas"].append("RegistrarOrigen")

    # CanjearTemporal, entera (rollback si falla).
    g = {"refPath": DW + ":CanjearTemporal"}
    out["vaciados"]["CanjearTemporal"] = vaciar(g)
    bt("write_graph_dsl", {"graph": g, "code": CANJEAR})
    out["escritas"].append("CanjearTemporal")
    bt("compile_blueprint", {"blueprint": {"refPath": DW}})
    st("save_assets", {"asset_paths": [DW_RUTA]})

    # --- BP_DA_WeaponDropComponent: AnotarOrigen + la cirugia ---------------
    if "AnotarOrigen" not in grafos(WD):
        bt("add_function_graph", {"blueprint": {"refPath": WD}, "graph_name": "AnotarOrigen"})
        out["escritas"].append("nuevo grafo -> AnotarOrigen")
    if not entradas_datos("AnotarOrigen", WD):
        bt("add_object_function_param", {"graph": {"refPath": WD + ":AnotarOrigen"},
                                         "param_name": "Destino",
                                         "object_class": {"refPath": DW + "_C"},
                                         "input_param": True})
        out["escritas"].append("entrada nueva -> AnotarOrigen.Destino")
    g = {"refPath": WD + ":AnotarOrigen"}
    out["vaciados"]["AnotarOrigen"] = vaciar(g)
    bt("write_graph_dsl", {"graph": g, "code": ANOTAR})
    out["escritas"].append("AnotarOrigen")
    bt("compile_blueprint", {"blueprint": {"refPath": WD}})

    out["cirugia"] = splice_dropone()
    bt("compile_blueprint", {"blueprint": {"refPath": WD}})
    st("save_assets", {"asset_paths": [WD_RUTA]})

    out["releido"] = {
        "CanjearTemporal": str(bt("read_graph_dsl", {"graph": {"refPath": DW + ":CanjearTemporal"}})),
        "AnotarOrigen": str(bt("read_graph_dsl", {"graph": {"refPath": WD + ":AnotarOrigen"}})),
        "DropOne": str(bt("read_graph_dsl", {"graph": {"refPath": WD + ":DropOne"}})),
    }
    return out
