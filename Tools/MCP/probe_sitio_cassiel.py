import json
import math

# Tantea donde plantar a Cassiel: a la izquierda del cofre visto por el jugador
# que llega, y sobre pavimento limpio.
#
# LATERALIDAD EN UNREAL, que ya nos mordio una vez: a yaw 90 el lado DERECHO es
# -X. O sea que con `adelante = (fx, fy)`, la derecha es `(-fy, fx)` y la
# izquierda `(fy, -fx)`. Ver la nota de lateralidad y proyeccion.
#
# De cada candidato interesa la cota del suelo y si tiene techo encima: el sitio
# actual de Cassiel da 296 de "suelo" al trazar desde muy arriba, lo que huele a
# roca por encima.

ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"
ETIQUETA = "LI_06_SantuarioMalkuth"

LLEGADA = (43940.0, 47600.0)
COFRE = (44400.0, 48200.0)
DISTANCIAS = [150.0, 200.0, 250.0, 300.0, 350.0]


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    if not sc("get_current_level", {}).startswith(ASSET):
        li = None
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == ETIQUETA:
                li = a
                break
        if li is None:
            return {"error": "no encontrado " + ETIQUETA}
        sc("edit_level_instance", {"level_instance": li})

    dx, dy = COFRE[0] - LLEGADA[0], COFRE[1] - LLEGADA[1]
    n = math.sqrt(dx * dx + dy * dy)
    adelante = (dx / n, dy / n)
    izquierda = (adelante[1], -adelante[0])

    out = {"adelante": [round(adelante[0], 3), round(adelante[1], 3)],
           "izquierda": [round(izquierda[0], 3), round(izquierda[1], 3)],
           "yaw_hacia_la_llegada": round(math.degrees(math.atan2(-dy, -dx)), 1),
           "candidatos": []}

    for d in DISTANCIAS:
        x = COFRE[0] + izquierda[0] * d
        y = COFRE[1] + izquierda[1] * d
        # Suelo: desde 400 hacia abajo, que es muy por encima del pavimento (13).
        suelo = sc("trace_world", {"start": {"x": x, "y": y, "z": 400.0},
                                   "end": {"x": x, "y": y, "z": -300.0}})
        # Techo: desde justo encima del suelo hacia arriba.
        techo = sc("trace_world", {"start": {"x": x, "y": y, "z": 60.0},
                                   "end": {"x": x, "y": y, "z": 1200.0}})
        out["candidatos"].append({
            "dist": d, "xy": [round(x, 1), round(y, 1)],
            "suelo_z": round(400.0 - suelo, 1) if suelo is not None else "sin suelo",
            "altura_libre": round(techo, 1) if techo is not None else "despejado"})
    return out
