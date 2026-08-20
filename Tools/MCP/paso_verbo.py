# -*- coding: utf-8 -*-
import json

# `VerboPaso`: la palabra que sale en el cartel de DCS cuando miras un
# `BP_DA_Paso`. Vive AQUI, en `BP_DA_GameState`, y no en el paso.
#
# POR QUE NO ES UNA VARIABLE DEL ACTOR (que es como lo hace
# `BP_DA_Interactuable` con su `Verbo`): porque la palabra depende del estado
# narrativo —si el paso esta sellado o abierto— y **el DSL no sabe crear el
# getter de una variable de OTRO blueprint**. Llamar a una funcion suya si. O
# sea que para que el texto pueda mirar los flags, el texto tiene que vivir
# junto a los flags. Es la misma razon por la que `Resumen` e `Historial` estan
# aqui y no en el HUD.
#
# Y HAY UN SEGUNDO MOTIVO, este de diseno: asi las TRES palabras de todos los
# pasos de Malkuth se cambian en un sitio. Si cada instancia llevara su cadena,
# renombrar "Sellado" seria repasar el mapa entero.
#
# EL REQUISITO VACIO ES "ABIERTO", no "cerrado". Un paso recien colocado, sin
# nada escrito en `Requisito`, funciona; sellarlo es una decision explicita. Al
# reves se colocarian pasos muertos sin enterarse.
#
# ### `Lleva` MIRA EN LOS DOS ALMACENES, Y ESO NO ES PEREZA
#
# El GameState guarda dos cosas distintas: `Flags` (ganchos de exploracion, los
# pone `MarcarFlag`) y `MarcaNombre` (el historico de decisiones, lo pone
# `AnotarMarca`). Un cerrojo puede colgar de cualquiera de las dos, y de hecho el
# primero que hay --la puerta de El Claro-- cuelga de una MARCA: se abre si
# llevas `FURIA`, que es la que anota `Decision_Sariel` al arrebatarle la llave.
#
# La alternativa era que la decision escribiera ademas un flag, y eso obligaba a
# **reescribir `Elegir` en `BP_DA_Decision`**, blueprint compartido cuyo script
# canonico (`decision_grafos.py`) ya NO coincide con el asset vivo: le faltan
# `ObjetoMalla`, `ObjetoItem` y la rama que mete la llave en la mochila.
# Regenerarlo habria sido una regresion silenciosa. Leyendo lo que la decision YA
# apunta no hay que tocar nada de nadie.
#
# `ContainsItem` en linea y no `TieneFlag`: una llamada a otra funcion PROPIA no
# devuelve valor por esta via (el grafo se lee perfecto y sale vacio), asi que
# se duplica la linea a proposito. Mismo apaño que ya tiene `LeerFuerza`.
#
# Y `select` en vez de `if` por lo mismo que `LeerFuerza`: `(return X)` dentro
# de las ramas de un `if` es otra de las que el DSL escribe y luego no devuelven
# nada. `select` es puro y deja un unico `return`.

BPP = "/Game/DarkAngels/Blueprints/World/BP_DA_GameState.BP_DA_GameState"
BP = {"refPath": BPP}

ABIERTO = "Cruzar"
FORZAR  = "Forzar"
SELLADO = "Sellado"

LLEVA = '''(fn Lleva (Nombre)
  (return (or (Utilities|Array|ContainsItem
                :TargetArray (Variables|Default|GetFlags) :ItemToFind Nombre)
              (Utilities|Array|ContainsItem
                :TargetArray (Variables|Default|GetMarcaNombre) :ItemToFind Nombre))))
'''

# Tres estados, no dos. `Abierta` es el flag que dice que este paso YA esta
# franqueado --lo pone forzarlo--, y por eso se mira antes que nada: una vez
# abierto da igual como llegaste.
#
# Todo va EN LINEA, sin llamar a `Lleva`, aunque queden seis `ContainsItem`
# repetidos. No es descuido: una llamada a otra funcion PROPIA no devuelve valor
# por esta via, y aqui el resultado tiene que llegar al `return`.
VERBO = '''(fn VerboPaso (Requerido Forzar Abierta)
  (bind _abierta (and (not (Utilities|String|IsEmpty Abierta))
                      (or (Utilities|Array|ContainsItem
                            :TargetArray (Variables|Default|GetFlags) :ItemToFind Abierta)
                          (Utilities|Array|ContainsItem
                            :TargetArray (Variables|Default|GetMarcaNombre)
                            :ItemToFind Abierta))))
  (bind _puede (or (Utilities|String|IsEmpty Requerido)
                   (or _abierta
                       (or (Utilities|Array|ContainsItem
                             :TargetArray (Variables|Default|GetFlags) :ItemToFind Requerido)
                           (Utilities|Array|ContainsItem
                             :TargetArray (Variables|Default|GetMarcaNombre)
                             :ItemToFind Requerido)))))
  (bind _forzar (and (not _puede)
                     (and (not (Utilities|String|IsEmpty Forzar))
                          (or (Utilities|Array|ContainsItem
                                :TargetArray (Variables|Default|GetFlags) :ItemToFind Forzar)
                              (Utilities|Array|ContainsItem
                                :TargetArray (Variables|Default|GetMarcaNombre)
                                :ItemToFind Forzar)))))
  (return (select _puede "%s" (select _forzar "%s" "%s"))))
''' % (ABIERTO, FORZAR, SELLADO)

FUNCIONES = [
    ("Lleva", [("Nombre", "string", True), ("Tiene", "bool", False)], LLEVA),
    ("VerboPaso", [("Requerido", "string", True), ("Forzar", "string", True),
                   ("Abierta", "string", True),
                   ("Verbo", "string", False)], VERBO),
]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def st(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def vaciar(g):
    """Deja la funcion con su entrada y su salida y nada mas.

    `write_graph_dsl` sobre una funcion con cuerpo NO lo reemplaza: **anade otra
    copia entera** y deja la anterior huerfana.
    """
    n = 0
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        tid = str(info(nodo)["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            continue
        bt("delete_node", {"node": nodo})
        n += 1
    return n


def params_puestos(g):
    """`add_function_param` no es idempotente: relanzar duplicaria los pines."""
    nombres = set()
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        i = info(nodo)
        tid = str(i["type_id"]) + nodo["refPath"]
        if "FunctionEntry" in tid or "FunctionResult" in tid:
            for lado in ("output_pins", "input_pins"):
                if lado not in i:
                    continue
                for p in i[lado]:
                    nombres.add(p["name"])
    return nombres


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {}

    for nombre, params, codigo in FUNCIONES:
        grafos = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": BP})]
        if nombre not in grafos:
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
        g = {"refPath": BPP + ":" + nombre}

        ya = params_puestos(g)
        for pn, pt, entrada in params:
            if pn in ya:
                continue
            bt("add_function_param", {"graph": g, "param_name": pn,
                                      "param_type": pt, "input_param": entrada})
        out["vaciados"] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": ["/Game/DarkAngels/Blueprints/World/BP_DA_GameState"]})

    # Releer siempre: el `true` de estas APIs solo dice que acepto la llamada.
    out["funciones"] = sorted([str(f["name"]) for f in bt("list_functions", {"blueprint": BP})])
    for _n in ("Lleva", "VerboPaso"):
        out[_n] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + _n}}))
    return out
