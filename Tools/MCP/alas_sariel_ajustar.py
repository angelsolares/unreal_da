import json
import math

# Ajusta tamano y sitio de las alas de Sariel midiendo, no a ojo.
#
# ESTADO DEL ENGANCHE: las alas cuelgan de su `SkeletalMeshComponent`, asi que
# le siguen si el actor se mueve. **Lo que NO hacen todavia es seguir al hueso**:
# el MCP no expone `AttachSocketName`, ni para leer ni para escribir, asi que el
# socket `Alas` —ya creado sobre `spine_05`— hay que asignarlo a mano en el
# desplegable "Parent Socket" del actor. Al hacerlo las alas saltaran a la
# posicion del hueso y habra que relanzar esto para recolocarlas.
#
# LA ORIENTACION: las alas se giran con el mismo yaw que Sariel, para que abran
# hacia sus costados. Van detras de el, en su -X local (los personajes miran a
# su +X), y a la altura de los omoplatos.

ETIQUETA = "LI_03_MiradorSariel"
ASSET = "/Game/DarkAngels/Maps/L_DA_Malkuth_Mirador_Sub"

ENVERGADURA = 230.0     # ancho total buscado, en unidades de mundo
ALTURA_RELATIVA = 0.74  # que fraccion de la altura de Sariel: los omoplatos
DETRAS = 18.0           # cuanto se retrasan respecto a su centro
# Las alas abren por su X local, asi que hay que cruzarlas 90 grados respecto a
# Sariel para que la envergadura vaya de hombro a hombro y no de pecho a espalda.
YAW_EXTRA = 90.0


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


def caja(a):
    b = at("get_actor_bounds", {"actor": a})
    return {"min": [round(b["min"][k], 1) for k in ("x", "y", "z")],
            "max": [round(b["max"][k], 1) for k in ("x", "y", "z")],
            "tamano": [round(b["max"][k] - b["min"][k], 1) for k in ("x", "y", "z")]}


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

    sariel = en_el_asset("NPC_Sariel")
    alas = en_el_asset("Sariel_Alas")
    if sariel is None or alas is None:
        return {"error": "falta NPC_Sariel o Sariel_Alas"}

    t_s = at("get_actor_transform", {"actor": sariel})
    b_s = at("get_actor_bounds", {"actor": sariel})
    yaw = t_s["rotation"]["yaw"]
    alto = b_s["max"]["z"] - b_s["min"]["z"]
    centro = [(b_s["min"]["x"] + b_s["max"]["x"]) / 2.0,
              (b_s["min"]["y"] + b_s["max"]["y"]) / 2.0]

    # Su espalda: hacia -X local, o sea al reves de su vector de avance.
    adelante = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
    destino = {"x": round(centro[0] - adelante[0] * DETRAS, 1),
               "y": round(centro[1] - adelante[1] * DETRAS, 1),
               "z": round(b_s["min"]["z"] + alto * ALTURA_RELATIVA, 1)}

    # Escala: se mide lo que ocupan AHORA y se corrige por regla de tres, que es
    # inmune a como se hereden las escalas del padre.
    antes = at("get_actor_bounds", {"actor": alas})
    t_a = at("get_actor_transform", {"actor": alas})
    ancho_actual = max(antes["max"]["x"] - antes["min"]["x"],
                       antes["max"]["y"] - antes["min"]["y"])
    factor = ENVERGADURA / ancho_actual if ancho_actual > 0.01 else 1.0
    nueva = round(t_a["scale"]["x"] * factor, 2)

    at("set_actor_transform", {"actor": alas,
                               "xform": {"location": t_a["location"],
                                         "rotation": {"pitch": 0.0, "yaw": yaw + YAW_EXTRA, "roll": 0.0},
                                         "scale": {"x": nueva, "y": nueva, "z": nueva}},
                               "worldspace": True})

    # EL PIVOTE DE LA MALLA ESTA EN LA BASE, como en todos los props de Tripo:
    # colocada por su origen, el ala CRECE HACIA ARRIBA y le sale de la cabeza.
    # Asi que se mide otra vez ya escalada, se calcula cuanto se desvia el centro
    # de la caja respecto del origen del actor, y se corrige con esa diferencia.
    ya = at("get_actor_bounds", {"actor": alas})
    t_a2 = at("get_actor_transform", {"actor": alas})
    desvio = {k: (ya["min"][k] + ya["max"][k]) / 2.0 - t_a2["location"][k] for k in ("x", "y", "z")}
    final = {k: round(destino[k] - desvio[k], 1) for k in ("x", "y", "z")}
    at("set_actor_transform", {"actor": alas,
                               "xform": {"location": final,
                                         "rotation": {"pitch": 0.0, "yaw": yaw + YAW_EXTRA, "roll": 0.0},
                                         "scale": {"x": nueva, "y": nueva, "z": nueva}},
                               "worldspace": True})
    destino = final

    out = {"sariel": {"yaw": round(yaw, 1), "alto": round(alto, 1), "caja": caja(sariel)},
           "alas": {"escala_antes": round(t_a["scale"]["x"], 2), "escala_ahora": nueva,
                    "ancho_antes": round(ancho_actual, 1),
                    "destino": [destino["x"], destino["y"], destino["z"]],
                    "caja": caja(alas)},
           "socket_pendiente": "asignar 'Alas' en Parent Socket, a mano"}

    if directo:
        call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ASSET]})
    else:
        sc("commit_level_instance", {"level_instance": li, "discard": False})
    out["sucio"] = call("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": ASSET})
    return out
