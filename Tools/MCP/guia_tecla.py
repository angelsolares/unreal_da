import json

# La tecla G: suelta un fuego fatuo por cada ruta del nivel y deja que se
# descarten solos los que no vienen a cuento (ver `guia_fuego_grafo.py`).
#
# Se engancha como `Guia_Tick`, una funcion mas del HUD llamada desde el evento
# de dibujado, que es el patron que ya usa `SaltoZonas_Tick` para el teclado
# numerico. Asi no hay que tocar el IMC de DCS ni anadir un InputAction.
#
# LA G ESTABA LIBRE: en `IMC_Player` estan cogidas A, C, D, E, F, I, Q, R, S, U,
# W, X, Tab, Shift, Ctrl, Space y los botones del raton; y el HUD ya usa K, L y
# el bloque numerico.
#
# **ESTO NO SE PUEDE MONTAR CON EL DSL.** Hacen falta dos Cast —el de
# `GetAllActorsOfClass`, que devuelve `Actor` a secas, y el de
# `SpawnActorFromClass`, igual— y el DSL **no sabe coger la salida de objeto de
# un Cast**: el `bind` se queda con su pin booleano de exito, asi que lo que
# acaba conectando es un `bool`. Y el accesor `.` solo admite componentes de
# struct (x, y, z, pitch, yaw, roll, location, rotation, scale), no pines
# cualesquiera. Nodo a nodo se conecta el pin bueno por su nombre y ya.
#
# El pin de objeto de un Cast se llama `As<Clase con espacios>`: para
# `BP_DA_Ruta` es `AsBP DA Ruta`.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
FN = "Guia_Tick"
GRAFO = {"refPath": BP + ":" + FN}

RUTA_C = "/Game/DarkAngels/Blueprints/Level/BP_DA_Ruta.BP_DA_Ruta_C"
FUEGO_C = "/Game/DarkAngels/Blueprints/Level/BP_DA_Fuego.BP_DA_Fuego_C"
TECLA = "G"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def nodo(tipo, x, y):
    return bt("create_node", {"graph": GRAFO, "type_id": tipo, "pos": {"x": x, "y": y}})


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    bp = {"refPath": BP}
    grafos = [str(g["refPath"]).split(":")[-1] for g in bt("list_graphs", {"blueprint": bp})]
    if FN not in grafos:
        bt("add_function_graph", {"blueprint": bp, "graph_name": FN})

    # Se vacia el grafo menos su nodo de entrada, para que relanzar el script
    # rehaga la funcion desde cero en vez de duplicar nodos.
    entrada = None
    for n in bt("find_nodes", {"graph": GRAFO, "title": "", "entry_points_only": True}):
        entrada = n
    for n in bt("find_nodes", {"graph": GRAFO, "title": "", "entry_points_only": False}):
        if entrada is None or n["refPath"] != entrada["refPath"]:
            bt("delete_node", {"node": n})

    creados = {
        "pc": nodo("Game|GetPlayerController", -900, 300),
        "pj": nodo("Game|GetPlayerCharacter", -900, 420),
        "tecla": nodo("Game|Player|WasInputKeyJustPressed", -650, 300),
        "branch": nodo("Utilities|FlowControl|Branch", -420, 0),
        "todas": nodo("Actor|GetAllActorsOfClass", -200, 0),
        "bucle": nodo("Utilities|Array|ForEachLoop", 60, 0),
        "castR": nodo("Utilities|Casting|CastToBP_DA_Ruta", 340, 0),
        "trans": nodo("Transformation|GetActorTransform", 340, 300),
        "spawn": nodo("Game|SpawnActorfromClass", 600, 0),
        "castF": nodo("Utilities|Casting|CastToBP_DA_Fuego", 900, 0),
        "setRuta": nodo("Class|BPDAFuego|SetRuta", 1160, 0),
        "esPpal": nodo("Class|BPDARuta|GetEsPrincipal", 1160, 300),
        "setPpal": nodo("Class|BPDAFuego|SetPrincipal", 1400, 0),
        "setListo": nodo("Class|BPDAFuego|SetListo", 1640, 0),
    }

    n = creados

    def pin(nodo_, direccion, nombre):
        clave = "input_pins" if direccion == "in" else "output_pins"
        for p in info(nodo_)[clave]:
            if p["name"] == nombre:
                return p["pin_id"]
        raise RuntimeError("sin pin '%s' en %s" % (nombre, info(nodo_)["type_id"]))

    def unir(a, sa, b, eb):
        bt("connect_pins", {"output_pin": pin(n.get(a, entrada), "out", sa),
                            "input_pin": pin(n[b], "in", eb)})

    def valor(k, nombre, v):
        bt("set_pin_value", {"pin": pin(n[k], "in", nombre), "value": v})

    # --- la tecla ---
    bt("connect_pins", {"output_pin": pin(entrada, "out", "then"),
                        "input_pin": pin(n["branch"], "in", "execute")})
    unir("pc", "ReturnValue", "tecla", "self")
    valor("tecla", "Key", TECLA)
    unir("tecla", "ReturnValue", "branch", "Condition")

    # --- una vuelta por cada ruta del nivel ---
    unir("branch", "then", "todas", "execute")
    valor("todas", "ActorClass", RUTA_C)
    unir("todas", "then", "bucle", "Exec")
    unir("todas", "OutActors", "bucle", "Array")
    unir("bucle", "LoopBody", "castR", "execute")
    unir("bucle", "Array Element", "castR", "Object")

    # --- y un fuego por cada una ---
    unir("castR", "then", "spawn", "execute")
    valor("spawn", "Class", FUEGO_C)
    # Sin esto el spawn puede abortarse si el sitio esta ocupado, y nace justo
    # encima del jugador.
    valor("spawn", "CollisionHandlingOverride", "AlwaysSpawn")
    unir("pj", "ReturnValue", "trans", "self")
    unir("trans", "ReturnValue", "spawn", "SpawnTransform")

    # `SpawnActorFromClass` devuelve `Actor`, asi que hace falta castear tambien
    # a la salida para poder tocarle las variables al fuego.
    unir("spawn", "then", "castF", "execute")
    unir("spawn", "ReturnValue", "castF", "Object")

    unir("castF", "then", "setRuta", "execute")
    for destino in ("setRuta", "setPpal", "setListo"):
        bt("connect_pins", {"output_pin": pin(n["castF"], "out", "AsBP DA Fuego"),
                            "input_pin": pin(n[destino], "in", "self")})
    bt("connect_pins", {"output_pin": pin(n["castR"], "out", "AsBP DA Ruta"),
                        "input_pin": pin(n["setRuta"], "in", "Ruta")})
    bt("connect_pins", {"output_pin": pin(n["castR"], "out", "AsBP DA Ruta"),
                        "input_pin": pin(n["esPpal"], "in", "self")})
    unir("setRuta", "then", "setPpal", "execute")
    unir("esPpal", "EsPrincipal", "setPpal", "Principal")
    unir("setPpal", "then", "setListo", "execute")
    valor("setListo", "Listo", "true")

    # `arrange_nodes` quiere la LISTA de nodos, no el grafo.
    bt("arrange_nodes", {"nodes": [n[k] for k in n]})
    bt("compile_blueprint", {"blueprint": bp})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [BP.split(".")[0]]})
    return {"funcion": bt("read_graph_dsl", {"graph": GRAFO}),
            "sucio": call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                          {"asset_path": BP.split(".")[0]})}
