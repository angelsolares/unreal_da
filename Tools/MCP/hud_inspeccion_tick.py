import json

# Engancha `Inspeccion_Tick` al EventTick de `BP_DA_HUD`.
#
# Va aparte porque el enganche de `hud_inspeccion.py` no encontro el evento: el
# `type_id` del tick es **`AddEvent|EventTick`**, no `ReceiveTick`, que es como
# se llama en `list_events`. El de dibujado si casa: `AddEvent|EventReceiveDrawHUD`.
# Nombres de evento y type_id de nodo NO son lo mismo.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
EG = {"refPath": BP + ":EventGraph"}
# Ojo: para CREAR el nodo hace falta `CallFunction|InspeccionTick` —sin guiones
# bajos—, pero el nodo YA CREADO se reporta como `|Inspeccion_Tick`. No son el
# mismo texto y hay que usar cada uno donde toca.
CREAR = "CallFunction|InspeccionTick"
PUESTO = "|Inspeccion_Tick"
MARCA = "AddEvent|EventTick"


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t, json.dumps(a))["returnValue"]


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def pin_salida(n, nombre):
    for p in info(n)["output_pins"]:
        if p["name"] == nombre:
            return p
    return None


def run():
    ev = None
    for n in bt("find_nodes", {"graph": EG, "title": ""}):
        i = info(n)
        if str(i["type_id"]) == MARCA:
            ev = n
        if str(i["type_id"]) == PUESTO:
            return {"ya_estaba": "la llamada a Inspeccion_Tick ya existe"}
    if ev is None:
        return {"error": "no se encontro " + MARCA}

    llamada = bt("create_node", {"graph": EG, "type_id": CREAR, "pos": {"x": 400, "y": 2300}})

    p = pin_salida(ev, "then")
    seguia = p["connected_pins"][0] if p["connected_pins"] else None

    entrada = None
    for q in info(llamada)["input_pins"]:
        if q["name"] == "execute":
            entrada = q["pin_id"]
    bt("connect_pins", {"output_pin": p["pin_id"], "input_pin": entrada})
    if seguia is not None:
        salida = None
        for q in info(llamada)["output_pins"]:
            if q["name"] == "then":
                salida = q["pin_id"]
        bt("connect_pins", {"output_pin": salida, "input_pin": seguia})

    bt("compile_blueprint", {"blueprint": {"refPath": BP}})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))
    return {"enganchado": "SI", "reencadenado": seguia is not None,
            "grafo": bt("read_graph_dsl", {"graph": EG})[-420:]}
