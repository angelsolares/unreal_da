# -*- coding: utf-8 -*-
"""BP_DA_MedidorDano: mide el daño enemigo DESDE DENTRO del juego.

    node ue.mjs script medidor_dano.py

POR QUE EXISTE. Medir el ritmo de daño desde fuera por MCP no funciona: cada llamada
tarda segundos y el combate cambia de fase dentro de una sola ventana. Se intento el
25/08 con `Stat.ReceivedHitCount` y dos ventanas sobre el MISMO combate dieron 12 golpes
en 7,4 s y 1 golpe en 21 s — un factor 35. Con esa varianza no se calibra nada, y de ahi
cuelgan la Guardia fuera de banda y la receta demasiado holgada.

COMO MIDE. Un actor colocado en el nivel que muestrea a 50 Hz (0,02 s) con un temporizador
DENTRO del juego. No hace falta engancharse a nada: DCS mete todo el daño por un embudo
unico, `BP_StatsManagerComponent.TakeDamage`, que sube `Stat.ReceivedHitCount` en 1 por
golpe y descuenta `Stat.Health.Current`. Muestreando esos dos stats salen los golpes
EXACTOS y el daño EXACTO, sin depender del arma ni del atacante. A 50 Hz no se escapa
ninguno: los ataques van separados por medio segundo largo.

SOLO LEE. Curar al jugador, arrancar y parar se hacen desde fuera por Python — nada de
eso necesita latencia baja, y asi el medidor no escribe en el estado de DCS ni se salta
su `OnStatChanged`.

POR INDICE, NO POR TAG. `Interface|GetStatValue` es un mensaje de interfaz y el escritor
del DSL NO sabe cablear su pin `self` (ni desde una variable de Actor ni en linea: da
"Could not connect pin ... to self"). La via que si pasa es el componente:
`Actor|GetComponentbyClass` -> `Class|BPStatsManagerComponent|GetStats` -> el array, y de
ahi `Utilities|Struct|BreakFStat`. Como es por indice, esta pasada VERIFICA los indices
contra el array vivo antes de escribir nada y aborta si DCS los ha movido.

USO EN PIE:
    medidor.call_method("Arrancar")
    ...dejar pelear...
    # y se leen las variables desde fuera: Golpes, DanoTotal, Intervalos, TInicio
"""
import json

RUTA = "/Game/DarkAngels/Blueprints/Debug/BP_DA_MedidorDano"
BPP = RUTA + ".BP_DA_MedidorDano"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeMedidor"
CLS_STATS = ("/Game/DynamicCombatSystem/DCS/Blueprints/Components/StatsManager/"
             "BP_StatsManagerComponent.BP_StatsManagerComponent_C")
AHORA = "(Utilities|Time|GetGameTimeinSeconds)"

# Los que se esperan encontrar; se verifican contra el array vivo antes de escribir.
INDICE_VIDA = 0
INDICE_GOLPES = 12

VARIABLES = [
    ("Midiendo", "bool", "false", ""),
    ("Intervalo", "float", "0.02", ""),
    ("IndiceVida", "int", str(INDICE_VIDA), ""),
    ("IndiceGolpes", "int", str(INDICE_GOLPES), ""),
    ("TInicio", "float", "0.0", ""),
    ("TUltimoGolpe", "float", "0.0", ""),
    ("UltimaVida", "float", "0.0", ""),
    ("UltimosGolpes", "float", "0.0", ""),
    ("Golpes", "float", "0.0", ""),
    ("DanoTotal", "float", "0.0", ""),
    ("EnGolpe", "bool", "false", ""),
    ("Intervalos", "float", "", "Array"),
]
PUBLICAS = ["Midiendo", "Intervalo", "IndiceVida", "IndiceGolpes", "EnGolpe",
            "Golpes", "DanoTotal", "Intervalos", "TInicio", "UltimaVida"]

_COMP = '(Actor|GetComponentbyClass (Game|GetPlayerCharacter 0) "%s")' % CLS_STATS
_ARR = '(Class|BPStatsManagerComponent|GetStats %s)' % _COMP


def _stat(indice_expr):
    """El BaseValue del stat que hay en ese indice del array."""
    return ('(bind (_tag _base _mod _cm _cn) (Utilities|Struct|BreakFStat '
            '(Utilities|Array|Get(acopy) %s %s)))' % (_ARR, indice_expr))


