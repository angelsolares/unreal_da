import json
import math

GAZEBO = {"x": 64000.0, "y": 16000.0, "z": 262.0}
LARGO = 3000000.0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def traza(yaw, elev):
    y = math.radians(yaw)
    e = math.radians(elev)
    d = (math.cos(y) * math.cos(e), math.sin(y) * math.cos(e), math.sin(e))
    fin = {"x": GAZEBO["x"] + d[0] * LARGO, "y": GAZEBO["y"] + d[1] * LARGO,
           "z": GAZEBO["z"] + d[2] * LARGO}
    return call("editor_toolset.toolsets.scene.SceneTools.trace_world",
                {"start": GAZEBO, "end": fin})


def run():
    filas = []
    for yaw in range(0, 360, 15):
        techo = None
        for e in [4, 8, 12, 16, 20, 25, 30, 40, 50, 60]:
            if traza(float(yaw), float(e)) is not None:
                techo = e
        filas.append({"yaw": yaw, "techoDeg": techo})
    flojos = [f for f in filas if f["techoDeg"] is None or f["techoDeg"] < 12]
    return {"agujeros": flojos, "perfil": filas}
