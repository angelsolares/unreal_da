# -*- coding: utf-8 -*-
#
# LO QUE LA ARENA SABE CONTARLE AL DEBUG HUD (§10): la linea por enemigo de la
# cadena tactica, y el resalte de los drops garantizados.
#
#   node ue.mjs script arena_hud.py
#
# ### QUE PIDE EL PDF
#
# Tres entradas del §10 que faltaban: "Show recommended tactical chain (DEBUG
# ONLY)", "Highlight Guaranteed Tactical Drops (DEBUG ONLY)" y el watchdog en
# pantalla. El watchdog no necesita nada de aqui — el HUD lee las variables de
# la arena directamente (GetEstado, GetHayVivos... los getters cruzados por
# Class|BPDAArena|GetX escriben bien; la nota vieja de que no se podia esta
# derogada por el propio generador, que los usa desde el 23/08).
#
# ### LA CADENA TACTICA ES LO QUE LA ARENA YA SABE
#
# No hay guion secreto: la cadena recomendada del encuentro SON las oleadas mas
# los drops garantizados — exactamente lo que el diseñador codifico en la receta
# y el exportador escribio en los actores. `DbgLineaEnemigo(i)` devuelve una
# linea ya formateada por enemigo:
#
#     O1  Forja_lancero_del_alba_...   *DROP GARANTIZADO*
#     O2  Forja_escudero_...           [MUERTO]
#
# y el HUD las pinta en bucle, como la lista de teleports. Garantizado =
# probabilidad entera Y algun permiso — la misma definicion que fijo la piedad
# del 26/08 ("garantizado es permiso Y probabilidad entera").
#
# ### EL RESALTE
#
# `DbgResaltarDrops()`: esfera y letrero de debug 4 s sobre cada enemigo VIVO
# con drop garantizado. DrawDebug*, asi que no existe en Shipping ni aunque el
# nivel se colara: DEBUG ONLY de verdad.

import json

BPP = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena.BP_DA_Arena"
RUTA = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Arena"
BP = {"refPath": BPP}
SCRATCH = "ZZProbeCol"

WD = ("/Game/DarkAngels/Blueprints/Combat/BP_DA_WeaponDropComponent."
      "BP_DA_WeaponDropComponent_C")
AZUL = '(Utilities|Struct|MakeLinearColor 0.3 0.62 1.0 1.0)'

GARANTIZADO = ('(and (>= (Class|BPDAWeaponDropComponent|GetProbabilidadDrop _comp) 1.0)'
               ' (or (Class|BPDAWeaponDropComponent|GetDropMainHandWeapon _comp)'
               ' (Class|BPDAWeaponDropComponent|GetDropOffHandWeapon _comp)))')

# OJO: `CanBeAttacked|IsAlive` es un nodo CON EXEC (llamada de interfaz), no un
# puro. Metido dentro de una expresion se crea con el execute SIN CONECTAR y
# devuelve false siempre — los cinco salian [MUERTO] con cuatro vivos. La cura
# es la de VigilarArena: izarlo a un `bind` en posicion de SENTENCIA.
LINEA = '''(fn DbgLineaEnemigo (Indice)
  (bind _e (Utilities|Array|Get(acopy) (Variables|Default|GetEnemigos) Indice))
  (bind _o (Utilities|Array|Get(acopy) (Variables|Default|GetOleadasEnemigos) Indice))
  (bind _comp (Utilities|Casting|CastToBP_DA_WeaponDropComponent (Actor|GetComponentByClass _e "%(wd)s")))
  (bind _gar %(gar)s)
  (bind _vivo (CanBeAttacked|IsAlive(Message) _e))
  (return (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append "O" (Utilities|String|ToString(Integer) _o)) "  ") (Utilities|GetDisplayName _e)) (select _vivo (select _gar "   *DROP GARANTIZADO*" "") "   [MUERTO]"))))
''' % {"wd": WD, "gar": GARANTIZADO}

