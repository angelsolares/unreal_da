import json

# Levanta la foto del Santuario antes de mover nada: por donde llega el jugador,
# como estan plantados el cofre y Cassiel, y que luz es la que quema.
#
# Lo que se busca de cada actor: la cota del SUELO justo debajo, para saber si
# esta enterrado o flotando, y su caja para saber cuanto ocupa.

ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"
ETIQUETA = "LI_06_SantuarioMalkuth"

ACTORES = ["PlayerStart", "Santuario_Cofre", "Santuario_Cofre_Abierto", "NPC_Cassiel",
           "Santuario_Fuente", "Interact_Cofre", "Interact_Cassiel"]
PROPS_LUZ = ["Intensity", "AttenuationRadius", "SourceRadius", "CastShadows",
             "VolumetricScatteringIntensity", "Mobility"]

# El salto de zona deja al jugador aqui (tabla de `hud_salto_zonas.py`).
LLEGADA = {"x": 43940.0, "y": 47600.0, "z": 118.0}


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo"}

    directo = sc("get_current_level", {}).startswith(ASSET)
    if not directo:
        li = None
        for a in sc("find_actors", {"name": "LI_", "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) == ETIQUETA:
                li = a
                break
        if li is None:
            return {"error": "no encontrado " + ETIQUETA}
        sc("edit_level_instance", {"level_instance": li})

    out = {"llegada_del_salto": [LLEGADA["x"], LLEGADA["y"], LLEGADA["z"]], "actores": {}}

    for nombre in ACTORES:
        for a in sc("find_actors", {"name": nombre, "tag": "", "collision_channels": []}):
            if at("get_label", {"actor": a}) != nombre or not a["refPath"].startswith(ASSET):
                continue
            t = at("get_actor_transform", {"actor": a})
            p = t["location"]
            b = at("get_actor_bounds", {"actor": a})
            # El suelo justo debajo, arrancando por encima de la cabeza para no
            # salir ya dentro de la propia malla.
            arriba = {"x": p["x"], "y": p["y"], "z": b["max"]["z"] + 50.0}
            d = sc("trace_world", {"start": arriba, "end": {"x": p["x"], "y": p["y"], "z": p["z"] - 600.0}})
            out["actores"][nombre] = {
                "xyz": [round(p["x"], 1), round(p["y"], 1), round(p["z"], 1)],
                "yaw": round(t["rotation"]["yaw"], 1),
                "base_caja": round(b["min"]["z"], 1),
                "alto": round(b["max"]["z"] - b["min"]["z"], 1),
                "suelo_debajo": round(arriba["z"] - d, 1) if d is not None else "sin suelo",
            }
            break

    luces = {}
    for a in sc("find_actors", {"name": "Luz", "tag": "", "collision_channels": []}):
        if not a["refPath"].startswith(ASSET):
            continue
        nombre = at("get_label", {"actor": a})
        for c in at("get_components", {"actor": a}):
            if "LightComponent" not in c["refPath"]:
                continue
            p = at("get_actor_transform", {"actor": a})["location"]
            d = json.loads(ot("get_properties", {"instance": c, "properties": PROPS_LUZ}))
            d["z"] = round(p["z"])
            d["tipo"] = c["refPath"].split(".")[-1]
            luces[nombre] = d
    out["luces"] = luces
    return out
