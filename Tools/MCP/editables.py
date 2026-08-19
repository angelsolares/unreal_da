import json

BASE = "/Game/DarkAngels/Blueprints/Combat/"
QUE = {
    "BP_DA_NotifyCamara": ["Lado", "Frente", "Alto", "Mira", "FOV", "Desfase"],
    "BP_DA_NotifySacudida": ["Escala"],
    "BP_DA_NotifyHitStop": ["Dilatacion"],
}


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def run():
    hecho = {}
    for nombre, variables in QUE.items():
        ref = {"refPath": BASE + nombre + "." + nombre}
        for v in variables:
            bp("set_variable_instance_editable",
               {"blueprint": ref, "variable_name": v, "instance_editable": True})
        bp("compile_blueprint", {"blueprint": ref})
        execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                     json.dumps({"asset_paths": [BASE + nombre]}))
        hecho[nombre] = variables
    return hecho
