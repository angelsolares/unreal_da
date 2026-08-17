import json

# La tecla G, montada DENTRO de `BP_DA_Ruta`: cada ruta mira si la has pulsado y
# suelta su propio fuego fatuo. Once actores comprobando una tecla por frame, que
# no es nada, y el fuego se descarta solo si la ruta le pilla lejos (ver
# `guia_fuego_grafo.py`).
#
# POR QUE AQUI Y NO EN EL HUD. La primera version era una funcion `Guia_Tick` del
# HUD que recorria las rutas con `GetAllActorsOfClass`. Compilaba, pero **no hay
# forma de crear el nodo que la llame**: ni por DSL ni por `create_node`, con
# ningun `type_id` —se probaron `Class|BPDAHUD|Guia_Tick`, `|Guia_Tick`,
# `CallFunction|Guia_Tick`, `Default|Guia_Tick` y a secas—, y eso que
# `list_functions` la daba por implementada y el editor se habia reiniciado. Las
# funciones propias solo parecen enlazables si el nodo ya estaba puesto a mano.
#
# Aqui no hace falta ninguna llamada, y ademas sale mejor: desaparece el
# `GetAllActorsOfClass` y su cast, porque cada ruta ya ES del tipo bueno.
#
# NO SE PUEDE MONTAR CON EL DSL: hace falta castear lo que devuelve
# `SpawnActorFromClass` —da `Actor` a secas— y el DSL **no sabe coger la salida de
# objeto de un Cast**, se queda con su pin booleano de exito. Nodo a nodo se
# conecta el pin bueno por su nombre: `AsBP DA Fuego`.
#
# Y NO HAY NODO `Self` QUE CREAR. La referencia a uno mismo se saca por
# `GetDefaultSceneRoot` -> `Components|GetOwner` -> cast, que es el mismo rodeo
# que usa `BP_DA_Interactuable`.

BP = "/Game/DarkAngels/Blueprints/Level/BP_DA_Ruta.BP_DA_Ruta"
EG = {"refPath": BP + ":EventGraph"}
FUEGO_C = "/Game/DarkAngels/Blueprints/Level/BP_DA_Fuego.BP_DA_Fuego_C"
TECLA = "G"

