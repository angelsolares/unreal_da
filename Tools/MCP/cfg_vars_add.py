import json

BP = {"refPath": "/Game/DarkAngels/Debug/BP_DA_DebugConfig.BP_DA_DebugConfig"}


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def run():
    floats = ["MovMult", "DmgMult", "EnemyMult"]
    ints = ["TipoSel", "CantSel", "DistSel", "BossSel", "CheckSel"]
    bools = ["God", "ManaInf", "OneHit", "Trazas", "Colisiones", "LogOn",
             "Congelada", "Apagada", "Ignorar", "TieneGuardada"]
    structs = [("GuardadaLoc", "/Script/CoreUObject.Vector"),
               ("GuardadaRot", "/Script/CoreUObject.Rotator")]

    hechas = []
    for n in floats:
        bp("add_variable", {"blueprint": BP, "name": n, "type_name": "float"})
        hechas.append(n)
    for n in ints:
        bp("add_variable", {"blueprint": BP, "name": n, "type_name": "int"})
        hechas.append(n)
    for n in bools:
        bp("add_variable", {"blueprint": BP, "name": n, "type_name": "bool"})
        hechas.append(n)
    for n, tipo in structs:
        bp("add_struct_variable",
           {"blueprint": BP, "name": n, "struct_type": {"refPath": tipo}})
        hechas.append(n)

    bp("compile_blueprint", {"blueprint": BP})
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 json.dumps({"asset_paths":
                             ["/Game/DarkAngels/Debug/BP_DA_DebugConfig"]}))
    return {"anadidas": len(hechas), "nombres": hechas}
