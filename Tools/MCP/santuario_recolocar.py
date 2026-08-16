import json
import math

# Recoloca la escena del Santuario mirando a la llegada del jugador, y baja la
# luz que quemaba.
#
# LA LUZ: `Luz_Rayo` era la unica de la zona, junto a la del cofre, con
# `VolumetricScatteringIntensity = 1`; las otras once estan a 0. Con 700 de
# intensidad y 1800 de radio, eso pinta un globo blanco enorme. No se apaga del
# todo —se llama Rayo y el haz es intencionado, va con la direccion de arte— sino
# que se le baja a un tercio de intensidad y a 0,15 de dispersion. La del cofre
# si va a 0, como el resto.
#
# LAS ORIENTACIONES: el frente del cofre es su -Y local, asi que su yaw es el
# angulo al objetivo MAS 90. Los personajes miran a su +X, asi que su yaw es el
# angulo tal cual.
#
# LA LATERALIDAD: a yaw 90 la derecha es -X. Con `adelante = (fx, fy)`, la
# izquierda es `(fy, -fx)`. Cassiel va 250 a la izquierda del cofre visto por
# quien llega.
#
# LA COTA: Cassiel estaba 57 unidades POR DEBAJO del pavimento, por eso no se le
# veian los pies. Su base cae 11,4 por debajo del origen del actor, asi que para
# apoyarlo en el suelo el actor va a `suelo + 11,4`.

ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Santuario_Sub"
ETIQUETA = "LI_06_SantuarioMalkuth"

LLEGADA = (43940.0, 47600.0)
COFRE = (44400.0, 48200.0)

CASSIEL = (44598.4, 48047.9)
SUELO_CASSIEL = 16.9
BASE_BAJO_ORIGEN = 11.4      # cuanto cae la base de Cassiel por debajo de su origen
LUZ_SOBRE_CASSIEL = 300.0

ADELANTO_LUZ_COFRE = 210.0   # la luz del cofre, por delante de su nueva cara
ALTURA_LUZ_COFRE = 194.0

LUCES = {
    "Luz_Rayo": {"VolumetricScatteringIntensity": 0.15, "Intensity": 350.0},
    "Luz_Cofre": {"VolumetricScatteringIntensity": 0.0},
}


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


def mover(actor, xyz, yaw=None):
    """set_actor_transform resetea escala y rotacion si no se le pasan las tres."""
    t = at("get_actor_transform", {"actor": actor})
    rot = dict(t["rotation"])
    if yaw is not None:
        rot["yaw"] = yaw
        rot["pitch"] = 0.0
        rot["roll"] = 0.0
    at("set_actor_transform", {"actor": actor,
                               "xform": {"location": {"x": xyz[0], "y": xyz[1], "z": xyz[2]},
                                         "rotation": rot, "scale": t["scale"]},
                               "worldspace": True})


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

    # --- el cofre y su gemelo abierto, encarando la llegada ---
    ang_cofre = math.degrees(math.atan2(LLEGADA[1] - COFRE[1], LLEGADA[0] - COFRE[0]))
    yaw_cofre = round(ang_cofre + 90.0, 1)
    for nombre in ("Santuario_Cofre", "Santuario_Cofre_Abierto"):
        a = en_el_asset(nombre)
        if a is None:
            out[nombre] = "no encontrado"
            continue
        t = at("get_actor_transform", {"actor": a})["location"]
        mover(a, [t["x"], t["y"], t["z"]], yaw_cofre)
        out[nombre] = {"yaw": yaw_cofre}
    out["angulo_a_la_llegada"] = round(ang_cofre, 1)

    # La luz del cofre se adelanta hacia su nueva cara.
    n = math.sqrt((LLEGADA[0] - COFRE[0]) ** 2 + (LLEGADA[1] - COFRE[1]) ** 2)
    hacia = ((LLEGADA[0] - COFRE[0]) / n, (LLEGADA[1] - COFRE[1]) / n)
    luz_cofre = en_el_asset("Luz_Cofre")
    if luz_cofre is not None:
        mover(luz_cofre, [round(COFRE[0] + hacia[0] * ADELANTO_LUZ_COFRE, 1),
                          round(COFRE[1] + hacia[1] * ADELANTO_LUZ_COFRE, 1),
                          ALTURA_LUZ_COFRE])

    # --- Cassiel: a la izquierda del cofre, con los pies en el suelo ---
    yaw_cassiel = round(math.degrees(math.atan2(LLEGADA[1] - CASSIEL[1],
                                                LLEGADA[0] - CASSIEL[0])), 1)
    z_cassiel = round(SUELO_CASSIEL + BASE_BAJO_ORIGEN, 1)
    npc = en_el_asset("NPC_Cassiel")
    if npc is not None:
        mover(npc, [CASSIEL[0], CASSIEL[1], z_cassiel], yaw_cassiel)
        b = at("get_actor_bounds", {"actor": npc})
        out["NPC_Cassiel"] = {"xyz": [CASSIEL[0], CASSIEL[1], z_cassiel],
                              "yaw": yaw_cassiel,
                              "base_resultante": round(b["min"]["z"], 1),
                              "suelo": SUELO_CASSIEL}

    # Su volumen de interaccion y su foco lo siguen.
    zona = en_el_asset("Interact_Cassiel")
    if zona is not None:
        mover(zona, [CASSIEL[0], CASSIEL[1], SUELO_CASSIEL])
    foco = en_el_asset("Luz_Cassiel")
    if foco is not None:
        mover(foco, [CASSIEL[0], CASSIEL[1], round(SUELO_CASSIEL + LUZ_SOBRE_CASSIEL, 1)])

    # --- las luces ---
    for nombre in LUCES:
        a = en_el_asset(nombre)
        if a is None:
            out[nombre] = "no encontrada"
            continue
        for c in at("get_components", {"actor": a}):
            if "LightComponent" not in c["refPath"]:
                continue
            for k in LUCES[nombre]:
                ot("set_properties", {"instance": c, "values": json.dumps({k: LUCES[nombre][k]})})
            out[nombre] = json.loads(ot("get_properties", {"instance": c, "properties": [
                "Intensity", "VolumetricScatteringIntensity", "AttenuationRadius"]}))

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
