import json
import math

LARGO = 3000000.0
# Sol del Master: pitch -38, yaw 150 (direccion en la que VIAJA la luz).
# Mirar hacia el sol es la direccion contraria.
SOL_YAW = 150.0
SOL_PITCH = -38.0

# Puntos repartidos por la plaza de El Claro, a la altura del ojo.
PUNTOS = [
    ("centro", 44000.0, -13650.0, 320.0),
    ("norte", 44000.0, -11000.0, 320.0),
    ("sur", 44000.0, -16000.0, 320.0),
    ("este", 41500.0, -13650.0, 320.0),
    ("oeste", 46500.0, -13650.0, 320.0),
]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def dir_al_sol():
    y = math.radians(SOL_YAW)
    p = math.radians(SOL_PITCH)
    viaja = (math.cos(y) * math.cos(p), math.sin(y) * math.cos(p), math.sin(p))
    return (-viaja[0], -viaja[1], -viaja[2])


def run():
    d = dir_al_sol()
    filas = []
    for nombre, x, y, z in PUNTOS:
        ini = {"x": x, "y": y, "z": z}
        fin = {"x": x + d[0] * LARGO, "y": y + d[1] * LARGO, "z": z + d[2] * LARGO}
        dist = call("editor_toolset.toolsets.scene.SceneTools.trace_world",
                    {"start": ini, "end": fin})
        f = {"punto": nombre, "bloqueado": dist is not None,
             "distM": None if dist is None else round(dist / 100)}
        if dist:
            p = (x + d[0] * dist, y + d[1] * dist, z + d[2] * dist)
            f["hitZ"] = round(p[2])
            r = 500.0
            box = {"min": {"x": p[0] - r, "y": p[1] - r, "z": p[2] - r},
                   "max": {"x": p[0] + r, "y": p[1] + r, "z": p[2] + r}, "isValid": True}
            q = []
            for h in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                          {"name": "", "tag": "", "collision_channels": [], "bounds": box})[:10]:
                lab = call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": h})
                if lab.startswith("LI_") or lab in ("WaterZone", "SkyDomeMesh"):
                    continue
                q.append(lab)
            f["quien"] = q
        filas.append(f)
    return {"dirAlSol": [round(v, 3) for v in d],
            "yawAlSol": round(math.degrees(math.atan2(d[1], d[0])), 1),
            "elevAlSol": round(math.degrees(math.asin(d[2])), 1),
            "puntos": filas}
