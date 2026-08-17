import json

# Mete la llamada a `Guia_Tick` en la cadena del HUD, detras de `SaltoZonas_Tick`.
#
# SE INSERTA, NO SE PEGA AL FINAL. Un pin de ejecucion de SALIDA solo admite una
# conexion, asi que enchufar `Guia_Tick` a `SaltoZonas_Tick.then` a secas
# desconectaria lo que hubiera detras. Se mira primero a donde iba y se vuelve a
# atar por el otro lado.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
EG = {"refPath": BP + ":EventGraph"}
ANTES = "SaltoZonas_Tick"
NUEVA = "Guia_Tick"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def salida(n, nombre):
    for p in info(n)["output_pins"]:
        if p["name"] == nombre:
            return p
    return None


def entrada_pin(n, nombre):
    for p in info(n)["input_pins"]:
        if p["name"] == nombre:
            return p["pin_id"]
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    anterior = None
    ya = None
    for n in bt("find_nodes", {"graph": EG, "title": "", "entry_points_only": False}):
        t = str(info(n)["type_id"])
        if t.endswith("|" + ANTES) or t.endswith(ANTES):
            anterior = n
        if t.endswith("|" + NUEVA) or t.endswith(NUEVA):
            ya = n
    if anterior is None:
        return {"error": "no encuentro la llamada a " + ANTES}
    if ya is not None:
        return {"estado": "ya estaba enganchada"}

    # EL TIPO DE UNA FUNCION PROPIA ES `|<Nombre>`: barra delante y categoria
    # vacia. No es `CallFunction|<Nombre>` —eso es solo como lo escribe el DSL al
    # leer— y **`find_node_types` no las lista**, ni reiniciando el editor: no
    # entran en ese indice. Se comprobo leyendo el `type_id` de las llamadas que
    # ya habia en el grafo, que salen como `|Dialogo_Tick`, `|SaltoZonas_Tick`.
    nuevo = None
    fallos = []
    for tipo in ("Class|BPDAHUD|" + NUEVA, "|" + NUEVA, "CallFunction|" + NUEVA,
                 "Default|" + NUEVA, NUEVA):
        try:
            nuevo = bt("create_node", {"graph": EG, "type_id": tipo,
                                       "pos": {"x": 400, "y": 1800}})
            break
        except Exception as e:
            fallos.append(tipo)
    if nuevo is None:
        return {"error": "ningun type_id vale", "probados": fallos}

    p = salida(anterior, "then")
    detras = list(p.get("connected_pins") or [])
    bt("connect_pins", {"output_pin": p["pin_id"],
                        "input_pin": entrada_pin(nuevo, "execute")})
    for d in detras:
        bt("connect_pins", {"output_pin": salida(nuevo, "then")["pin_id"],
                            "input_pin": d})

    bt("compile_blueprint", {"blueprint": {"refPath": BP}})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         {"asset_paths": [BP.split(".")[0]]})
    return {"reenganchados_detras": len(detras),
            "sucio": call("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                          {"asset_path": BP.split(".")[0]})}
