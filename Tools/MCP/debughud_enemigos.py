import json

# DA Debug HUD (fase 4) — datos de la pestana AI.
#
# Mismo patron que los destinos de teleport: una linea de texto por entrada en
# un Data Asset, porque el MCP no puede crear structs (ver debughud_datos.py).
#
# LOS ENEMIGOS SON LOS QUE EXISTEN DE VERDAD. Comprobado uno a uno que heredan
# de `BP_BaseAI`, que es lo que los hace IA de DCS y no un prop:
#   Vigilante, Lancero, Arquero, Heraldo, Inspector -> BP_BaseAI
#   BP_DA_WarriorAI -> BP_WarriorAI -> BP_BaseAI
# Quedan fuera a proposito `BP_Angel_Messenger` y `BP_Archangel` (son Character
# pelados, NPCs) y `BP_LightShield` (un Actor). No se inventa ninguno.

CARPETA = "/Game/DarkAngels/Debug"
CLASE_NOM = "BP_DA_DebugEnemigos"
CLASE = CARPETA + "/" + CLASE_NOM + "." + CLASE_NOM
ASSET_NOM = "DA_DA_DebugEnemigos"
ASSET = CARPETA + "/" + ASSET_NOM + "." + ASSET_NOM

E = "/Game/DarkAngels/Blueprints/Enemies/"

# Nombre | ruta de la clase
TIPOS = [
    ("Vigilante", E + "BP_DA_Vigilante.BP_DA_Vigilante_C"),
    ("Lancero", E + "BP_DA_Lancero.BP_DA_Lancero_C"),
    ("Arquero", E + "BP_DA_Arquero.BP_DA_Arquero_C"),
    ("Heraldo", E + "BP_DA_Heraldo.BP_DA_Heraldo_C"),
    ("Inspector", E + "BP_DA_Inspector.BP_DA_Inspector_C"),
    ("Warrior DCS",
     "/Game/DarkAngels/Blueprints/Characters/BP_DA_WarriorAI.BP_DA_WarriorAI_C"),
]

# Nombre | indice_de_tipo:cantidad, indice_de_tipo:cantidad
# Marcados TEST a proposito: son para probar la mecanica, no el diseno final
# de los encuentros de Malkuth.
ENCUENTROS = [
    ("TEST Melee basico", "0:2"),
    ("TEST Mixto a distancia", "0:2, 2:1"),
]

# Los DOS actores tipo boss que existen hoy. No son la misma arquitectura:
#
#   BP_DA_GiantBoss  hereda de BP_Giant (asset de pago) y LLEVA StatsManager de
#                    DCS, asi que su vida si se puede tocar por la via oficial.
#                    Tiene ademas MaxHealth/CurrentHealth propios y `FaseRitual`,
#                    que es el paso del guion del ritual, no una fase de boss.
#   BP_Gabriel       hereda de BP_Archangel, que es un Character pelado con `HP`,
#                    `Phase`, `bDormant` y `bShieldUp` sueltos. SIN StatsManager:
#                    su vida no es alcanzable desde el HUD (ver las notas).
BOSSES = [
    ("Giant Boss", "/Game/DarkAngels/Blueprints/Bosses/BP_DA_GiantBoss.BP_DA_GiantBoss_C"),
    ("Gabriel (Archangel)",
     "/Game/DarkAngels/Blueprints/Enemies/BP_Gabriel.BP_Gabriel_C"),
]


def bp(t, a):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + t,
                        json.dumps(a))["returnValue"]


def ast(t, a):
    return execute_tool("editor_toolset.toolsets.asset.AssetTools." + t,
                        json.dumps(a))["returnValue"]


def dat(t, a):
    return execute_tool("editor_toolset.toolsets.data_asset.DataAssetTools." + t,
                        json.dumps(a))["returnValue"]


def obj(t, a):
    return execute_tool("editor_toolset.toolsets.object.ObjectTools." + t,
                        json.dumps(a))["returnValue"]


def run():
    out = {}
    ast("create_folder", {"path": CARPETA})

    if not ast("exists", {"path": CARPETA + "/" + CLASE_NOM}):
        bp("create", {"folder_path": CARPETA, "asset_name": CLASE_NOM,
                      "asset_type": {"refPath": "/Script/Engine.PrimaryDataAsset"}})
    ya = bp("list_variables", {"blueprint": {"refPath": CLASE}})
    for nombre in ["Tipos", "Encuentros", "Bosses"]:
        if nombre not in ya:
            bp("add_variable", {"blueprint": {"refPath": CLASE}, "name": nombre,
                                "type_name": "string", "container_type": "ARRAY"})
        bp("set_variable_instance_editable", {"blueprint": {"refPath": CLASE},
                                              "variable_name": nombre,
                                              "instance_editable": True})
        bp("set_variable_category", {"blueprint": {"refPath": CLASE},
                                     "variable_name": nombre, "category": "DA Debug"})
    bp("compile_blueprint", {"blueprint": {"refPath": CLASE}})

    if not ast("exists", {"path": CARPETA + "/" + ASSET_NOM}):
        dat("create", {"folder_path": CARPETA, "asset_name": ASSET_NOM,
                       "asset_type": {"refPath": CLASE + "_C"}})
    inst = {"refPath": ASSET}
    obj("set_properties", {"instance": inst, "values": json.dumps({
        "Tipos": ["%s | %s" % (n, c) for n, c in TIPOS],
        "Encuentros": ["%s | %s" % (n, c) for n, c in ENCUENTROS],
        "Bosses": ["%s | %s" % (n, c) for n, c in BOSSES]})})

    leido = json.loads(obj("get_properties", {"instance": inst,
                                              "properties": ["Tipos", "Encuentros", "Bosses"]}))
    out["tipos"] = len(leido["Tipos"])
    out["encuentros"] = len(leido["Encuentros"])
    out["bosses"] = leido["Bosses"]
    out["ultimo_tipo"] = leido["Tipos"][-1] if leido["Tipos"] else None
    ast("save_assets", {"asset_paths": []})
    return out
