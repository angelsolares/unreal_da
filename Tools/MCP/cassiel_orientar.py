import json
import math

# Corrige la orientacion de Cassiel, que quedo 90 grados girado.
#
# El fallo: al recolocarlo se calculo su yaw como `atan2(dy, dx)`, dando por
# hecho que los personajes miran a su +X local. **Miran a su +Y.** Se comprueba
# con su propia caja: el eje ANCHO de un humano es el de los hombros, asi que si
# el ancho cae en X, el que mira es el Y.
#
# La formula buena, para que su frente apunte a (dx, dy):
#     yaw = atan2(-dx, dy)
#
# Sariel se libro porque su yaw venia puesto a mano de una sesion anterior.

ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"
ETIQUETA = "LI_06_SantuarioMalkuth"

NPC = "NPC_Cassiel"
LLEGADA = (43940.0, 47600.0)   # por donde aparece el jugador al saltar a la zona


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def en_el_asset(nombre):
    for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
        if at("get_label", {"actor": a}) == nombre and a["refPath"].startswith(ASSET):
            return a
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    directo = sc("get_current_level", {}).startswith(ASSET)
    li = None
    if not directo:
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == ETIQUETA:
                li = a
                break
        if li is None:
            return {"error": "no encontrado " + ETIQUETA}
        sc("edit_level_instance", {"level_instance": li})

    npc = en_el_asset(NPC)
    if npc is None:
        return {"error": "no se encontro " + NPC}

    t = at("get_actor_transform", {"actor": npc})
    b = at("get_actor_bounds", {"actor": npc})
    p = t["location"]

    dx, dy = LLEGADA[0] - p["x"], LLEGADA[1] - p["y"]
    yaw = round(math.degrees(math.atan2(-dx, dy)), 1)

    at("set_actor_transform", {"actor": npc,
                               "xform": {"location": p,
                                         "rotation": {"pitch": 0.0, "yaw": yaw, "roll": 0.0},
                                         "scale": t["scale"]},
                               "worldspace": True})

    b2 = at("get_actor_bounds", {"actor": npc})
    ancho_x = b2["max"]["x"] - b2["min"]["x"]
    ancho_y = b2["max"]["y"] - b2["min"]["y"]
    # Sus hombros tienen que quedar PERPENDICULARES a la linea que le une con la
    # llegada. Si mira casi de frente a ese punto, el eje ancho sera el otro.
    out = {"yaw_antes": round(t["rotation"]["yaw"], 1), "yaw_ahora": yaw,
           "caja_ahora": [round(ancho_x, 1), round(ancho_y, 1)],
           "eje_hombros": "X" if ancho_x > ancho_y else "Y"}

    # Su volumen de interaccion y su foco no llevan rotacion, no hay que tocarlos.
    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
