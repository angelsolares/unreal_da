import json

# Sonda: ¿el MCP sabe escribir arrays, o no sabe ninguno? Se prueba primero uno
# de enteros —lo mas simple que hay— para separar "los arrays no van" de "los
# arrays de structs no van".

BP = "/Game/DarkAngels/Blueprints/Level/BP_DA_Ruta.BP_DA_Ruta"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def probar(actor, clave, valor):
    try:
        ot("set_properties", {"instance": actor, "values": json.dumps({clave: valor})})
        leido = json.loads(ot("get_properties", {"instance": actor,
                                                 "properties": [clave]}))[clave]
        return {"ok": True, "leido": leido}
    except Exception as e:
        return {"ok": False, "error": str(e)[-160:]}


def run():
    bp = {"refPath": BP}
    if "Prueba" not in str(bt("list_variables", {"blueprint": bp})):
        bt("add_variable", {"blueprint": bp, "name": "Prueba", "type_name": "int",
                            "container_type": "ARRAY"})
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": "Prueba", "instance_editable": True})
        bt("compile_blueprint", {"blueprint": bp})

    actor = None
    for a in sc("find_actors", {"name": "", "tag": "", "collision_channels": []}):
        if "BP_DA_Ruta" in a["refPath"] and "UEDPIE" not in a["refPath"]:
            actor = a
            break
    if actor is None:
        return {"error": "no hay instancia de BP_DA_Ruta"}

    out = {"valor_actual_puntos": probar(actor, "puntos", None)}
    out["enteros: uno"] = probar(actor, "prueba", [7])
    out["enteros: dos"] = probar(actor, "prueba", [7, 8])
    out["enteros: vaciar"] = probar(actor, "prueba", [])
    out["vectores: uno"] = probar(actor, "puntos", [{"x": 1.0, "y": 2.0, "z": 3.0}])
    return out
