# -*- coding: utf-8 -*-
#
# ACTIVACION ESCALONADA EN `BP_DA_Arena` (§6 del PDF).
#
# La Forja ya sabe simular oleadas y midio que la receta 6.1 pasa del 0% al 94%
# con espada sola. Lo que faltaba era que el motor supiera hacerlo: sin esto,
# exportar la receta coloca a los cinco de golpe, que es el encuentro que se
# pierde siempre.
#
# ### DONDE VIVE EL NUMERO DE OLEADA: EN LOS TAGS DEL ACTOR
#
# No en una variable del AI. Los cinco enemigos heredan de `BP_BaseAI`, que es de
# DCS: meterle una variable seria una modificacion viva de un asset de pago, de
# las que DCS revierte sin avisar. Y ponerla en los cinco Blueprints propios
# serian cinco variables que mantener a la vez.
#
# Un Tag lo tiene TODO actor, se edita en el panel Details (Actor > Tags), lo
# escribe el exportador de la Forja sin tocar ningun asset, y funciona sobre
# enemigos ya colocados. `Oleada2`, `Oleada3`, `Oleada4`; sin tag = primera.
#
# ### PERO LOS TAGS SE LEEN UNA SOLA VEZ
#
# `ReiniciarEncuentro` —el reintento al morir— DESTRUYE y vuelve a spawnear a
# cada enemigo desde su clase, y el actor nuevo NO conserva los tags de la
# instancia. Por eso al sellar se vuelca el numero a `OleadasEnemigos`, un array
# paralelo a `Enemigos` que el reintento mantiene indice a indice, igual que ya
# hace con `TransformsEnemigos`. A partir de ahi nadie vuelve a mirar un tag.
#
# ### COMO SE DUERME UN ENEMIGO
#
# `StopLogic` / `RestartLogic` sobre el Behavior Tree: exactamente lo que ya hace
# el boton FREEZE IA del Debug HUD, que esta probado en juego. El que duerme
# sigue estando, se le puede matar y cuenta para la victoria, igual que en el
# simulador.
#
# ### LO QUE EL ESCRITOR DEL DSL NO SABE HACER, Y COSTO UNA PASADA EN FALSO
#
# Su catalogo es MAS CORTO QUE EL DE SU LECTOR. `read_graph_dsl` devuelve
# `Math|Vector|Vector_GetAbs` y `Utilities|NotEqual(Object)`, y `write_graph_dsl`
# no sabe crear ninguno de los dos. O sea que releer un grafo y volver a
# escribirlo NO es una operacion segura, y como `vaciar()` corre ANTES de
# escribir, el primer intento dejo `BuscarEnemigos` en blanco.
#
# De ahi las dos reglas de este script:
#   1. PREVUELO: cada funcion se escribe primero en un grafo de usar y tirar. Si
#      falla, no se toca la de verdad.
#   2. `VigilarArena` NO SE REESCRIBE. Usa un nodo de mensaje de interfaz
#      (`CanBeAttacked|IsAlive`) que el escritor no sabe cablear desde un pin de
#      Actor. Ese grafo se opera nodo a nodo desde `oleadas_vigilar.py`.

import json

BPP = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena.BP_DA_Arena"
RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BP = {"refPath": BPP}
BASE_AI = "/Game/DynamicCombatSystem/DCS/Blueprints/AI/BP_BaseAI.BP_BaseAI_C"

# El numero de oleada de un enemigo, leido de sus tags. Va EN LINEA y no en una
# funcion propia porque una llamada a otra funcion propia no devuelve valor por
# esta via — el mismo apaño documentado en `paso_verbo.py`.
OLA_DE = ('(select (Actor|ActorHasTag %(e)s "Oleada4") 4'
          ' (select (Actor|ActorHasTag %(e)s "Oleada3") 3'
          ' (select (Actor|ActorHasTag %(e)s "Oleada2") 2 1)))')

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
''' % (OLA_DE % {"e": "_e"})

# Idempotente a proposito: se la llama al sellar Y despues de cada reintento.
# Volver a parar un arbol ya parado no hace nada.
APLICAR = '''(fn AplicarOleadas ()
  (Variables|Default|SetOleadaActual 1)
  (Variables|Default|SetOleadaEnCamino false)
  (Utilities|Array|Clear (Variables|Default|GetEnemigosActivos))
  (for _index (range (Utilities|Array|Length (Variables|Default|GetEnemigos)))
    (if (> %(ola)s 1)
      (bind _c (AI|GetAIController :ControlledActor %(en)s))
      (Utilities|IsValid _c
        (:"Is Valid"
          (AI|Logic|StopLogic :self _c :Reason "Oleada pendiente")))
      (else
        (Utilities|Array|Add (Variables|Default|GetEnemigosActivos) %(en)s))))
  (return))
