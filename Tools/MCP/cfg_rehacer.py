import json

RUTA = "/Game/DarkAngels/Debug/BP_DA_DebugConfig"
BP = {"refPath": RUTA + ".BP_DA_DebugConfig"}


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def ast(t, a):
    return execute_tool("editor_toolset.toolsets.asset.AssetTools." + t,
                        json.dumps(a))["returnValue"]


FLOATS = ["Dilatacion", "MatarEn", "CamaraLado", "CamaraAlto", "CamaraFrente",
          "CamaraFOV", "Escala", "MovMult", "DmgMult", "EnemyMult"]
INTS = ["Indice", "Tab", "TipoSel", "CantSel", "DistSel", "BossSel", "CheckSel"]
BOOLS = ["God", "ManaInf", "OneHit", "Trazas", "Colisiones", "LogOn",
         "Congelada", "Apagada", "Ignorar", "TieneGuardada"]
STRUCTS = [("GuardadaLoc", "/Script/CoreUObject.Vector"),
           ("GuardadaRot", "/Script/CoreUObject.Rotator")]


def run():
    ast("delete", {"path": RUTA})
    bp("create", {"folder_path": "/Game/DarkAngels/Debug",
                  "asset_name": "BP_DA_DebugConfig",
                  "asset_type": {"refPath": "/Script/Engine.SaveGame"}})
    for n in FLOATS:
        bp("add_variable", {"blueprint": BP, "name": n, "type_name": "float"})
    for n in INTS:
        bp("add_variable", {"blueprint": BP, "name": n, "type_name": "int"})
    for n in BOOLS:
        bp("add_variable", {"blueprint": BP, "name": n, "type_name": "bool"})
    for n, tipo in STRUCTS:
        bp("add_struct_variable",
           {"blueprint": BP, "name": n, "struct_type": {"refPath": tipo}})
    bp("compile_blueprint", {"blueprint": BP})
    ast("save_assets", {"asset_paths": [RUTA]})
    return {"variables": bp("list_variables", {"blueprint": BP})}
