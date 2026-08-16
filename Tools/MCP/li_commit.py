import json

ETIQUETA = "LI_03_MiradorSariel"
DESCARTAR = False


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def run():
    for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                  {"name": "LI_", "tag": "", "collision_channels": []}):
        if call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a}) != ETIQUETA:
            continue
        call("editor_toolset.toolsets.scene.SceneTools.commit_level_instance",
             {"level_instance": a, "discard": DESCARTAR})
        return {"commit": ETIQUETA, "descartar": DESCARTAR}
    return {"error": "no encontrado " + ETIQUETA}
