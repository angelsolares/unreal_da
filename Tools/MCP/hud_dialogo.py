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
    """Una barra de fondo por linea, no un panel unico.

    El fondo es el mismo de la casa —`0.01 0.01 0.05` con alfa 0,72— que ya usan
    el mensaje de objetivo y el panel de salto de zona, para que el dialogo no
    desentone del resto del HUD.

    Se dibuja **una barra por linea, ajustada a su ancho**, y no un rectangulo
    unico que las envuelva a las tres. Dos razones: el DSL no tiene un `max` de
    tres valores sin encadenar `select`, y `HUD|GetTextSize` devuelve el ANCHO,
    asi que no hay de donde sacar el alto real del texto para dimensionar el
    panel. Con una barra por linea el alto es una constante y cada barra se
    cinie a lo que hay, que ademas es como se ven los subtitulos.

    La barra solo se pinta si la linea tiene texto: una cadena vacia mide 0 de
    ancho, y sin el `if` saldria un tocon del tamanio del margen. Cassiel deja
    la tercera vacia.
    """
    fondo = "(Utilities|Struct|MakeLinearColor 0.01 0.01 0.05 0.72)"
    tinta = "(Utilities|Struct|MakeLinearColor 0.94 0.93 0.88 1.0)"
    margen = 24.0
    l = ["(fn " + DIBUJAR + " ()",
         "  (bind sx (.x (Viewport|GetViewportSize)))",
         "  (bind sy (.y (Viewport|GetViewportSize)))",
         "  (bind alto (* sy %.3f))" % (INTERLINEA + 0.002)]
    for i, v in enumerate(LINEAS):
        y = ALTO + i * INTERLINEA
        l += ["  (bind t%d (Variables|Default|Get%s))" % (i, v),
              "  (bind w%d (HUD|GetTextSize self t%d 0 %.2f))" % (i, i, ESCALA),
              "  (bind y%d (* sy %.3f))" % (i, y),
              "  (if (> w%d 1.0)" % i,
              "    (HUD|DrawRect self %s (- (* sx 0.5) (+ (* w%d 0.5) %.1f))"
              " (- y%d 6.0) (+ w%d %.1f) alto)" % (fondo, i, margen, i, i, margen * 2.0),
              "    (HUD|DrawText self t%d %s (- (* sx 0.5) (* w%d 0.5)) y%d 0 %.2f))"
              % (i, tinta, i, i, ESCALA)]
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


def vaciar(g):
    """Borra los NODOS de una funcion, no la funcion.

    `remove_function_graph` + `add_function_graph` parece lo natural, pero el
    segundo **no reutiliza el nombre**: crea `Dialogo_Dibujar_0`. De ahi salen
    los `SaltoZonas_Dibujar_0` y `_1` que arrastra este blueprint desde otra
    sesion. Y si el script aborta entre medias, la funcion se queda borrada y
    las llamadas del EventGraph, colgando.
    """
    entrada = None
    for n in bt("find_nodes", {"graph": g, "title": ""}):
        if "FunctionEntry" in str(info(n)["type_id"]) or "FunctionEntry" in n["refPath"]:
            entrada = n
        else:
            bt("delete_node", {"node": n})
    return entrada


def enganchar(bp):
    res = {}
    for marca, funcion, crear, x, y in (
            ("AddEvent|EventReceiveDrawHUD", DIBUJAR, "CallFunction|DialogoDibujar", 700, 2700),
            ("AddEvent|EventTick", TICK, "CallFunction|DialogoTick", 700, 3100)):
        ev = None
        puesta = False
        for n in bt("find_nodes", {"graph": EG, "title": ""}):
            t = str(info(n)["type_id"])
            if t == marca:
                ev = n
            if t == "|" + funcion:
                puesta = True
        if puesta:
            res[marca] = "ya estaba enganchada"
            continue
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

    # Restos de un intento anterior que borro las funciones y aborto a medias.
    for g in bt("list_graphs", {"blueprint": bp}):
        nom = g["refPath"].split(":")[-1]
        if nom.startswith(DIBUJAR + "_") or nom.startswith(TICK + "_"):
            bt("remove_function_graph", {"blueprint": bp, "graph_name": nom})
            out.setdefault("restos_borrados", []).append(nom)

    # LAS DOS FUNCIONES PRIMERO, y compilar, ANTES de escribir nada. El escritor
    # de DSL compila en cada escritura, y si el EventGraph tiene una llamada a
    # una funcion que no existe —porque un intento anterior la borro— la
    # compilacion falla y no deja escribir la otra. `add_function_graph` es
    # idempotente: si ya existe, devuelve la que hay.
    for nom in (DIBUJAR, TICK):
        bt("add_function_graph", {"blueprint": bp, "graph_name": nom})
    bt("compile_blueprint", {"blueprint": bp})

    vaciar({"refPath": BP + ":" + TICK})
    out["tick"] = construir_tick({"refPath": BP + ":" + TICK})

    vaciar({"refPath": BP + ":" + DIBUJAR})
    bt("write_graph_dsl", {"graph": {"refPath": BP + ":" + DIBUJAR}, "code": dsl_dibujar()})
    out["dibujar"] = "escrita por DSL"

    out["enganche"] = enganchar(bp)
    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))
    out["compila"] = "SI"
    return out
