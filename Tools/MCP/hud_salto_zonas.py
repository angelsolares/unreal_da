import json

# Salto rapido de zona desde el HUD: teclas 1-9 y 0, con la leyenda dibujada
# pegada al borde derecho.
#
# Por que teclas y no botones de raton: las 13 zonas **no son mapas separados**,
# son Level Instances dentro de `L_DA_Malkuth_Master`, asi que no hay `OpenLevel`
# que valga: es teletransportar al pawn dentro del mismo mapa, y es instantaneo.
# Y para clicar harian falta `bShowMouseCursor` + `bEnableClickEvents`, que en un
# juego con camara al raton se pelean con mirar.
#
# POR QUE ESTE SCRIPT MONTA EL GRAFO NODO A NODO:
# `write_graph_dsl` **no conecta los pines `Target`** — reserva el pin llamado
# `self` y lo ata al propio blueprint—, asi que no puede llamar funciones sobre
# el PlayerController ni sobre el pawn. `create_node` + `connect_pins` si, porque
# trabajan con PinID explicito.
#
# La leyenda si va por DSL: solo dibuja sobre `self`, que es justo el caso que el
# DSL hace bien.
#
# Las cotas salen de trazas verticales sobre cada zona, +120 para dejar caer al
# jugador un poco en vez de encajarlo en el suelo. Gabriel apunta al tramo C2:
# la traza de C1 daba 28774, que es un tejado, no el suelo.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
TICK = "SaltoZonas_Tick"
DIBUJAR = "SaltoZonas_Dibujar"

ZONAS = [
    ("One",   "1", "Jardin",     -59649.0, -60004.0,   138.0),
    ("Two",   "2", "Mirador",    -16000.0, -23800.0,   438.0),
    ("Three", "3", "El Claro",    44000.0, -13650.0,    84.0),
    ("Four",  "4", "Gazebo",      64000.0,  15400.0,   184.0),
    ("Five",  "5", "Santuario",   43940.0,  47600.0,   118.0),
    ("Six",   "6", "Puente",      16000.0,  60000.0,  1532.0),
    ("Seven", "7", "Yesod",      -92000.0,  16000.0, 13213.0),
    ("Eight", "8", "Anfiteatro", -73649.0,  41996.0,   136.0),
    ("Nine",  "9", "Elevador",   -74000.0,   8000.0,    94.0),
    ("Zero",  "0", "Gabriel",    -66000.0, -15000.0,   281.0),
]


def call(tool, args):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + tool,
                        json.dumps(args))["returnValue"]


def pin(nodo, direccion, indice):
    return {"direction": direccion, "index_id": indice, "node": {"refPath": nodo["refPath"]}}


def salida(nodo, i):
    return pin(nodo, "EGPD_Output", i)


def entrada(nodo, i):
    return pin(nodo, "EGPD_Input", i)


def conectar(desde, hasta):
    call("connect_pins", {"output_pin": desde, "input_pin": hasta})


def valor(p, v):
    call("set_pin_value", {"pin": p, "value": v})


def dsl_dibujar():
    # Ojo con el ancho de pantalla: `HUD|GetViewportSize` resuelve a un nodo cuyo
    # Target es un PlayerController, y el DSL no sabe conectar Targets. El bueno
    # es `Viewport|GetViewportSize`, que **no tiene pines de entrada** y devuelve
    # un Vector2D; el DSL le mete solo la conversion al usar (.x ...).
    alto = 44.0 + len(ZONAS) * 26.0
    l = ["(fn " + DIBUJAR + " ()",
         "  (bind sx (.x (Viewport|GetViewportSize)))",
         '  (HUD|DrawRect self (Utilities|Struct|MakeLinearColor 0.01 0.01 0.05 0.62)'
         ' (- sx 250.0) 90.0 235.0 %.1f)' % alto,
         '  (HUD|DrawText self "SALTO DE ZONA"'
         ' (Utilities|Struct|MakeLinearColor 1.0 0.88 0.45 1.0) (- sx 236.0) 100.0 0 1.05)']
    for i, (_c, tecla, nombre, _x, _y, _z) in enumerate(ZONAS):
        l.append('  (HUD|DrawText self "%s   %s"'
                 ' (Utilities|Struct|MakeLinearColor 0.86 0.9 1.0 0.95)'
                 ' (- sx 236.0) %.1f 0 0.95)' % (tecla, nombre, 130.0 + i * 26.0))
    l.append("  (return))")
    return "\n".join(l)


