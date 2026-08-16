import json

# Abre en modo edicion el Level Instance cuyo label se indique.
ETIQUETA = "LI_01_JardinGeometrico"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def run():
    for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                  {"name": "LI_", "tag": "", "collision_channels": []}):
        if call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a}) != ETIQUETA:
            continue
        call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance", {"level_instance": a})
        return {"editando": a["refPath"]}
    return {"error": "no encontrado " + ETIQUETA}
