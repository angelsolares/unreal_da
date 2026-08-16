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
    filas = []
    for yaw in range(0, 360, 10):
        # +1.5 grados: justo por encima del ojo. Si no hay impacto, ese sector
        # del horizonte esta abierto al vacio.
        alto = traza(yaw, 1.5)
        # -0.3 grados: casi a ras. Impacto lejano = plano de referencia desnudo.
        bajo = traza(yaw, -0.3)
        filas.append({
            "yaw": yaw,
            "altoM": None if alto is None else round(alto / 100.0),
            "bajoM": None if bajo is None else round(bajo / 100.0),
        })
    return {"barrido": filas}
