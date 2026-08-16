import json
import math

# Ajuste del foco del cofre. Cenital no valia: quemaba la tapa y dejaba negra la
# cara frontal, que es justo la que se quiere enseniar (la de la cerradura).
# Se adelanta el foco hacia el centro de la explanada, que es adonde mira el
# cofre, y se baja: queda a unos 30 grados de elevacion en vez de a plomo.
#
# Requiere que la sesion de edicion del LI ya este abierta (la deja abierta
# `santuario_luz_cofre.py`). No vuelve a llamar a `edit_level_instance` porque
# encadenar ciclos edit/commit sobre el mismo LI acaba bloqueando el .umap.

ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"
LUZ = "Luz_Cofre"
COFRE = (44400.0, 48200.0)
CENTRO = (43940.0, 48000.0)   # la fuente

TAPA_Z = 79.0
ADELANTO = 210.0    # hacia el centro de la explanada
ALTURA = 115.0      # por encima de la tapa
INTENSIDAD = 230.0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def find(name):
    return call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": name, "tag": "", "collision_channels": []})


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    luz = None
    for a in find(LUZ):
        if label(a) == LUZ and a["refPath"].startswith(ASSET):
            luz = a
            break
    if luz is None:
        return {"error": "no se encontro " + LUZ + " en el asset (sesion de edicion cerrada?)"}

    dx, dy = CENTRO[0] - COFRE[0], CENTRO[1] - COFRE[1]
    n = math.sqrt(dx * dx + dy * dy)
    destino = {"x": round(COFRE[0] + dx / n * ADELANTO, 1),
               "y": round(COFRE[1] + dy / n * ADELANTO, 1),
               "z": round(TAPA_Z + ALTURA, 1)}

    call("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
        "actor": luz,
        "xform": {"location": destino,
                  "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                  "scale": {"x": 1.0, "y": 1.0, "z": 1.0}},
        "worldspace": True})

    out = {"xyz": [destino["x"], destino["y"], destino["z"]],
           "elevacion_grados": round(math.degrees(math.atan2(ALTURA, ADELANTO)), 1)}

    for c in call("editor_toolset.toolsets.actor.ActorTools.get_components", {"actor": luz}):
        if "LightComponent" not in c["refPath"]:
            continue
        call("editor_toolset.toolsets.object.ObjectTools.set_properties", {
            "instance": c, "values": json.dumps({"Intensity": INTENSIDAD})})
        out["luz"] = json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                                     {"instance": c,
                                      "properties": ["Intensity", "AttenuationRadius",
                                                     "Mobility", "CastShadows"]}))

    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
