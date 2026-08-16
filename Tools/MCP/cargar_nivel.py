import json

# Carga un mapa en el editor. Hace falta a menudo: el nivel actual cambia solo
# entre el maestro y los sublevels, y con un sublevel abierto NO hay Level
# Instances que abrir, asi que los scripts de otras zonas no encuentran nada.

NIVEL = "/Game/DarkAngels/Maps/L_DA_Malkuth_Master"


def run():
    execute_tool("editor_toolset.toolsets.scene.SceneTools.load_level",
                 json.dumps({"level_path": NIVEL}))
    return {"nivel": execute_tool("editor_toolset.toolsets.scene.SceneTools.get_current_level",
                                  json.dumps({}))["returnValue"]}
