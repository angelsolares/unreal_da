import json
import math

CLARO = {"x": 44000.0, "y": -13650.0, "z": 320.0}
GAZEBO = {"x": 64000.0, "y": 16000.0, "z": 262.0}
LARGO = 3000000.0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def traza(cam, yaw, elev):
    y = math.radians(yaw)
    e = math.radians(elev)
    d = (math.cos(y) * math.cos(e), math.sin(y) * math.cos(e), math.sin(e))
    fin = {"x": cam["x"] + d[0] * LARGO, "y": cam["y"] + d[1] * LARGO, "z": cam["z"] + d[2] * LARGO}
    return call("editor_toolset.toolsets.scene.SceneTools.trace_world", {"start": cam, "end": fin})


def perfil(cam, yaws):
    """Para cada yaw, la elevacion mas alta a la que todavia hay geometria."""
    out = []
    for yaw in yaws:
        techo = None
        for e in range(2, 76, 4):
            if traza(cam, float(yaw), float(e)) is not None:
                techo = e
        out.append({"yaw": yaw, "techoDeg": techo})
    return out


def run():
    return {
        "desdeElClaro": perfil(CLARO, [60, 75, 90, 105, 120]),
        "desdeElGazebo": perfil(GAZEBO, [180, 195, 210, 225, 240, 255]),
    }
