import json
import math

# Pone un foco propio al cofre del Santuario, como ya lo tienen la llave del
# Mirador y el Fragmento del Gazebo. El cofre cayo en la sombra de la explanada
# y solo se distingue por el brillo morado de la cerradura.
#
# Convencion del Santuario, leida de sus dos luces existentes:
#   PointLight | Stationary | 6500 K | Candelas | radio 520
#   Luz_Altar    z=215  int 220  con sombras
#   Luz_Cassiel  z=320  int 110  sin sombras
#
# OJO CON EL SOLAPE: las luces **Stationary** tienen presupuesto. A partir de
# cuatro solapandose en un punto, las sobrantes caen a dinamicas y se pierde el
# lightmap. `Luz_Altar` esta a ~500 del cofre con radio 520, o sea que ya llega.
# Por eso el radio de esta se queda corto (420) y el script cuenta cuantas
# estacionarias cubren el punto antes de crear nada.

ETIQUETA = "LI_06_SantuarioMalkuth"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"

COFRE = "Santuario_Cofre"
LUZ = "Luz_Cofre"

ALTURA = 150.0        # por encima de la tapa del cofre
RADIO = 420.0
INTENSIDAD = 260.0


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def find(name):
    return call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": name, "tag": "", "collision_channels": []})


def label(a):
    return call("editor_toolset.toolsets.actor.ActorTools.get_label", {"actor": a})


def en_el_asset(nombre):
    """El actor real, no la copia instanciada en /Temp."""
    for a in find(nombre):
        if label(a) == nombre and a["refPath"].startswith(ASSET):
            return a
    return None


def componente_de_luz(actor):
    for c in call("editor_toolset.toolsets.actor.ActorTools.get_components", {"actor": actor}):
        if "LightComponent" in c["refPath"]:
            return c
    return None


def run():
    if call("EditorToolset.EditorAppToolset.IsPIERunning", {}):
        return {"error": "PIE esta corriendo: parar antes o los cambios se pierden"}

    li = None
    for a in find("LI_"):
        if label(a) == ETIQUETA:
            li = a
            break
    if li is None:
        return {"error": "no encontrado " + ETIQUETA}

    call("editor_toolset.toolsets.scene.SceneTools.edit_level_instance", {"level_instance": li})

    out = {}
    if en_el_asset(LUZ) is not None:
        return {"error": "ya existe " + LUZ + ", no se duplica"}

    cofre = en_el_asset(COFRE)
    if cofre is None:
        return {"error": "no se encontro " + COFRE + " en el asset"}

    b = call("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": cofre})
    destino = {"x": round((b["min"]["x"] + b["max"]["x"]) / 2.0, 1),
               "y": round((b["min"]["y"] + b["max"]["y"]) / 2.0, 1),
               "z": round(b["max"]["z"] + ALTURA, 1)}
    out["cofre"] = {"tapa_z": round(b["max"]["z"], 1), "base_z": round(b["min"]["z"], 1)}

    # Cuantas estacionarias cubren ya este punto (el presupuesto son 4).
    solapan = []
    for a in find("Luz"):
        nom = label(a)
        if not a["refPath"].startswith(ASSET):
            continue
        c = componente_de_luz(a)
        if c is None:
            continue
        p = json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                            {"instance": c, "properties": ["AttenuationRadius", "Mobility"]}))
        if p["Mobility"] != "Stationary":
            continue
        t = call("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": a})
        l = t["location"]
        d = math.sqrt((l["x"] - destino["x"]) ** 2 + (l["y"] - destino["y"]) ** 2 +
                      (l["z"] - destino["z"]) ** 2)
        if d < p["AttenuationRadius"]:
            solapan.append({"luz": nom, "dist": round(d)})
    out["estacionarias_que_ya_cubren"] = solapan

    luz = call("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_class", {
        "actor_type": {"refPath": "/Script/Engine.PointLight"},
        "name": LUZ,
        "xform": {"location": destino,
                  "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                  "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}})
    call("editor_toolset.toolsets.actor.ActorTools.set_label", {"actor": luz, "label": LUZ})

    c = componente_de_luz(luz)
    call("editor_toolset.toolsets.object.ObjectTools.set_properties", {
        "instance": c,
        "values": json.dumps({
            "Mobility": "Stationary",
            "Intensity": INTENSIDAD,
            "IntensityUnits": "Candelas",
            "AttenuationRadius": RADIO,
            "CastShadows": True,
            "SourceRadius": 12.0,
        })})

    out["luz"] = json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                                 {"instance": c,
                                  "properties": ["Intensity", "AttenuationRadius", "Mobility",
                                                 "CastShadows", "IntensityUnits"]}))
    out["luz"]["xyz"] = [destino["x"], destino["y"], destino["z"]]
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