''' % {"ola": OLEADA_I, "en": ENEMIGO_I}

# El hueco entre oleadas. `OleadaEnCamino` es la guarda: el watchdog corre cada
# 0,5 s y sin ella pediria una oleada nueva en cada pasada.
PEDIR = '''(fn PedirSiguienteOleada ()
  (if (Variables|Default|GetOleadaEnCamino)
    (return))
  (Variables|Default|SetOleadaEnCamino true)
  (Utilities|Time|SetTimerbyFunctionName self "EntrarOleada"
    (Variables|Default|GetRetardoEntreOleadas))
  (return))
'''

ENTRAR = '''(fn EntrarOleada ()
  (Variables|Default|SetOleadaActual (+ (Variables|Default|GetOleadaActual) 1))
  (for _index (range (Utilities|Array|Length (Variables|Default|GetEnemigos)))
    (if (== %(ola)s (Variables|Default|GetOleadaActual))
      (Utilities|Array|Add (Variables|Default|GetEnemigosActivos) %(en)s)
      (bind _c (AI|GetAIController :ControlledActor %(en)s))
      (Utilities|IsValid _c
        (:"Is Valid"
          (AI|Logic|RestartLogic :self _c)))))
  (Variables|Default|SetOleadaEnCamino false)
  (return))
''' % {"ola": OLEADA_I, "en": ENEMIGO_I}

# --------------------------------------------------------------------------
# Los dos grafos que ya existian y se reescriben enteros.
#
# `BuscarEnemigos` va SIN `Vector_GetAbs`, que el escritor no sabe crear: el
# mismo cuadrado sale de comparar cada componente contra +R y -R. Es literalmente
# la misma condicion, escrita con nodos que si existen.

_LOC = ('(Math|Transform|InverseTransformLocation'
        ' (Transformation|GetActorTransform self)'
        ' (Transformation|GetActorLocation _e))')
_R = '(Variables|Default|GetRadioArena)'
_MENOS_R = '(- 0.0 (Variables|Default|GetRadioArena))'

BUSCAR = '''(fn BuscarEnemigos ()
  (if (Variables|Default|GetAutoDetectarEnemigos)
    (for _e (Actor|GetAllActorsOfClass "%(ai)s")
      (bind _lx (.x %(loc)s))
      (bind _ly (.y %(loc)s))
      (if (and (and (< _lx %(r)s) (> _lx %(mr)s))
               (and (< _ly %(r)s) (> _ly %(mr)s)))
        (Utilities|Array|AddUnique (Variables|Default|GetEnemigos) _e))))
  (CallFunction|LeerOleadas)
  (CallFunction|AplicarOleadas)
  (return))
''' % {"ai": BASE_AI, "loc": _LOC, "r": _R, "mr": _MENOS_R}

MORIR = '''(fn AlMorirElJugador ()
  (if (Variables|Default|GetReintentarAlMorir)
    (CallFunction|ReiniciarEncuentro)
    (CallFunction|AplicarOleadas)
    (else
      (CallFunction|RestaurarObjetivo)
      (CallFunction|Abrir)
      (CallFunction|ReponerEnemigos)
      (CallFunction|AplicarOleadas)
      (Variables|Default|SetEstado 0)))
  (return))
'''

VARIABLES = [
    ("OleadasEnemigos", "int", "", "Array"),
    ("EnemigosActivos", "AActor", "", "Array"),
    ("MaxOleada", "int", "1", ""),
]

FUNCIONES = [
    ("LeerOleadas", LEER),
    ("AplicarOleadas", APLICAR),
    ("PedirSiguienteOleada", PEDIR),
    ("EntrarOleada", ENTRAR),
    ("BuscarEnemigos", BUSCAR),
    ("AlMorirElJugador", MORIR),
]

SCRATCH = "ZZProbeOleadas"


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
    """`write_graph_dsl` sobre una funcion con cuerpo NO lo reemplaza: añade otra
    copia entera y deja la anterior huerfana."""
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def prevuelo(codigo, nombre):
    """Escribe el cuerpo en el grafo de usar y tirar, con el nombre de la funcion
    de destino cambiado. Si esto pasa, la pasada buena tambien."""
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
        return ("NO SE PUEDE ESCRIBIR: " + m[max(0, i - 70):i + 14]) if i > 0 else m[:160]


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

    # 1. PREVUELO ENTERO. Si algo no se puede escribir, no se toca nada.
    for nombre, codigo in FUNCIONES:
        fallo = prevuelo(codigo, nombre)
        out["prevuelo"][nombre] = fallo or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado ninguna funcion"
        return out

    # 2. La pasada buena.
    for nombre, codigo in FUNCIONES:
        if nombre not in grafos():
            creado = bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
            out["escritas"].append("nuevo grafo -> " + str(creado))
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    # 3. Releer siempre: el `true` de estas APIs solo dice que acepto la llamada.
    out["releido"] = {}
    for nombre, _ in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
