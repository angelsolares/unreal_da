import json

# De que rama del Branch cuelga cada nodo de DbgOcultarJuego.
#
# Sospecha: el DSL podria estar tratando el SEGUNDO statement de un `if` sin
# `(else ...)` como la rama falsa (estilo Lisp) en vez de como la segunda
# instruccion de la rama verdadera. Si fuera asi, los widgets VISIBLES solo se
# apuntarian en la lista y nunca se esconderian — que es justo lo que se ve.

G = {"refPath": "/Game/DarkAngels/Debug/BP_DA_DebugHUD.BP_DA_DebugHUD:DbgOcultarJuego"}


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def run():
    infos = {}
    for n in bp("find_nodes", {"graph": G, "title": ""}):
        i = bp("get_node_infos", {"nodes": [n]})[0]
        infos[n["refPath"].split(".")[-1]] = i["type_id"]

    salida = {"nodos": infos, "ramas": []}
    for n in bp("find_nodes", {"graph": G, "title": ""}):
        i = bp("get_node_infos", {"nodes": [n]})[0]
        if "Branch" not in i["type_id"]:
            continue
        for p in i["output_pins"]:
            destinos = []
            for c in p["connected_pins"]:
                destinos.append(c["node"]["refPath"].split(".")[-1])
            salida["ramas"].append({"branch": n["refPath"].split(".")[-1],
                                    "pin": p["name"], "va_a": destinos})
    return salida
