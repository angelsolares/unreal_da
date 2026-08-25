# -*- coding: utf-8 -*-
"""Segunda pasada sobre BP_DA_Arena: despertar por proximidad, y el Oleada5 que faltaba.

    node ue.mjs script despertar_proximidad.py

La primera pasada esta en `oleadas_arena.py` y sigue siendo la buena para las cuatro
funciones de oleadas. Esta añade dos cosas.

1. EL TAG QUE NO SE LEIA. `LeerOleadas` solo reconocia `Oleada2/3/4`. La receta de
   «Romper la linea» se recompuso el 25/08 a CINCO oleadas de uno, asi que su quinto
   enemigo llevaba un `Oleada5` que nadie miraba: se leia como oleada 1 y arrancaba
   DESPIERTO, justo la pareja simultanea que la receta evita. Ahora se leen hasta
   `Oleada8`, que da margen sin coste.

2. DESPERTAR POR PROXIMIDAD. Escalonar de uno en uno deja a cuatro de los cinco
   quietos casi todo el encuentro, y uno de ellos plantado en mitad del claro. Ahora
   un dormido al que te acercas se levanta aunque su oleada no haya entrado.

EL RADIO NO ES LIBRE, y esto es lo que mas importa de este fichero. Al que despiertas
TE PERSIGUE y ya no lo despegas, asi que pasarse reconstruye la pareja simultanea que
la receta evita a proposito. Medido en la Forja, 400 partidas por politica sobre
«Romper la linea»:

      radio        gana a espada   a la vez   atascadas
        0                 98%          1          1
      150                 92%          2          1     <- el veredicto NO se mueve
      200                 90%          2          1
      250                 88%          3          6
      300                 84%          3         12
      700                 35%          4         12
   sin limite              0%          5          0

Por eso el valor por defecto son 150: la capsula de Malakh mide 42 de radio y la del
enemigo 50, o sea que a 150 centro a centro las superficies estan a 58 cm. Hay que
pasarle por encima. La variable es publica; subirla cuesta lo que dice la tabla.

DOS REGLAS QUE VIENEN DE LA PASADA ANTERIOR Y SIGUEN VALIENDO:

  - PREVUELO. Cada funcion se escribe primero en un grafo de usar y tirar. El
    escritor del DSL tiene MENOS vocabulario que su lector, y como `vaciar()` corre
    antes de escribir, un fallo deja la funcion en blanco.
  - `VigilarArena` NO SE REESCRIBE. Aqui solo se le INSERTA un nodo: la llamada entra
    entre la rama `else` del branch que compara el jugador y el `SetHayVivos` que abre
    la cuenta del watchdog. Ese punto es exactamente "sellada y con el jugador vivo",
    que es cuando tiene sentido mirar quien esta cerca.
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BPP = RUTA + ".BP_DA_Arena"
# Los toolsets de Epic quieren la ruta del OBJETO; los de VibeUE, la del paquete.
BP = {"refPath": BPP}
SCRATCH = "ZZProbeOleadas"
MAX_OLEADA_LEIBLE = 8


# `select` anidado porque no hay forma de construir el nombre del tag en el DSL;
# el porque completo esta en oleadas_arena.py.
def ola_de(e):
    expr = "1"
    for n in range(2, MAX_OLEADA_LEIBLE + 1):
        expr = '(select (Actor|ActorHasTag %s "Oleada%d") %d %s)' % (e, n, n, expr)
    return expr


ENEMIGO_I = '(Utilities|Array|Get(acopy) (Variables|Default|GetEnemigos) _index)'
OLEADA_I = '(Utilities|Array|Get(acopy) (Variables|Default|GetOleadasEnemigos) _index)'

LEER = '''(fn LeerOleadas ()
  (Utilities|Array|Clear (Variables|Default|GetOleadasEnemigos))
  (Variables|Default|SetMaxOleada 1)
  (for _e (Variables|Default|GetEnemigos)
    (bind _o %s)
    (Utilities|Array|Add (Variables|Default|GetOleadasEnemigos) _o)
    (if (> _o (Variables|Default|GetMaxOleada))
      (Variables|Default|SetMaxOleada _o)))
  (return))
''' % ola_de("_e")

# El guardia de "ya esta despierto" es OBLIGATORIO: sin el, RestartLogic se llamaria
# cada 0,5 s sobre un arbol ya corriendo y el enemigo no llegaria a rematar un golpe.
DESPERTAR = '''(fn DespertarPorProximidad ()
  (if (> (Variables|Default|GetRadioDespertar) 0.0)
    (bind _p (Game|GetPlayerCharacter 0))
    (Utilities|IsValid _p
      (:"Is Valid"
        (for _index (range (Utilities|Array|Length (Variables|Default|GetEnemigos)))
          (bind _e %(en)s)
          (if (and (> %(ola)s (Variables|Default|GetOleadaActual))
                   (not (Utilities|Array|ContainsItem (Variables|Default|GetEnemigosActivos) _e)))
            (if (< (Transformation|GetDistanceTo _e _p)
                   (Variables|Default|GetRadioDespertar))
              (Utilities|Array|Add (Variables|Default|GetEnemigosActivos) _e)
              (bind _c (AI|GetAIController :ControlledActor _e))
              (Utilities|IsValid _c
                (:"Is Valid"
                  (AI|Logic|RestartLogic :self _c)))))))))
  (return))
''' % {"en": ENEMIGO_I, "ola": OLEADA_I}

VARIABLES = [("RadioDespertar", "float", "150.0", "")]
PUBLICAS = ["RadioDespertar"]
FUNCIONES = [("LeerOleadas", LEER), ("DespertarPorProximidad", DESPERTAR)]


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
        i = m.find("does not exist")
        vaciar(g)
        return ("NO SE PUEDE ESCRIBIR: " + m[max(0, i - 70):i + 14]) if i > 0 else m[:200]


def enchufar():
    """Inserta la llamada en VigilarArena. Idempotente: si ya esta, no toca nada.

    El punto de insercion se busca POR FORMA, no por nombre de nodo: el branch cuya
    salida `else` va a un `SetHayVivos`. Ese es el camino "sellada y jugador vivo".
    """
    g = {"refPath": BPP + ":VigilarArena"}
    nodos = bt("find_nodes", {"graph": g, "title": ""})
    infos = bt("get_node_infos", {"nodes": nodos})
    # El sandbox del ProgrammaticToolset usa un dict estricto: `.get(k, default)`
    # revienta. Aqui se accede por clave y se comprueba con `in`.
    for i in infos:
        if "DespertarPorProximidad" in str(i["type_id"]):
            return "ya estaba enchufada"

    porRef = {}
    for i in infos:
        porRef[i["node"]["refPath"]] = i

    branch = None
    destino = None
    for i in infos:
        if str(i["type_id"]) != "Utilities|FlowControl|Branch":
            continue
        for p in i["output_pins"]:
            if p["name"] != "else":
                continue
            for c in p["connected_pins"]:
                ref = c["node"]["refPath"]
                if ref not in porRef:
                    continue
                d = porRef[ref]
                if str(d["type_id"]) == "|SetHayVivos":
                    branch, destino = i, d
    if branch is None:
        return "NO ENCONTRADO el punto de insercion (branch.else -> SetHayVivos)"

    pos = destino["position"]
    nuevo = bt("create_node", {"graph": g, "type_id": "CallFunction|DespertarPorProximidad",
                               "pos": {"x": int(pos["x"]) - 240, "y": int(pos["y"]) - 200}})

    salida = None
    for p in branch["output_pins"]:
        if p["name"] == "else":
            salida = p["pin_id"]
    entrada = None
    for p in destino["input_pins"]:
        if p["name"] == "execute":
            entrada = p["pin_id"]

    ni = info(nuevo)
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
    out = {"variables": [], "prevuelo": {}, "escritas": []}

    existentes = set(str(v["variableName"]) for v in vue("ListVariables", {"blueprintPath": RUTA}))
    for nombre, tipo, defecto, cont in VARIABLES:
        if nombre in existentes:
            out["variables"].append(nombre + " (ya estaba)")
        else:
            vue("AddMemberVariable", {"blueprintPath": RUTA, "variableName": nombre,
                                      "variableType": tipo, "defaultValue": defecto,
                                      "containerType": cont})
            out["variables"].append(nombre + " (creada)")
    # EL `defaultValue` DE AddMemberVariable NO ENTRA, al menos en floats: la variable
    # nacio con 700, que es el `RadioArena` que ya estaba en el Blueprint. Se fija
    # aparte y se relee mas abajo, porque este `true` tampoco quiere decir nada.
    for nombre, _tipo, defecto, _cont in VARIABLES:
        vue("SetVariableDefaultValue", {"blueprintPath": RUTA, "variableName": nombre,
                                        "defaultValue": defecto})

    # Nace privada, y entonces ni se ve en Details ni se puede tocar en la instancia.
    # OJO: esta llamada NO acepta la ruta de paquete que valen las demas; quiere la
    # del objeto (`...BP_DA_Arena.BP_DA_Arena`).
    for nombre in PUBLICAS:
        bt("set_variable_instance_editable", {"blueprint": BP,
                                              "variable_name": nombre,
                                              "instance_editable": True})

    if SCRATCH not in grafos():
        bt("add_function_graph", {"blueprint": BP, "graph_name": SCRATCH})

    for nombre, codigo in FUNCIONES:
        out["prevuelo"][nombre] = prevuelo(codigo, nombre) or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado ninguna funcion"
        return out

    for nombre, codigo in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
        g = {"refPath": BPP + ":" + nombre}
        vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    out["enchufe"] = enchufar()
    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    # Releer: el `true` de estas APIs solo dice que acepto la llamada.
    out["releido"] = {}
    out["releido"]["RadioDespertar (por defecto)"] = str(
        vue("GetVariableInfo", {"blueprintPath": RUTA, "variableName": "RadioDespertar", "outInfo": {}}))
    for nombre, _ in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    out["releido"]["VigilarArena"] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":VigilarArena"}}))
    return out
