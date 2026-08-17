import json

# `BP_DA_Fuego`: el fuego fatuo. Recorre una polilinea que le pasan al nacer y se
# destruye al llegar al final o al agotarse su tiempo.
#
# Es una luz sin malla: en una zona con niebla la luz se lee mucho mejor que un
# objeto pequenio, y ademas ilumina el suelo por el que hay que ir, que es
# justo lo que se quiere ensenar.

RUTA = "/Game/DarkAngels/Blueprints/Level"
NOMBRE = "BP_DA_Fuego"
BP = RUTA + "/" + NOMBRE + "." + NOMBRE

# Cuanto sube el fuego sobre la losa del camino, para que no quede enterrado.
ALTURA = 110.0
VELOCIDAD = 1400.0        # uu/s
CERCA = 90.0              # a que distancia se da por alcanzado un punto
VIDA = 14.0               # segundos como mucho, por si se queda atascado


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def bt(t, a):
    return call("editor_toolset.toolsets.blueprint.BlueprintTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def ast(t, a):
    return call("editor_toolset.toolsets.asset.AssetTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    out = {}
    if not ast("exists", {"path": RUTA + "/" + NOMBRE}):
        bt("create", {"folder_path": RUTA, "asset_name": NOMBRE,
                      "asset_type": {"refPath": "/Script/Engine.Actor"}})
        out["blueprint"] = "creado"
    else:
        out["blueprint"] = "ya estaba"
    bp = {"refPath": BP}

    variables = str(bt("list_variables", {"blueprint": bp}))
    for nombre, tipo, contenedor in (("Puntos", "vector", "ARRAY"),
                                     ("Indice", "int", None),
                                     ("Velocidad", "float", None),
                                     ("Altura", "float", None),
                                     ("Cerca", "float", None)):
        if nombre not in variables:
            a = {"blueprint": bp, "name": nombre, "type_name": tipo}
            if contenedor:
                a["container_type"] = contenedor
            bt("add_variable", a)
        bt("set_variable_instance_editable",
           {"blueprint": bp, "variable_name": nombre, "instance_editable": True})

    # La luz. Un actor recien creado por MCP trae solo `DefaultSceneRoot`.
    tenia = {}
    cdo = bt("get_default_object", {"blueprint": bp})
    for c in at("get_components", {"actor": cdo}):
        tenia[c["refPath"].split(":")[-1].replace("_GEN_VARIABLE", "")] = c
    luz = tenia.get("Luz")
    if luz is None:
        luz = at("add_component", {"owner": bp, "name": "Luz",
                                   "component_type": {"refPath": "/Script/Engine.PointLightComponent"}})
    out["componentes"] = sorted(tenia)

    bt("compile_blueprint", {"blueprint": bp})
    # Los valores por defecto van DESPUES de compilar: hasta entonces el CDO no
    # tiene las propiedades recien creadas.
    cdo = bt("get_default_object", {"blueprint": bp})
    for k, v in (("Velocidad", VELOCIDAD), ("Altura", ALTURA), ("Cerca", CERCA)):
        ot("set_properties", {"instance": cdo, "values": json.dumps({k: v})})
    bt("compile_blueprint", {"blueprint": bp})
    ast("save_assets", {"asset_paths": [RUTA + "/" + NOMBRE]})

    out["defaults"] = json.loads(ot("get_properties", {
        "instance": bt("get_default_object", {"blueprint": bp}),
        "properties": ["Velocidad", "Altura", "Cerca"]}))
    out["variables"] = bt("list_variables", {"blueprint": bp})
    out["grafos"] = [str(g["refPath"]).split(":")[-1]
                     for g in bt("list_graphs", {"blueprint": bp})]
    return out
