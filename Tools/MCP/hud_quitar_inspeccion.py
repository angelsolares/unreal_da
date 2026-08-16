import json

# Quita del HUD el cartel "ESC para salir" y su tick.
#
# Se cae entero porque ESC no vale como tecla de salida: en el editor Escape
# **para la sesion de PIE**. Ahora se entra y se sale con la misma E, y el aviso
# lo da el propio cartel de DCS, que pasa a decir "Aceptar" mientras estas
# dentro. Un sitio menos donde mirar y una funcion menos que mantener.
#
# Al borrar un nodo de una cadena de ejecucion hay que volver a unir lo que
# quedaba a cada lado, o el resto de la cadena se queda huerfano.

BP = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
EG = {"refPath": BP + ":EventGraph"}

LLAMADAS = ["|Inspeccion_Dibujar", "|Inspeccion_Tick"]
FUNCIONES = ["Inspeccion_Dibujar", "Inspeccion_Tick"]
VAR = "Inspeccionando"


def bt(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t, json.dumps(a))["returnValue"]


def info(n):
    return bt("get_node_infos", {"nodes": [n]})[0]


def run():
    bp = {"refPath": BP}
    out = {"quitados": []}

    for marca in LLAMADAS:
        objetivo = None
        for n in bt("find_nodes", {"graph": EG, "title": ""}):
            if str(info(n)["type_id"]) == marca:
                objetivo = n
                break
        if objetivo is None:
            out["quitados"].append({marca: "no estaba"})
            continue

        i = info(objetivo)
        antes = None
        for p in i["input_pins"]:
            if p["name"] == "execute" and p["connected_pins"]:
                antes = p["connected_pins"][0]
        despues = None
        for p in i["output_pins"]:
            if p["name"] == "then" and p["connected_pins"]:
                despues = p["connected_pins"][0]

        bt("delete_node", {"node": objetivo})
        if antes is not None and despues is not None:
            bt("connect_pins", {"output_pin": antes, "input_pin": despues})
        out["quitados"].append({marca: "borrado, cadena recosida" if antes and despues else "borrado"})

    existentes = [g["refPath"].split(":")[-1] for g in bt("list_graphs", {"blueprint": bp})]
    for f in FUNCIONES:
        if f in existentes:
            bt("remove_function_graph", {"blueprint": bp, "graph_name": f})
    if VAR in str(bt("list_variables", {"blueprint": bp})):
        bt("remove_variable", {"blueprint": bp, "name": VAR})

    bt("compile_blueprint", {"blueprint": bp})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths": [BP.split(".")[0]]}))
    out["grafo"] = bt("read_graph_dsl", {"graph": EG})[-260:]
    return out
