import json
import math

# Mide por que las dos luces del Mirador dibujan un circulo duro en la pared y
# las del Santuario no. Traza desde cada luz hacia abajo y en ocho direcciones
# para saber a que distancia tiene suelo y paredes.
#
# La sospecha: estan altas y pegadas al muro, con `SourceRadius` 0 —un punto
# perfecto, la caida mas dura posible— y un `AttenuationRadius` de 800 que llega
# de sobra hasta la pared. Las del Santuario van a 420-520 y en explanada
# abierta, sin nada cerca donde estamparse.

ETIQUETA = "LI_03_MiradorSariel"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub"
LUCES = ["Mirador_Luz_Llave", "Mirador_Luz_Estatua"]
ALCANCE = 1200.0
PROPS = ["Intensity", "AttenuationRadius", "SourceRadius", "SoftSourceRadius",
         "CastShadows", "LightFalloffExponent", "bUseInverseSquaredFalloff",
         "VolumetricScatteringIntensity", "Mobility"]


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

    out = {}
    for nombre in LUCES:
        a = en_el_asset(nombre)
        if a is None:
            out[nombre] = "no encontrada"
            continue
        p = at("get_actor_transform", {"actor": a})["location"]
        d = {"xyz": [round(p["x"]), round(p["y"]), round(p["z"])]}
        for c in at("get_components", {"actor": a}):
            if "LightComponent" in c["refPath"]:
                d.update(json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                                         {"instance": c, "properties": PROPS})))

        suelo = sc("trace_world", {"start": p, "end": {"x": p["x"], "y": p["y"], "z": p["z"] - ALCANCE}})
        d["al_suelo"] = round(suelo) if suelo is not None else "sin suelo"

        cerca = []
        for i in range(8):
            ang = math.radians(i * 45.0)
            fin = {"x": p["x"] + math.cos(ang) * ALCANCE,
                   "y": p["y"] + math.sin(ang) * ALCANCE, "z": p["z"]}
            h = sc("trace_world", {"start": p, "end": fin})
            if h is not None:
                cerca.append({"grados": i * 45, "dist": round(h)})
        cerca.sort(key=lambda x: x["dist"])
        d["paredes_mas_cercanas"] = cerca[:4]
        out[nombre] = d
    return out
