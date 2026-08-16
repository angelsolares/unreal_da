import json

# Dibuja el dialogo del interactuable que se esta inspeccionando.
#
# COMO SABE EL HUD QUE TEXTO TOCA, sin que nadie se lo diga: le pregunta al
# **view target** del PlayerController. Mientras dura el modo inspeccion la
# camara esta puesta en el propio actor interactuable, asi que basta con hacerle
# un Cast y leerle sus variables. Si el cast falla —la camara esta en el pawn,
# o sea que no estamos dentro— se limpia el texto y no se dibuja nada.
#
# TRES LINEAS SUELTAS Y NO UNA CADENA LARGA: `HUD|DrawText` no parte el texto,
# y no hay nodo de ajuste de linea. Con tres campos el corte lo decide quien
# escribe el dialogo, que ademas es como se controla el ritmo de una frase.
#
# Reparto de siempre: el tick va NODO A NODO porque necesita pines Target, y el
# dibujado por DSL porque solo pinta sobre `self`.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
EG = {"refPath": BP + ":EventGraph"}
TICK = "Dialogo_Tick"
DIBUJAR = "Dialogo_Dibujar"

LINEAS = ["Dia1", "Dia2", "Dia3"]
ALTO = 0.70        # el banner de zona esta en 0,72; esto arranca justo encima
INTERLINEA = 0.045
ESCALA = 1.45


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
    raise RuntimeError("sin pin '" + nombre + "' en " + str(info(n)["type_id"]))


def ent(n, nombre):
    return pin(n, "EGPD_Input", nombre)


def sal(n, nombre):
    return pin(n, "EGPD_Output", nombre)


def unir(a, b):
    bt("connect_pins", {"output_pin": a, "input_pin": b})


def valor(p, v):
    bt("set_pin_value", {"pin": p, "value": v})


def dsl_dibujar():
    l = ["(fn " + DIBUJAR + " ()",
         "  (bind sx (.x (Viewport|GetViewportSize)))",
         "  (bind sy (.y (Viewport|GetViewportSize)))"]
    for i, v in enumerate(LINEAS):
        y = ALTO + i * INTERLINEA
        l += ["  (bind t%d (Variables|Default|Get%s))" % (i, v),
              "  (bind w%d (HUD|GetTextSize self t%d 0 %.2f))" % (i, i, ESCALA),
              '  (HUD|DrawText self t%d (Utilities|Struct|MakeLinearColor 0.94 0.93 0.88 1.0)'
              ' (- (* sx 0.5) (* w%d 0.5)) (* sy %.3f) 0 %.2f)' % (i, i, y, ESCALA)]
    l.append("  (return))")
    return "\n".join(l)


def construir_tick(g):
    """view target -> Cast -> sus tres lineas. Si el cast falla, se limpian."""
    entrada = None
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        if "FunctionEntry" in str(info(n)["type_id"]) or "FunctionEntry" in n["refPath"]:
            entrada = n
            break
    if entrada is None:
        return "no se encontro el nodo de entrada"

    pc = nodo(g, "Game|GetPlayerController", -1100, 300)
    vista = nodo(g, "Pawn|GetViewTarget", -900, 300)
    cast = nodo(g, "Utilities|Casting|CastToBP_DA_Interactuable", -650, 0)
    unir(sal(pc, "ReturnValue"), ent(vista, "self"))
    unir(sal(vista, "ReturnValue"), ent(cast, "Object"))
    unir(info(entrada)["output_pins"][0]["pin_id"], ent(cast, "execute"))

    # Rama buena: copiar las tres lineas del actor.
    anterior = sal(cast, "then")
    for i, v in enumerate(LINEAS):
        lee = nodo(g, "Class|BPDAInteractuable|GetDialogo%d" % (i + 1), -350, 250 + i * 140)
        pon = nodo(g, "Variables|Default|Set" + v, -100, i * 140)
        unir(sal(cast, "AsBP DA Interactuable"), ent(lee, "self"))
        unir(sal(lee, "Dialogo%d" % (i + 1)), ent(pon, v))
        unir(anterior, ent(pon, "execute"))
        anterior = sal(pon, "then")

    # Rama mala: vaciarlas, o el texto se quedaria pegado al salir.
    anterior = sal(cast, "CastFailed")
    for i, v in enumerate(LINEAS):
        pon = nodo(g, "Variables|Default|Set" + v, 400, i * 140)
        valor(ent(pon, v), "")
        unir(anterior, ent(pon, "execute"))
        anterior = sal(pon, "then")
    return "montado"


def enganchar(bp):
    res = {}
    for marca, funcion, crear, x, y in (
            ("AddEvent|EventReceiveDrawHUD", DIBUJAR, "CallFunction|DialogoDibujar", 700, 2700),
            ("AddEvent|EventTick", TICK, "CallFunction|DialogoTick", 700, 3100)):
        ev = None
        for n in bt("find_nodes", {"graph": EG, "title": ""}):
            if str(info(n)["type_id"]) == marca:
                ev = n
                break
        if ev is None:
            res[marca] = "evento no encontrado"
            continue
        llamada = nodo(EG, crear, x, y)
        p = None
        for q in info(ev)["output_pins"]:
            if q["name"] == "then":
                p = q
        seguia = p["connected_pins"][0] if p["connected_pins"] else None
        unir(p["pin_id"], ent(llamada, "execute"))
        if seguia is not None:
            unir(sal(llamada, "then"), seguia)
        res[marca] = "enganchado" + ("" if seguia is None else " y reencadenado")
    return res


def run():
    bp = {"refPath": BP}
    out = {}

    ya = str(bt("list_variables", {"blueprint": bp}))
    for v in LINEAS:
        if v not in ya:
            bt("add_variable", {"blueprint": bp, "name": v, "type_name": "string"})

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
