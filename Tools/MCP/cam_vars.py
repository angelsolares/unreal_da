import json

BP = {"refPath": "/Game/DarkAngels/Blueprints/Combat/BP_DA_NotifyCamara.BP_DA_NotifyCamara"}


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def run():
    for n in ["Lado", "Frente", "Alto", "Mira", "FOV", "Desfase"]:
        bp("add_variable", {"blueprint": BP, "name": n, "type_name": "float"})
    bp("compile_blueprint", {"blueprint": BP})
    execute_tool("editor_toolset.toolsets.object.ObjectTools.set_properties",
                 json.dumps({"instance": {"refPath": "/Game/DarkAngels/Blueprints/Combat/BP_DA_NotifyCamara.Default__BP_DA_NotifyCamara_C"},
                             "values": json.dumps({"Lado": 200.0, "Frente": 140.0,
                                                   "Alto": -20.0, "Mira": 0.0,
                                                   "FOV": 80.0, "Desfase": 61.0})}))
    return {"vars": bp("list_variables", {"blueprint": BP})}
