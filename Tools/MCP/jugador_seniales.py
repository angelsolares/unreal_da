# -*- coding: utf-8 -*-
#
# DOS SEÑALES DEL JUGADOR: los Arqueros reaccionan a la Lanza (§5.1) y la
# pestaña WEAPON gana FLECHAS y ENEMIGO DE ORIGEN (§10).
#
#   node ue.mjs script jugador_seniales.py
#
# ### §5.1 — "Arquero retrocede al ver a Malakh con lanza", POR EVENTO
#
# La forma obvia —un decorador propio sobre el umbral de retirada del arbol— esta
# MEDIDA Y ENTERRADA en `bt_arquero_da.py`: la rama de huir del BT_ArcherAI lleva
# un Force Success que APAGA EL DISPARO mientras el jugador este dentro del
# umbral, la EQS no tiene adonde mandar a un arquero cuyo balcon (400x550) es mas
# pequeño que el propio umbral, y el 450 que se probo el 25/08 se revirtio el
# mismo dia: cualquier numero ahi solo compra una burbuja de silencio. La
# conclusion escrita alli: la señal pide UN PASO ATRAS VISIBLE, no un umbral.
#
# Eso es lo que monta esto: en el momento en que Malakh ADQUIERE la Lanza
# —`SustituirArmaTemporal`, el embudo unico del canje, asi que vale para el
# pickup y para el give del Debug HUD—, todo Arquero vivo a menos de 2500 da un
# salto atras: un LaunchCharacter alejandose del jugador, CON COMPROBACION DE
# SUELO, porque los arqueros viven en balcones y un empujon sin mirar los tira a
# la arena y cambia el encuentro. Si detras no hay suelo, ese arquero no salta.
#
# Y LA VENTANA DE LA TRAZA IMPORTA, que la primera version bajaba 500 cm y
# ENCONTRABA EL SUELO DE LA ARENA 4,5 m por debajo del balcon: los dos arqueros
# saltaron... y se cayeron (medido en PIE: dz -360). "Hay suelo" no es "hay
# suelo A TU ALTURA": la traza baja como mucho 250 desde el punto de destino,
# asi que un desnivel mayor cuenta como vacio y ese arquero NO salta. La señal
# se pierde para quien no tiene sitio detras, que es exactamente lo correcto.
#
# El arbol NO se toca: el arquero sigue disparando igual que antes. La señal es
# un gesto, no un estado.
#
# ### §10 — DbgEstadoArma pasa de 4 a 6 salidas
#
# Se añaden FLECHAS (el ammo del §10: la cuenta real de DA_ElvenArrow en el
# inventario) y ORIGEN (quien solto el arma que llevas). El origen lo escribe el
# camino de recogida (`arma_origen.py`): aqui solo vive la variable, su limpieza
# en el swap, y la salida. Un arma dada por el Debug HUD queda con origen vacio
# — el panel enseña "--", que es la verdad.
#
# La cuenta de flechas evita el Accessed None a proposito: el indice que se lee
# es `(select encontrada indice 0)`, o sea que cuando no hay flechas se lee el
# item 0 (el inventario nunca esta vacio) y el SELECT descarta ese valor por la
# rama "0". Cero avisos por frame con el panel abierto.
#
# ### LA TRAMPA DE AÑADIR SALIDAS A UNA FUNCION VIVA
#
# `add_function_param` NO es idempotente: relanzar duplica el parametro. Aqui se
# cuentan antes las salidas del FunctionResult y solo se añaden si faltan. Y las
# nuevas van AL FINAL: la pestaña WEAPON destructura por ORDEN, asi que las
# cuatro de siempre conservan su posicion y el HUD viejo sigue funcionando hasta
# la regeneracion.

import json

BPP = "/Game/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter.BP_DA_PlayerCharacter"
RUTA = "/Game/DarkAngels/Blueprints/Characters/BP_DA_PlayerCharacter"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeDosManos"

INV = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/Inventory/"
       "BP_InventoryComponent.BP_InventoryComponent_C")
