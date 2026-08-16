import json
import math

CAM = {"x": -73649.0, "y": 41996.0, "z": 262.0}
LARGO = 900000.0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def traza(yaw, elev):
    y = math.radians(yaw)
    e = math.radians(elev)
    d = (math.cos(y) * math.cos(e), math.sin(y) * math.cos(e), math.sin(e))
    fin = {"x": CAM["x"] + d[0] * LARGO, "y": CAM["y"] + d[1] * LARGO, "z": CAM["z"] + d[2] * LARGO}
    return call("editor_toolset.toolsets.scene.SceneTools.trace_world", {"start": CAM, "end": fin})


def run():
    malas = []
    todas = []
    yaw = 128.0
    while yaw <= 228.0:
        # Justo por encima del ojo: si el impacto esta lejos (o no hay), por ahi
        # se sigue viendo el plano de referencia desnudo.
        d = traza(yaw, 0.4)
        m = None if d is None else round(d / 100.0)
        todas.append({"yaw": round(yaw), "m": m})
        if m is None or m > 120:
            malas.append({"yaw": round(yaw), "m": m})
        yaw += 2.5
    return {"rendijas": malas, "barrido": todas}
