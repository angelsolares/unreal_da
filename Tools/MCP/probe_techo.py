import json
import math

CLARO = {"x": 44000.0, "y": -13650.0, "z": 320.0}
LARGO = 3000000.0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def traza(yaw, elev):
    y = math.radians(yaw)
    e = math.radians(elev)
    d = (math.cos(y) * math.cos(e), math.sin(y) * math.cos(e), math.sin(e))
    fin = {"x": CLARO["x"] + d[0] * LARGO, "y": CLARO["y"] + d[1] * LARGO,
           "z": CLARO["z"] + d[2] * LARGO}
    dist = call("editor_toolset.toolsets.scene.SceneTools.trace_world",
                {"start": CLARO, "end": fin})
    if dist is None:
        return None, None
    return dist, (CLARO["x"] + d[0] * dist, CLARO["y"] + d[1] * dist, CLARO["z"] + d[2] * dist)


def quien(p, r=500.0):
    box = {"min": {"x": p[0] - r, "y": p[1] - r, "z": p[2] - r},
           "max": {"x": p[0] + r, "y": p[1] + r, "z": p[2] + r}, "isValid": True}
    out = []
    for h in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                  {"name": "", "tag": "", "collision_channels": [], "bounds": box})[:10]:
        lab = call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": h})
        if lab.startswith("LI_") or lab in ("WaterZone", "SkyDomeMesh"):
            continue
        zona = h["refPath"].split("/")[-1].split(".")[0].split("_LevelInstance")[0] \
            .replace("L_DA_Malkuth_", "")
        out.append(lab + " [" + zona + "]")
    return out


def run():
    filas = []
    for yaw in [60, 75, 90, 105, 120]:
        # Busca la elevacion mas alta con impacto, con paso de 1 grado
        techo = None
        for e in range(2, 60):
            if traza(float(yaw), float(e)) [0] is not None:
                techo = e
        f = {"yaw": yaw, "techoDeg": techo}
        if techo:
            d, p = traza(float(yaw), float(techo))
            f["distM"] = round(d / 100)
            f["hitZ"] = round(p[2])
            f["quien"] = quien(p)
        filas.append(f)
    return {"techos": filas}
