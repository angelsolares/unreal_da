import json

# Abre el Gazebo en edicion, deja la camara en la pose de aproximacion del
# jugador y enciende o apaga la rotonda.
#
# Sirve para localizar las columnas por diferencia de imagen: se captura con y
# sin rotonda y los pixeles que cambian son exactamente ella. Es mas fiable que
# adivinar por luma, y las trazas no valen porque un SkeletalMesh no colisiona.

ETIQUETA = "LI_05_RuinasGazebo"
SUBNIVEL = "L_DA_Malkuth_Gazebo_Sub"
VISIBLE = True
CAMARA = {"location": {"x": 64000.0, "y": 15700.0, "z": 470.0},
          "rotation": {"pitch": -3.0, "yaw": 90.0, "roll": 0.0},
          "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def run():
    for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                  {"name": "LI_", "tag": "", "collision_channels": []}):
        if label(a) == ETIQUETA:
            call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance",
                 {"level_instance": a})
            break

    call("EditorToolset.EditorAppToolset.SetCameraTransform", {"transform": CAMARA})

    for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                  {"name": "Gazebo_Rotonda", "tag": "", "collision_channels": []}):
        if SUBNIVEL not in a["refPath"] or label(a) != "Gazebo_Rotonda":
            continue
        for c in call("editor_toolset.toolsets.actor.ActorTools.get_components", {"actor": a}):
            if "MeshComponent" not in c["refPath"]:
                continue
            call("editor_toolset.toolsets.object.ObjectTools.set_properties",
                 {"instance": c, "values": json.dumps({"bVisible": VISIBLE})})
            return {"rotonda_visible": json.loads(call(
                "editor_toolset.toolsets.object.ObjectTools.get_properties",
                {"instance": c, "properties": ["bVisible"]}))["bVisible"]}
    return {"error": "no encontrada la rotonda"}
