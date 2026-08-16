import json
import math

CENTRO = (44000.0, -13650.0, 320.0)
SOL_YAW = -30.0      # azimut hacia el sol
SOL_ELEV = 38.0      # elevacion del sol


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def run():
    filas = []
    for pref in ["Claro_Cliff", "Claro_Abeto", "Claro_GateRock"]:
        for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                      {"name": pref, "tag": "", "collision_channels": []}):
            if "Claro" not in a["refPath"]:
                continue
            lab = call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})
            b = call("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": a})
            cx = (b["min"]["x"] + b["max"]["x"]) / 2.0
            cy = (b["min"]["y"] + b["max"]["y"]) / 2.0
            dx, dy = cx - CENTRO[0], cy - CENTRO[1]
            d = math.hypot(dx, dy)
            if d < 1.0:
                continue
            az = math.degrees(math.atan2(dy, dx))
            # diferencia angular con el azimut del sol, en [-180, 180]
            dif = (az - SOL_YAW + 180.0) % 360.0 - 180.0
            elev = math.degrees(math.atan2(b["max"]["z"] - CENTRO[2], d))
            # semiancho angular aproximado del actor visto desde el centro
            radio = max(b["max"]["x"] - b["min"]["x"], b["max"]["y"] - b["min"]["y"]) / 2.0
            semi = math.degrees(math.atan2(radio, d))
            if abs(dif) - semi > 35.0:
                continue          # muy lejos del sector del sol
            filas.append({
                "label": lab, "difAzim": round(dif), "semiAncho": round(semi),
                "distM": round(d / 100), "cima": round(b["max"]["z"]),
                "elev": round(elev, 1),
                "tapaElSol": elev > SOL_ELEV and abs(dif) - semi < 0,
                "cimaParaNoTapar": round(CENTRO[2] + d * math.tan(math.radians(SOL_ELEV))),
            })
    filas.sort(key=lambda r: -r["elev"])
    return {"n": len(filas), "tapan": [f for f in filas if f["tapaElSol"]],
            "resto": [f for f in filas if not f["tapaElSol"]][:12]}