RESALTAR = '''(fn DbgResaltarDrops ()
  (for _i (range (Utilities|Array|Length (Variables|Default|GetEnemigos)))
    (bind _e (Utilities|Array|Get(acopy) (Variables|Default|GetEnemigos) _i))
    (bind _comp (Utilities|Casting|CastToBP_DA_WeaponDropComponent (Actor|GetComponentByClass _e "%(wd)s")))
    (bind _gar %(gar)s)
    (bind _vivo (CanBeAttacked|IsAlive(Message) _e))
    (if (and _gar _vivo)
      (Rendering|Debug|DrawDebugSphere (+ (Transformation|GetActorLocation _e) (Math|Vector|MakeVector 0.0 0.0 110.0)) 70.0 12 %(azul)s 4.0)
      (Rendering|Debug|DrawDebugString (+ (Transformation|GetActorLocation _e) (Math|Vector|MakeVector 0.0 0.0 210.0)) "DROP GARANTIZADO" 0 %(azul)s 4.0))))
''' % {"wd": WD, "gar": GARANTIZADO, "azul": AZUL}

FUNCIONES = [("DbgLineaEnemigo", LINEA), ("DbgResaltarDrops", RESALTAR)]


def call(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


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


def pines_de(nombre, clase):
    g = {"refPath": BPP + ":" + nombre}
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        i = info(n)
        if clase in str(i["type_id"]) + n["refPath"]:
            lado = "output_pins" if clase == "FunctionEntry" else "input_pins"
            return [p for p in i[lado] if str(p["type_id"]) != "Exec"]
    return []


def prevuelo(codigo, nombre):
    g = {"refPath": BPP + ":" + SCRATCH}
    vaciar(g)
    cuerpo = codigo.replace("(fn " + nombre + " (Indice)", "(fn " + nombre + " ()", 1)
    cuerpo = cuerpo.replace("(fn " + nombre + " ", "(fn " + SCRATCH + " ", 1)
    cuerpo = cuerpo.replace(" Indice)", " 0)")
    cuerpo = cuerpo.replace("(return ", "(bind _zz ", 1)
    try:
        bt("write_graph_dsl", {"graph": g, "code": cuerpo})
        vaciar(g)
        return None
    except Exception as e:
        m = str(e)
        vaciar(g)
        return m[:220]


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo; parar antes de tocar blueprints"}
    out = {"prevuelo": {}, "escritas": [], "vaciados": {}}

    for nombre, _ in FUNCIONES:
        if nombre not in grafos():
            bt("add_function_graph", {"blueprint": BP, "graph_name": nombre})
            out["escritas"].append("nuevo grafo -> " + nombre)

    if not pines_de("DbgLineaEnemigo", "FunctionEntry"):
        bt("add_function_param", {"graph": {"refPath": BPP + ":DbgLineaEnemigo"},
                                  "param_name": "Indice", "param_type": "int",
                                  "input_param": True})
        out["escritas"].append("entrada -> Indice")
    if not pines_de("DbgLineaEnemigo", "FunctionResult"):
        bt("add_function_param", {"graph": {"refPath": BPP + ":DbgLineaEnemigo"},
                                  "param_name": "Linea", "param_type": "string",
                                  "input_param": False})
        out["escritas"].append("salida -> Linea")

    for nombre, codigo in FUNCIONES:
        out["prevuelo"][nombre] = prevuelo(codigo, nombre) or "OK"
    if any(v != "OK" for v in out["prevuelo"].values()):
        out["abortado"] = "el prevuelo fallo; no se ha tocado nada"
        return out

    for nombre, codigo in FUNCIONES:
        g = {"refPath": BPP + ":" + nombre}
        out["vaciados"][nombre] = vaciar(g)
        bt("write_graph_dsl", {"graph": g, "code": codigo})
        out["escritas"].append(nombre)

    bt("compile_blueprint", {"blueprint": BP})
    st("save_assets", {"asset_paths": [RUTA]})

    out["releido"] = {}
    for nombre, _ in FUNCIONES:
        out["releido"][nombre] = str(bt("read_graph_dsl", {"graph": {"refPath": BPP + ":" + nombre}}))
    return out
