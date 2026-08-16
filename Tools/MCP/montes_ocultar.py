import json

# Abre el Level Instance indicado y apaga la visibilidad de sus montes de telon.
# Oculta, no borra: bVisible=False en el StaticMeshComponent, que se guarda y
# vale tanto en el editor como en juego.
#
# Editar las dos constantes antes de lanzar. Un solo ciclo edit/commit por LI:
# encadenar varios sobre el mismo Level Instance filtra un handle del .umap y
# a partir de ahi el guardado falla hasta reiniciar el editor.

ETIQUETA = "LI_13_PortalYesod"
SUBNIVEL = "L_DA_Malkuth_Yesod_Sub"


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def find(name):
    return call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": name, "tag": "", "collision_channels": []})


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def run():
    li = None
    for a in find("LI_"):
        if label(a) == ETIQUETA:
            li = a
            break
    if li is None:
        return {"error": "no encontrado " + ETIQUETA}

    call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance", {"level_instance": li})

    ocultados = []
    fallos = []
    for a in find("Monte"):
        if SUBNIVEL not in a["refPath"]:
            continue
        lab = label(a)
        for c in call("editor_toolset.toolsets.actor.ActorTools.get_components", {"actor": a}):
            if "StaticMeshComponent" not in c["refPath"]:
                continue
            call("editor_toolset.toolsets.object.ObjectTools.set_properties",
                 {"instance": c, "values": json.dumps({"bVisible": False})})
            v = json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                                {"instance": c, "properties": ["bVisible"]}))
            (ocultados if v["bVisible"] is False else fallos).append(lab)

    return {"li": ETIQUETA, "ocultados": len(ocultados), "fallos": fallos}
