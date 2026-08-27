# -*- coding: utf-8 -*-
"""§8 del PDF: el director de drops.

    node ue.mjs script director_drops.py

EL PDF pide cuatro politicas —Guaranteed Tactical / Standard Opportunity / Mercy Drop /
No Drop— y hasta hoy `BP_DA_WeaponDropComponent` tenia **dos booleanos por mano y nada
mas**: determinista, sin probabilidad, sin contexto y sin piedad.

LAS CUATRO POLITICAS CABEN EN DOS NUMEROS, y se hace asi a proposito en vez de con un
enum. Un enum obliga a comparar valores de enum dentro del DSL, que es justo donde el
escritor tiene menos vocabulario, y a cambio no expresa nada que estos dos campos no
expresen ya:

    Guaranteed Tactical   ProbabilidadDrop 1.0
    Standard Opportunity  ProbabilidadDrop 0.5   (el mismo 0,5 que declara armas.json)
    Mercy Drop            PiedadActiva true, con la probabilidad que sea
    No Drop               ProbabilidadDrop 0.0

**El defecto es 1.0, o sea que sin tocar nada el comportamiento es el de hoy**, que para
las recetas guionizadas esta bien y no se quiere perder.

LA PIEDAD, MEDIDA CONTRA EL CONTRATO. `armas.json` ya declara la regla en su seccion
`reglas.piedad`: `segundosSinArma: 35` y `vidaPorDebajoDe: 0.5`. Se copian esos dos
numeros para que el motor y el simulador digan lo mismo. El umbral de vida va en PUNTOS
ABSOLUTOS (50) y no en fraccion porque leer la vida maxima de DCS pide un campo del
struct que no esta identificado; Malakh tiene 100 de vida base, asi que 50 es ese 0,5.

DE DONDE SALE "CUANTO LLEVA SIN ARMA". De `TUltimoTemporal`, el sello de tiempo que
`SustituirArmaTemporal` anota en el jugador (ver `regla_dos_manos.py`). Vale -1 mientras
no haya tocado ninguna, y entonces "ahora menos -1" es un numero enorme: el jugador que
nunca ha tenido herramienta cuenta como el que mas la necesita, que es lo que se quiere.

DONDE SE MIDE LA DECISION. En el EventGraph, justo detras del `SetDropped` que marca la
muerte del dueño y antes de que se reparta nada — que es cuando la piedad tiene que mirar
como esta el jugador. La llamada se inserta con cirugia de nodos y por FORMA (el unico
`SetDropped` del grafo), no por nombre de nodo, para que aguante renumeraciones.

La decision es UNA por enemigo, no una por mano: `AplicarPolitica` tira el dado una sola
vez y con el resultado apaga los dos permisos. Esto importa para el Vigilante, que es el
unico que suelta la mano izquierda.
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_WeaponDropComponent"
BPP = RUTA + ".BP_DA_WeaponDropComponent"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeDirector"

CLS_STATS = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/StatsManager/"
             "BP_StatsManagerComponent.BP_StatsManagerComponent_C")
JUGADOR = "(Game|GetPlayerCharacter 0)"
AHORA = "(Utilities|Time|GetGameTimeinSeconds)"

VARIABLES = [
    ("ProbabilidadDrop", "float", "1.0"),
    ("PiedadActiva", "bool", "false"),
    ("SegundosSinArma", "float", "35.0"),
    ("VidaPiedad", "float", "50.0"),
]
PUBLICAS = ["ProbabilidadDrop", "PiedadActiva", "SegundosSinArma", "VidaPiedad"]

# La misma via que usa el medidor de daño, que esta probada: el mensaje de interfaz
# `GetStatValue` no se puede cablear por DSL, asi que se va por el componente y el indice.
_COMP = '(Actor|GetComponentbyClass %s "%s")' % (JUGADOR, CLS_STATS)
_ARR = '(Class|BPStatsManagerComponent|GetStats %s)' % _COMP
INDICE_VIDA = 0

# TODO EN UNA SOLA FUNCION SIN RETORNO, Y NO ES POR GUSTO.
#
# La version limpia eran tres funciones —`JugadorNecesitaArma`, `DebeSoltar` y
# `AplicarPolitica`— encadenadas. **El escritor del DSL no sabe crear el pin de retorno de
# una funcion**: al escribirlas salieron las dos primeras VACIAS, sin `ReturnNode`, y la
# tercera fallo con "expression produced no output pin" al intentar leer su resultado.
# Comprobado contra DCS, cuyas funciones si tienen `|ReturnNode` con pin `ReturnValue`:
# eso lo pone quien declara la funcion, y `add_function_graph` no declara salidas.
#
# La forma que si pasa es esta: una funcion VOID cuyo cuerpo son expresiones puras. No
# hace falta ningun retorno porque lo unico que hay que hacer al final es escribir dos
# variables, y eso es una sentencia, no un valor.
#
# NO SE PUEDE REESCRIBIR "DropOne", y por eso la decision entra por aqui y no envolviendo
# la accion. Su cuerpo usa un SpawnActor, que el LECTOR del DSL representa como
# "Game|SpawnActorBPDADroppedWeapon" pero el ESCRITOR no sabe crear: probado, y el prevuelo
# lo canta. Es la asimetria de siempre entre los dos.
#
# Asi que en vez de envolver la accion se apaga el PERMISO antes de que llegue: los dos
# booleanos que ya deciden que mano suelta se ponen a false si el director dice que no, y
# los "if" que ya existen en el EventGraph se saltan solos. Sin ramas nuevas y sin tocar
# "DropOne".
#
# SI LA PARTIDA NO TIENE JUGADOR VALIDO el cast falla, `GetTUltimoTemporal` devuelve 0 y
# "ahora - 0" es un numero grande: la piedad se dispara. Es el fallo benigno a proposito —
# ante la duda, repartir— y ademas en juego no pasa nunca.
APLICAR = '''(fn AplicarPolitica ()
  (bind (_tag _vida _mod _cm _cn) (Utilities|Struct|BreakFStat
    (Utilities|Array|Get(acopy) %(arr)s %(iv)d)))
  (bind _p (Utilities|Casting|CastToBP_DA_PlayerCharacter %(jug)s))
  (bind _necesita (and (Variables|Default|GetPiedadActiva)
                       (and (> (- %(ahora)s (Class|BPDAPlayerCharacter|GetTUltimoTemporal _p))
                               (Variables|Default|GetSegundosSinArma))
                            (< _vida (Variables|Default|GetVidaPiedad)))))
  (bind _suelta (or _necesita
                    (<= (Math|Random|RandomFloat) (Variables|Default|GetProbabilidadDrop))))
  (Variables|Default|SetDropMainHandWeapon (and (Variables|Default|GetDropMainHandWeapon) _suelta))
  (Variables|Default|SetDropOffHandWeapon (and (Variables|Default|GetDropOffHandWeapon) _suelta)))
''' % {"arr": _ARR, "iv": INDICE_VIDA, "jug": JUGADOR, "ahora": AHORA}

FUNCIONES = [("AplicarPolitica", APLICAR, [])]

# Restos del intento anterior: se vacian para que no dejen nodos sueltos que ensucien la
# compilacion. Si algun dia el escritor aprende a declarar salidas, aqui es donde volveria
# a partirse en tres.
A_VACIAR = ["JugadorNecesitaArma", "DebeSoltar"]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def vue(t, a):
    return call("VibeUE.BlueprintService." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def grafos():
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]


def vaciar(g):
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(bt("get_node_infos", {"nodes": [nodo]})[0]["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})


def prevuelo(codigo, nombre, params):
    """Sin esto, un nodo que no existe deja la funcion EN BLANCO, porque `vaciar()` corre
    antes de escribir. Y aqui `DropOne` ya funciona: perderla es peor que no tocar nada.
    Los parametros se cambian por un local porque el grafo de pruebas no los tiene: lo
    que se comprueba es el VOCABULARIO, no la firma."""
    g = {"refPath": BPP + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + nombre + " ", "(fn " + SCRATCH + " ", 1)
    if params:
        # Fuera la lista de parametros entera, y los usos a un local. De larga a corta,
        # que si no "Item" se come la mitad de "WeaponItem".
        cuerpo = "(fn " + SCRATCH + " ()" + cuerpo[cuerpo.index(")") + 1:]
        for p in sorted(params, key=len, reverse=True):
            cuerpo = cuerpo.replace(p, "_local")
        # Y hay que DARLE valor: el banco no tiene los parametros, asi que sin este bind
        # el escritor se queja de variable indefinida y esconde el error que si importa.
        # Se ata al OWNER, no a `self`: los parametros de `DropOne` son actores y `self`
        # aqui es un componente, asi que atarlo a self hace fallar el cableado por tipo
        # y esconde el error que si importa.
        cuerpo = cuerpo.replace("(fn " + SCRATCH + " ()",
                                "(fn " + SCRATCH + " ()\n  (bind _local (Components|GetOwner))", 1)
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        vaciar(g)
        i = m.find("does not exist")
        if i > 0:
            return "NO SE PUEDE ESCRIBIR: " + m[max(0, i - 90):i + 14]
        return m[:300]


def enchufar():
    """Mete la llamada a AplicarPolitica en el EventGraph, detras del SetDropped.

    Se busca POR FORMA —el unico setter de `Dropped` del grafo— y no por nombre de nodo,
    para que aguante renumeraciones. Idempotente: si la llamada ya esta, no toca nada.
    """
    GRAFO = {"refPath": BPP + ":EventGraph"}
    nodos = bt("find_nodes", {"graph": GRAFO, "title": ""})
    infos = bt("get_node_infos", {"nodes": nodos})
    for i in infos:
        if "AplicarPolitica" in str(i["type_id"]):
            return "ya estaba enchufada"

    porRef = {}
    for i in infos:
        porRef[i["node"]["refPath"]] = i

    origen = None
    for i in infos:
        if str(i["type_id"]) == "|SetDropped":
            origen = i
    if origen is None:
        return "NO ENCONTRADO el SetDropped del EventGraph"

    salida = None
    siguiente = None
    for pin in origen["output_pins"]:
        if pin["name"] != "then":
            continue
        salida = pin["pin_id"]
        for conectado in pin["connected_pins"]:
            ref = conectado["node"]["refPath"]
            if ref in porRef:
                siguiente = porRef[ref]
    if salida is None or siguiente is None:
        return "el SetDropped no tiene a quien encadenar"

    entrada = None
    for pin in siguiente["input_pins"]:
        if pin["type_id"] == "Exec" and pin["name"] in ("execute", "then"):
            entrada = pin["pin_id"]
    if entrada is None:
        return "el nodo siguiente no tiene pin de ejecucion de entrada"

    pos = origen["position"]
    nuevo = bt("create_node", {"graph": GRAFO, "type_id": "CallFunction|AplicarPolitica",
                               "pos": {"x": int(pos["x"]) + 140, "y": int(pos["y"]) + 220}})
    ni = bt("get_node_infos", {"nodes": [nuevo]})[0]
    pin_in = None
    pin_out = None
    for pin in ni["input_pins"]:
        if pin["type_id"] == "Exec":
            pin_in = pin["pin_id"]
    for pin in ni["output_pins"]:
        if pin["type_id"] == "Exec":
            pin_out = pin["pin_id"]
    if pin_in is None or pin_out is None:
        return "el nodo nuevo no tiene pines de ejecucion"

    bt("break_pins", {"output_pin": salida, "input_pin": entrada})
    bt("connect_pins", {"output_pin": salida, "input_pin": pin_in})
    bt("connect_pins", {"output_pin": pin_out, "input_pin": entrada})
    return "enchufada"


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"variables": [], "prevuelo": {}, "escritas": []}

    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": RUTA}))
    for nombre, tipo, defecto in VARIABLES:
        if nombre in existentes:
            out["variables"].append(nombre + " (ya estaba)")
        else:
            vue("AddMemberVariable", {"blueprintPath": RUTA, "variableName": nombre,
                                      "variableType": tipo, "defaultValue": defecto,
                                      "containerType": ""})
            out["variables"].append(nombre + " (creada)")
        # AddMemberVariable ignora el defaultValue: se fija aparte.
        vue("SetVariableDefaultValue", {"blueprintPath": RUTA, "variableName": nombre,
                                        "defaultValue": defecto})
    for nombre in PUBLICAS:
        bt("set_variable_instance_editable", {"blueprint": BP, "variable_name": nombre,
                                              "instance_editable": True})

    # LOS GRAFOS, ANTES DEL PREVUELO. "DebeSoltar" llama a "JugadorNecesitaArma" y
    # "AplicarPolitica" a "DebeSoltar": una funcion que todavia no existe no tiene nodo que
    # crear, y el prevuelo la cantaria como vocabulario ausente cuando lo unico que pasa es
    # que aun no le ha tocado el turno.
    for nombre, _c, _p in [(SCRATCH, None, None)] + FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})

    out["copiaDeSeguridad"] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":EventGraph"}}))

    out["vaciadas"] = []
    for nombre in A_VACIAR:
        if nombre in grafos():
            vaciar({"refPath": BPP + ":" + nombre})
            out["vaciadas"].append(nombre)

    # PREVUELO Y ESCRITURA VAN JUNTOS, FUNCION A FUNCION Y EN ORDEN DE DEPENDENCIA.
    # Probarlas todas primero no funciona aqui: `AplicarPolitica` hace
    # `(bind _suelta (CallFunction|DebeSoltar))` y una funcion VACIA todavia no tiene pin
    # de retorno, asi que el banco se queja de que la expresion no produce salida. Hay que
    # escribir `DebeSoltar` antes de poder siquiera probar a quien la llama.
    #
    # Se puede hacer asi porque las tres son NUEVAS: aqui no hay nada que perder si una
    # falla a mitad. La lista esta ordenada de hoja a raiz a proposito.
    for nombre, codigo, params in FUNCIONES:
        fallo = prevuelo(codigo, nombre, params)
        out["prevuelo"][nombre] = fallo or "OK"
        if fallo:
            out["abortado"] = "fallo el prevuelo de " + nombre
            return out
        g = {"refPath": BPP + ":" + nombre}
        vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        bt("compile_blueprint", {"blueprint": BP})
        out["escritas"].append(nombre)

    out["enchufe"] = enchufar()

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    out["releido"] = {}
    for nombre, _c, _p in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))[:1200]
    return out
