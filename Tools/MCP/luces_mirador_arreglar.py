import json

# Quita el globo de niebla que dibujaban las dos luces del Mirador.
#
# LA CAUSA NO ERA LA PARED. Medido con trazas: la mas cercana esta a 432 y 545,
# lejos de sobra. Lo que se veia era `VolumetricScatteringIntensity = 1` con la
# niebla volumetrica del mapa: la luz se hace visible EN EL AIRE y dibuja una
# bola brillante alrededor del punto. En el Mirador canta porque la escena es
# oscura y la bola queda contra un fondo negro.
#
# Es el mismo remedio que se uso con el coloso del Jardin: la niebla volumetrica
# no la filtran los canales de luz, hay que apagarla luz por luz.
#
# De paso se les pone `SourceRadius`: con 0 la luz es un punto perfecto, que da
# el reflejo especular mas duro posible y bordes de sombra de navaja. Un radio
# de fuente real ablanda las dos cosas sin cambiar la iluminacion.
#
# NO se toca ni la intensidad ni el alcance: el problema era que se VEIA la
# bombilla, no que iluminara mal.

ETIQUETA = "LI_03_MiradorSariel"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub"

LUCES = ["Mirador_Luz_Llave", "Mirador_Luz_Estatua"]
VALORES = {"VolumetricScatteringIntensity": 0.0, "SourceRadius": 25.0}


def call(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def sc(t, a):
    return call("editor_toolset.toolsets.scene.SceneTools." + t, a)


def at(t, a):
    return call("editor_toolset.toolsets.actor.ActorTools." + t, a)


def ot(t, a):
    return call("editor_toolset.toolsets.object.ObjectTools." + t, a)


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

    out = {}
    for nombre in LUCES:
        a = en_el_asset(nombre)
        if a is None:
            out[nombre] = "no encontrada"
            continue
        for c in at("get_components", {"actor": a}):
            if "LightComponent" not in c["refPath"]:
                continue
            # Un campo por llamada: el setter se deja campos por el camino.
            for k in VALORES:
                ot("set_properties", {"instance": c, "values": json.dumps({k: VALORES[k]})})
            out[nombre] = json.loads(ot("get_properties", {"instance": c, "properties": [
                "VolumetricScatteringIntensity", "SourceRadius", "Intensity", "AttenuationRadius"]}))

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
