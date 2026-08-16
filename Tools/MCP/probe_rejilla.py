import json
import math

LARGO = 3000000.0
SOL = (0.682, -0.394, 0.616)   # direccion HACIA el sol (yaw -30, elev 38)


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def traza(ini, d, largo=LARGO):
    fin = {"x": ini["x"] + d[0] * largo, "y": ini["y"] + d[1] * largo,
           "z": ini["z"] + d[2] * largo}
    return call("editor_toolset.toolsets.scene.SceneTools.trace_world",
                {"start": ini, "end": fin})


def run():
    puntos = []
    soleados = 0
    for i in range(7):
        for j in range(7):
            x = 40000.0 + i * 1500.0
            y = -18000.0 + j * 1600.0
            # Buscar el suelo: traza hacia abajo desde z alto
            arriba = {"x": x, "y": y, "z": 2500.0}
            dsuelo = traza(arriba, (0.0, 0.0, -1.0), 6000.0)
            if dsuelo is None:
                continue
            suelo = 2500.0 - dsuelo
            if suelo < -400.0 or suelo > 1200.0:
                continue      # no es la plaza (roca alta o hueco)
            ojo = {"x": x, "y": y, "z": suelo + 180.0}
            dsol = traza(ojo, SOL)
            sol = dsol is None
            if sol:
                soleados += 1
            puntos.append({"x": int(x), "y": int(y), "sueloZ": round(suelo),
                           "sol": sol, "bloqueoM": None if dsol is None else round(dsol / 100)})
    return {"nPuntos": len(puntos), "conSol": soleados,
            "porcentaje": None if not puntos else round(100.0 * soleados / len(puntos)),
            "puntos": puntos}
