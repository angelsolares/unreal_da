import json
BT = "editor_toolset.toolsets.blueprint.BlueprintTools."
VE = "/Game/DarkAngels/Blueprints/Combat/BP_DA_Vetas.BP_DA_Vetas"
STATS = "/Game/DynamicCombatSystem/DCS/Blueprints/Components/StatsManager/BP_StatsManagerComponent.BP_StatsManagerComponent_C"
BASEAI = "/Game/DynamicCombatSystem/DCS/Blueprints/AI/BP_BaseAI.BP_BaseAI_C"
out = {}


def bt(t, a):
    r = execute_tool(BT + t, json.dumps(a))
    return r["returnValue"] if isinstance(r, dict) and "returnValue" in r else r


def grafos():
    return [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": {"refPath": VE}})]


def variables():
    return [str(v) for v in bt("list_variables", {"blueprint": {"refPath": VE}})]


def fn(nombre, code):
    g = {"refPath": VE + ":" + nombre}
    if nombre in grafos():
        for nodo in bt("find_nodes", {"graph": g, "title": ""}):
            if "FunctionEntry" in nodo["refPath"] or "FunctionResult" in nodo["refPath"]:
                continue
            bt("delete_node", {"node": nodo})
    else:
        bt("add_function_graph", {"blueprint": {"refPath": VE}, "graph_name": nombre})
    bt("write_graph_dsl", {"graph": g, "code": code})
    out[nombre] = "escrita"


def run():
    vs = variables()
    for n, t in (("EnemigosVivosAhora", "int"), ("EnemigosVivosPrev", "int"),
                 ("CuraCadena", "float"), ("RadioCadena", "float")):
        if n not in vs:
            bt("add_variable", {"blueprint": {"refPath": VE}, "name": n, "type_name": t})
            out["var " + n] = "creada"
    bt("compile_blueprint", {"blueprint": {"refPath": VE}})

    # Sello 2 (Corrupto): con Masacre activa, cada baja en cadena cura un 10 %.
    # Se cuenta por latido en vez de engancharse a la muerte del enemigo, porque
    # Kill es del padre de DCS y no se puede sobrescribir por DSL.
    fn("CurarCadena", """
(fn CurarCadena ()
  (bind _jug (Game|GetPlayerCharacter 0))
  (Utilities|IsValid _jug
    (:"Is Valid"
      (bind _sm (Actor|GetComponentByClass _jug "%s"))
      (bind _loc (Transformation|GetActorLocation _jug))
      (Variables|Default|SetEnemigosVivosAhora 0)
      (for _e (Actor|GetAllActorsOfClass "%s")
        (if (< (Math|Vector|Distance(Vector) _loc (Transformation|GetActorLocation _e)) (Variables|Default|GetRadioCadena))
          (bind _vivo (CanBeAttacked|IsAlive(Message) _e))
          (if _vivo
            (Variables|Default|SetEnemigosVivosAhora (+ (Variables|Default|GetEnemigosVivosAhora) 1)))))
      (if (and (and (== (Variables|Default|GetSello) 2) (Variables|Default|GetMasacreActiva))
               (and (>= (Variables|Default|GetEnemigosVivosPrev) 0)
                    (< (Variables|Default|GetEnemigosVivosAhora) (Variables|Default|GetEnemigosVivosPrev))))
        (Interface|ModifyStat _sm "(TagName=\\"Stat.Health.Current\\")"
          (* (* (Interface|GetStatValue _sm "(TagName=\\"Stat.Health.Max\\")") (Variables|Default|GetCuraCadena))
             (Math|Conversions|ToFloat(Integer) (- (Variables|Default|GetEnemigosVivosPrev) (Variables|Default|GetEnemigosVivosAhora))))))
      (Variables|Default|SetEnemigosVivosPrev (Variables|Default|GetEnemigosVivosAhora)))
    (:"Is Not Valid")))
""" % (STATS, BASEAI))

    # el latido no se toca: la cura va en su propio temporizador
    g = {"refPath": VE + ":EventGraph"}
    for nodo in bt("find_nodes", {"graph": g, "title": ""}):
        bt("delete_node", {"node": nodo})
    bt("write_graph_dsl", {"graph": g, "code": """
(event EventBeginPlay
  (Utilities|Time|SetTimerbyFunctionName self "Latir" 0.25 true)
  (Utilities|Time|SetTimerbyFunctionName self "CurarCadena" 0.25 true))
"""})
    out["EventGraph"] = "reescrito"
    r = execute_tool(BT + "compile_blueprint", json.dumps({"blueprint": {"refPath": VE}}))
    out["compile"] = str(r)[:120]
    out["CurarCadena releida"] = bt("read_graph_dsl", {"graph": {"refPath": VE + ":CurarCadena"}})
    out["EventGraph releido"] = bt("read_graph_dsl", {"graph": g})
    return out
