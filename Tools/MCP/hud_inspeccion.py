import json

# El cartel "ESC para salir" mientras se esta inspeccionando un objeto.
#
# COMO SABE EL HUD QUE ESTAMOS DENTRO, sin que nadie se lo cuente: comparando
# el **view target** del PlayerController con el pawn. Si no coinciden, es que
# la camara esta puesta en otro actor, o sea que estamos inspeccionando. Asi no
# hace falta que `BP_DA_Interactuable` le escriba nada al HUD —que seria una
# llamada con pin Target, justo lo que el DSL no sabe hacer— y ademas el cartel
# sale con cualquier cosa que robe la camara en el futuro.
#
# Reparto habitual: el tick va montado NODO A NODO porque necesita Targets, y
# el dibujado por DSL porque solo pinta sobre `self`.
#
# El cartel va a 0,88 de alto; el banner de zona esta a 0,72, para que no choquen.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
TICK = "Inspeccion_Tick"
DIBUJAR = "Inspeccion_Dibujar"
VAR = "Inspeccionando"
TEXTO = "ESC para salir"
ALTO = 0.88
ESCALA = 1.6


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t, json.dumps(a))["returnValue"]


def nodo(g, tipo, x, y):
    return bt("create_node", {"graph": g, "type_id": tipo, "pos": {"x": x, "y": y}})


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def pin(n, direccion, nombre):
    clave = "input_pins" if direccion == "EGPD_Input" else "output_pins"
    for p in info(n)[clave]:
        if p["name"] == nombre:
            return p["pin_id"]
    raise RuntimeError("sin pin " + nombre + " en " + str(info(n)["type_id"]))


def ent(n, nombre):
    return pin(n, "EGPD_Input", nombre)


def sal(n, nombre):
    return pin(n, "EGPD_Output", nombre)


def unir(a, b):
    bt("connect_pins", {"output_pin": a, "input_pin": b})


def dsl_dibujar():
    med = '(HUD|GetTextSize self "%s" 0 %.2f)' % (TEXTO, ESCALA)
    return "\n".join([
        "(fn " + DIBUJAR + " ()",
        "  (bind sx (.x (Viewport|GetViewportSize)))",
        "  (bind sy (.y (Viewport|GetViewportSize)))",
        "  (bind w " + med + ")",
        "  (bind x0 (- (* sx 0.5) (* w 0.5)))",
        "  (bind y0 (* sy %.2f))" % ALTO,
        "  (if (Variables|Default|Get" + VAR + ")",
        '    (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 0.01 0.01 0.05 0.72)'
        ' (- x0 28.0) (- y0 14.0) (+ w 56.0) (+ ' + med + ' 28.0))',
        '    (HUD|DrawText self "%s" (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 1.0)'
        ' x0 y0 0 %.2f)))' % (TEXTO, ESCALA),
    ])


def construir_tick(g):
    """view target != pawn  ->  Inspeccionando"""
    entrada = None
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        if "FunctionEntry" in str(info(n)["type_id"]) or "FunctionEntry" in n["refPath"]:
            entrada = n
            break
    if entrada is None:
        return "no se encontro el nodo de entrada"

    pc = nodo(g, "Game|GetPlayerController", -800, 200)
    vista = nodo(g, "Pawn|GetViewTarget", -600, 200)
    pawn = nodo(g, "Game|GetPlayerCharacter", -800, 320)
    distinto = nodo(g, "Utilities|Operators|NotEqual(!=)", -350, 250)
    marcar = nodo(g, "Variables|Default|Set" + VAR, -100, 0)

    unir(sal(pc, "ReturnValue"), ent(vista, "self"))
    unir(sal(vista, "ReturnValue"), ent(distinto, "A"))
    unir(sal(pawn, "ReturnValue"), ent(distinto, "B"))
    unir(sal(distinto, "ReturnValue"), ent(marcar, VAR))
    unir(info(entrada)["output_pins"][0]["pin_id"], ent(marcar, "execute"))
    return "montado"


def tipo_llamada(g, nombre):
    """El type_id de llamar a una funcion propia: se busca en vez de adivinarlo,
    que el nombre pierde los guiones bajos (`CallFunction|InspeccionTick`)."""
    for t in bt("find_node_types", {"graph": g, "type_id_filter": nombre.replace("_", ""),
                                    "context_pins": []}):
        return t
    return nombre


def enganchar(bp):
    eg = {"refPath": BP + ":EventGraph"}
    res = {}
    for marca, funcion, x, y in (("ReceiveDrawHUD", DIBUJAR, 400, 1900),
                                 ("ReceiveTick", TICK, 400, 2300)):
        ev = None
        for n in bt("find_nodes", {"graph": eg, "title": ""}):
            if marca in n["refPath"] or marca in str(info(n)["type_id"]):
                ev = n
                break
        if ev is None:
            res[marca] = "evento no encontrado"
            continue
        llamada = nodo(eg, tipo_llamada(eg, funcion), x, y)
        # Lo que ya colgaba del evento se reengancha detras de la llamada nueva.
        seguia = None
        for p in info(ev)["output_pins"]:
            if p["name"] in ("then", "Then") and p["connected_pins"]:
                seguia = p["connected_pins"][0]
                break
        salida_ev = None
        for p in info(ev)["output_pins"]:
            if p["name"] in ("then", "Then"):
                salida_ev = p["pin_id"]
        unir(salida_ev, ent(llamada, "execute"))
        if seguia is not None:
            unir(sal(llamada, "then"), seguia)
        res[marca] = "enganchado" + ("" if seguia is None else " y reencadenado")
    return res


def run():
    bp = {"refPath": BP}
    out = {}

    if VAR not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": VAR, "type_name": "bool"})

    existentes = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": bp})]
    for nom in (TICK, DIBUJAR):
        if nom in existentes:
            bt("remove_function_graph", {"blueprint": bp, "graph_name": nom})

    bt("add_function_graph", {"blueprint": bp, "graph_name": DIBUJAR})
    bt("write_graph_dsl", {"graph": {"refPath": BP + ":" + DIBUJAR}, "code": dsl_dibujar()})
    out["dibujar"] = "escrita por DSL"

    bt("add_function_graph", {"blueprint": bp, "graph_name": TICK})
    out["tick"] = construir_tick({"refPath": BP + ":" + TICK})

    out["enganche"] = enganchar(bp)
    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))
    out["compila"] = "SI"
    return out