FLECHA = ("/Game/DynamicCombatSystem/ArcheryModule/Blueprints/Items/ObjectItems/"
          "Instances/DA_ElvenArrow.DA_ElvenArrow")
ARQUERO = "/Game/DarkAngels/Blueprints/Enemies/BP_DA_Arquero.BP_DA_Arquero_C"

RADIO_AVISO = 2500.0     # hasta donde "ven" la lanza
SALTO = 380.0            # empuje horizontal del paso atras
SALTO_Z = 300.0          # y el brinco

REGISTRAR = '''(fn RegistrarOrigenArma (Nombre)
  (Variables|Default|SetEnemigoOrigenArma Nombre))
'''

AVISAR = '''(fn AvisarLanza ()
  (bind _j (Transformation|GetActorLocation self))
  (for _e (Actor|GetAllActorsOfClass "%(arquero)s")
    (bind _le (Transformation|GetActorLocation _e))
    (bind _dir (Math|Vector|Normalize (Math|Vector|MakeVector (- (.x _le) (.x _j)) (- (.y _le) (.y _j)) 0.0)))
    (bind _dest (+ _le (* _dir 300.0)))
    (bind (_hit _haysuelo) (Collision|LineTraceByChannel (+ _dest (Math|Vector|MakeVector 0.0 0.0 150.0)) (- _dest (Math|Vector|MakeVector 0.0 0.0 250.0))))
    (if (and (and (< (Math|Vector|Distance(Vector) _j _le) %(radio)s) (CanBeAttacked|IsAlive(Message) _e)) _haysuelo)
      (Character|LaunchCharacter _e (+ (* _dir %(salto)s) (Math|Vector|MakeVector 0.0 0.0 %(saltoz)s)) true true))))
''' % {"arquero": ARQUERO, "radio": RADIO_AVISO, "salto": SALTO, "saltoz": SALTO_Z}

SUSTITUIR_COLA = '''      (Variables|Default|SetArmaTemporal NuevaArma)
      (Variables|Default|SetTUltimoTemporal (Utilities|Time|GetGameTimeInSeconds))
      (Variables|Default|SetEnemigoOrigenArma "")
      (Utilities|Time|SetTimerbyFunctionName _self "AplicarReglaDosManos" 0.7)
      (Utilities|Time|SetTimerbyFunctionName _self "VigilarMunicion" 0.5 true)
      (if (Utilities|String|EqualExactly(String) (Utilities|GetObjectName NuevaArma) (Utilities|GetObjectName (Variables|Default|GetArmaArrojadiza)))
        (CallFunction|AvisarLanza))'''

SUSTITUIR = '''(fn SustituirArmaTemporal (NuevaArma)
  (bind _self self)
  (bind _armatemporal (Variables|Default|GetArmaTemporal))
  (Variables|Default|SetMotivoSalidaArma "SWAP")
  (Utilities|IsValid _armatemporal
    (:"Is Valid"
      (bind _asbp_inventory_component (Utilities|Casting|CastToBP_InventoryComponent (Actor|GetComponentByClass _self "%(inv)s")))
      (Modify|RemoveItem _asbp_inventory_component _armatemporal false 1)
%(cola)s)
    (:"Is Not Valid"
%(cola)s)))
''' % {"inv": INV, "cola": SUSTITUIR_COLA}

ESTADO = '''(fn DbgEstadoArma ()
  (bind _inv (Variables|Components|GetInventory))
  (bind (_f _i) (Getters|FindItem _inv "%(flecha)s"))
  (bind (_fid _fit _fam) (Utilities|Struct|BreakFStoredItem (Getters|GetItemAtIndex _inv (select _f _i 0))))
  (return (Utilities|GetDisplayName (Variables|Default|GetArmaTemporal)) (Utilities|GetClassDisplayName (Utilities|GetClass (Variables|Default|GetArmaTemporal))) (Utilities|String|ToString(Float) (- (Utilities|Time|GetGameTimeInSeconds) (Variables|Default|GetTUltimoTemporal))) (Variables|Default|GetMotivoSalidaArma) (select _f (Utilities|String|ToString(Integer) _fam) "0") (Variables|Default|GetEnemigoOrigenArma)))
''' % {"flecha": FLECHA}