def construir_tick(graph):
    """Monta a mano: entrada -> 10 x (rama por tecla -> mover el pawn)."""
    # El nodo de entrada de la funcion ya existe al crearla.
    entrada_fn = None
    for n in call("find_nodes", {"graph": graph, "title": ""}):
        info = str(call("get_node_infos", {"nodes": [n]}))
        if "FunctionEntry" in info or "K2Node_FunctionEntry" in n["refPath"]:
            entrada_fn = n
            break
    if entrada_fn is None:
        return {"error": "no se encontro el nodo de entrada"}

    pc = call("create_node", {"graph": graph, "type_id": "Game|GetPlayerController",
                              "pos": {"x": -600, "y": -200}})
    pawn = call("create_node", {"graph": graph, "type_id": "Game|GetPlayerCharacter",
                                "pos": {"x": -600, "y": -80}})

    anterior_exec = salida(entrada_fn, 0)
    for i, (clave, _t, _n, x, y, z) in enumerate(ZONAS):
        fila = i * 180
        tecla = call("create_node", {"graph": graph,
                                     "type_id": "Game|Player|WasInputKeyJustPressed",
                                     "pos": {"x": -300, "y": fila}})
        rama = call("create_node", {"graph": graph, "type_id": "Utilities|FlowControl|Branch",
                                    "pos": {"x": 0, "y": fila}})
        mover = call("create_node", {"graph": graph, "type_id": "Transformation|SetActorLocation",
                                     "pos": {"x": 300, "y": fila}})

        # La lectura de la tecla, sobre el PlayerController
        conectar(salida(pc, 0), entrada(tecla, 0))      # self  <- PlayerController
        valor(entrada(tecla, 1), clave)                 # Key
        conectar(salida(tecla, 0), entrada(rama, 1))    # Condition <- ReturnValue

        # El hilo de ejecucion entra en la rama
        conectar(anterior_exec, entrada(rama, 0))

        # Rama verdadera: mover al pawn
        conectar(salida(rama, 0), entrada(mover, 0))    # then -> execute
        conectar(salida(pawn, 0), entrada(mover, 1))    # self <- Character
        valor(entrada(mover, 2), "(X=%.3f,Y=%.3f,Z=%.3f)" % (x, y, z))
        valor(entrada(mover, 4), "true")                # bTeleport

        # La rama falsa encadena con la siguiente tecla
        anterior_exec = salida(rama, 1)

    # Los nodos ya se colocan con `pos` al crearlos; `arrange_nodes` pide una
    # lista de nodos, no un grafo, y no hace falta.
    return {"nodos": 2 + len(ZONAS) * 3}


def buscar_evento(grafo, marca):
    for n in call("find_nodes", {"graph": grafo, "title": ""}):
        if marca in n["refPath"]:
            return n
    return None


def enganchar(bp):
    """Mete las dos llamadas en el EventGraph sin tocar la logica existente.

    El dibujado se inserta ANTES de lo que ya hubiera colgando de DrawHUD: el
    panel va pegado al borde derecho y el objetivo al centro, asi que no se
    pisan, y asi no hay que buscar el final de una cadena que acaba en rama.
    """
    eg = {"refPath": BP + ":EventGraph"}
    res = {}

    for marca, funcion, x, y in [("ReceiveDrawHUD", DIBUJAR, 400, 900),
                                  ("ReceiveTick", TICK, 400, 1400)]:
        ev = buscar_evento(eg, marca)
        if ev is None:
            res[marca] = "no encontrado"
            continue
        llamada = call("create_node", {"graph": eg, "type_id": funcion,
                                       "pos": {"x": x, "y": y}})
        # Que colgaba del exec del evento, para volver a encadenarlo detras.
        info = call("get_node_infos", {"nodes": [ev]})
        seguia = None
        for p in info[0]["output_pins"]:
            if p["pin_id"]["index_id"] == 0 and p["connected_pins"]:
                seguia = p["connected_pins"][0]
                break
        conectar(salida(ev, 0), entrada(llamada, 0))
        if seguia is not None:
            conectar(salida(llamada, 0), seguia)
        res[marca] = "enganchado" + ("" if seguia is None else " y reencadenado")
    return res


def run():
    bp = {"refPath": BP}
    salida_ = {}

    # Partir de cero por si quedaron restos de un intento anterior. Hay que
    # mirar antes si existe: los errores de estas herramientas abortan el script
    # entero, no los caza un try/except.
    existentes = [g["refPath"].split(":")[-1]
                  for g in call("list_graphs", {"blueprint": bp})]
    for nom in (TICK, DIBUJAR):
        if nom in existentes:
            call("remove_function_graph", {"blueprint": bp, "graph_name": nom})

    # Ojo: hay que usar la ruta construida a mano, no el refPath que devuelve
    # add_function_graph — con ese, write_graph_dsl no encuentra el nodo de
    # entrada y falla con "AddEvent|<nombre> does not exist".
    call("add_function_graph", {"blueprint": bp, "graph_name": DIBUJAR})
    call("write_graph_dsl", {"graph": {"refPath": BP + ":" + DIBUJAR}, "code": dsl_dibujar()})
    salida_["dibujar"] = "escrita por DSL"

    call("add_function_graph", {"blueprint": bp, "graph_name": TICK})
    salida_["tick"] = construir_tick({"refPath": BP + ":" + TICK})

    salida_["enganche"] = enganchar(bp)
    call("compile_blueprint", {"blueprint": bp})
    salida_["compila"] = "SI"
    return salida_
