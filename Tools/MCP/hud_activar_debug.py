import json

# Arregla las dos cosas que hacian que el salto de zona no funcionase:
#
# 1. **`BP_DA_HUD` no llegaba a instanciarse.** El `GlobalDefaultGameMode` del
#    proyecto es `BP_DCSGameMode`, cuyo `HUDClass` es el `HUD` pelado del motor,
#    y el mapa no lo sobreescribe (`DefaultGameMode` = None en World Settings).
#    Quien deberia activarlo es `BP_DA_HUDSpawner`, con su `ClientSetHUD`...
#    **pero ese actor no esta puesto en el mapa**. Asi que el HUD del proyecto
#    nunca se activaba y mi codigo vivia en un blueprint muerto.
#
#    Se arregla con un actor de debug propio que solo hace `ClientSetHUD`. Se
#    eligio eso y no colocar el `BP_DA_HUDSpawner` entero para **no cambiar lo
#    que se ve en juego**: el spawner ademas mete `WBP_DA_HUD` en pantalla, que
#    se solaparia con el HUD de DCS que ya sale.
#
# 2. **Las teclas 1-9 y 0 ya estaban cogidas por los hechizos.** Se pasan a
#    **F1-F10**, que estan libres: asi no hay que desactivar nada del input de
#    DCS y quitar el debug no deja rastro.

BP_HUD = "/Game/DarkAngels/Blueprints/UI/BP_DA_HUD.BP_DA_HUD"
TICK = BP_HUD + ":SaltoZonas_Tick"
CARPETA = "/Game/DarkAngels/Blueprints/Level"
ACTOR = "BP_DA_DebugZonas"

# Mismo orden que en hud_salto_zonas.py: la fila i de la leyenda se corresponde
# con la tecla i.
TECLAS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"]


def call(tool, args):
    return execute_tool("editor_toolset.toolsets.blueprint.BlueprintTools." + tool,
                        json.dumps(args))["returnValue"]


def run():
    out = {}

    # --- 1. Repasar las teclas del grafo ya montado, en su sitio ---
    cambiadas = []
    i = 0
    for n in call("find_nodes", {"graph": {"refPath": TICK}, "title": ""}):
        info = call("get_node_infos", {"nodes": [n]})[0]
        for p in info["input_pins"]:
            if p["name"] != "Key":
                continue
            if i < len(TECLAS):
                call("set_pin_value", {"pin": p["pin_id"], "value": TECLAS[i]})
                cambiadas.append(TECLAS[i])
                i += 1
    out["teclas"] = cambiadas

    # --- 2. El actor que activa nuestro HUD ---
    existe = execute_tool("editor_toolset.toolsets.asset.AssetTools.exists",
                          json.dumps({"path": CARPETA + "/" + ACTOR}))["returnValue"]
    if not existe:
        call("create", {"folder_path": CARPETA, "asset_name": ACTOR,
                        "asset_type": {"refPath": "/Script/Engine.Actor"}})
    ruta = CARPETA + "/" + ACTOR + "." + ACTOR
    call("write_graph_dsl", {
        "graph": {"refPath": ruta + ":EventGraph"},
        "code": ('(event EventBeginPlay\n'
                 '  (HUD|ClientSetHUD (Game|GetPlayerController 0)'
                 ' "' + BP_HUD + '_C"))')})
    call("compile_blueprint", {"blueprint": {"refPath": ruta}})
    call("compile_blueprint", {"blueprint": {"refPath": BP_HUD}})
    out["actor"] = ruta
    return out