VARIABLES = [("EnemigoOrigenArma", "string", "", "")]
FUNCIONES = [("RegistrarOrigenArma", REGISTRAR), ("AvisarLanza", AVISAR),
             ("SustituirArmaTemporal", SUSTITUIR), ("DbgEstadoArma", ESTADO)]
SALIDAS_NUEVAS = [("Flechas", "string"), ("Origen", "string")]


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


def prevuelo(codigo, nombre, con_param=None):
    """`SustituirArmaTemporal` tiene parametro: en el scratch no existe, asi que
    la cabecera pasa a `()` y las referencias al parametro se sustituyen por un
    valor del mismo tipo — se prueban los NODOS, no el cableado del parametro.

    `RegistrarOrigenArma` y `DbgEstadoArma` NO se prevuelan: una es un Set de
    una variable propia y la otra un return multiple — el scratch no tiene sus
    salidas y el transform para fingirlas ya fallo una vez. Todos sus nodos
    estan probados en este mismo blueprint."""
    if nombre in ("RegistrarOrigenArma", "DbgEstadoArma"):
        return None
    g = {"refPath": BPP + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + nombre + " (NuevaArma)", "(fn " + nombre + " ()", 1)
    cuerpo = cuerpo.replace("(fn " + nombre + " ", "(fn " + SCRATCH + " ", 1)
    if con_param:
        cuerpo = cuerpo.replace(con_param, "(Variables|Default|GetArmaTemporal)")
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        vaciar(g)
        return m[:220]


def salidas_de(nombre):
    """Cuenta las salidas de datos del FunctionResult de un grafo."""
    g = {"refPath": BPP + ":" + nombre}
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        i = info(n)
        if "FunctionResult" in str(i["type_id"]) + n["refPath"]:
            return [p for p in i["input_pins"] if str(p["type_id"]) != "Exec"]
    return []


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
        out["variables"].append(nombre + " (creada)")

    if SCRATCH not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": SCRATCH})
    for nombre, _ in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
            out["escritas"].append("nuevo grafo -> " + nombre)

    for nombre, codigo in FUNCIONES:
        out["prevuelo"][nombre] = prevuelo(
            codigo, nombre, con_param="NuevaArma" if "NuevaArma" in codigo else None) or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado nada"
        return out

    # `RegistrarOrigenArma` es un grafo nuevo: su parametro de ENTRADA hay que
    # crearlo antes de poder escribir un cuerpo que lo use. Idempotente por
    # conteo de los pines de salida del FunctionEntry.
    g_reg = {"refPath": BPP + ":RegistrarOrigenArma"}
    entradas = []
    for n in bt("find_nodes", {"graph": g_reg, "title": ""}):
        i = info(n)
        if "FunctionEntry" in str(i["type_id"]) + n["refPath"]:
            entradas = [p for p in i["output_pins"] if str(p["type_id"]) != "Exec"]
    if not entradas:
        bt("add_function_param", {"graph": g_reg, "param_name": "Nombre",
                                  "param_type": "string", "input_param": True})
        out["escritas"].append("entrada nueva -> RegistrarOrigenArma.Nombre")

    # Las dos salidas nuevas de DbgEstadoArma, ANTES de reescribirla y solo si
    # faltan (add_function_param duplica si se relanza).
    actuales = salidas_de("DbgEstadoArma")
    out["salidas_antes"] = [str(p["name"]) for p in actuales]
    if len(actuales) < 4 + len(SALIDAS_NUEVAS):
        for pn, pt in SALIDAS_NUEVAS:
            bt("add_function_param", {"graph": {"refPath": BPP + ":DbgEstadoArma"},
                                      "param_name": pn, "param_type": pt,
                                      "input_param": False})
            out["escritas"].append("salida nueva -> " + pn)

    for nombre, codigo in FUNCIONES:
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    out["salidas_despues"] = [str(p["name"]) for p in salidas_de("DbgEstadoArma")]
    out["releido"] = {}
    for nombre, _ in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