ARRANCAR = '''(fn Arrancar ()
  (bind (_tv _v _mv _cmv _cnv) (Utilities|Struct|BreakFStat
    (Utilities|Array|Get(acopy) %(arr)s (Variables|Default|GetIndiceVida))))
  (bind (_tg _g _mg _cmg _cng) (Utilities|Struct|BreakFStat
    (Utilities|Array|Get(acopy) %(arr)s (Variables|Default|GetIndiceGolpes))))
  (Variables|Default|SetUltimaVida _v)
  (Variables|Default|SetUltimosGolpes _g)
  (Variables|Default|SetGolpes 0.0)
  (Variables|Default|SetEnGolpe false)
  (Variables|Default|SetDanoTotal 0.0)
  (Utilities|Array|Clear (Variables|Default|GetIntervalos))
  (Variables|Default|SetTInicio %(ahora)s)
  (Variables|Default|SetTUltimoGolpe %(ahora)s)
  (Variables|Default|SetMidiendo true)
  (Utilities|Time|SetTimerbyFunctionName self "Muestrear"
    (Variables|Default|GetIntervalo) true)
  (return))
''' % {"arr": _ARR, "ahora": AHORA}

# El intervalo se guarda ENTERO, no solo la media: la varianza era el problema, y una
# media esconde justo lo que hay que ver.
# CUENTA POR CAIDAS DE VIDA, NO POR ReceivedHitCount — y esto no es un capricho.
# `Stat.ReceivedHitCount` NO es un total: `TakeDamage` lo sube en 1 y arma un
# temporizador de 4 s a `ResetRecentHit`, o sea que es un contador de golpes RECIENTES
# que vuelve a cero. Con una comparacion `>` se pierden todos los golpes posteriores a
# un reset: medido, 4 golpes reales dejaron UN solo intervalo registrado.
#
# La vida si es monotona mientras nadie cure. Un "golpe" es una racha contigua de
# muestras en las que la vida baja; `EnGolpe` evita contar dos veces un golpe que
# reparte su daño en varios fotogramas.
MUESTREAR = '''(fn Muestrear ()
  (if (Variables|Default|GetMidiendo)
    (bind (_tv _v _mv _cmv _cnv) (Utilities|Struct|BreakFStat
      (Utilities|Array|Get(acopy) %(arr)s (Variables|Default|GetIndiceVida))))
    (bind _delta (- (Variables|Default|GetUltimaVida) _v))
    (if (> _delta 0.0)
      (Variables|Default|SetDanoTotal (+ (Variables|Default|GetDanoTotal) _delta))
      (if (not (Variables|Default|GetEnGolpe))
        (Variables|Default|SetGolpes (+ (Variables|Default|GetGolpes) 1.0))
        (Utilities|Array|Add (Variables|Default|GetIntervalos)
          (- %(ahora)s (Variables|Default|GetTUltimoGolpe)))
        (Variables|Default|SetTUltimoGolpe %(ahora)s)
        (Variables|Default|SetEnGolpe true))
      (else
        (Variables|Default|SetEnGolpe false)))
    (Variables|Default|SetUltimaVida _v))
  (return))
''' % {"arr": _ARR, "ahora": AHORA}

FUNCIONES = [("Arrancar", ARRANCAR), ("Muestrear", MUESTREAR)]


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


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


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
    """El escritor del DSL tiene menos vocabulario que su lector, y `vaciar()` corre
    ANTES de escribir: sin prevuelo, un nodo que no existe deja la funcion en blanco."""
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
        return ("NO SE PUEDE ESCRIBIR: " + m[max(0, i - 80):i + 14]) if i > 0 else m[:220]


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
    # AddMemberVariable ignora el defaultValue (al menos en floats): se fija aparte.
    for nombre, _t, defecto, cont in VARIABLES:
        if defecto and not cont:
            vue("SetVariableDefaultValue", {"blueprintPath": RUTA, "variableName": nombre,
                                            "defaultValue": defecto})
    for nombre in PUBLICAS:
        bt("set_variable_instance_editable", {"blueprint": BP, "variable_name": nombre,
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
    st("save_assets", {"asset_paths": [RUTA]})

    out["releido"] = {}
    for nombre, _ in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))[:500]
    return out