# DONDE LA GUIA SE CALLA. Al mudarse la tecla a las rutas, el `PermiteGuia` de
# los triggers de zona dejo de tener quien lo leyera: para eso haria falta que
# cada ruta recorriese los triggers, los casteara y midiera distancias, y son
# quince nodos para lo mismo. Se apaga por RUTA, que es un bool y una bifurcacion:
# los corredores de Gabriel no sueltan fuego, asi que con el jefe la G no hace
# nada. El bool del trigger se queda puesto para cuando haga falta un criterio
# mas fino por zona.
SIN_GUIA = ["ElevadorGabrielC1", "GabrielC1C2", "GabrielC2C3", "GabrielC3Yesod"]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def nodo(tipo, x, y):
    return bt("create_node", {"graph": EG, "type_id": tipo, "pos": {"x": x, "y": y}})


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}
    bp = {"refPath": BP}

    if "PermiteGuia" not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": "PermiteGuia", "type_name": "bool"})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": "PermiteGuia", "instance_editable": True})
        bt("compile_blueprint", {"blueprint": bp})
        call("editor_toolset.toolsets.object.ObjectTools.set_properties",
             {"instance": bt("get_default_object", {"blueprint": bp}),
              "values": json.dumps({"PermiteGuia": True})})
        bt("compile_blueprint", {"blueprint": bp})

    # De cero: se borra todo lo que no sea un evento, para que relanzar el script
    # rehaga el grafo en vez de duplicar nodos.
    for n in bt("find_nodes", {"graph": EG, "title": "", "entry_points_only": False}):
        if not str(info(n)["type_id"]).startswith("AddEvent|"):
            bt("delete_node", {"node": n})
    ev = bt("add_event", {"blueprint": bp, "event_name": "ReceiveTick",
                          "position": {"x": -1200, "y": 0}})

    n = {
        "pc": nodo("Game|GetPlayerController", -1200, 400),
        "tecla": nodo("Game|Player|WasInputKeyJustPressed", -950, 400),
        "branch": nodo("Utilities|FlowControl|Branch", -700, 0),
        "permite": nodo("Variables|Default|GetPermiteGuia", -560, 200),
        "branch2": nodo("Utilities|FlowControl|Branch", -420, 0),
        "raiz": nodo("Variables|Default|GetDefaultSceneRoot", -700, 600),
        "duenio": nodo("Components|GetOwner", -480, 600),
        "castYo": nodo("Utilities|Casting|CastToBP_DA_Ruta", -260, 0),
        "pj": nodo("Game|GetPlayerCharacter", -260, 400),
        "trans": nodo("Transformation|GetActorTransform", -60, 400),
        "spawn": nodo("Game|SpawnActorfromClass", 180, 0),
        "castF": nodo("Utilities|Casting|CastToBP_DA_Fuego", 480, 0),
        "setRuta": nodo("Class|BPDAFuego|SetRuta", 760, 0),
        "ppal": nodo("Variables|Default|GetEsPrincipal", 760, 400),
        "setPpal": nodo("Class|BPDAFuego|SetPrincipal", 1000, 0),
        "setListo": nodo("Class|BPDAFuego|SetListo", 1260, 0),
    }

    def pin(nd, direccion, nombre):
        clave = "input_pins" if direccion == "in" else "output_pins"
        for p in info(nd)[clave]:
            if p["name"] == nombre:
                return p["pin_id"]
        raise RuntimeError("sin pin '%s' en %s; hay %s" % (
            nombre, info(nd)["type_id"], [p["name"] for p in info(nd)[clave]]))

    def unir(a, sa, b, eb):
        bt("connect_pins", {"output_pin": pin(n[a], "out", sa),
                            "input_pin": pin(n[b], "in", eb)})

    def valor(k, nombre, v):
        bt("set_pin_value", {"pin": pin(n[k], "in", nombre), "value": v})

    # En un nodo de EVENTO el pin de ejecucion no es el 0 (el 0 es el
    # OutputDelegate): se busca por nombre.
    salida_ev = None
    for p in info(ev)["output_pins"]:
        if p["name"] in ("then", "Then"):
            salida_ev = p["pin_id"]
    bt("connect_pins", {"output_pin": salida_ev,
                        "input_pin": pin(n["branch"], "in", "execute")})

    unir("pc", "ReturnValue", "tecla", "self")
    valor("tecla", "Key", TECLA)
    unir("tecla", "ReturnValue", "branch", "Condition")

    # Yo mismo, para pasarselo al fuego.
    unir("raiz", "DefaultSceneRoot", "duenio", "self")
    unir("duenio", "ReturnValue", "castYo", "Object")
    # Segunda condicion: esta ruta no se ensena donde no toca.
    unir("branch", "then", "branch2", "execute")
    unir("permite", "PermiteGuia", "branch2", "Condition")
    unir("branch2", "then", "castYo", "execute")

    # El fuego, sobre el jugador.
    unir("castYo", "then", "spawn", "execute")
    valor("spawn", "Class", FUEGO_C)
    # Sin esto el spawn puede abortarse por aparecer dentro del jugador.
    valor("spawn", "CollisionHandlingOverride", "AlwaysSpawn")
    unir("pj", "ReturnValue", "trans", "self")
    unir("trans", "ReturnValue", "spawn", "SpawnTransform")

    unir("spawn", "then", "castF", "execute")
    unir("spawn", "ReturnValue", "castF", "Object")
    unir("castF", "then", "setRuta", "execute")
    for destino in ("setRuta", "setPpal", "setListo"):
        bt("connect_pins", {"output_pin": pin(n["castF"], "out", "AsBP DA Fuego"),
                            "input_pin": pin(n[destino], "in", "self")})
    bt("connect_pins", {"output_pin": pin(n["castYo"], "out", "AsBP DA Ruta"),
                        "input_pin": pin(n["setRuta"], "in", "Ruta")})
    unir("setRuta", "then", "setPpal", "execute")
    unir("ppal", "EsPrincipal", "setPpal", "Principal")
    unir("setPpal", "then", "setListo", "execute")
    valor("setListo", "Listo", "true")

    bt("arrange_nodes", {"nodes": [n[k] for k in n]})
    bt("compile_blueprint", {"blueprint": bp})

    # Y se apagan las rutas donde la guia estorba.
    apagadas = []
    for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                  {"name": "Ruta_", "tag": "", "collision_channels": []}):
        if "UEDPIE" in a["refPath"]:
            continue
        etiqueta = call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})
        permite = etiqueta.replace("Ruta_", "") not in SIN_GUIA
        call("editor_toolset.toolsets.object.ObjectTools.set_properties",
             {"instance": a, "values": json.dumps({"PermiteGuia": permite})})
        if not permite:
            apagadas.append(etiqueta)

    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [BP.split(".")[0], "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"]})
    return {"apagadas": apagadas,
            "grafo": bt("read_graph_dsl", {"graph": EG}),
            "sucio": call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                          {"asset_path": BP.split(".")[0]})}
